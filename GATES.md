# Submission gates

Every submission (PR) must pass four mechanical gates before a human reviewer
looks at it. The gates are ordered cheapest-first.

| # | Gate | Tool | Enforces | On failure |
|---|------|------|----------|------------|
| 1 | **Sorry lint** | `scripts/check_no_sorry.sh` | no `sorry`/`admit` | reject (advisory; gate 2 is authoritative) |
| 2 | **Compile** | `lake build` | the Lean actually type-checks | reject |
| 3 | **Axiom** | `scripts/Checker.lean` | no axioms beyond `propext`, `Classical.choice`, `Quot.sound` | reject |
| 4 | **Link completeness** | `scripts/check_links.py` | every prose statement is linked to an existing Lean decl, and every link resolves | reject |

Plus one **advisory** pass, not a reject:

* **Hypothesis audit** (`scripts/Checker.lean`) — prints the propositional
  hypotheses of every exported theorem. This is the defense against the
  *vacuity-via-hypothesis* loophole: a theorem `(h : H) : P` is axiom-clean and
  `sorry`-free yet says nothing if `H` does the real work. The audit surfaces
  every `H` (the `H → P` antecedent form) so the human reviewer can judge whether
  a result is genuinely unconditional. Axiom-cleanliness alone cannot catch this.

## Why these four

Compile + no-`sorry` + axiom-clean is what the existing Lean quantum libraries do
(at most). It is **not sufficient**: a submission can pass all three and still
have flagship theorems that are conditional on unproven assumed inputs (observed
in the wild). Gate 4 + the hypothesis audit close that hole mechanically by
forcing conditionality into the prose, where the link check and reviewer act on it.

## The linking contract

* Mark each public result with `@[qlean_export]` (see `Qlean/Meta/Export.lean`).
* In `blueprint/src/content.tex`, every `definition`/`theorem`/`lemma`/
  `proposition`/`corollary` must contain a `\lean{Qlean.Fully.Qualified.Name}`
  naming its Lean counterpart.
* `scripts/Checker.lean` writes the list of exported names to
  `build/qlean_exports.txt`; `check_links.py` checks completeness + resolution
  against it.

## Run locally

```sh
source "$HOME/.elan/env"
bash scripts/check_no_sorry.sh Qlean          # gate 1
lake build                                     # gate 2
lake env lean scripts/Checker.lean             # gate 3 + audit + export dump
python3 scripts/check_links.py                 # gate 4
```

## What stays human

The gates verify *form*, never *faithfulness*. A reviewer still confirms that
each Lean statement is a correct formalization of its prose — especially
**definitions** (a wrong definition silently poisons everything downstream) and
any **hypotheses** flagged by the audit.
