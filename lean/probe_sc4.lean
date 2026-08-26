import Mathlib

noncomputable def wordMap (d S c x : ℕ) : ℕ := (3 ^ d * x + c) / 2 ^ S

def survivesWord (d S c B x : ℕ) : Prop := B ≤ wordMap d S c x

lemma wordMap_mono {d S c x₁ x₂ : ℕ} (h : x₁ ≤ x₂) :
    wordMap d S c x₁ ≤ wordMap d S c x₂ := by
  unfold wordMap
  exact Nat.div_le_div_right <|
    Nat.add_le_add (Nat.mul_le_mul_left _ h) (le_refl c)

lemma survival_suffix_lift {d S c B q1 q2 : ℕ} (hle : q1 ≤ q2)
    (hsurv : survivesWord d S c B q1) :
    survivesWord d S c B q2 := by
  refine le_trans hsur ?_
  refine wordMap_mono ?_
  omega
