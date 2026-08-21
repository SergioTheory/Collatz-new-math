import Mathlib

open Nat

lemma mod_div_two (a b m : ℕ) (h_m : 1 ≤ m) :
    (2 * a) % 2^m = (2 * b) % 2^m ↔ a % 2^(m-1) = b % 2^(m-1) := by
  have h2 : 2^m = 2 * 2^(m-1) := by
    calc 2^m = 2^(m - 1 + 1) := by congr 1; omega
    _ = 2^(m - 1) * 2 := by rw [Nat.pow_succ]
    _ = 2 * 2^(m - 1) := by ring
  rw [h2]
  rw [Nat.mul_mod_mul_left, Nat.mul_mod_mul_left]
  omega

lemma mul_unit_mod_equiv (d m q R : ℕ) (h_m : 2 ≤ m)
    (h_unit : IsUnit ((3 : ZMod (2^(m-1)))^d)) :
    (3^d * q) % 2^(m-1) = (3^d * R) % 2^(m-1) ↔ q % 2^(m-1) = R % 2^(m-1) := by
  set n := 2^(m-1)
  constructor
  · intro h
    have h_zmod : ((3^d * q : ℕ) : ZMod n) = ((3^d * R : ℕ) : ZMod n) := (ZMod.natCast_eq_natCast_iff _ _ n).mpr h
    push_cast at h_zmod
    rcases h_unit with ⟨u, hu⟩
    have h_inv : (u.inv : ZMod n) * ((3^d : ZMod n) * (q : ZMod n)) = 
                 (u.inv : ZMod n) * ((3^d : ZMod n) * (R : ZMod n)) := by rw [h_zmod]
    rw [← mul_assoc, ← mul_assoc] at h_inv
    have hu_inv : (u.inv : ZMod n) * (3^d : ZMod n) = 1 := by rw [← hu]; exact u.inv_val
    rw [hu_inv, one_mul, one_mul] at h_inv
    exact (ZMod.natCast_eq_natCast_iff q R n).mp h_inv
  · intro h
    have h_zmod : (q : ZMod n) = (R : ZMod n) := (ZMod.natCast_eq_natCast_iff q R n).mpr h
    have h_mul : (3^d : ZMod n) * (q : ZMod n) = (3^d : ZMod n) * (R : ZMod n) := by rw [h_zmod]
    have h_unpushed : ((3^d * q : ℕ) : ZMod n) = ((3^d * R : ℕ) : ZMod n) := by push_cast; exact h_mul
    exact (ZMod.natCast_eq_natCast_iff (3^d * q) (3^d * R) n).mp h_unpushed

lemma add_cancel_mod (a b c n : ℕ) (hn : 0 < n) :
    (a + b) % n = (a + c) % n ↔ b % n = c % n := by
  constructor
  · intro h
    have h_zmod : ((a + b : ℕ) : ZMod n) = ((a + c : ℕ) : ZMod n) := (ZMod.natCast_eq_natCast_iff _ _ n).mpr h
    push_cast at h_zmod
    have h_cancel := add_left_cancel h_zmod
    exact (ZMod.natCast_eq_natCast_iff b c n).mp h_cancel
  · intro h
    have h_zmod : (b : ZMod n) = (c : ZMod n) := (ZMod.natCast_eq_natCast_iff b c n).mpr h
    have h_add : (a : ZMod n) + (b : ZMod n) = (a : ZMod n) + (c : ZMod n) := by rw [h_zmod]
    have h_unpushed : ((a + b : ℕ) : ZMod n) = ((a + c : ℕ) : ZMod n) := by push_cast; exact h_add
    exact (ZMod.natCast_eq_natCast_iff (a + b) (a + c) n).mp h_unpushed

lemma endpoint_bijection (d m y_w r : ℕ) (h_m : 2 ≤ m)
    (hy : Odd y_w) (hr : Odd r)
    (h_unit : IsUnit ((3 : ZMod (2^(m-1)))^d)) :
    ∃ R < 2^(m-1), ∀ q,
      (y_w + 2 * 3^d * q) % 2^m = r % 2^m ↔ q % 2^(m-1) = R := by
  set n := 2^(m-1)
  -- The target R is given by ((r - y_w)/2) * (3^d)⁻¹ mod 2^{m-1}
  -- Since we work in Nat, we first find an integer s such that y_w + 2s ≡ r (mod 2^m)
  -- We know y_w and r are odd, so r - y_w is even.
  sorry
