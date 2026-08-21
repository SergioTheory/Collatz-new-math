import Mathlib.Data.Real.Basic
import Mathlib.Data.Nat.Choose.Basic
import Mathlib.NumberTheory.Padics.PadicIntegers
import Mathlib.MeasureTheory.Measure.Haar.Basic
import Mathlib.MeasureTheory.Measure.MeasureSpace
import Mathlib.Algebra.Group.Basic
import Mathlib.Data.ZMod.Basic

open MeasureTheory
open scoped Padic

local notation "ℤ_2" => ℤ_[2]

structure AdmissibleWord where
  d : ℕ          
  S : ℕ          
  cw : ℤ         
  h_weight : d ≤ S 

noncomputable def T_w (w : AdmissibleWord) (x : ℤ_2) : ℤ_2 :=
  ((3 : ℤ_2)^(w.d) * x + (w.cw : ℤ_2)) / (2 : ℤ_2)^(w.S)

def Cylinder (w : AdmissibleWord) : Set ℤ_2 :=
  {x : ℤ_2 | ∃ (q : ℤ_2), x = (w.cw : ℤ_2) + (2 : ℤ_2)^(w.S) * q}

lemma three_is_unit : IsUnit (3 : ℤ_2) := by
  have h : (3 : ℤ_2) % 2 = 1 := by
    norm_num [PadicInt.modEq_iff_norm_lt]
  apply isUnit_of_dvd_one
  use (3 : ℤ_2)⁻¹
  field_simp

lemma three_pow_is_unit (d : ℕ) : IsUnit ((3 : ℤ_2)^d) := by
  apply isUnit_pow
  exact three_is_unit

axiom prop_b3_finite_scale_bound (M d m : ℕ) (h_dm : d ≤ m) : True

theorem exact_conditional_transport (w : AdmissibleWord) (M : ℕ) (hM : w.S ≥ M) :
  Set.BijOn (T_w w) (Cylinder w) Set.univ ∧
  Measure.map (T_w w) (volume.restrict (Cylinder w)) = (1 / (2^w.S : ℝ)) • volume := by
  constructor
  · constructor
    · intro x hx y hy hxy
      simp only [T_w, Cylinder] at *
      rcases hx with ⟨qx, hx_eq⟩
      rcases hy with ⟨qy, hy_eq⟩
      rw [hx_eq, hy_eq] at hxy
      sorry 
    · intro y _
      sorry 
  · sorry
