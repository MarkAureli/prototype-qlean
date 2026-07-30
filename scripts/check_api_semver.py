#!/usr/bin/env python3
"""Signature-based semver gate for the core library.

Core's public API = the set of CORE `@[qlean_export]` declarations and their type
signatures (dumped to `build/qlean_core_api.txt` by `Checker.lean`; Contrib is
excluded). This gate diffs the current API against the committed baseline
(`core-api.baseline.txt`) and enforces that the `VERSION` bump matches the change:

  * a removed or signature-changed core decl  -> MAJOR bump required
  * only additions                            -> MINOR (or MAJOR) bump required
  * identical                                 -> no bump required

Proof-only changes leave signatures untouched, so they need no bump. At release,
regenerate the baseline with `scripts/update_api_baseline.sh`.
"""
import pathlib
import re
import sys


def parse_api(text):
    api = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, typ = line.partition(" : ")
        if sep:
            api[name.strip()] = typ.strip()
    return api


def parse_semver(text):
    m = re.search(r"([0-9]+)\.([0-9]+)\.([0-9]+)", text)
    return tuple(int(x) for x in m.groups()) if m else None


def bump_level(old, new):
    if new == old:
        return "none"
    if new < old:
        return "invalid"
    if new[0] > old[0]:
        return "major"
    if new[1] > old[1]:
        return "minor"
    return "patch"


base_path = pathlib.Path("core-api.baseline.txt")
cur_path = pathlib.Path("build/qlean_core_api.txt")
ver_path = pathlib.Path("VERSION")

if not cur_path.exists():
    sys.exit("semver gate: build/qlean_core_api.txt missing (run Checker.lean first)")
if not base_path.exists():
    sys.exit("semver gate: core-api.baseline.txt missing")

base_text = base_path.read_text()
base = parse_api(base_text)
cur = parse_api(cur_path.read_text())

removed = sorted(set(base) - set(cur))
added = sorted(set(cur) - set(base))
changed = sorted(n for n in (set(base) & set(cur)) if base[n] != cur[n])

if removed or changed:
    required = "major"
elif added:
    required = "minor"
else:
    required = "patch"

cur_ver = parse_semver(ver_path.read_text()) if ver_path.exists() else None
base_ver = None
for line in base_text.splitlines():
    if "version:" in line:
        base_ver = parse_semver(line)
        break

print(f"core API: {len(cur)} decls | +{len(added)} -{len(removed)} ~{len(changed)}")
for n in added:
    print(f"  + {n}")
for n in removed:
    print(f"  - {n}")
for n in changed:
    print(f"  ~ {n}")
print(f"required bump: {required} | baseline {base_ver} -> VERSION {cur_ver}")

if required == "patch":
    print("✓ SEMVER GATE: core API unchanged; no version bump required.")
    sys.exit(0)

if cur_ver is None or base_ver is None:
    sys.exit("✗ SEMVER GATE: missing/invalid VERSION or baseline version header.")

actual = bump_level(base_ver, cur_ver)
ok = (required == "minor" and actual in ("minor", "major")) or \
     (required == "major" and actual == "major")

if ok:
    print(f"✓ SEMVER GATE: {required} core-API change with a {actual} VERSION bump.")
    sys.exit(0)

print(f"✗ SEMVER GATE FAILED: a {required.upper()} core-API change requires a "
      f"{required} VERSION bump (got '{actual}'). Bump VERSION accordingly "
      f"(baseline is refreshed at release via scripts/update_api_baseline.sh).")
sys.exit(1)
