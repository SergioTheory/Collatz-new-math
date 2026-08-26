import Mathlib
import CollatzLean.CycleBasic

/-!
# CycleBounds: Diophantine bounds from the master inequality

Turns the integer master inequality
    `2^S · xmin^K < 3^K · (xmin+1)^K`
into the real-exponent form
    `2^S / 3^K < (1 + 1/xmin)^K`,
the input for the Baker–Rhin Diophantine-approximation bound
(cycle-length exclusion below 10^9).
-/

open Finset Nat
open scoped BigOperators

namespace CollatzCycle

variable {K : ℕ} [NeZero K] (C : CollatzCycle K)

/-- Real version of the master inequality, obtained by casting the natural
numbers into ℝ (strictly monotone embedding). -/
lemma master_ineq_real :
    (2 : ℝ) ^ C.S * (C.xmin : ℝ) ^ K < (3 : ℝ) ^ K * ((C.xmin + 1 : ℕ) : ℝ) ^ K := by
  have hnat := C.master_ineq
  exact_mod_cast hnat

/-- The growth factor ratio: `2^S / 3^K < (1 + 1/xmin)^K`. -/
lemma ratio_lt (hxpos : 0 < C.xmin) :
    (2 : ℝ) ^ C.S / (3 : ℝ) ^ K < (1 + 1 / (C.xmin : ℝ)) ^ K := by
  have hx : (C.xmin : ℝ) ≠ 0 := by exact_mod_cast (ne_of_gt hxpos)
  have hmain := C.master_ineq_real
  have hpos3 : (0 : ℝ) < 3 ^ K := pow_pos (by norm_num) _
  have hposx : (0 : ℝ) < (C.xmin : ℝ) ^ K := pow_pos (by exact_mod_cast hxpos) _
  have hdiv := div_lt_div_of_pos_right hmain (mul_pos hpos3 hposx)
  have hleft : (2 : ℝ) ^ C.S * (C.xmin : ℝ) ^ K / (3 ^ K * (C.xmin : ℝ) ^ K)
      = (2 : ℝ) ^ C.S / (3 : ℝ) ^ K := by
    field_simp [hx]
  have hright : (3 : ℝ) ^ K * ((C.xmin + 1 : ℕ) : ℝ) ^ K / (3 ^ K * (C.xmin : ℝ) ^ K)
      = (1 + 1 / (C.xmin : ℝ)) ^ K := by
    have hcancel : (3 : ℝ) ^ K * ((C.xmin + 1 : ℕ) : ℝ) ^ K / (3 ^ K * (C.xmin : ℝ) ^ K)
        = ((C.xmin + 1 : ℕ) : ℝ) ^ K / (C.xmin : ℝ) ^ K := by
      field_simp [hx]
    rw [hcancel, ← div_pow]
    congr 1
    field_simp [hx]
    norm_num
  rw [hleft, hright] at hdiv
  exact hdiv

end CollatzCycle