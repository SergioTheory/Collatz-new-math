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

/-- Multiplication by the unit `3^d` reflects congruences modulo `2^(m-1)`
(provided the reference point `R` is reduced). -/
lemma mul_unit_mod_equiv (d m q R : ℕ) (h_m : 2 ≤ m) (hRlt : R < 2^(m-1))
    (h_unit : IsUnit ((3 : ZMod (2^(m-1)))^d)) :
    (3^d * q) % 2^(m-1) = (3^d * R) % 2^(m-1) ↔ q % 2^(m-1) = R := by
  set n := 2^(m-1)
  have hRred : R % n = R := Nat.mod_eq_of_lt hRlt
  constructor
  · intro h
    have h_zmod : ((3^d * q : ℕ) : ZMod n) = ((3^d * R : ℕ) : ZMod n) :=
      (ZMod.natCast_eq_natCast_iff _ _ n).mpr h
    push_cast at h_zmod
    rcases h_unit with ⟨u, hu⟩
    have h_inv : (u.inv : ZMod n) * ((3^d : ZMod n) * (q : ZMod n)) =
                 (u.inv : ZMod n) * ((3^d : ZMod n) * (R : ZMod n)) := by rw [h_zmod]
    rw [← mul_assoc, ← mul_assoc] at h_inv
    have hu_inv : (u.inv : ZMod n) * (3^d : ZMod n) = 1 := by rw [← hu]; exact u.inv_val
    rw [hu_inv, one_mul, one_mul] at h_inv
    have hMe : q % n = R % n := (ZMod.natCast_eq_natCast_iff q R n).mp h_inv
    rwa [Nat.mod_eq_of_lt hRlt] at hMe
  · intro h
    have h_red : q % n = R % n := by rw [h, hRred]
    have h_zmod : (q : ZMod n) = (R : ZMod n) :=
      (ZMod.natCast_eq_natCast_iff q R n).mpr h_red
    have h_mul : (3^d : ZMod n) * (q : ZMod n) = (3^d : ZMod n) * (R : ZMod n) := by rw [h_zmod]
    have h_unpushed : ((3^d * q : ℕ) : ZMod n) = ((3^d * R : ℕ) : ZMod n) := by push_cast; exact h_mul
    exact (ZMod.natCast_eq_natCast_iff (3^d * q) (3^d * R) n).mp h_unpushed

lemma add_cancel_mod (a b c n : ℕ) (_hn : 0 < n) :
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

/-- Adding a multiple of `c` does not change the residue modulo `c`. -/
lemma add_dvd_mod (a b c : ℕ) (h : c ∣ b) : (a + b) % c = a % c := by
  rw [Nat.add_mod, Nat.mod_eq_zero_of_dvd h, Nat.add_zero, Nat.mod_mod]

/-! ### Auxiliary lemmas for the endpoint transport -/

/-- Half of an even number, without invoking division reasoning in context. -/
lemma exists_two_mul_of_mod_two_eq_zero {D : ℕ} (h : D % 2 = 0) : ∃ K, D = K + K :=
  ⟨D / 2, by
    have hdm := Nat.div_add_mod D 2
    rw [two_mul, h, Nat.add_zero] at hdm
    linarith⟩

/-- Congruence modulo `2 * n` of doubles is congruence modulo `n`. -/
lemma two_mul_mod_eq_iff (a b n : ℕ) :
    (2 * a) % (2 * n) = (2 * b) % (2 * n) ↔ a % n = b % n := by
  rw [Nat.mul_mod_mul_left, Nat.mul_mod_mul_left]
  constructor
  · intro h; omega
  · intro h; omega

/-- Shifting the first summand to its residue does not change the total residue. -/
lemma mod_add_mod_left (a b c : ℕ) : (a % c + b) % c = (a + b) % c :=
  Nat.ModEq.add_right b (Nat.mod_modEq a c)

/-- A balanced increment forces even half-step: `D + P = Q + 2 * m` and `P ≡ Q (mod 2)`
imply `D` is even. -/
lemma balance_even {D P Q m : ℕ} (h : D + P = Q + 2 * m)
    (hpq : P % 2 = Q % 2) : D % 2 = 0 := by
  have h1 : (D + P) % 2 = (Q + 2 * m) % 2 := by rw [h]
  rw [show (Q + 2 * m) % 2 = Q % 2 from by
      rw [Nat.add_mod, Nat.mul_mod_right, Nat.add_zero, Nat.mod_mod]] at h1
  rw [Nat.add_mod] at h1
  rw [← hpq] at h1
  -- h1 : (D % 2 + P % 2) % 2 = P % 2 % 2
  rcases Nat.mod_two_eq_zero_or_one D with hD0 | hD1
  · exact hD0
  · rcases Nat.mod_two_eq_zero_or_one P with hP0 | hP1
    · rw [hD1, hP0] at h1; simp at h1
    · rw [hD1, hP1] at h1; simp at h1

/-- Any residue class of the same parity as `p` is reached by `p + 2 * t` with `t < n`. -/
lemma exists_lt_add_two_mul (p q n : ℕ) (hn : 0 < n) (hpar : p % 2 = q % 2) :
    ∃ t, t < n ∧ (p + 2 * t) % (2 * n) = q % (2 * n) := by
  have hdvd : 2 ∣ 2 * n := Nat.dvd_mul_right 2 n
  have e1' : p % (2 * n) % 2 = p % 2 := Nat.mod_mod_of_dvd _ hdvd
  have e2' : q % (2 * n) % 2 = q % 2 := Nat.mod_mod_of_dvd _ hdvd
  obtain ⟨D, hD⟩ : ∃ D, D + p % (2 * n) = q % (2 * n) + 2 * n :=
    ⟨q % (2 * n) + 2 * n - p % (2 * n),
      Nat.sub_add_cancel (by
        have hlt : p % (2 * n) < 2 * n := Nat.mod_lt _ (by positivity)
        have hq0 : (0:Nat) <= q % (2 * n) := Nat.zero_le _
        linarith)⟩
  have hpar2 : p % (2 * n) % 2 = q % (2 * n) % 2 := by rw [e1', e2', hpar]
  have hDeven : D % 2 = 0 := balance_even hD hpar2
  obtain ⟨K, hK⟩ := exists_two_mul_of_mod_two_eq_zero hDeven
  have hk : p % (2 * n) + 2 * K = q % (2 * n) + 2 * n := by linarith [hD, hK]
  refine ⟨K % n, Nat.mod_lt _ hn, ?_⟩
  -- balance identity
  have hKsplit : n * (K / n) + K % n = K := Nat.div_add_mod K n
  have hbal : p % (2 * n) + 2 * K
      = p % (2 * n) + 2 * (K % n) + 2 * n * (K / n) := by
    have h2X : 2 * n * (K / n) = 2 * (n * (K / n)) := by ring
    have hK2 : (2:Nat) * ((n * (K / n)) + K % n) = 2 * (n * (K / n)) + 2 * (K % n) := by
      rw [Nat.mul_add]
    have hK3 : (2:Nat) * ((n * (K / n)) + K % n) = 2 * K := by rw [hKsplit]
    linarith
  -- stripping the divisible tails
  have hdvdA : (2 * n) ∣ 2 * n * (K / n) := Dvd.intro (K / n) rfl
  have T1 : ((p % (2 * n) + 2 * (K % n)) + 2 * n * (K / n)) % (2 * n)
      = (p % (2 * n) + 2 * (K % n)) % (2 * n) :=
    add_dvd_mod (p % (2 * n) + 2 * (K % n)) (2 * n * (K / n)) (2 * n) hdvdA
  calc (p + 2 * (K % n)) % (2 * n)
      = (p % (2 * n) + 2 * (K % n)) % (2 * n) :=
        (mod_add_mod_left p (2 * (K % n)) (2 * n)).symm
    _ = ((p % (2 * n) + 2 * (K % n)) + 2 * n * (K / n)) % (2 * n) := T1.symm
    _ = (p % (2 * n) + 2 * K) % (2 * n) := by rw [hbal]
    _ = q % (2 * n) := by
        have hkAdd : p % (2 * n) + 2 * K = q % (2 * n) + 2 * n := by omega
        rw [hkAdd, Nat.add_mod_right]
        exact Nat.mod_eq_of_lt (Nat.mod_lt q (by positivity))

/-- Every unit hits every residue class modulo `n`. -/
lemma exists_mul_mod_eq_of_isUnit (u n t : ℕ) (hn : 0 < n) (hu : IsUnit (u : ZMod n)) :
    ∃ R, R < n ∧ (u * R) % n = t % n := by
  obtain ⟨v, hv⟩ := hu
  have hinv : (↑(v⁻¹) : ZMod n) * (u : ZMod n) = 1 := by
    rw [← hv]
    exact Units.inv_mul_of_eq rfl
  obtain ⟨w, hw⟩ : ∃ w : ℕ, w = ZMod.val (↑(v⁻¹) : ZMod n) := ⟨_, rfl⟩
  haveI : NeZero n := ⟨ne_of_gt hn⟩
  have hcast : ((w : ℕ) : ZMod n) = (↑(v⁻¹) : ZMod n) := by
    rw [hw]
    simpa using ZMod.natCast_val (R := ZMod n) (↑(v⁻¹) : ZMod n)
  have hwu : (w * u) % n = 1 % n := by
    have hz : ((w * u : ℕ) : ZMod n) = ((1 : ℕ) : ZMod n) := by
      push_cast
      rw [hcast, hinv]
    exact (ZMod.natCast_eq_natCast_iff (w * u) 1 n).mp hz
  refine ⟨(w * t) % n, Nat.mod_lt _ hn, ?_⟩
  have me1 : u * ((w * t) % n) ≡ u * (w * t) [MOD n] :=
    Nat.ModEq.mul_left u (Nat.mod_modEq (w * t) n)
  have me2 : u * w ≡ 1 [MOD n] := by
    rw [Nat.mul_comm]
    exact hwu
  have me3 : (u * w) * t ≡ 1 * t [MOD n] := Nat.ModEq.mul_right t me2
  have me4 : u * ((w * t) % n) ≡ (u * w) * t [MOD n] := by
    rw [Nat.mul_assoc]; try exact me1
  have fin : (1 : ℕ) * t ≡ t [MOD n] := by
    rw [Nat.one_mul]
  exact me4.trans (me3.trans fin)

/-! ### Main transport lemma -/

lemma endpoint_bijection (d m y_w r : ℕ) (h_m : 2 ≤ m)
    (hy : Odd y_w) (hr : Odd r)
    (h_unit : IsUnit ((3 : ZMod (2^(m-1)))^d)) :
    ∃ R < 2^(m-1), ∀ q,
      (y_w + 2 * 3^d * q) % 2^m = r % 2^m ↔ q % 2^(m-1) = R := by
  set n := 2^(m-1) with hn_def
  have hn : 0 < n := by
    rw [hn_def]
    exact Nat.two_pow_pos _
  have hm1 : m = (m - 1) + 1 := by omega
  have hpow : 2 ^ m = 2 * n := by
    rw [hm1, Nat.pow_succ]
    ring
  rw [hpow]
  -- both endpoints are odd, hence some shift t0 < n realizes r from y_w
  have hpar : y_w % 2 = r % 2 := by
    rw [Nat.odd_iff.mp hy, Nat.odd_iff.mp hr]
  obtain ⟨t0, ht0lt, ht0⟩ := exists_lt_add_two_mul y_w r n hn hpar
  -- choose R < n with 3^d * R ≡ t0 (mod n)
  have hunit' : IsUnit ((3 ^ d : ℕ) : ZMod n) := by
    have heq : ((3 ^ d : ℕ) : ZMod n) = ((3 : ZMod n) ^ d) := by
      simp
    rw [heq]
    exact h_unit
  obtain ⟨R, hRlt, hR⟩ := exists_mul_mod_eq_of_isUnit (3 ^ d) n t0 hn hunit'
  refine ⟨R, hRlt, fun q => ?_⟩
  have step1 : ((y_w + 2 * 3 ^ d * q) % (2 * n) = r % (2 * n))
      ↔ ((y_w + 2 * 3 ^ d * q) % (2 * n) = (y_w + 2 * t0) % (2 * n)) := by rw [ht0]
  have step2 : ((y_w + 2 * 3 ^ d * q) % (2 * n) = (y_w + 2 * t0) % (2 * n))
      ↔ ((2 * 3 ^ d * q) % (2 * n) = (2 * t0) % (2 * n)) :=
    add_cancel_mod _ _ _ _ (by positivity)
  have step3 : ((2 * 3 ^ d * q) % (2 * n) = (2 * t0) % (2 * n))
      ↔ ((3 ^ d * q) % n = t0 % n) := by
    rw [Nat.mul_assoc]
    exact two_mul_mod_eq_iff _ _ _
  have step4 : ((3 ^ d * q) % n = t0 % n)
      ↔ ((3 ^ d * q) % n = (3 ^ d * R) % n) := by rw [hR]
  have step5 : ((3 ^ d * q) % n = (3 ^ d * R) % n)
      ↔ (q % n = R) := mul_unit_mod_equiv d m q R h_m hRlt h_unit
  exact step1.trans (step2.trans (step3.trans (step4.trans step5)))
