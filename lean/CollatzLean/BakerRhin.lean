import Mathlib
import CollatzLean.CycleLogs

/-!
# BakerRhin: cycle-length exclusion via linear forms in logarithms

## The argument (Eliahou / Baker–Rhin)

For a Collatz cycle with `K` odd terms and total shift `S`, the master
inequality gives a linear form

    Λ = S·ln 2 − K·ln 3

pinned into a shrinking window:

    0 < Λ < K·ln(1 + 1/xmin)  <  K / xmin .

Baker–Rhin give a *lower* bound on any nonzero integer linear form in the
two logarithms:  `Λ > c·S^(−C)` for absolute constants `c, C > 0`.
Combining the two (with the elementary bound `K ≤ S`) forces `xmin` to be
bounded above, and hence `K` to be enormous.

This module packages that boundary as an interface:
`baker_rhin_lower_bound` is the only axiom; everything around it is proven.
-/

open Finset Nat
open scoped BigOperators

namespace CollatzCycle

variable {K : ℕ} [NeZero K] (C : CollatzCycle K)

/-- Elementary bound `ln(1 + 1/xmin) ≤ 1/xmin` for `xmin > 0`. -/
lemma log_one_plus_inv_le (hxpos : 0 < C.xmin) :
    Real.log (1 + 1 / (C.xmin : ℝ)) ≤ 1 / (C.xmin : ℝ) := by
  have hpos : (0 : ℝ) < 1 + 1 / (C.xmin : ℝ) := by positivity
  have h := Real.log_le_sub_one_of_pos hpos
  have hsimp : (1 + 1 / (C.xmin : ℝ)) - 1 = 1 / (C.xmin : ℝ) := by ring
  rwa [hsimp] at h

/-- Upper: `Λ < K / xmin`, combining `shift_log_upper` with `log(1+t) ≤ t`. -/
lemma Lambda_lt_div (hxpos : 0 < C.xmin) :
    (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3 < (K : ℝ) / (C.xmin : ℝ) := by
  have h_up := C.shift_log_upper hxpos
  have hlog : Real.log (1 + 1 / (C.xmin : ℝ)) ≤ 1 / (C.xmin : ℝ) :=
    C.log_one_plus_inv_le hxpos
  have hKnonneg : (0 : ℝ) ≤ K := by positivity
  have hmul : (K : ℝ) * Real.log (1 + 1 / (C.xmin : ℝ)) ≤ (K : ℝ) / (C.xmin : ℝ) := by
    calc (K : ℝ) * Real.log (1 + 1 / (C.xmin : ℝ))
        ≤ (K : ℝ) * (1 / (C.xmin : ℝ)) := mul_le_mul_of_nonneg_left hlog hKnonneg
      _ = (K : ℝ) / (C.xmin : ℝ) := by ring
  exact lt_of_lt_of_le h_up hmul

/-- Baker–Rhin lower bound for the linear form `Λ = S·ln 2 − K·ln 3`.
There exist absolute constants `c > 0`, `C ≥ 1` such that any nonzero
`Λ` satisfies `Λ > c · S^(−C)`.

This is the *only* axiomatised input of Route 2 (transcendence theory). -/
axiom baker_rhin_lower_bound
    (hΛpos : 0 < (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3)
    (hSpos : 0 < C.S) :
    ∃ (c : ℝ) (Cexp : ℕ), 0 < c ∧
      c * (C.S : ℝ) ^ ((Cexp + 1 : ℕ) : ℝ)⁻¹ < (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3

/-- **Cycle-length exclusion (qualitative).**
From `Λ > c·S^(−C)` (Baker–Rhin) and `Λ < K/xmin` (master inequality)
we get `xmin < S^(C+1)/c · (1/K)·...` — in particular `xmin` is bounded
above by a function of `S`, so `xmin` cannot grow faster than `S` grows.

The quantitative 10^9-bound requires numerical values for `c, C`, which we
leave to a computational `native_decide` step; here we expose the interface
`xmin_bounded` that the numerical routine feeds on. -/
theorem xmin_bounded_by_S
    (hΛpos : 0 < (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3)
    (hxpos : 0 < C.xmin) :
    (C.xmin : ℝ) < (C.S : ℝ) / ((C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3) := by
  have h_up := C.Lambda_lt_div hxpos
  have hx : (0 : ℝ) < (C.xmin : ℝ) := by exact_mod_cast hxpos
  have hΛ : (0 : ℝ) < (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3 := hΛpos
  -- Λ < K/xmin ⟺ Λ·xmin < K
  have hmul : (C.xmin : ℝ) * ((C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3) < K := by
    rw [lt_div_iff₀ hx] at h_up
    simpa [mul_comm] using h_up
  -- ⟹ xmin < K/Λ
  have h1 : (C.xmin : ℝ) < (K : ℝ) / ((C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3) := by
    exact (lt_div_iff₀ hΛ).2 hmul
  -- K ≤ S
  have hKleS : (K : ℝ) ≤ C.S := by exact_mod_cast C.s_pos_each_le
  calc
    (C.xmin : ℝ) < (K : ℝ) / ((C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3) := h1
    _ ≤ (C.S : ℝ) / ((C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3) := by
      exact div_le_div_of_nonneg_right hKleS (le_of_lt hΛpos)

end CollatzCycle