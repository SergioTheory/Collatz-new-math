import Mathlib
import CollatzLean.ShadowEscape

/-!
# ShadowDescent: from Shadow Growth to LTE Descent (Path A)

## Honest purpose

`ShadowEscape` established the *growth* structure of the class `n = M·2^a − 1`:
for `a` steps the orbit follows `M·3^j·2^(a-j) − 1`, then at the exit
(`j = a`) it reaches a value `Y` with

    Y · 2^s = 2·(M·3^a − 1),   s = 1 + v₂(M·3^a − 1).

This is a **Shadow Descent** file: it pins down the exact algebraic condition
under which the exit value `Y` is *strictly smaller than the starting value*
`n₀ = M·2^a − 1`.  Honest scope: we do NOT claim the Collatz conjecture; we
exactly describe when the stubborn `trailing-ones` class returns below its
start.

The descent condition involves the shift `s` itself (equivalently
`v₂(M·3^a − 1) + 1`): it is the moment when the *bonus* division by `2^s`
overcomes the `3/2`-growth of the mountain.

## Conventions

Shadow values are in `ℤ`, moves relational (`step31_Z`, shift `s : ℕ`), as in
`ShadowEscape`.  We avoid `Nat` subtraction by stating the descent condition
directly in `ℤ` with casts `(M : ℤ)`, `(3 : ℤ)`, `(2 : ℤ)`.

## Descent lemma

We avoid division: from `Y·2^s = 2·(M·3^a − 1)` (the exit relation) we prove
`Y < M·2^a − 1` by multiplying both sides of the inequality by the positive
`2^s` and then cancelling — pure `ℤ` integer arithmetic, no `ediv`.
-/

open Finset Nat

namespace ShadowDescent

open ShadowEscape

/-- Starting value of the shadow class. -/
def start_val (M a : ℕ) : ℤ := (M : ℤ) * (2 : ℤ)^a - 1

/-- **Descent of the exit value.**
If `Y·2^s = 2·(M·3^a − 1)` (the exit relation) and the scaled descent
inequality `2·(M·3^a − 1) < (M·2^a − 1)·2^s` holds, then
`Y < M·2^a − 1`: the exit lands strictly below the start. -/
lemma descent_exit (M a s Y : ℕ) (ha : 0 < a)
    (hstep : step31_Z (shadow_val_Z M a (a - 1)) Y s)
    (hcond : 2 * ((M : ℤ) * (3 : ℤ)^a - 1) <
      ((M : ℤ) * (2 : ℤ)^a - 1) * (2 : ℤ)^s) :
    (Y : ℤ) < start_val M a := by
  have hE : (Y : ℤ) * (2 : ℤ)^s = 2 * ((M : ℤ) * (3 : ℤ)^a - 1) :=
    shadow_exit_Z M a ha s (Y : ℤ) hstep
  have hs_ge : (0 : ℤ) ≤ (2 : ℤ)^s := by positivity
  have h_bound : (2 : ℤ)^s * (Y : ℤ) < (2 : ℤ)^s * ((M : ℤ) * (2 : ℤ)^a - 1) := by
    calc
      (2 : ℤ)^s * (Y : ℤ) = (Y : ℤ) * (2 : ℤ)^s := by ring
        _ = 2 * ((M : ℤ) * (3 : ℤ)^a - 1) := by rw [hE]
        _ < ((M : ℤ) * (2 : ℤ)^a - 1) * (2 : ℤ)^s := hcond
        _ = (2 : ℤ)^s * ((M : ℤ) * (2 : ℤ)^a - 1) := by ring
  have h_res : (Y : ℤ) < (M : ℤ) * (2 : ℤ)^a - 1 := by
    exact lt_of_mul_lt_mul_left h_bound hs_ge
  unfold start_val
  exact h_res

end ShadowDescent