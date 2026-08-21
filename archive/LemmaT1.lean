import Mathlib.Data.Real.Basic
import Mathlib.Data.Nat.Choose.Basic
import Mathlib.NumberTheory.Padics.PadicIntegers
import Mathlib.MeasureTheory.Measure.Haar.Basic
import Mathlib.MeasureTheory.Measure.MeasureSpace
import Mathlib.Algebra.Group.Basic
import Mathlib.Data.ZMod.Basic

open MeasureTheory
open scoped Padic

section AdmissibleWords

structure AdmissibleWord where
  d : ℕ          
  S : ℕ          
  cw : ℤ         
  h_weight : d ≤ S  

noncomputable def T_w (w : AdmissibleWord) (x : ℤ_[2]) : ℤ_[2] :=
  ((3 : ℤ_[2])^(w.d) * x + (w.cw : ℤ_[2])) / (2 : ℤ_[2])^(w.S)

def Cylinder (w : AdmissibleWord) : Set ℤ_[2] :=
  {x : ℤ_[2] | ∃ (q : ℤ_[2]), x = (w.cw : ℤ_[2]) + (2 : ℤ_[2])^(w.S) * q}

noncomputable def rho_w (w : AdmissibleWord) : ℤ_[2] :=
  ((2 : ℤ_[2])^(w.S) - (w.cw : ℤ_[2])) * (3 : ℤ_[2])^(-(w.d : ℤ))

noncomputable def y_w (w : AdmissibleWord) : ℤ_[2] :=
  (w.cw : ℤ_[2]) / (2 : ℤ_[2])^(w.S)

end AdmissibleWords

section AuxiliaryLemmas

lemma three_is_unit : IsUnit (3 : ℤ_[2]) := by
  rw [isUnit_iff_ne_zero]
  norm_num

lemma three_pow_is_unit (d : ℕ) : IsUnit ((3 : ℤ_[2])^d) := by
  exact pow_isUnit three_is_unit d

lemma three_pow_odd (d : ℕ) : Odd (3^d : ℕ) := by
  exact Nat.odd_pow_of_odd (by norm_num) d

lemma three_pow_unit_mod (d m : ℕ) (hm : m ≥ 2) :
    IsUnit ((3^d : ZMod (2^(m-1)))) := by
  have h3 : IsUnit (3 : ZMod (2^(m-1))) := by
    rw [ZMod.isUnit_iff_ne_zero]
    have h : (3 : ZMod (2^(m-1))) ≠ 0 := by
      have h2 : 2^(m-1) > 3 ∨ m - 1 ≤ 1 := by
        omega
      cases h2 with
      | inl h2 =>
        have : (3 : ZMod (2^(m-1))) ≠ 0 := by
          intro h3eq0
          have := ZMod.val_eq_zero_iff.mp h3eq0
          have : (2^(m-1) : ℕ) ∣ 3 := this
          have : (2^(m-1) : ℕ) ≤ 3 := Nat.le_of_dvd (by norm_num) this
          omega
        exact this
      | inr h2 =>
        have hm2 : m = 2 := by omega
        subst hm2
        norm_num
    exact h
  exact pow_isUnit h3 d

noncomputable def count_in_residue (a b r n : ℤ) : ℕ :=
  (Finset.Icc a b).filter (fun x => x % n = r % n) |>.card

lemma count_residue_discrepancy (a b r n : ℤ) (hn : 0 < n) :
    |((count_in_residue a b r n : ℝ)) - ((b - a + 1 : ℝ) / n)| ≤ 1 := by
  sorry

lemma word_count_bound (d : ℕ) :
    ∑ S in Finset.range (2*d + 1), (Nat.choose (S-1) (d-1)) ≤ 2^d := by
  sorry

end AuxiliaryLemmas
