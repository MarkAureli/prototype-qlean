#!/usr/bin/env python3
"""One-way import gate: Core must never import Contrib.

The core layer (`Qlean/Core.lean` and everything under `Qlean/Core/`) must not
`import Qlean.Contrib…`. This keeps core self-contained — promotable, separately
versionable, and un-entangled from contributed content. Contrib freely imports
Core; the reverse is forbidden.

Usage: scripts/check_import_direction.py
"""
import pathlib
import re
import sys

IMPORT_CONTRIB = re.compile(r"^\s*(?:public\s+|private\s+)?import\s+Qlean\.Contrib(?:\.|\s|$)")


def is_core_layer(path: str) -> bool:
    return path == "Qlean/Core.lean" or path.startswith("Qlean/Core/")


violations = []
for p in sorted(pathlib.Path("Qlean").rglob("*.lean")):
    sp = str(p)
    if not is_core_layer(sp):
        continue
    for i, line in enumerate(p.read_text().splitlines(), 1):
        if IMPORT_CONTRIB.match(line):
            violations.append((sp, i, line.strip()))

if violations:
    print("✗ IMPORT-DIRECTION GATE FAILED — core must not import Contrib:")
    for path, ln, text in violations:
        print(f"  {path}:{ln}: {text}")
    print("Core is the stable foundation; move the dependency, or promote the "
          "Contrib content into Core.")
    sys.exit(1)

print("✓ IMPORT-DIRECTION GATE: no core file imports Qlean.Contrib.")
