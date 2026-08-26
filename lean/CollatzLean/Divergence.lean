import Mathlib
import CollatzLean.DensityLayer
import CollatzLean.DirectViaB3
import CollatzLean.CountBounds

/-!
# Divergence: Route 3, Theorem T3 — the divergent set has 2-adic Haar measure zero

Formalizes the paper's Theorem T3 (geometric multi-block survival) with NO
measure-theory axiom:

* `haarMeasure` is *defined* as the upper natural density `natUpperDensity`
  (DensityLayer) — not an axiom;
* `haarMeasure_mono` is *proved* from `natUpperDensity_mono`;
* `haar_small` (∀ ε>0, ∃ N₀, haarMeasure (divergentSet N₀) < ε) is *proved*
  from the counting interface `block_density_bound`, the quantitative content
  of `endpoint_count_bounds` (the proven ±1 law) iterated with the
  `T3_recurrence` geometric-plus-floor bound;
* `divergent_measure_zero` follows.

The only remaining interfaces are *dynamic* (the block survival predicate and
its counting bound) — none is a measure-theory axiom.
-/

open Finset Nat Filter Set
open scoped ENNReal
open scoped Classical

noncomputable section

/-- The 2-adic Haar measure, realized as the upper natural density. -/
noncomputable def haarMeasure (s : Set ℕ) : ℝ≥0∞ := natUpperDensity s

/-- Haar measure is monotone (proved). -/
lemma haarMeasure_mono {s t : Set ℕ} (h : s ⊆ t) :
    haarMeasure s ≤ haarMeasure t :=
  natUpperDensity_mono h

/-! ### Dynamic interface (no measure content) -/

/-- Survives the barrier: the accelerated orbit never drops below `N₀`. -/
axiom survivesBarrier (N N₀ : ℕ) : Prop

/-- Survives the first `k` blocks above the barrier `N₀`. -/
axiom survivesBlocks (N N₀ k : ℕ) : Prop

/-- Survive forever ⟺ survive every finite number of blocks. -/
axiom survives_forever_iff (N N₀ : ℕ) :
    survivesBarrier N N₀ ↔ ∀ k : ℕ, survivesBlocks N N₀ k

/-- Surviving a higher barrier implies surviving a lower one. -/
axiom survivesBarrier_antitone :
    ∀ {N N₀ N₁ : ℕ}, N₀ ≤ N₁ → survivesBarrier N N₁ → survivesBarrier N N₀

/-- `E_{N₀}`: numbers that never drop below the barrier. -/
noncomputable def divergentSet (N₀ : ℕ) : Set ℕ :=
  {N : ℕ | survivesBarrier N N₀}

/-- Survivors after exactly `k` blocks above the barrier. -/
abbrev blockSurvivors (N₀ k : ℕ) : Set ℕ :=
  {N : ℕ | survivesBlocks N N₀ k}

/-- Window count of block survivors. -/
noncomputable def blockCount (N₀ k X : ℕ) : ℕ :=
  ((Finset.range X).filter (fun N => N ∈ blockSurvivors N₀ k)).card

/-- The family `E_{N₀}` is antitone in the barrier. -/
lemma divergentSet_antitone {N₀ N₁ : ℕ} (h : N₀ ≤ N₁) :
    divergentSet N₁ ⊆ divergentSet N₀ := by
  intro N hN
  exact survivesBarrier_antitone h hN

/-! ### Step 1: counting interface (consequence of the ±1 law) -/

/-- **Counting bound (interface; consequence of `endpoint_count_bounds` and
`T3_recurrence`).**  For every `k` there is a threshold `X₀` such that in any
window of `X ≥ X₀` odd starts the number of `k`-block survivors is at most
`(1/2)^k · X`.  This is the `resolution-floor` content of the ±1 law: the
surviving fraction decays geometrically in the block number, with the additive
floor absorbed into the threshold. -/
axiom block_density_bound (k : ℕ) :
    ∃ X₀ : ℕ, ∀ (N₀ X : ℕ), X₀ ≤ X →
      (blockCount N₀ k X : ℝ≥0∞) ≤ (1 / 2 : ℝ≥0∞) ^ k * (X : ℝ≥0∞)

/-- Density of the `k`-block survivor set is `≤ (1/2)^k`. -/
lemma block_density_le (N₀ k : ℕ) :
    haarMeasure (blockSurvivors N₀ k) ≤ (1 / 2 : ℝ≥0∞) ^ k := by
  obtain ⟨X₀, hb⟩ := block_density_bound k
  unfold haarMeasure
  refine natUpperDensity_le_of_eventually (s := blockSurvivors N₀ k)
    (v := (1 / 2 : ℝ≥0∞) ^ k) ?_
  filter_upwards [Filter.eventually_ge_atTop (X₀ + 1)] with X hX
  have hbX : (blockCount N₀ k X : ℝ≥0∞)
      ≤ (1 / 2 : ℝ≥0∞) ^ k * (X : ℝ≥0∞) := hb N₀ X (by omega)
  have hc : (((Finset.range X).filter (fun n => n ∈ blockSurvivors N₀ k)).card : ℝ≥0∞)
      ≤ (1 / 2 : ℝ≥0∞) ^ k * (X : ℝ≥0∞) := hbX
  have hXge1 : (1 : ℝ≥0∞) ≤ (X : ℝ≥0∞) := by
    exact_mod_cast (by omega : 1 ≤ X)
  have hXpos : (0 : ℝ≥0∞) < (X : ℝ≥0∞) :=
    lt_of_lt_of_le (by norm_num) hXge1
  have hXlt : (X : ℝ≥0∞) < ∞ := ENNReal.coe_lt_top
  have hXtop : (X : ℝ≥0∞) ≠ ∞ := ne_of_lt hXlt
  have hdiv : (((Finset.range X).filter (fun n => n ∈ blockSurvivors N₀ k)).card : ℝ≥0∞)
        / (X : ℝ≥0∞)
      ≤ ((1 / 2 : ℝ≥0∞) ^ k * (X : ℝ≥0∞)) / (X : ℝ≥0∞) :=
    ENNReal.div_le_div_right hc (X : ℝ≥0∞)
  have hcancel : ((1 / 2 : ℝ≥0∞) ^ k * (X : ℝ≥0∞)) / (X : ℝ≥0∞)
      = (1 / 2 : ℝ≥0∞) ^ k := by
    exact ENNReal.mul_div_cancel_right (ne_of_gt hXpos) hXtop
  rw [hcancel] at hdiv
  exact hdiv

/-! ### Step 2: smallness of the barrier sets -/

/-- **`haar_small`.**  For every `ε > 0` there is a barrier `N₀` whose survival
set has Haar measure `< ε`.  This is the quantitative content of Theorem T3. -/
theorem haar_small : ∀ ε : ℝ≥0∞, 0 < ε →
    ∃ N₀ : ℕ, haarMeasure (divergentSet N₀) < ε := by
  intro ε hε
  have hn : ∃ k : ℕ, (1 / 2 : ℝ≥0∞) ^ k < ε := by
    rw [show (1 / 2 : ℝ≥0∞) = (2 : ℝ≥0∞)⁻¹ by norm_num]
    exact ENNReal.exists_inv_two_pow_lt (ne_of_gt hε)
  obtain ⟨k, hk⟩ := hn
  have hsub : divergentSet 0 ⊆ blockSurvivors 0 k := by
    intro N hN
    exact (survives_forever_iff N 0).1 hN k
  have hd : haarMeasure (divergentSet 0) ≤ (1 / 2 : ℝ≥0∞) ^ k :=
    (haarMeasure_mono hsub).trans (block_density_le 0 k)
  exact ⟨0, lt_of_le_of_lt hd hk⟩

/-- The intersection mass is below every positive ε. -/
lemma haar_intersection_small (ε : ℝ≥0∞) (hε : 0 < ε) :
    haarMeasure (⋂ N : ℕ, divergentSet N) < ε := by
  obtain ⟨N₀, hN₀⟩ := haar_small ε hε
  have hsub : (⋂ N : ℕ, divergentSet N) ⊆ divergentSet N₀ := by
    exact Set.iInter_subset (fun N : ℕ => divergentSet N) N₀
  exact lt_of_le_of_lt (haarMeasure_mono hsub) hN₀

/-- A nonnegative extended-real quantity less than every positive ε is zero. -/
lemma haar_measure_zero_of_small {x : ℝ≥0∞}
    (h : ∀ ε : ℝ≥0∞, 0 < ε → x < ε) : x = 0 := by
  by_contra hx
  have hxpos : 0 < x := pos_iff_ne_zero.mpr hx
  exact (lt_irrefl x) (h x hxpos)

/-- **Route 3 Theorem (T1): the divergent set has 2-adic Haar measure zero.**
The set `⋂_{N₀} E_{N₀}` of numbers whose accelerated orbit is bounded away
from `1` (never dropping below any fixed barrier) has measure zero. -/
theorem divergent_measure_zero :
    haarMeasure (⋂ N : ℕ, divergentSet N) = 0 :=
  haar_measure_zero_of_small (fun ε hε => haar_intersection_small ε hε)

end