#!/usr/bin/env python3
"""Link gate — prose <-> Lean.

Scans every `blueprint/src/**/*.tex` and enforces:

  (a) every formal environment (definition/theorem/lemma/proposition/corollary)
      contains at least one `\\lean{...}` link;
  (b) every `\\lean{...}` names a real exported declaration; and
  (c) every *contribution* tex (`blueprint/src/contrib/**`) references at least one
      contributed declaration — `\\lean{Qlean.Contrib...}`.

Not every Lean declaration needs prose: a theorem's proof may be split into
technical lemmata that need no narration. Only the reverse (prose -> Lean) links
are required, plus the one-anchor rule (c) per contribution.

Usage: scripts/check_links.py [BLUEPRINT_DIR] [EXPORTS_FILE]
"""
import pathlib
import re
import sys

bp_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("blueprint/src")
exports_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("build/qlean_exports.txt")

FORMAL_ENVS = ("definition", "theorem", "lemma", "proposition", "corollary")
lean_re = re.compile(r"\\lean\{([^}]*)\}")
label_re = re.compile(r"\\label\{([^}]*)\}")
env_re = re.compile(r"\\begin\{(%s)\}(.*?)\\end\{\1\}" % "|".join(FORMAL_ENVS), re.DOTALL)


def strip_comments(s: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", s)


if not exports_path.exists():
    sys.exit(f"link gate: exports file not found: {exports_path} (run Checker.lean first)")
exports = {ln.strip() for ln in exports_path.read_text().splitlines() if ln.strip()}

tex_files = sorted(bp_dir.rglob("*.tex"))
errors = []
total_refs = 0

for tex in tex_files:
    rel = str(tex).replace("\\", "/")
    text = strip_comments(tex.read_text())
    refs = [n.strip() for n in lean_re.findall(text)]
    total_refs += len(refs)

    # (a) every formal environment links to Lean.
    for m in env_re.finditer(text):
        env, body = m.group(1), m.group(2)
        lab = label_re.search(body)
        tag = lab.group(1) if lab else "(unlabelled)"
        if not lean_re.search(body):
            errors.append(f"{rel}: <{env}> {tag}: no \\lean{{...}} link.")

    # (b) every reference resolves to an exported declaration.
    for n in refs:
        if n not in exports:
            errors.append(f"{rel}: \\lean{{{n}}}: not an exported declaration.")

    # (c) a contribution tex must anchor to at least one contributed declaration.
    if "blueprint/src/contrib/" in rel:
        if not any(n.startswith("Qlean.Contrib.") and n in exports for n in refs):
            errors.append(f"{rel}: a contribution's prose must reference at least one "
                          f"submitted declaration — \\lean{{Qlean.Contrib...}}.")

if errors:
    print("✗ LINK GATE FAILED:")
    for e in sorted(set(errors)):
        print("  " + e)
    sys.exit(1)

print(f"✓ LINK GATE: {len(tex_files)} tex file(s); every formal environment linked; "
      f"all {total_refs} \\lean{{}} reference(s) resolve.")
