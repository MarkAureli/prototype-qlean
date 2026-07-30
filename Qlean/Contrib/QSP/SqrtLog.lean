/-
  QSP/QSVT polynomial approximation of  f(x) = √(-log x²)  on  [1/κ, 1].

  Contributed formalization of the algebraic/analytic core behind the
  construction. Companion prose: `blueprint/src/contrib/SqrtLog.tex`.

  We formalize the exact identities the transcendental estimates are applied to:

    * `factorization`      : exact extraction of the √(1-u) branch point.
    * `hasSum_g`           : Mercator series for the smooth factor g.
    * `g_pos`              : positivity of g on (0,1).
    * `coeff_recurrence`   : the explicit square-root coefficients r₀..r₄.
    * `rho_eq`             : the Bernstein-ellipse parameter ρ = (κ+1)/(κ-1).
    * `f_factor`           : f(x) = √(1-x²)·R(x), the QSP off-diagonal form.
    * `error_propagation`  : sup-error of R transfers to f, cusp-suppressed.

  The transcendental estimates (Bernstein's theorem itself, degree = O(κ log 1/ε))
  are quoted from the literature in the PDF; here we prove the exact algebra that
  those estimates are applied to. Everything below is complete and axiom-clean.
-/
import Qlean.Core

namespace Qlean.Contrib.QSP

/-! ### Lemma 1 — exact extraction of the branch point -/

/-- For `0 < u < 1`,
    `√(-log u) = √(1-u) · √((-log u)/(1-u))`.
    The whole square-root cusp of `√(-log u)` is carried by the explicit
    factor `√(1-u)`; the residual `√((-log u)/(1-u))` is smooth. -/
@[qlean_export]
theorem factorization (u : ℝ) (h0 : 0 < u) (h1 : u < 1) :
    Real.sqrt (-Real.log u)
      = Real.sqrt (1 - u) * Real.sqrt (-Real.log u / (1 - u)) := by
  have hb : (0 : ℝ) < 1 - u := by linarith
  have hne : (1 : ℝ) - u ≠ 0 := ne_of_gt hb
  rw [← Real.sqrt_mul hb.le]
  congr 1
  field_simp

/-- The smooth factor `g(u) = (-log u)/(1-u)` is strictly positive on `(0,1)`. -/
@[qlean_export]
theorem g_pos (u : ℝ) (h0 : 0 < u) (h1 : u < 1) :
    0 < -Real.log u / (1 - u) := by
  have hlog : Real.log u < 0 := Real.log_neg h0 h1
  have hb : (0 : ℝ) < 1 - u := by linarith
  exact div_pos (by linarith) hb

/-! ### Lemma 2 — Mercator series of the smooth factor -/

/-- With `w = 1 - u`, the smooth factor equals the power series
    `g = ∑ₖ wᵏ/(k+1)`.  Formally, for `0 < w < 1`,
    `∑ₖ wᵏ/(k+1) = (-log(1-w))/w`.
    Derived from Mathlib's Mercator series `∑ₙ wⁿ⁺¹/(n+1) = -log(1-w)`
    by dividing through by `w`. -/
@[qlean_export]
theorem hasSum_g (w : ℝ) (hw0 : 0 < w) (hw1 : w < 1) :
    HasSum (fun k : ℕ => w ^ k / ((k : ℝ) + 1)) (-Real.log (1 - w) / w) := by
  have habs : |w| < 1 := by rw [abs_of_pos hw0]; exact hw1
  have hwne : w ≠ 0 := ne_of_gt hw0
  have H := (Real.hasSum_pow_div_log_of_abs_lt_one habs).div_const w
  have hfun :
      (fun n : ℕ => w ^ (n + 1) / ((n : ℝ) + 1) / w)
        = (fun k : ℕ => w ^ k / ((k : ℝ) + 1)) := by
    funext n
    have hn : ((n : ℝ) + 1) ≠ 0 := by positivity
    field_simp
    ring
  rwa [hfun] at H

/-! ### Lemma 3 — explicit square-root coefficients

`R = √g = ∑ⱼ rⱼ wʲ` is fixed by `∑_{i+j=n} rᵢ rⱼ = 1/(n+1)`.  We verify the
closed-form values `r₀,…,r₄` satisfy these convolution identities exactly. -/
@[qlean_export]
theorem coeff_recurrence :
    let r0 : ℚ := 1
    let r1 : ℚ := 1 / 4
    let r2 : ℚ := 13 / 96
    let r3 : ℚ := 35 / 384
    let r4 : ℚ := 6271 / 92160
    (r0 * r0 = 1 / 1) ∧
    (2 * r0 * r1 = 1 / 2) ∧
    (2 * r0 * r2 + r1 * r1 = 1 / 3) ∧
    (2 * r0 * r3 + 2 * r1 * r2 = 1 / 4) ∧
    (2 * r0 * r4 + 2 * r1 * r3 + r2 * r2 = 1 / 5) := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> norm_num

/-! ### Proposition 1 — the Bernstein-ellipse parameter -/

/-- With `c = (κ²+1)/(κ²-1)`, the largest singularity-free Bernstein ellipse has
    parameter `ρ = c + √(c²-1) = (κ+1)/(κ-1)`.  This governs the geometric
    convergence rate `O(ρ⁻ⁿ)` of the Chebyshev expansion of `R`. -/
@[qlean_export]
theorem rho_eq (κ : ℝ) (hκ : 1 < κ) :
    (κ ^ 2 + 1) / (κ ^ 2 - 1)
        + Real.sqrt (((κ ^ 2 + 1) / (κ ^ 2 - 1)) ^ 2 - 1)
      = (κ + 1) / (κ - 1) := by
  have hκ0 : (0 : ℝ) < κ := by linarith
  have h2 : (0 : ℝ) < κ ^ 2 - 1 := by nlinarith
  have hden : (κ : ℝ) ^ 2 - 1 ≠ 0 := ne_of_gt h2
  have hden2 : (κ : ℝ) - 1 ≠ 0 := by linarith
  have hstep :
      ((κ ^ 2 + 1) / (κ ^ 2 - 1)) ^ 2 - 1 = (2 * κ / (κ ^ 2 - 1)) ^ 2 := by
    field_simp
    ring
  rw [hstep, Real.sqrt_sq (div_nonneg (by linarith) h2.le)]
  field_simp
  ring

/-! ### The target function and its exact factorization -/

/-- Target: `f(x) = √(-log x²)`. -/
@[qlean_export]
noncomputable def f (x : ℝ) : ℝ := Real.sqrt (-Real.log (x ^ 2))

/-- Smooth residual factor `R(x) = √((-log x²)/(1-x²))`. -/
@[qlean_export]
noncomputable def R (x : ℝ) : ℝ := Real.sqrt (-Real.log (x ^ 2) / (1 - x ^ 2))

/-- Main identity: `f(x) = √(1-x²)·R(x)` for `0 < x < 1`.
    The right-hand side is exactly the `√(1-x²)·(polynomial)` shape produced as
    the off-diagonal element of a QSP sequence (take `R ≈ Q`, a polynomial). -/
@[qlean_export]
theorem f_factor (x : ℝ) (h0 : 0 < x) (h1 : x < 1) :
    f x = Real.sqrt (1 - x ^ 2) * R x := by
  have hx2 : (0 : ℝ) < x ^ 2 := pow_pos h0 2
  have hx2' : x ^ 2 < 1 := by nlinarith
  simpa [f, R] using factorization (x ^ 2) hx2 hx2'

/-! ### Lemma 7 — error propagation, with cusp suppression -/

/-- If a polynomial value `Q` approximates the smooth factor `R x` to error `ε`,
    then `√(1-x²)·Q` approximates `f x` to the same error `ε`, and the bound is
    suppressed by the factor `√(1-x²) ≤ 1` near the cusp `x → 1`. -/
@[qlean_export]
theorem error_propagation (x : ℝ) (hx0 : 0 < x) (hx1 : x < 1)
    (Q ε : ℝ) (hQ : |R x - Q| ≤ ε) :
    |f x - Real.sqrt (1 - x ^ 2) * Q| ≤ ε := by
  have hsnn : (0 : ℝ) ≤ Real.sqrt (1 - x ^ 2) := Real.sqrt_nonneg _
  have hsle : Real.sqrt (1 - x ^ 2) ≤ 1 := by
    have h := Real.sqrt_le_sqrt (show 1 - x ^ 2 ≤ 1 by nlinarith [sq_nonneg x])
    simpa using h
  rw [f_factor x hx0 hx1, ← mul_sub, abs_mul, abs_of_nonneg hsnn]
  calc
    Real.sqrt (1 - x ^ 2) * |R x - Q|
        ≤ 1 * |R x - Q| := mul_le_mul_of_nonneg_right hsle (abs_nonneg _)
    _ = |R x - Q| := one_mul _
    _ ≤ ε := hQ

end Qlean.Contrib.QSP
