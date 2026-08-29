import Mathlib
import CollatzLean.CycleBounds

/-!
# CycleLogs: the Diophantine linear form `Λ = S·ln2 − K·ln3`

From the integer bounds of `CycleBasic` and `CycleBounds` we derive real
logarithmic inequalities that express how close `S/K` must be to `log₂ 3`:

* `shift_lower_log`: `K·ln3 < S·ln2`  (from `S_lower_bound`)
* `Lambda_pos`: `0 < S·ln2 − K·ln3`
* `shift_log_upper`: `S·ln2 − K·ln3 < K·ln(1 + 1/xmin)`  (from `ratio_lt`)

Together they pin the linear form `Λ` into a shrinking window as `xmin`
grows — the input to the Baker–Rhin lower bound (cycle exclusion).
-/

open Finset Nat
open scoped BigOperators

namespace CollatzCycle

variable {K : ℕ} [NeZero K] (C : CollatzCycle K)

/-- `ln 2 > 0`. -/
private lemma ln2_pos : (0 : ℝ) < Real.log 2 := by
  exact Real.log_pos (by norm_num)

/-- `ln 3 > 0`. -/
private lemma ln3_pos : (0 : ℝ) < Real.log 3 := by
  exact Real.log_pos (by norm_num)

/-- Casts `3^K < 2^S` into ℝ, then applies `ln` (strictly increasing on ℝ₊). -/
lemma shift_lower_log : (K : ℝ) * Real.log 3 < (C.S : ℝ) * Real.log 2 := by
  have hnat : 3 ^ K < 2 ^ C.S := C.S_lower_bound
  have hreal : (3 : ℝ) ^ K < (2 : ℝ) ^ C.S := by exact_mod_cast hnat
  have hlog : Real.log ((3 : ℝ) ^ K) < Real.log ((2 : ℝ) ^ C.S) :=
    Real.log_lt_log (by positivity) hreal
  rw [Real.log_pow, Real.log_pow] at hlog
  exact hlog

/-- The linear form `Λ = S·ln2 − K·ln3` is positive. -/
theorem Lambda_pos : (0 : ℝ) < (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3 := by
  linarith [C.shift_lower_log]

/-- Upper: `Λ < K·ln(1 + 1/xmin)`, from the master inequality ratio. -/
lemma shift_log_upper (hxpos : 0 < C.xmin) :
    (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3
      < (K : ℝ) * Real.log (1 + 1 / (C.xmin : ℝ)) := by
  have hratio := C.ratio_lt hxpos
  have hpos_lhs : (0 : ℝ) < (2 : ℝ) ^ C.S / (3 : ℝ) ^ K := by
    positivity
  have hlog : Real.log ((2 : ℝ) ^ C.S / (3 : ℝ) ^ K)
      < Real.log ((1 + 1 / (C.xmin : ℝ)) ^ K) :=
    Real.log_lt_log hpos_lhs hratio
  have hlog_lhs : Real.log ((2 : ℝ) ^ C.S / (3 : ℝ) ^ K)
      = (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3 := by
    rw [Real.log_div]
    · rw [Real.log_pow, Real.log_pow]
    · exact pow_ne_zero _ (by norm_num)
    · exact pow_ne_zero _ (by norm_num)
  have hlog_rhs : Real.log ((1 + 1 / (C.xmin : ℝ)) ^ K)
      = (K : ℝ) * Real.log (1 + 1 / (C.xmin : ℝ)) := by
    rw [Real.log_pow]
  rw [hlog_lhs, hlog_rhs] at hlog
  exact hlog

/-- `ln (1 + 1/xmin) ≤ 1/xmin`, from the elementary bound `ln t ≤ t−1`. -/
lemma log_one_add_inv_le (hxpos : 0 < C.xmin) :
    Real.log (1 + 1 / (C.xmin : ℝ)) ≤ 1 / (C.xmin : ℝ) := by
  have hpos : (0 : ℝ) < 1 + 1 / (C.xmin : ℝ) := by positivity
  have h := Real.log_le_sub_one_of_pos hpos
  -- h : ln(1 + 1/xmin) ≤ (1 + 1/xmin) − 1
  have hsimp : (1 + 1 / (C.xmin : ℝ)) - 1 = 1 / (C.xmin : ℝ) := by ring
  rwa [hsimp] at h

/-- **The logarithmic clamp (log₂ form).**
The Diophantine linear form `Λ = S·ln2 − K·ln3` is pinned strictly:
`0 < Λ < K / xmin`.  This is the tight window that feeds the Baker–Rhin
lower bound on `|Λ|`: a non-trivial cycle would force `Λ` to be a nonzero
integer linear form in ln 2 and ln 3 of size `< K/xmin`, arbitrarily small as
`xmin → ∞` — the Diophantine obstruction. -/
theorem cycle_log_clamp (hxpos : 0 < C.xmin) :
    (0 : ℝ) < (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3 ∧
    (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3 < (K : ℝ) / (C.xmin : ℝ) := by
  have hlow := C.Lambda_pos
  have h_up := C.shift_log_upper hxpos
  have hlog := C.log_one_add_inv_le hxpos
  -- K·ln(1+1/xmin) ≤ K·(1/xmin) = K/xmin   (K ≥ 0)
  have hKmul : (K : ℝ) * Real.log (1 + 1 / (C.xmin : ℝ)) ≤ (K : ℝ) * (1 / (C.xmin : ℝ)) := by
    exact mul_le_mul_of_nonneg_left hlog (by positivity : 0 ≤ (K : ℝ))
  have hup2 : (C.S : ℝ) * Real.log 2 - (K : ℝ) * Real.log 3 < (K : ℝ) / (C.xmin : ℝ) := by
    have hle : (K : ℝ) * Real.log (1 + 1 / (C.xmin : ℝ)) ≤ (K : ℝ) / (C.xmin : ℝ) := by
      have h1 : (K : ℝ) * Real.log (1 + 1 / (C.xmin : ℝ)) ≤ (K : ℝ) * (1 / (C.xmin : ℝ)) := hKmul
      have h2 : (K : ℝ) * (1 / (C.xmin : ℝ)) = (K : ℝ) / (C.xmin : ℝ) := by ring_nf
      rwa [h2] at h1
    exact lt_of_lt_of_le h_up hle
  exact ⟨hlow, hup2⟩

/-- `K ≤ S`: each of the K shifts is at least 1. -/
lemma s_pos_each_le : K ≤ C.S := by
  calc K
    _ = ∑ i : Fin K, (1 : ℕ) := by simp
    _ ≤ ∑ i : Fin K, C.s i := by
      apply Finset.sum_le_sum
      intro i _
      exact C.s_pos i

end CollatzCycle