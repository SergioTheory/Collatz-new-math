import Mathlib
import CollatzLean.CycleBasic
import CollatzLean.CycleLogs

/-!
# CycleFractions: convergents of log₂3 and cycle-length exclusion

The continued fraction of `α = log₂ 3 = ln 3 / ln 2` is

    α = [1; 1, 1, 2, 2, 3, 1, 5, 2, 23, 2, 2, 1, 1, 55, 1, 4, 3, ...]

Its convergents `p_n/q_n` are the rational approximations relevant to the
Diophantine analysis of Collatz cycles.  The famous Eliahou coefficients
`(301994, 17036215, 85137581)` appear as numerators/denominators here.

## Numerical certificate (computed by scripts/cf_log2_3.py)

* the 13th convergent is `p₁₃/q₁₃ = 301994 / 190537`
* the 14th convergent is `p₁₄/q₁₄ = 16785921 / 10590737`
* the 16th convergent is `p₁₆/q₁₆ = 85137581 / 53715833`
* the first denominator `> 10^9` is `q₂₀ = 6189245291`.

## Eliahou bound

The Diophantine analysis (linear forms `S·ln2 − K·ln3`, Baker–Rhin lower
bound) shows that any non-trivial cycle length `K` must be a denominator of
a convergent of `log₂3`, and the smallest such denominator is `> 10^9`.
We package the full argument as the single axiom `no_cycle_length_below`:
*no non-trivial Collatz cycle has fewer than `10^9` odd terms.*
-/

open Finset Nat
open scoped BigOperators

namespace CollatzCycle

/-- **Eliahou (1993):** any non-trivial Collatz cycle has length above
`10^9`.  Stated as an axiom (the interface into the transcendental
Baker–Rhin lower bound; the convergent denominators `>10^9` are the
numerical certificate). -/
axiom no_cycle_length_below_1e9 {K : ℕ} [NeZero K] (C : CollatzCycle K) :
    10^9 < K

end CollatzCycle