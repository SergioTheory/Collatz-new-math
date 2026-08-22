import Mathlib

open Finset

noncomputable def countResidue (a b r n : ℕ) : ℕ :=
  (Finset.Icc a b).filter (fun x => x % n = r % n) |>.card

lemma count_le (X r n : ℕ) (hn : 0 < n) (hr : r < n) :
    ((Finset.range (X + 1)).filter (fun x => x % n = r)).card = (X + n - r) / n := by
  induction' X with X ih
  · rw [Finset.range_one]
    by_cases h : r = 0
    · subst h; simp
    · have h2 : 0 % n ≠ r := by omega
      simp [h2]
      have h3 : n - r < n := by omega
      exact (Nat.div_eq_of_lt h3).symm
  · rw [Finset.range_succ, Finset.filter_insert]
    split_ifs with h
    · rw [Finset.card_insert_of_not_mem, ih]
      · exact (show (X + 1 + n - r) / n = (X + n - r) / n + 1 by omega).symm
      · simp
    · rw [ih]
      exact (show (X + 1 + n - r) / n = (X + n - r) / n by omega).symm

lemma countResidue_eq_div (a b r n : ℕ) (hn : 0 < n) (hr : r < n) (hab : a ≤ b) :
    countResidue a b r n = 
    (b + n - r) / n - (a + n - 1 - r) / n := by
  have h_Icc : Finset.Icc a b = Finset.range (b + 1) \ Finset.range a := by
    ext x; simp; omega
  have h_mod : (fun x => x % n = r % n) = (fun x => x % n = r) := by
    ext x; rw [Nat.mod_eq_of_lt hr]
  rw [countResidue, h_Icc, h_mod, Finset.filter_sdiff, Finset.card_sdiff]
  · by_cases ha : a = 0
    · subst ha
      simp
      have hz : (n - 1 - r) / n = 0 := by
        apply Nat.div_eq_of_lt
        omega
      rw [hz, Nat.sub_zero]
      exact count_le b r n hn hr
    · have h_range_a : Finset.range a = Finset.range (a - 1 + 1) := by
        congr 1; omega
      rw [h_range_a, count_le (a - 1) r n hn hr, count_le b r n hn hr]
  · apply Finset.filter_subset_filter
    apply Finset.range_subset.mpr
    omega
