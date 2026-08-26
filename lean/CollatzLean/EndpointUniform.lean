import Mathlib
import CollatzLean.LemmaT1_step1_pure

/-!
# Step 2: The endpoint law — exact uniformity on odd classes

Finite, fully checked formulation of the "conditional transport = Haar" claim:

Fix an admissible word prefix realized by the odd start class
`x₀ = ρ_w + 2^(S+1) * q`.  For any window size `M ≤ S+1` the map

  `q ↦ (y_w + 2 * 3^d * q) % 2^M`

from `ZMod 2^(M-1)` onto the odd classes of `ZMod 2^M` is a bijection.
Consequently:

* every odd class modulo `2^M` contains **exactly one** lift among the
  `2^(M-1)` normalized starting points (`endpoint_card_uniform`);
* even classes contain none (`endpoint_odd`);

which is precisely the statement that the conditional endpoint law on the
`S`-layer coincides with the uniform (Haar) measure on the odd classes
`(ℤ / 2^M ℤ)^×`.
-/

open Nat

/-! ### Endpoints are always odd -/

/-- Reduction modulo `2^M` preserves parity when `1 ≤ M`. -/
lemma mod_pow_two_par {M : ℕ} (hM : 1 ≤ M) (x : ℕ) :
    (x % 2 ^ M) % 2 = x % 2 := by
  have hdvd : 2 ∣ 2 ^ M := by
    match M with
    | 0 => omega
    | k + 1 => exact ⟨2 ^ k, by rw [Nat.pow_succ]; ring⟩
  exact Nat.mod_mod_of_dvd _ hdvd

/-- Endpoints never land in even classes. -/
theorem endpoint_odd (d M y_w q : ℕ) (hM : 1 ≤ M) (hy : Odd y_w) :
    (y_w + 2 * 3 ^ d * q) % 2 ^ M % 2 = 1 := by
  have hpar := mod_pow_two_par (M := M) hM (y_w + 2 * 3 ^ d * q)
  rw [hpar]
  have hm : (2 * 3 ^ d * q) % 2 = 0 := by
    rw [Nat.mul_assoc]
    exact Nat.mul_mod_right _ _
  rw [Nat.add_mod, Nat.odd_iff.mp hy, hm, Nat.add_zero]

/-! ### Exact uniformity: one lift per odd class -/

/-- **Endpoint law.** Every odd class modulo `2^M` is hit by exactly one of the
`2^(M-1)` normalized lifts `q ∈ [0, 2^(M-1))`.  This is the finite form of the
statement that the conditional endpoint law on an `S`-layer equals the uniform
(Haar) measure on the odd classes. -/
theorem endpoint_card_uniform (d M y_w : ℕ) (hM : 2 ≤ M) (hy : Odd y_w)
    (h_unit : IsUnit ((3 : ZMod (2 ^ (M - 1))) ^ d)) :
    ∀ r, Odd r →
      ((Finset.range (2 ^ (M - 1))).filter
        (fun q => (y_w + 2 * 3 ^ d * q) % 2 ^ M = r % 2 ^ M)).card = 1 := by
  intro r hrOdd
  obtain ⟨R, hRlt, hRiff⟩ := endpoint_bijection d M y_w r hM hy hrOdd h_unit
  refine Finset.card_eq_one.mpr ⟨R, ?_⟩
  ext q
  simp only [Finset.mem_filter, Finset.mem_range, Finset.mem_singleton]
  constructor
  · rintro ⟨hlt, heq⟩
    have hmod := (hRiff q).mp heq
    rwa [Nat.mod_eq_of_lt hlt] at hmod
  · intro h
    subst h
    exact ⟨hRlt, (hRiff q).mpr (Nat.mod_eq_of_lt hRlt)⟩
