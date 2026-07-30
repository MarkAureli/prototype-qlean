# Contributing to qlean

qlean is a standard Lean 4 + Mathlib library for quantum information. It has two
layers:

- **Core** (`Qlean/Core/**`, namespace `Qlean.*`) — curated, general-interest
  definitions and results. Maintainer-owned; grows only by *promotion*.
- **Contrib** (`Qlean/Contrib/**`, namespace `Qlean.Contrib.*`) — contributed
  findings. **This is where your contribution goes.**

Every submission is checked automatically before a human reviews it. If you
follow this guide, your PR will pass the automated gates.

---

## What you may change

As a contributor (non-maintainer), a PR may **only** touch:

| Path | For |
|------|-----|
| `Qlean/Contrib/**/*.lean` | your Lean content |
| `Qlean/Contrib.lean` | one `import` line wiring your module in |
| `blueprint/src/contrib/<Name>.tex` | a **fresh** file with your result's prose |

Anything else — `Qlean/Core/**`, the repo root, scripts, CI, `lakefile` — is
maintainer-only and is **rejected automatically** by the `policy` check. If you
believe something belongs in Core, add it to Contrib first and open an issue
proposing promotion (see *Promotion* below).

## Setup

```sh
# one-time: install elan (the Lean toolchain manager) from https://leanprover-community.github.io
git clone https://github.com/MarkAureli/prototype-qlean && cd prototype-qlean
source "$HOME/.elan/env"
lake exe cache get      # download prebuilt Mathlib oleans (do NOT rebuild Mathlib)
lake build              # builds qlean (Core + Contrib) on top — fast
```

Toolchain and Mathlib are pinned (`lean-toolchain`, `lakefile.toml`) — don't
change them.

## Add your contribution

1. **Create a module** at `Qlean/Contrib/<Area>/<Name>.lean`. Every path segment
   must be `PascalCase` (e.g. `Qlean/Contrib/ChannelCapacity/Holevo.lean`).

2. **Use the right namespace and build on Core.** Put declarations under
   `Qlean.Contrib.*`; reuse Core rather than redefining it:

   ```lean
   import Qlean.Core            -- gives you the Qlean.* core defs + @[qlean_export]

   namespace Qlean.Contrib.ChannelCapacity

   /-- Your result, documented with a real docstring. -/
   @[qlean_export]
   theorem my_result : … := …

   end Qlean.Contrib.ChannelCapacity
   ```

   Mark each public definition/theorem you want to expose with **`@[qlean_export]`**.
   Your module may import Core; it may **not** be imported by Core.

3. **Wire it in.** Add one line to `Qlean/Contrib.lean`:

   ```lean
   import Qlean.Contrib.ChannelCapacity.Holevo
   ```

   (Unimported files are rejected — the axiom checker must be able to see yours.)

4. **Document it in a fresh tex.** Add **one new file**
   `blueprint/src/contrib/<Name>.tex` describing your contribution. It must
   contain **at least one** `\lean{Qlean.Contrib...}` link to a declaration you
   submitted — that is the anchor tying your prose to your Lean:

   ```latex
   \begin{theorem}[Holevo bound]
     \label{thm:holevo}
     \lean{Qlean.Contrib.ChannelCapacity.my_result}
     The accessible information is at most the Holevo quantity.
   \end{theorem}
   ```

   You do **not** need prose for every Lean statement — a proof often splits into
   technical lemmata that need no narration. But every formal environment you
   *do* write must carry a `\lean{}`, and every `\lean{}` must resolve to a real
   exported declaration. Edit the shared core prose (`content.tex`)? That's
   maintainer-only — your contribution lives in its own `contrib/` file.

5. **Add sanity lemmas for new definitions.** If you introduce a definition,
   prove a couple of basic facts about it (e.g. a new entropy is non-negative,
   or reduces to a known quantity in a special case). This guards against
   definitions that are subtly wrong, and it's what reviewers look for.

## The gates (run them locally before you push)

```sh
source "$HOME/.elan/env"
bash    scripts/check_no_sorry.sh Qlean      # no sorry / admit
python3 scripts/check_import_direction.py    # (core ⊥ contrib — n/a to you, but runs)
lake build                                   # it must compile
lake env lean scripts/Checker.lean           # axiom-clean + hypothesis audit + dumps
python3 scripts/check_coverage.py            # your file is imported
python3 scripts/check_api_semver.py          # (core unchanged by a contrib PR)
python3 scripts/check_links.py               # prose ↔ Lean links
```

What they require of your PR:

- **No `sorry`/`admit`, and no extra axioms.** Proofs must be complete and depend
  only on `propext`, `Classical.choice`, `Quot.sound`. (`sorry` is caught as
  `sorryAx`.)
- **It compiles** against pinned Mathlib + Core.
- **Your module is imported** (step 3) and **every export is linked to prose**
  (step 4).
- **Watch your hypotheses.** The checker prints the hypotheses of every exported
  theorem. A result of the form `(h : HardThing) → Conclusion` is honest only if
  `HardThing` is reasonable — don't smuggle the real work into an assumed
  hypothesis. Conditional results are fine when the condition is stated in the
  prose; reviewers will look here.

## Open the pull request

Push to a branch on your fork and open a PR. Two required checks run:

- **`policy`** — confirms your PR only touches contributor-allowed paths.
- **`gates`** — the checks above.

Both must be green. Then a **maintainer reviews** that each Lean statement is a
faithful formalization of its prose (especially definitions). This human step is
the one thing the gates can't do — write prose and Lean that obviously match, and
review is quick.

If CI is red, read the failing step's message — each gate says exactly what to fix.

---

## For maintainers

- **Promotion (Contrib → Core).** To elevate a result of general interest: move
  the declaration to `Qlean/Core/<Area>/<Name>.lean` and the clean `Qlean.*`
  namespace, leave a `@[deprecated]` alias at the old `Qlean.Contrib.*` name,
  re-review it as core (highest scrutiny, sanity lemmas, stable API), and update
  the prose link.

- **Core changes are versioned.** The `Core semver` gate diffs the core API
  signatures against `core-api.baseline.txt` and requires a matching `VERSION`
  bump: additions → minor, removals/signature changes → major, proof-only → none.
  At release, bump `VERSION`, run `scripts/update_api_baseline.sh`, commit the new
  baseline, and tag. Remember a core version is effectively
  `(core tag, Mathlib rev, toolchain)` — peg releases to Mathlib's tagged releases.

- **Bypass.** Maintainers (repo role ≥ Maintain) may open non-content PRs; the
  `policy` gate waives the structure rules for them.
