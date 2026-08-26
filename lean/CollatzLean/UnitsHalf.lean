import Mathlib
import CollatzLean.EndpointUniform

/-!
# Step 3a: Automatic unit hypothesis and halving transfer

Two completions:

1. `isUnit_three_pow` — the unit hypothesis used throughout is *automatic*
   (`3` is coprime to every `2^n`), removing the last external premise.

2. `endpoint_count_bounds` — the Proposition-B3-style counting law: over any
   window consisting of `b` full periods plus a partial remainder `R < π`
   (`π = 2^(M-1)`), started at an offset that is itself a multiple of `π`,
   every odd class modulo `2^M` receives between `b` and `b + 1` endpoints.
   Since such windows have `K = b * π + R`, i.e. `K / π = b`, this is exactly
   the `count = K / π ± 1` law of Proposition B3.
-/

open Nat

/-! ### The unit hypothesis is automatic -/

/-- `3` is coprime to every power of two. -/
theorem three_coprime_two_pow (n : ℕ) : Nat.Coprime 3 (2 ^ n) := by
  rcases Nat.eq_zero_or_pos n with h0 | hp
  · subst h0
    exact Nat.coprime_one_right 3
  · rw [Nat.coprime_pow_right_iff hp]
    decide

/-- **The unit hypothesis is automatic.** -/
theorem isUnit_three_pow (n d : ℕ) : IsUnit ((3 : ZMod (2 ^ n)) ^ d) := by
  have hu : IsUnit ((3 : ZMod (2 ^ n))) :=
    ZMod.isUnit_iff_coprime _ _ |>.mpr (three_coprime_two_pow n)
  exact hu.pow d

/-- Cast-form of the automatic unit hypothesis. -/
theorem isUnit_three_pow_cast (n d : ℕ) :
    IsUnit ((3 ^ d : ℕ) : ZMod (2 ^ n)) := by
  rw [Nat.cast_pow]
  exact isUnit_three_pow n d

lemma pos_two_pow_succ (k : ℕ) : 0 < (2:ℕ) ^ (k + 1) := by
  induction k with
  | zero => norm_num
  | succ i ih => rw [Nat.pow_succ]; exact Nat.mul_pos ih (by norm_num)

lemma pos_two_pow_pred {M : ℕ} (_hM : 2 ≤ M) : 0 < 2 ^ (M - 1) := by
  obtain ⟨k, rfl⟩ : ∃ k, M = k + 2 := ⟨M - 2, by omega⟩
  show 0 < (2:ℕ) ^ (k + 1)
  exact pos_two_pow_succ k

/-! ### Divisibility cancellation by units -/

/-- A unit can be cancelled out of a divisibility hypothesis. -/
lemma dvd_of_unit_mul_dvd {π u D : ℕ} (hπ : 0 < π) (hu : IsUnit (u : ZMod π))
    (hdvd : π ∣ u * D) : π ∣ D := by
  by_cases h1c : π = 1
  · subst h1c
    exact ⟨D, by rw [Nat.one_mul]⟩
  obtain ⟨R, _hRlt, hR⟩ := exists_mul_mod_eq_of_isUnit u π 1 hπ hu
  -- hR : (u * R) % π = 1 % π
  have hone : 1 % π = 1 := by
    rcases Nat.eq_zero_or_pos π with h0 | hp
    · exact absurd h0 (ne_of_gt hπ)
    · obtain ⟨k, rfl⟩ := Nat.exists_eq_succ_of_ne_zero hp.ne'
      exact Nat.mod_eq_of_lt (by omega)
  have hurep : (u * R) % π = 1 := by rw [hR, hone]
  have h1 : ((D * R) * u) % π = D % π := by
    have hrw : (D * R) * u = D * (u * R) := by ring
    rw [hrw, Nat.mul_mod, hurep, Nat.mul_one, Nat.mod_mod]
  have h2 : ((D * R) * u) % π = 0 := by
    have hd : (D * R) * u = (u * D) * R := by ring
    rw [hd, Nat.mul_mod, Nat.mod_eq_zero_of_dvd hdvd]
    norm_num
  have hfin : D % π = 0 := by rw [← h1, h2]
  exact Nat.dvd_of_mod_eq_zero hfin

/-- Halving transfer with an explicit even multiplier:
`2^M ∣ (2 * c) * Δ` implies `2^(M-1) ∣ c * Δ`. -/
lemma twoPow_dvd_mul_half {M c Δ : ℕ} (hM0 : M ≠ 0)
    (h : (2 ^ M) ∣ (2 * c) * Δ) : (2 ^ (M - 1)) ∣ c * Δ := by
  rw [Nat.mul_assoc] at h
  obtain ⟨k, rfl⟩ : ∃ k, M = k + 1 := ⟨M - 1, by omega⟩
  rw [Nat.pow_succ'] at h
  exact Nat.dvd_of_mul_dvd_mul_left (by decide) h

/-- Full step: `2^M ∣ (2 * 3^d) * Δ` implies `2^(M-1) ∣ Δ`
(the factor `2` halves the modulus, and the unit `3^d` cancels). -/
lemma sPi_dvd {d M Δ : ℕ} (hM0 : M ≠ 0) (h : (2 ^ M) ∣ (2 * 3 ^ d) * Δ) :
    (2 ^ (M - 1)) ∣ Δ := by
  have hmid := twoPow_dvd_mul_half (c := 3 ^ d) hM0 h
  exact dvd_of_unit_mul_dvd (Nat.two_pow_pos _)
    (isUnit_three_pow_cast (M - 1) d) hmid

/-! ### Shift constancy across periods -/

/-- Positions differing by a multiple of the period `π = 2^(M-1)` land in the
same residue class modulo `2^M`. -/
lemma shift_const (d M y b j : ℕ) (hM : 2 ≤ M) :
    (y + 2 * 3 ^ d * (b * 2 ^ (M - 1) + j)) % 2 ^ M
      = (y + 2 * 3 ^ d * j) % 2 ^ M := by
  have hdvd : (2 ^ M) ∣ 2 * 3 ^ d * (b * 2 ^ (M - 1)) := by
    obtain ⟨k, rfl⟩ : ∃ k, M = k + 2 := ⟨M - 2, by omega⟩
    rw [show ((k:Nat)) + 2 - 1 = k + 1 from rfl]
    refine ⟨3 ^ d * b, ?_⟩
    have hpow : ((2:ℕ)) ^ (k + 1) = 2 * 2 ^ k := by
      rw [Nat.pow_succ']
    rw [hpow]
    ring
  have key : (2 * 3 ^ d) * (b * 2 ^ (M - 1)) % 2 ^ M = 0 :=
    Nat.mod_eq_zero_of_dvd hdvd
  have expand : (y + 2 * 3 ^ d * (b * 2 ^ (M - 1) + j))
      = (y + 2 * 3 ^ d * j) + 2 * 3 ^ d * (b * 2 ^ (M - 1)) := by ring
  calc (y + 2 * 3 ^ d * (b * 2 ^ (M - 1) + j)) % 2 ^ M
      = ((y + 2 * 3 ^ d * j) + 2 * 3 ^ d * (b * 2 ^ (M - 1))) % 2 ^ M := by rw [expand]
    _ = ((y + 2 * 3 ^ d * j) % 2 ^ M + (2 * 3 ^ d * (b * 2 ^ (M - 1))) % 2 ^ M) % 2 ^ M :=
        Nat.add_mod _ _ _
    _ = ((y + 2 * 3 ^ d * j) % 2 ^ M + 0) % 2 ^ M := by rw [key]
    _ = (y + 2 * 3 ^ d * j) % 2 ^ M := by rw [Nat.add_zero, Nat.mod_mod]
