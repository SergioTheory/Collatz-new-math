import Mathlib

-- T0: базовая резолюция гипотезы
example {B x : ℕ} (hs : B ≤ x) : B ≤ x := hs

-- T1: через def-обёртку
def wrappedLE (B x : ℕ) : Prop := B ≤ x

example {B x : ℕ} (hs : wrappedLE B x) : wrappedLE B x := hs

-- T2: noncomputable wrapper над div
noncomputable def wrapNC (d S c x : ℕ) : ℕ := (3 ^ d * x + c) / 2 ^ S

example {d S c B x : ℕ} (hsurv : B ≤ wrapNC d S c x) : B ≤ wrapNC d S c x := hsurv

-- T3: с неявными переменными и subscripts
example {d S c B q₁ q₂ : ℕ} (hle : q₁ ≤ q₂)
    (hsurv : B ≤ wrapNC d S c q₁) : B ≤ wrapNC d S c q₂ :=
  le_trans hsurv (by gcongr)
