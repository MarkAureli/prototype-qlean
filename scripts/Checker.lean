/-
Qlean submission checker.

Run with:  lake env lean scripts/Checker.lean

Performs three of the four submission gates over every `@[qlean_export]`
declaration (and every `Qlean.*` declaration):

  * AXIOM GATE (fails)      — no axioms beyond {propext, Classical.choice, Quot.sound}.
  * HYPOTHESIS AUDIT (warns) — surfaces the propositional hypotheses of each
                               exported theorem, so a reviewer sees exactly what
                               a result is conditional on (the `H → P` form).
  * EXPORT DUMP             — writes `build/qlean_exports.txt`, consumed by the
                               link-completeness gate (`scripts/check_links.py`).

The compile gate is `lake build`; the fast sorry lint is `scripts/check_no_sorry.sh`.
-/
import Qlean
open Lean Elab Command

namespace QleanCheck

/-- The only axioms a submission may depend on. -/
def allowedAxioms : List Name := [``propext, ``Classical.choice, ``Quot.sound]

end QleanCheck

run_cmd do
  let env ← getEnv
  let mut exports : Array Name := #[]
  let mut axBad : Array (Name × List Name) := #[]
  for (name, info) in env.constants.toList do
    if Qlean.Meta.qleanExportAttr.hasTag env name then
      exports := exports.push name
    if (`Qlean).isPrefixOf name && !name.isInternalDetail then
      match info with
      | .thmInfo _ | .defnInfo _ =>
          let axs ← liftCoreM (Lean.collectAxioms name)
          let bad := axs.toList.filter (fun a => !(QleanCheck.allowedAxioms.contains a))
          unless bad.isEmpty do
            axBad := axBad.push (name, bad)
      | _ => pure ()

  -- EXPORT DUMP (for the link-completeness gate).
  IO.FS.createDirAll "build"
  IO.FS.writeFile "build/qlean_exports.txt"
    (String.intercalate "\n" (exports.toList.map (·.toString)) ++ "\n")
  logInfo m!"exported declarations ({exports.size}): {exports.toList}"

  -- HYPOTHESIS AUDIT (informational — routes conditionality to human review).
  liftTermElabM do
    for name in exports do
      match env.find? name with
      | some (.thmInfo ci) =>
          Meta.forallTelescopeReducing ci.type fun args _ => do
            let hyps ← args.filterMapM fun a => do
              let t ← Meta.inferType a
              if (← Meta.isProp t) then pure (some (← Meta.ppExpr t)) else pure none
            if hyps.isEmpty then
              logInfo m!"[hyp-audit] {name}: unconditional ✓"
            else
              logWarning m!"[hyp-audit] {name}: conditional on {hyps.size} hypothesis(es): {hyps.toList}"
      | _ => pure ()

  -- AXIOM GATE (authoritative — a `sorry` shows up here as `sorryAx`).
  if axBad.isEmpty then
    logInfo "✓ AXIOM GATE passed: all Qlean declarations use only {propext, Classical.choice, Quot.sound}."
  else
    for (name, bad) in axBad do
      logError m!"✗ {name} depends on disallowed axioms: {bad}"
    throwError "AXIOM GATE FAILED"
