#!/usr/bin/env python3
"""Contribution-policy gate (role-based structural enforcement).

Runs UNTAMPERABLY from the base branch via `pull_request_target`, using only
metadata: the PR author's role and the list of changed filenames. It never
checks out or executes the PR's code (that is the `pull_request_target`
footgun, and we avoid it).

Policy:
  * Maintainers (repo role >= Maintain, or the repo OWNER) may open ANY PR.
  * Non-maintainers may open *content* PRs only. Every changed file must be:
      - `Qlean.lean` (the library root import file), or
      - `Qlean/**/*.lean` with PascalCase path segments, EXCEPT `Qlean/Meta/**`
        (harness infra), or
      - `blueprint/src/**/*.tex`.
    Everything else — scripts, CI workflows, lakefile, LICENSE, Qlean/Meta —
    is maintainer-only. In particular a non-maintainer cannot open a PR that
    edits the checks (this file, the workflows) *or* smuggles Lean content in
    under a non-conforming name: both are rejected here, and this job runs from
    the base branch so the PR cannot weaken it.

Local test hooks (never set in CI):
  POLICY_TEST_ROLE = maintainer | contributor   # skip the API role lookup
  FILES = "<status> <path>\\n<status> <path>..."  # skip the API file lookup
"""
import json
import os
import re
import subprocess
import sys

REPO = os.environ.get("REPO", "")
AUTHOR = os.environ.get("PR_AUTHOR", "")
PR = os.environ.get("PR_NUMBER", "")
ASSOC = os.environ.get("PR_ASSOC", "")

# Content Lean module: PascalCase segments under Qlean/, ending in a PascalCase file.
LEAN_RE = re.compile(r"^Qlean/(?:[A-Z][A-Za-z0-9]*/)*[A-Z][A-Za-z0-9]*\.lean$")
# Blueprint prose: any .tex under blueprint/src/.
TEX_RE = re.compile(r"^blueprint/src/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+\.tex$")


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def is_maintainer():
    forced = os.environ.get("POLICY_TEST_ROLE")
    if forced:
        return forced == "maintainer", f"test-role={forced}"
    if ASSOC == "OWNER":
        return True, "author_association=OWNER"
    code, out, err = run(["gh", "api", f"repos/{REPO}/collaborators/{AUTHOR}/permission"])
    if code != 0:
        # Fail closed: if we cannot confirm the role, treat as a non-maintainer.
        return False, f"role lookup failed -> non-maintainer ({err.strip()[:80]})"
    role = (json.loads(out).get("role_name") or "").lower()
    return role in ("admin", "maintain"), f"role={role or 'none'}"


def changed_files():
    if "FILES" in os.environ:
        lines = [l for l in os.environ["FILES"].splitlines() if l.strip()]
    else:
        code, out, err = run(["gh", "api", "--paginate",
                              f"repos/{REPO}/pulls/{PR}/files",
                              "--jq", '.[] | .status + " " + .filename'])
        if code != 0:
            print(f"::error::could not list PR files: {err.strip()}")
            sys.exit(2)
        lines = [l for l in out.splitlines() if l.strip()]
    out = []
    for l in lines:
        status, _, name = l.partition(" ")
        out.append((status, name))
    return out


def violation(f):
    """Reason a non-maintainer may not touch `f`, or None if it is allowed content."""
    if f == "Qlean.lean":
        return None
    if f.startswith("Qlean/Meta/"):
        return "harness infra (Qlean/Meta/**) — maintainer-only"
    if f.startswith("Qlean/"):
        if not f.endswith(".lean"):
            return "only .lean files are allowed under Qlean/"
        if not LEAN_RE.match(f):
            return "bad name/location — must be Qlean/<PascalCase>/.../<PascalCase>.lean"
        return None
    if f.startswith("blueprint/"):
        if not TEX_RE.match(f):
            return "blueprint files must be blueprint/src/**/*.tex"
        return None
    return "non-content path — maintainer-only"


def main():
    maint, why = is_maintainer()
    print(f"author={AUTHOR!r}  maintainer={maint}  ({why})")
    if maint:
        print("✓ POLICY GATE: maintainer — structural rules waived.")
        return 0

    files = changed_files()
    if not files:
        print("✓ POLICY GATE: no files changed.")
        return 0

    bad = [(f, r) for (_s, f) in files for r in [violation(f)] if r]
    if bad:
        print("✗ POLICY GATE FAILED — non-maintainers may open content PRs only:")
        for f, r in bad:
            print(f"  {f}: {r}")
        print("A maintainer must make this change, or restructure it as a content PR.")
        return 1

    print(f"✓ POLICY GATE: content PR — all {len(files)} changed file(s) conform.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
