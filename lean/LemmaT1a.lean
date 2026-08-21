import Mathlib

lemma three_pow_unit_mod (d m : ℕ) (hm : 2 ≤ m) :
    IsUnit ((3 : ZMod (2^(m-1)))^d) := by
  have h32 : Nat.Coprime 3 2 := by norm_num
  have hcop : Nat.Coprime (3^d) (2^(m-1)) := Nat.Coprime.pow d (m-1) h32
  exact ZMod.isUnit_of_coprime _ _ hcop
