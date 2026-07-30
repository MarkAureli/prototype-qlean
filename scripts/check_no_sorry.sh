#!/usr/bin/env bash
# Fast sorry lint (gate 1, advisory).
#
# The AXIOM GATE is authoritative — `sorry` compiles to `sorryAx`, which the
# axiom check rejects — but this grep gives fast, precise, line-level feedback
# before the (slower) build + checker run.
#
# Usage: scripts/check_no_sorry.sh [DIR]   (default: Qlean)
set -euo pipefail
target="${1:-Qlean}"

# Match `sorry`/`admit` as whole words. (Crude: may flag the words inside
# comments; the authoritative gate is the axiom check.)
if violations=$(grep -rInwE 'sorry|admit' "$target" --include='*.lean'); then
  echo "✗ SORRY GATE FAILED — found sorry/admit:"
  echo "$violations"
  exit 1
fi
echo "✓ SORRY GATE passed: no sorry/admit in ${target}/"
