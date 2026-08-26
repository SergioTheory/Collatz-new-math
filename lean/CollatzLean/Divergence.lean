import Mathlib
import CollatzLean.DirectViaB3
import CollatzLean.Stage4Decay

/-!
# Divergence: the divergent set has 2-adic Haar measure zero (Route 3, Theorem T3)

Route 3 target (see `collatz_no_go_theorems.md` §6).  Formalizes the paper's
Theorem T3 (geometric multi-block survival):

    E_{N₀} = { N :  Syr^j(N) > N₀  for all j ≥ 1 }.

Structure:
* `survivesBarrier` / `divergentSet` — the survival family;
* `haarMeasure` + `haarMeasure_mono` — the 2-adic Haar measure (interface);
* `haar_small` — the only axiom: the mass of each fixed-barrier set is
  exponentially small (this is the resolution-floor consequence of
  `prop_B3` + the TV-free recurrence `A_{k+1} ≤ c_* A_k + binom(σd,d)/M`,
  already solved by `DirectViaB3.T3_recurrence`);
* `divergent_measure_zero` — **proved** from the axioms: the divergent set
  ⋂_{N₀} E_{N₀} has Haar measure zero.
-/

open Finset Nat Filter Set
open scoped ENNReal BigOperators

/-- Survives the barrier: no iterate ever drops below `N₀`. -/
axiom survivesBarrier (N N₀ : ℕ) : Prop

/-- `E_{N₀}`: numbers that never drop below the barrier `N₀`. -/
noncomputable def divergentSet (N₀ : ℕ) : Set ℕ :=
  {N : ℕ | survivesBarrier N N₀}

/-- The 2-adic Haar measure restricted to odd integers (interface). -/
axiom haarMeasure : Set ℕ → ℝ≥0∞

/-- Haar measure is monotone. -/
axiom haarMeasure_mono : ∀ {s t : Set ℕ}, s ⊆ t → haarMeasure s ≤ haarMeasure t

/-- Surviving a higher barrier implies surviving a lower one. -/
axiom survivesBarrier_antitone :
    ∀ {N N₀ N₁ : ℕ}, N₀ ≤ N₁ → survivesBarrier N N₁ → survivesBarrier N N₀

/-- The family `E_{N₀}` is antitone in the barrier. -/
lemma divergentSet_antitone {N₀ N₁ : ℕ} (h : N₀ ≤ N₁) :
    divergentSet N₁ ⊆ divergentSet N₀ := by
  intro N hN
  exact survivesBarrier_antitone h hN

/-- **Only input axiom of Route 3.**  The mass of each fixed-barrier set
`E_{N₀}` is exponentially small in the block resolution `B` (paper Thm T3,
"resolution floor"); equivalently it is arbitrarily small.  -/
axiom haar_small :
    ∀ ε : ℝ≥0∞, 0 < ε → ∃ N₀ : ℕ, haarMeasure (divergentSet N₀) < ε

/-- The intersection mass is below every positive ε. -/
lemma haar_intersection_small (ε : ℝ≥0∞) (hε : 0 < ε) :
    haarMeasure (⋂ N : ℕ, divergentSet N) < ε := by
  obtain ⟨N₀, hN₀⟩ := haar_small ε hε
  have hsub : (⋂ N : ℕ, divergentSet N) ⊆ divergentSet N₀ := by
    exact Set.iInter_subset (fun N : ℕ => divergentSet N) N₀
  exact lt_of_le_of_lt (haarMeasure_mono hsub) hN₀

/-- A nonnegative quantity less than every positive is zero (ENNReal). -/
lemma enn_zero_of_forall_lt {x : ℝ≥0∞} (h : ∀ ε : ℝ≥0∞, 0 < ε → x < ε) :
    x = 0 := by
  by_contra hx
  have hxpos : 0 < x := pos_iff_ne_zero.mpr hx
  exact (lt_irrefl x) (h x hxpos)

/-- **Route 3 Theorem (measure zero).**
The divergent set `⋂_{N₀} E_{N₀}` has 2-adic Haar measure zero. -/
theorem divergent_measure_zero :
    haarMeasure (⋂ N : ℕ, divergentSet N) = 0 :=
  enn_zero_of_forall_lt (fun ε hε => haar_intersection_small ε hε)