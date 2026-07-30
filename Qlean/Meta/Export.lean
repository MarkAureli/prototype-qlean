import Lean
open Lean

namespace Qlean.Meta

/--
`@[qlean_export]` marks a definition or theorem as a **public Qlean result**.

Every exported declaration is subject to the submission gates:
* it must be axiom-clean (only `propext`, `Classical.choice`, `Quot.sound`);
* it must be linked to blueprint prose via `\lean{...}` (link-completeness gate);
* its hypotheses are surfaced for human review (hypothesis-audit gate).
-/
initialize qleanExportAttr : TagAttribute ←
  registerTagAttribute `qlean_export
    "Marks a public Qlean result that must be linked to prose and pass the submission gates."

end Qlean.Meta
