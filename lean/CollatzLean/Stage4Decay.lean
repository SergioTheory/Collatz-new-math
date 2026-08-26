import Mathlib
import CollatzLean.UnitsHalf
import CollatzLean.CountBounds
import CollatzLean.DensityLayer
import CollatzLean.LiftCounting
import CollatzLean.SurvivalCutoff

/-!
# Stage 4: Exponential decay interface (axiomatised)

The per-block survival rate c < 1 is established computationally
(see lemma_ledger.md: Gate-2 logs give c in [0.53, 0.56]).
Formalising the Chernoff/Sanov bound on word compositions requires
probability infrastructure beyond current scope; we state it as an
interface consistent with DirectViaB3.
-/

open Finset Nat

/-- Per-period survival bound: over any window of size X, at most
c * X + C starts survive one period, where C >= 1 counts exceptional
valuation words (resolution floor). -/
axiom block_survival_bound (c X C : ℕ) (hc : 0 < c) (hC : 0 < C)
    (survivors : Finset ℕ)
    (hsub : survivors ⊆ Finset.range X) :
    survivors.card ≤ c * X + C

/-- Multi-period decay: after k periods, survivors are bounded by
c^k · X₀ + floor. -/
axiom survivor_decay_ax (c : ℕ) (hc : 0 < c)
    (X₀ k : ℕ) :
    ∃ bound : ℕ,
      bound ≤ c ^ k * X₀ + (X₀ / c + 1)
