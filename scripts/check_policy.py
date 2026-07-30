#!/usr/bin/env python3
"""Contribution-policy gate (role-based structural enforcement).

Runs UNTAMPERABLY from the base branch via `pull_request_target`, using only
metadata: the PR author's role and the list of changed filenames. It never
checks out or executes the PR's code (that is the `pull_request_target`
footgun, and we avoid it).

Policy:
  * Maintainers (repo role >= Maintain, or the repo OWNER) may open ANY PR.
  * Non-maintainers may open *Contrib content* PRs only. Every changed file must be:
      - `Qlean/Contrib/**/*.lean` with PascalCase path segments, or
      - `Qlean/Contrib.lean` (the contrib aggregator — where they wire their import), or
      - `blueprint/src/contrib/**/*.tex` (their contribution prose).
    A PR that adds/changes Contrib Lean must also *add* a fresh contrib .tex file.
    Everything else — the core library (`Qlean.lean`, `Qlean/Core/**`,
    `Qlean/Meta/**`), scripts, CI workflows, lakefile, LICENSE — is
    maintainer-only. Core grows only by maintainer promotion. In particular a
    non-maintainer cannot edit the checks, the core, or smuggle Lean content in
    under a non-conforming name; this job runs from the base branch so the PR
    cannot weaken it.

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

# Contrib Lean module: PascalCase segments under Qlean/Contrib/, PascalCase file.
CONTRIB_LEAN_RE = re.compile(r"^Qlean/Contrib/(?:[A-Z][A-Za-z0-9]*/)*[A-Z][A-Za-z0-9]*\.lean$")
# Contribution prose: a fresh .tex under blueprint/src/contrib/.
CONTRIB_TEX_RE = re.compile(r"^blueprint/src/contrib/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+\.tex$")


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
    if f == "Qlean/Contrib.lean":
        return None  # contrib aggregator — contributors wire their import here
    if f.startswith("Qlean/Contrib/"):
        if not f.endswith(".lean"):
            return "only .lean files are allowed under Qlean/Contrib/"
        if not CONTRIB_LEAN_RE.match(f):
            return "bad name — must be Qlean/Contrib/<PascalCase>/.../<PascalCase>.lean"
        return None
    if f.startswith("blueprint/"):
        if not CONTRIB_TEX_RE.match(f):
            return ("contribution prose must be a fresh blueprint/src/contrib/<Name>.tex "
                    "(core prose and other blueprint files are maintainer-only)")
        return None
    if f == "Qlean.lean" or f.startswith("Qlean/"):
        return "core / library infra — maintainer-only (contributions go in Qlean/Contrib/)"
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

    # A contribution that adds/changes Contrib Lean must ship a fresh prose file.
    contrib_lean = [f for (_s, f) in files if f.startswith("Qlean/Contrib/") and f.endswith(".lean")]
    if contrib_lean:
        fresh_tex = [f for (s, f) in files if s == "added" and CONTRIB_TEX_RE.match(f)]
        if not fresh_tex:
            print("✗ POLICY GATE FAILED — a contribution must include a fresh prose file:")
            print("  add a new blueprint/src/contrib/<Name>.tex documenting your result,")
            print("  with at least one \\lean{Qlean.Contrib...} link to your submitted code.")
            return 1

    print(f"✓ POLICY GATE: content PR — all {len(files)} changed file(s) conform.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
