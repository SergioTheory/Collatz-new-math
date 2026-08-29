import Mathlib
import CollatzLean.CycleBasic

/-!
# ShadowEscape: exact structure of the `2^a·M − 1` shadow (Route 4 strong)
-/

open Finset Nat

namespace ShadowEscape

/-- Relational accelerated step on ℤ: `b·2^s = 3·a + 1`. -/
def step31_Z (a b : ℤ) (s : ℕ) : Prop := b * (2 : ℤ)^s = 3 * a + 1

/-- j-th point of the shadow class at shadow time `j` (in ℤ). -/
def shadow_val_Z (M a j : ℕ) : ℤ :=
  (M : ℤ) * (3 : ℤ)^j * (2 : ℤ)^(a - j) - 1

/-- Shadow value at time `a` equals `M·3^a − 1`. -/
lemma shadow_peak_Z (M a : ℕ) : shadow_val_Z M a a = (M : ℤ) * (3 : ℤ)^a - 1 := by
  unfold shadow_val_Z
  have hz : a - a = 0 := by omega
  rw [hz, pow_zero, mul_one]

/-- Internal shadow move (in ℤ), shift `s = 1`, for `j < a`. -/
lemma shadow_step_Z (M a j : ℕ) (hj : j < a) :
    step31_Z (shadow_val_Z M a j) (shadow_val_Z M a (j+1)) 1 := by
  unfold step31_Z shadow_val_Z
  have hsub : a - (j + 1) = a - j - 1 := by omega
  have h2a : (2 : ℤ) ^ (a - j) = (2 : ℤ) ^ (a - j - 1) * 2 := by
    calc
      (2 : ℤ) ^ (a - j) = (2 : ℤ) ^ (a - j - 1 + 1) := by congr 1; omega
      _ = (2 : ℤ) ^ (a - j - 1) * (2 : ℤ) ^ 1 := by rw [pow_add]
      _ = (2 : ℤ) ^ (a - j - 1) * 2 := by rw [pow_one]
  have h3a : (3 : ℤ) ^ (j + 1) = (3 : ℤ) ^ j * 3 := by
    calc
      (3 : ℤ) ^ (j + 1) = (3 : ℤ) ^ j * (3 : ℤ) ^ 1 := by rw [pow_add]
      _ = (3 : ℤ) ^ j * 3 := by rw [pow_one]
  calc
    ((M : ℤ) * (3 : ℤ)^(j + 1) * (2 : ℤ)^(a - (j + 1)) - 1) * (2 : ℤ)^1
      = ((M : ℤ) * (3 : ℤ)^(j + 1) * (2 : ℤ)^(a - j - 1) - 1) * 2 := by rw [hsub, pow_one]
    _ = (M : ℤ) * (3 : ℤ)^(j + 1) * (2 : ℤ)^(a - j - 1) * 2 - 2 := by ring
    _ = (M : ℤ) * ((3 : ℤ)^j * 3) * (2 : ℤ)^(a - j - 1) * 2 - 2 := by rw [h3a]
    _ = (M : ℤ) * (3 : ℤ)^j * 3 * ((2 : ℤ)^(a - j - 1) * 2) - 2 := by ring
    _ = (M : ℤ) * (3 : ℤ)^j * 3 * (2 : ℤ)^(a - j) - 2 := by rw [← h2a]
    _ = 3 * ((M : ℤ) * (3 : ℤ)^j * (2 : ℤ)^(a - j)) - 2 := by ring
    _ = 3 * ((M : ℤ) * (3 : ℤ)^j * (2 : ℤ)^(a - j) - 1) + 1 := by ring

/-- The iterated shadow trajectory: values follow the exact pattern for all `j ≤ a`. -/
lemma shadow_orbit_step (M a j : ℕ) (hj : j < a) :
    shadow_val_Z M a (j+1) * 2 = 3 * (shadow_val_Z M a j) + 1 := by
  have h := shadow_step_Z M a j hj
  unfold step31_Z at h
  rw [pow_one] at h
  exact h

/-- The exit identity: `3·shadow(M a (a-1)) + 1 = 2·(M·3^a − 1)`. -/
lemma shadow_exit_algebra (M a : ℕ) (ha : 0 < a) :
    3 * (shadow_val_Z M a (a - 1)) + 1 = 2 * ((M : ℤ) * (3 : ℤ)^a - 1) := by
  unfold shadow_val_Z
  have h1 : a - (a - 1) = 1 := by omega
  have h3a : (3 : ℤ) ^ a = (3 : ℤ) ^ (a - 1) * 3 := by
    calc
      (3 : ℤ) ^ a = (3 : ℤ) ^ (a - 1 + 1) := by congr 1; omega
      _ = (3 : ℤ) ^ (a - 1) * (3 : ℤ) ^ 1 := by rw [pow_add]
      _ = (3 : ℤ) ^ (a - 1) * 3 := by rw [pow_one]
  rw [h1, pow_one]
  calc
    3 * ((M : ℤ) * (3 : ℤ) ^ (a - 1) * 2 - 1) + 1
      = (M : ℤ) * (3 : ℤ) ^ (a - 1) * 6 - 2 := by ring
    _ = (M : ℤ) * ((3 : ℤ) ^ (a - 1) * 3) * 2 - 2 := by ring
    _ = (M : ℤ) * (3 : ℤ) ^ a * 2 - 2 := by rw [← h3a]
    _ = 2 * ((M : ℤ) * (3 : ℤ) ^ a - 1) := by ring

/-- Exit move (in ℤ): from the shadow at `a-1`, a step of shift `s` (in ℕ) reaches `Y`. -/
lemma shadow_exit_Z (M a : ℕ) (ha : 0 < a) (s : ℕ) (Y : ℤ)
    (h : step31_Z (shadow_val_Z M a (a - 1)) Y s) :
    Y * (2 : ℤ)^s = 2 * ((M : ℤ) * (3 : ℤ)^a - 1) := by
  unfold step31_Z at h
  rw [shadow_exit_algebra M a ha] at h
  exact h

end ShadowEscape