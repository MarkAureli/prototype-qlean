# Submission gates

Every submission (PR) must pass four mechanical gates before a human reviewer
looks at it. The gates are ordered cheapest-first.

| # | Gate | Tool | Enforces | On failure |
|---|------|------|----------|------------|
| 1 | **Sorry lint** | `scripts/check_no_sorry.sh` | no `sorry`/`admit` | reject (advisory; gate 2 is authoritative) |
| 2 | **Compile** | `lake build` | the Lean actually type-checks | reject |
| 3 | **Axiom** | `scripts/Checker.lean` | no axioms beyond `propext`, `Classical.choice`, `Quot.sound` | reject |
| 4 | **Coverage** | `scripts/check_coverage.py` | every `Qlean/**/*.lean` is imported from `Qlean.lean` (no orphan modules the axiom gate can't see) | reject |
| 5 | **Link completeness** | `scripts/check_links.py` | every prose statement is linked to an existing Lean decl, and every link resolves | reject |

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

## Role-based policy gate

A fifth required check, `policy`, enforces *who may submit what*:

* **Maintainers** (repo role ≥ Maintain, or the repo owner) may open any PR.
* **Non-maintainers** may open **content PRs only** — every changed file must be
  `Qlean.lean`, `Qlean/**/*.lean` (PascalCase segments, excluding `Qlean/Meta/**`),
  or `blueprint/src/**/*.tex`. Anything else (scripts, CI, lakefile, LICENSE,
  harness infra) is maintainer-only.

Why it can't be bypassed: the check runs from the **base branch** via
`pull_request_target` (a PR cannot edit the policy that judges it) and is
**metadata-only** — it reads the author's role and the changed-file list via the
API and never checks out or runs PR code. Because editing a workflow or script
is itself a non-content change, a non-maintainer literally cannot open a PR that
weakens the checks — it fails `policy` before anything runs.

Defense-in-depth: `.github/CODEOWNERS` marks the harness paths maintainer-owned
(active once you enable required code-owner review).

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
