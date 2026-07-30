#!/usr/bin/env python3
"""Link-completeness gate (gate 3).

Enforces the two mechanical rules that make prose <-> Lean linking un-fudgeable:

  1. COMPLETENESS: every formal environment (definition/theorem/lemma/
     proposition/corollary) in the blueprint must contain at least one
     `\\lean{...}` link. Unlinked prose -> reject.
  2. RESOLUTION: every `\\lean{Name}` must name a declaration that is actually
     exported from the Lean library (read from build/qlean_exports.txt).
     A dangling or misspelled link -> reject.

Usage: scripts/check_links.py [TEX] [EXPORTS]
  TEX      default: blueprint/src/content.tex
  EXPORTS  default: build/qlean_exports.txt   (written by scripts/Checker.lean)
"""
import re
import sys
import pathlib

tex_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("blueprint/src/content.tex")
exports_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("build/qlean_exports.txt")

FORMAL_ENVS = ("definition", "theorem", "lemma", "proposition", "corollary")


def strip_comments(s: str) -> str:
    # Drop TeX line comments (a % not preceded by a backslash).
    return re.sub(r"(?<!\\)%.*", "", s)


if not tex_path.exists():
    sys.exit(f"link gate: tex file not found: {tex_path}")

text = strip_comments(tex_path.read_text())

if exports_path.exists():
    exports = {ln.strip() for ln in exports_path.read_text().splitlines() if ln.strip()}
else:
    sys.exit(f"link gate: exports file not found: {exports_path} "
             f"(run `lake env lean scripts/Checker.lean` first)")

lean_re = re.compile(r"\\lean\{([^}]*)\}")
label_re = re.compile(r"\\label\{([^}]*)\}")
env_re = re.compile(r"\\begin\{(%s)\}(.*?)\\end\{\1\}" % "|".join(FORMAL_ENVS), re.DOTALL)

errors = []

# Rule 1: completeness — each formal environment carries a \lean{} link.
for m in env_re.finditer(text):
    env, body = m.group(1), m.group(2)
    label = label_re.search(body)
    tag = label.group(1) if label else "(unlabelled)"
    names = [n.strip() for n in lean_re.findall(body)]
    if not names:
        errors.append(f"UNLINKED  <{env}> {tag}: no \\lean{{...}} link.")
    for name in names:
        if name not in exports:
            errors.append(f"BAD LINK  <{env}> {tag}: \\lean{{{name}}} is not an exported declaration.")

# Rule 2: resolution — every \lean{} anywhere resolves (catches links outside envs too).
all_refs = [n.strip() for n in lean_re.findall(text)]
for name in all_refs:
    if name not in exports:
        errors.append(f"BAD LINK  \\lean{{{name}}}: not an exported declaration.")

if errors:
    print("✗ LINK GATE FAILED:")
    for e in sorted(set(errors)):
        print("  " + e)
    sys.exit(1)

print(f"✓ LINK GATE passed: every formal environment is linked; "
      f"all {len(set(all_refs))} \\lean{{}} reference(s) resolve.")
