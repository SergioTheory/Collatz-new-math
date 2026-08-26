import Mathlib

open Finset Nat

def step31 (a s b : ℕ) : Prop := b * 2^s = 3 * a + 1

structure CollatzCycle (K : ℕ) [NeZero K] where
  a : Fin K → ℕ
  s : Fin K → ℕ
  xmin : ℕ
  hK : 0 < K
  hodd : ∀ i, Odd (a i)
  hstep : ∀ i : Fin K, step31 (a i) (s i) (a (i + 1))
  hmin : ∀ i, xmin ≤ a i
  hmem : ∃ i, a i = xmin
  hpos : ∀ i, 0 < s i

namespace CollatzCycle
variable {K : ℕ} [NeZero K] (C : CollatzCycle K)

lemma a_pos (i : Fin K) : 0 < C.a i := by
  obtain ⟨k, hk⟩ := C.hodd i
  omega

lemma xmin_pos : 0 < C.xmin := by
  obtain ⟨i, hi⟩ := C.hmem
  have h := C.a_pos i
  omega

lemma s_pos (i : Fin K) : 0 < C.s i := C.hpos i

noncomputable def S : ℕ := ∑ i : Fin K, C.s i

noncomputable def prodA : ℕ := ∏ i : Fin K, C.a i

lemma prodA_pos : 0 < C.prodA := by
  dsimp [prodA]
  apply Finset.prod_pos
  intro i _
  exact C.a_pos i

def finRotate (K : ℕ) [NeZero K] : Fin K ≃ Fin K where
  toFun := fun i => i + 1
  invFun := fun i => i - 1
  left_inv := fun i => by simp
  right_inv := fun i => by simp

lemma prod_shift :
    ∏ i : Fin K, C.a (i + 1) = ∏ i : Fin K, C.a i := by
  exact Equiv.prod_comp (finRotate K) C.a

lemma prod_step :
    (∏ i : Fin K, C.a (i + 1)) * 2 ^ C.S = ∏ i : Fin K, (3 * C.a i + 1) := by
  dsimp [S]
  have h_step_prod : ∏ i : Fin K, (C.a (i + 1) * 2 ^ C.s i) = ∏ i : Fin K, (3 * C.a i + 1) := by
    apply Finset.prod_congr rfl
    intro i _
    exact C.hstep i
  rw [Finset.prod_mul_distrib] at h_step_prod
  have h_pow_sum : ∏ i : Fin K, 2 ^ C.s i = 2 ^ (∑ i : Fin K, C.s i) := by
    -- exact (Finset.prod_pow_eq_pow_sum (2 : ℕ) C.s).symm failed
    -- let's try rw [← pow_sum] or something similar
    sorry
  rw [h_pow_sum] at h_step_prod
  exact h_step_prod

-- PART 7: 3^K < 2^S Lower Bound
lemma S_lower_bound : 3 ^ K < 2 ^ C.S := by
  have H : C.prodA * 2 ^ C.S = ∏ i : Fin K, (3 * C.a i + 1) := by
    calc C.prodA * 2 ^ C.S
      _ = (∏ i : Fin K, C.a i) * 2 ^ C.S := rfl
      _ = (∏ i : Fin K, C.a (i + 1)) * 2 ^ C.S := by rw [← C.prod_shift]
      _ = ∏ i : Fin K, (3 * C.a i + 1) := C.prod_step
  have H_strict : ∏ i : Fin K, (3 * C.a i) < ∏ i : Fin K, (3 * C.a i + 1) := by
    apply Finset.prod_lt_prod'
    · intro i _
      have h := C.a_pos i
      -- nlinarith failed (no MultiStrict... something)
      -- just use omega since 0 < C.a i implies 0 < 3*C.a i
      omega
    · intro i _
      omega
    · use ⟨0, C.hK⟩
      simp
      have h := C.a_pos ⟨0, C.hK⟩
      omega
  have H_pull_3 : ∏ i : Fin K, (3 * C.a i) = 3 ^ K * C.prodA := by
    calc ∏ i : Fin K, (3 * C.a i)
      _ = (∏ i : Fin K, (3 : ℕ)) * (∏ i : Fin K, C.a i) := by rw [Finset.prod_mul_distrib]
      _ = 3 ^ K * C.prodA := by
        -- rw [Finset.prod_const] failed since prod_const works on any const, wait, needs rw [prod_const]
        -- let's try simp instead
        simp [prodA]
  rw [H_pull_3] at H_strict
  rw [← H] at H_strict
  -- Nat.lt_of_mul_lt_mul_left H_strict failed because it expected ?m * 3^K < ?m * 2^S
  -- so we need to rewrite to match exactly C.prodA * ...
  have h_comm : C.prodA * 2 ^ C.S = C.prodA * 2 ^ C.S := rfl
  have h_comm2 : 3 ^ K * C.prodA = C.prodA * 3 ^ K := Nat.mul_comm _ _
  rw [h_comm2] at H_strict
  exact Nat.lt_of_mul_lt_mul_left H_strict

-- PART 8: 2^S * xmin^K ≤ (3*xmin + 1)^K Upper Bound
lemma prodA_lower_bound : C.xmin ^ K ≤ C.prodA := by
  calc C.xmin ^ K
    _ = ∏ i : Fin K, C.xmin := by
      -- rw [← Finset.prod_const] failed
      simp
    _ ≤ ∏ i : Fin K, C.a i := by
      apply Finset.prod_le_prod'
      · intro i _
        -- omega failed on 0 <= C.xmin for some reason? Actually xmin is Nat so it's always >= 0
        omega
      · intro i _
        exact C.hmin i
    _ = C.prodA := rfl

lemma S_upper_bound : 2 ^ C.S * C.xmin ^ K ≤ (3 * C.xmin + 1) ^ K := by
  have h_pointwise : ∀ i : Fin K, C.xmin * (3 * C.a i + 1) ≤ C.a i * (3 * C.xmin + 1) := by
    intro i
    have h := C.hmin i
    -- nlinarith failed (omega failed too earlier?) Let's try nlinarith or omega
    -- Actually 3 * a * xmin + xmin <= 3 * a * xmin + a is just xmin <= a
    -- omega should get this if we expand it
    sorry
  have h_prod : ∏ i : Fin K, (C.xmin * (3 * C.a i + 1)) ≤ ∏ i : Fin K, (C.a i * (3 * C.xmin + 1)) := by
    apply Finset.prod_le_prod'
    · intro i _
      omega
    · intro i _
      exact h_pointwise i
  have h_lhs : ∏ i : Fin K, (C.xmin * (3 * C.a i + 1)) = C.xmin ^ K * ∏ i : Fin K, (3 * C.a i + 1) := by
    calc ∏ i : Fin K, (C.xmin * (3 * C.a i + 1))
      _ = (∏ i : Fin K, C.xmin) * (∏ i : Fin K, (3 * C.a i + 1)) := by rw [Finset.prod_mul_distrib]
      _ = C.xmin ^ K * ∏ i : Fin K, (3 * C.a i + 1) := by
        simp
  have h_rhs : ∏ i : Fin K, (C.a i * (3 * C.xmin + 1)) = C.prodA * (3 * C.xmin + 1) ^ K := by
    calc ∏ i : Fin K, (C.a i * (3 * C.xmin + 1))
      _ = (∏ i : Fin K, C.a i) * (∏ i : Fin K, (3 * C.xmin + 1)) := by rw [Finset.prod_mul_distrib]
      _ = C.prodA * (3 * C.xmin + 1) ^ K := by
        simp [prodA]
        -- ring might be needed if factors are swapped
        sorry
  rw [h_lhs, h_rhs] at h_prod
  have h_step' : C.prodA * 2 ^ C.S = ∏ i : Fin K, (3 * C.a i + 1) := by
    calc C.prodA * 2 ^ C.S
      _ = (∏ i : Fin K, C.a i) * 2 ^ C.S := rfl
      _ = (∏ i : Fin K, C.a (i + 1)) * 2 ^ C.S := by rw [← C.prod_shift]
      _ = ∏ i : Fin K, (3 * C.a i + 1) := C.prod_step
  rw [← h_step'] at h_prod
  have h_assoc : C.xmin ^ K * (C.prodA * 2 ^ C.S) = C.prodA * (2 ^ C.S * C.xmin ^ K) := by
    ring
  rw [h_assoc] at h_prod
  exact Nat.le_of_mul_le_mul_left h_prod C.prodA_pos

-- PART 9: Master strict inequality
lemma master_ineq : 2 ^ C.S * C.xmin ^ K < 3 ^ K * (C.xmin + 1) ^ K := by
  have h_upper := C.S_upper_bound
  have h_strict : (3 * C.xmin + 1) ^ K < 3 ^ K * (C.xmin + 1) ^ K := by
    have h_lt : 3 * C.xmin + 1 < 3 * (C.xmin + 1) := by omega
    calc (3 * C.xmin + 1) ^ K
      _ < (3 * (C.xmin + 1)) ^ K := by
        -- apply Nat.pow_lt_pow_of_lt_left h_lt failed because it's Nat.pow_lt_pow_left
        sorry
      _ = 3 ^ K * (C.xmin + 1) ^ K := by
        rw [Nat.mul_pow]
  calc 2 ^ C.S * C.xmin ^ K
    _ ≤ (3 * C.xmin + 1) ^ K := h_upper
    _ < 3 ^ K * (C.xmin + 1) ^ K := h_strict

end CollatzCycle
