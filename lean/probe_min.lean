import Mathlib

noncomputable def wordMap (d S c x : ℕ) : ℕ := (3 ^ d * x + c) / 2 ^ S

def survivesWord (d S c B x : ℕ) : Prop := B ≤ wordMap d S c x

-- T1: trivial reference to bound hypothesis
example {B x : ℕ} (hs : B ≤ x) : B ≤ x := hs

-- T2: through wrapper def
example {B x : ℕ} (hsurv : survivesWord B x) : survivesWord B x := hsurv

-- T3: with extra unused binders and subscripts
example {d S c B q₁ q₂ : ℕ} (hle : q₁ ≤ q₂)
    (hsurv : survivesWord d S c B q₁) : True := trivial

-- T4: le_trans with wrapper
example {d S c B q₁ q₂ : ℕ} (hle : q₁ ≤ q₂)
    (hsurv : survivesWord d S c B q₁) : survivesWord d S c B q₂ := by
  refine le_trans hsur ?_
  exact wordMap_mono hle
