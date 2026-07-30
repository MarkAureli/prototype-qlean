import Mathlib
import Qlean.Meta.Export

/-!
# Qlean — basic facts (prototype)

A handful of elementary, fully-proven facts used to exercise the submission
gates end-to-end. Each `@[qlean_export]` declaration is linked to prose in
`blueprint/src/content.tex`.
-/

namespace Qlean

open Matrix
open scoped ComplexOrder

variable {n : ℕ}

/-- A **density matrix** on a finite-dimensional system: a positive semidefinite
operator with unit trace. -/
@[qlean_export]
def IsDensityMatrix (ρ : Matrix (Fin n) (Fin n) ℂ) : Prop :=
  ρ.PosSemidef ∧ ρ.trace = 1

/-- Sanity check for the definition: a density matrix has unit trace.
(Deliberately hypothesis-carrying, to exercise the hypothesis-audit gate.) -/
@[qlean_export]
theorem IsDensityMatrix.trace_eq_one {ρ : Matrix (Fin n) (Fin n) ℂ}
    (h : IsDensityMatrix ρ) : ρ.trace = 1 :=
  h.2

/-- The trace of the `n × n` identity operator equals the dimension `n`. -/
@[qlean_export]
theorem trace_one_eq : (1 : Matrix (Fin n) (Fin n) ℂ).trace = (n : ℂ) := by
  rw [Matrix.trace_one, Fintype.card_fin]

/-- For any operator `A`, the Gram operator `Aᴴ * A` is positive semidefinite. -/
@[qlean_export]
theorem gram_posSemidef (A : Matrix (Fin n) (Fin n) ℂ) :
    (Aᴴ * A).PosSemidef :=
  Matrix.posSemidef_conjTranspose_mul_self A

end Qlean
