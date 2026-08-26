import Mathlib

-- T1: pure order arithmetic
example {B q1 q2 : ℕ} (hle : q1 ≤ q2) (hs : B ≤ q1) : B ≤ q2 :=
  le_trans hs hle

-- T2: through def-wrapper
def wrappedLE (B x : ℕ) : Prop := B ≤ x

example {B q1 q2 : ℕ} (hle : q1 ≤ q2) (hs : wrappedLE B q1) : wrappedLE B q2 := by
  unfold wrappedLE
  exact le_trans hs (le_refl q2)

-- T3: noncomputable wrapper over div
noncomputable def wordMap (d S c x : ℕ) : ℕ := (3 ^ d * x + c) / 2 ^ S

example {d S c B q1 q2 : ℕ} (hle : q1 ≤ q2)
    (hsurv : B ≤ wordMap d S c q1) : B ≤ wordMap d S c q2 := by
  refine le_trans hsurv ?_
  exact wordMap_mono hle

-- T4: with subscripted names AND survivesWord indirection
example {d S c B q₁ q₂ : ℕ} (hle : q₁ ≤ q₂)
    (hsurv : survivesWord d S c B q₁) : survivesWord d S c B q₂ := by
  refine le_trans hsurv ?_
  exact wordMap_mono hle
