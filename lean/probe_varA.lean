import Mathlib
open Nat

-- Variant A: noncomputable + subscripts + unfold (как в SurvivalCutoff)
noncomputable def wordMap (d S c x : ℕ) : ℕ := (3 ^ d * x + c) / 2 ^ S

def survivesWord (d S c B x : ℕ) : Prop := B ≤ wordMap d S c x

lemma wordMap_mono {d S c x₁ x₂ : ℕ} (h : x₁ ≤ x₂) :
    wordMap d S c x₁ ≤ wordMap d S c x₂ := by
  unfold wordMap
  exact Nat.div_le_div_right <|
    Nat.add_le_add (Nat.mul_le_mul_left _ h) (le_refl c)

lemma survival_suffix_lift {d S c B q₁ q₂ : ℕ} (hle : q₁ ≤ q₂)
    (hsurv : survivesWord d S c B q₁) :
    survivesWord d S c B q₂ :=
  le_trans hsurv (wordMap_mono hle)
