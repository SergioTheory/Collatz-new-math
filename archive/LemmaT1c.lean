import Mathlib

open Finset

noncomputable def countResidue (a b r n : ℕ) : ℕ :=
  (Finset.Icc a b).filter (fun x => x % n = r % n) |>.card

lemma countResidue_eq_div (a b r n : ℕ) (hn : 0 < n) (hr : r < n) (hab : a ≤ b) :
    countResidue a b r n = 
    (b + n - r) / n - (a + n - 1 - r) / n := by
  sorry

lemma nat_div_bounds (x n : ℕ) (hn : 0 < n) :
    (x : ℝ) / (n : ℝ) - 1 < ((x / n : ℕ) : ℝ) ∧ ((x / n : ℕ) : ℝ) ≤ (x : ℝ) / (n : ℝ) := by
  constructor
  · have h1 : x < n * (x / n + 1) := Nat.lt_succ_div_mul x hn
    have h2 : (x : ℝ) < (n : ℝ) * ((x / n : ℕ) : ℝ) + (n : ℝ) := by
      calc (x : ℝ) < ↑(n * (x / n + 1)) := by exact_mod_cast h1
      _ = (n : ℝ) * ((x / n : ℕ) : ℝ) + (n : ℝ) := by push_cast; ring
    have hn_pos : (n : ℝ) > 0 := by exact_mod_cast hn
    rw [← sub_lt_iff_lt_add']
    exact (div_lt_iff₀ hn_pos).mpr h2
  · have h3 : n * (x / n) ≤ x := Nat.div_mul_le_self x n
    have hn_pos : (n : ℝ) > 0 := by exact_mod_cast hn
    rw [le_div_iff₀ hn_pos]
    exact_mod_cast h3

lemma count_residue_discrepancy (a b r n : ℕ)
    (hn : 1 < n) (hr : r < n) (hab : a ≤ b) :
    |((countResidue a b r n : ℝ)) - ((b - a + 1 : ℝ) / (n : ℝ))| ≤ 1 := by
  have hn0 : 0 < n := by omega
  rw [countResidue_eq_div a b r n hn0 hr hab]
  set u := b + n - r
  set v := a + n - 1 - r
  have huv_int : (u : ℤ) - (v : ℤ) = (b : ℤ) - (a : ℤ) + 1 := by omega
  have huv : (u : ℝ) - (v : ℝ) = (b : ℝ) - (a : ℝ) + 1 := by exact_mod_cast huv_int
  have huv_le : v ≤ u := by omega
  have huv_div : v / n ≤ u / n := Nat.div_le_div_right huv_le
  have hc : (((u / n - v / n : ℕ) : ℝ)) = ((u / n : ℕ) : ℝ) - ((v / n : ℕ) : ℝ) := by
    exact_mod_cast Nat.cast_sub huv_div
  rw [hc]
  have h_frac : ((b : ℝ) - (a : ℝ) + 1) / (n : ℝ) = ((u : ℝ) - (v : ℝ)) / (n : ℝ) := by rw [huv]
  rw [h_frac, abs_le]
  have hu := nat_div_bounds u n hn0
  have hv := nat_div_bounds v n hn0
  constructor <;> linarith [hu.1, hu.2, hv.1, hv.2]
