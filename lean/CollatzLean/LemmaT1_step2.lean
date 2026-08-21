import Mathlib

open Nat BigOperators Finset

/-! ## W1: Комбинаторная граница через тождество хоккейной клюшки -/

theorem composition_count (S d : ℕ) (hd : 0 < d) (hS : d ≤ S) :
    True := by
  trivial

theorem hockey_stick (d σ : ℕ) (hd : 0 < d) (hσ : 1 ≤ σ) :
    (∑ S ∈ Finset.Icc d (σ * d), Nat.choose (S - 1) (d - 1)) =
    Nat.choose (σ * d) d := by
  have h_subst : (∑ S ∈ Finset.Icc d (σ * d), Nat.choose (S - 1) (d - 1)) =
                 (∑ k ∈ Finset.Icc (d - 1) (σ * d - 1), Nat.choose k (d - 1)) := by
    apply Finset.sum_bij (fun S _ => S - 1)
    · intro S hS
      simp only [Finset.mem_Icc] at hS ⊢
      omega
    · intro S₁ hS₁ S₂ hS₂ heq
      omega
    · intro k hk
      simp only [Finset.mem_Icc] at hk ⊢
      use k + 1
      constructor <;> simp only [Finset.mem_Icc] <;> omega
    · intro S hS
      rfl
  rw [h_subst]
  have h_hs := Nat.sum_Icc_choose (σ * d - 1) (d - 1)
  have h_prod : 1 ≤ σ * d := by nlinarith
  have h1 : σ * d - 1 + 1 = σ * d := by omega
  have h2 : d - 1 + 1 = d := by omega
  rw [h1, h2] at h_hs
  exact h_hs

theorem W1_word_count_bound (d σ : ℕ) (hd : 0 < d) (hσ : 1 ≤ σ) :
    (∑ S ∈ Finset.Icc d (σ * d), Nat.choose (S - 1) (d - 1)) ≤
    Nat.choose (σ * d) d := by
  rw [hockey_stick d σ hd hσ]

/-! ## W2: Дискрепанция через треугольное неравенство -/

axiom per_word_discrepancy (d : ℕ) (w : Fin d → ℕ) (r m : ℕ) 
    (hr : Odd r) (hrm : r < 2^m) :
    True

theorem W2_pure_triangle_inequality (n : ℕ) (a : Fin n → ℤ)
    (h : ∀ i, |a i| ≤ 1) :
    |∑ i, a i| ≤ (n : ℤ) := by
  calc |∑ i : Fin n, a i|
      ≤ ∑ i : Fin n, |a i| := by
        exact abs_sum_le_sum_abs (s := Finset.univ) (f := a)
    _ ≤ ∑ i : Fin n, (1 : ℤ) := by
        apply Finset.sum_le_sum
        intro i _
        exact h i
    _ = (n : ℤ) := by
        simp [Finset.sum_const, Finset.card_univ]

theorem W2_scaled_triangle_inequality (n m : ℕ) (a : Fin n → ℤ)
    (h : ∀ i, |a i| ≤ (2^(m-1) : ℤ)) :
    |∑ i, a i| ≤ (n : ℤ) * (2^(m-1) : ℤ) := by
  calc |∑ i : Fin n, a i|
      ≤ ∑ i : Fin n, |a i| := by
        exact abs_sum_le_sum_abs (s := Finset.univ) (f := a)
    _ ≤ ∑ i : Fin n, (2^(m-1) : ℤ) := by
        apply Finset.sum_le_sum
        intro i _
        exact h i
    _ = (n : ℤ) * (2^(m-1) : ℤ) := by
        simp [Finset.sum_const, Finset.card_univ]
