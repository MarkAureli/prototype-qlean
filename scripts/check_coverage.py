#!/usr/bin/env python3
"""Coverage gate — reject unimported Lean files.

Every `Qlean/**/*.lean` file must be transitively imported from the library root
`Qlean.lean`; otherwise the axiom gate (which scans only the imported
environment) never sees it, and an orphan module could smuggle in a `sorry` or a
stray axiom unchecked.

`scripts/Checker.lean` writes `build/qlean_modules.txt` — the set of Qlean.*
modules actually loaded by `import Qlean`. This script compares that against the
files on disk and rejects any that are not loaded.

Usage: scripts/check_coverage.py   (run after `lake env lean scripts/Checker.lean`)
"""
import pathlib
import sys

loaded_path = pathlib.Path("build/qlean_modules.txt")
if not loaded_path.exists():
    sys.exit("coverage gate: build/qlean_modules.txt missing "
             "(run `lake env lean scripts/Checker.lean` first)")

loaded = {ln.strip() for ln in loaded_path.read_text().splitlines() if ln.strip()}

orphans = []
for p in sorted(pathlib.Path("Qlean").rglob("*.lean")):
    module = str(p.with_suffix("")).replace("/", ".")
    if module not in loaded:
        orphans.append((str(p), module))

if orphans:
    print("✗ COVERAGE GATE FAILED — unimported Lean file(s) (not reachable from Qlean.lean):")
    for path, module in orphans:
        print(f"  {path}  (module {module})")
    print("Add `import <Module>` to Qlean.lean (or a parent module) so the axiom gate covers it.")
    sys.exit(1)

n = len(list(pathlib.Path("Qlean").rglob("*.lean")))
print(f"✓ COVERAGE GATE: all {n} Qlean/**/*.lean file(s) are imported.")
