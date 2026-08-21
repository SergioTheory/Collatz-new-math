import Mathlib.Data.Real.Basic
import Mathlib.Data.Nat.Choose.Basic
import Mathlib.NumberTheory.Padics.PadicIntegers
import Mathlib.MeasureTheory.Measure.Haar.Basic
import Mathlib.MeasureTheory.Measure.MeasureSpace
import Mathlib.Analysis.SpecificLimits.Basic
import Mathlib.Topology.MetricSpace.Basic

open MeasureTheory
open scoped Padic

local notation "ℤ_2" => ℤ_[2]

noncomputable def syr (N : ℕ) : ℕ :=
  let val := 3 * N + 1
  let a := padicValNat 2 val
  val / (2^a)

noncomputable def syrBlock (d : ℕ) (N : ℕ) : ℕ :=
  Nat.iterate syr d N

def ExceptionalSet (N₀ : ℕ) : Set ℕ :=
  {N : ℕ | Odd N ∧ ∀ k : ℕ, syrBlock k N > N₀}

noncomputable def SurvivalProb (μ : Measure ℕ) (N₀ : ℕ) (d k : ℕ) : ℝ :=
  μ {N | Odd N ∧ ∀ i < k, syrBlock (i * d) N > N₀} / μ (Set.univ : Set ℕ)

noncomputable def I₂ (σ : ℝ) : ℝ :=
  sSup {s * σ - Real.log (∑' a : ℕ, (2 : ℝ)^(-a : ℤ) * Real.exp (s * a)) / Real.log 2 | s : ℝ}

theorem finite_scale_2adic_bound (M d m : ℕ) (hdm : d ≤ m) :
  let I := Finset.filter (fun N => Odd N) (Finset.range (2^M))
  let count := (I.filter (fun N => 
    sorry 
  )).card
  (count : ℝ) / I.card ≤ 
    sorry + (Nat.choose m d : ℝ) / (2^M : ℝ) := by
  sorry

theorem local_descent_window (B : ℕ) (α : ℝ) (t : ℝ) 
  (hα : 1 < α ∧ α < 2 / Real.logb 2 3)
  (ht : (α - 1) / (2 - Real.logb 2 3) < t ∧ t ≤ 1 / Real.logb 2 3) :
  let N₀ := 2^B
  let d := ⌊t * B⌋₊
  let σ := Real.logb 2 3 + (α - 1) / t
  let Y := ⌊(N₀ : ℝ)^α⌋₊
  let I := Finset.filter (fun N => Odd N ∧ N₀ ≤ N ∧ N ≤ Y) (Finset.range (Y + 1))
  let survivors := I.filter (fun N => ∀ i < d, syrBlock i N > N₀)
  (survivors.card : ℝ) / I.card ≤ 
    (N₀ : ℝ)^(-t * I₂ σ + sorry) 
  := by
  sorry

noncomputable def totalVariation (μ ν : Measure ℕ) : ℝ :=
  sSup {|μ s - ν s| | s : Set ℕ}

noncomputable def haarOddClasses (m : ℕ) : Measure ℕ :=
  sorry

theorem conditional_equidistribution (I : Finset ℕ) (M N₀ d m : ℕ)
  (hI : ∀ N ∈ I, Odd N)
  (hM : I.card = 2^(m - 1)) :
  let Q₁ := fun r => (I.filter (fun N => 
    (∀ i < d, syrBlock i N > N₀) ∧ 
    (syrBlock d N) % (2^m) = r
  )).card
  let Q₁_total := ∑ r in Finset.filter (fun r => Odd r) (Finset.range (2^m)), Q₁ r
  ∀ r : ℕ, Odd r → r < 2^m →
    |((Q₁ r : ℝ) - (Q₁_total : ℝ) / (2^(m - 1) : ℝ))| ≤ (2^d : ℝ)
  := by
  sorry

theorem one_block_survival_bound (μ : Measure ℕ) (N₀ m : ℕ) (d : ℕ) (ε : ℝ)
  (hμ_prob : μ Set.univ = 1)
  (hμ_support : ∀ N, N ∈ μ.support → N₀ ≤ N ∧ N ≤ N₀^10)
  (hμ_haar : totalVariation μ (haarOddClasses m) ≤ ε) :
  let c_star := (2 : ℝ)^(-(d : ℝ) * I₂ (Real.logb 2 3 + 0.1 / 0.3))
  SurvivalProb μ N₀ d 1 ≤ c_star + 2 * ε
  := by
  sorry

theorem lyapunov_drift (μ : Measure ℕ) (N₀ m : ℕ) (d : ℕ) (β ε c_star : ℝ)
  (hμ_prob : μ Set.univ = 1)
  (hμ_support : ∀ N, N ∈ μ.support → N₀ ≤ N ∧ N ≤ N₀^10)
  (hμ_haar : totalVariation μ (haarOddClasses m) ≤ ε)
  (hβ : 0 < β ∧ β ≤ sorry) 
  :
  let V := fun x => ((x : ℝ) / N₀)^β
  let survivors := {N | N ∈ μ.support ∧ ∀ i < d, syrBlock i N > N₀}
  let x_plus := fun N => syrBlock d N
  ∃ (u₀ w δ : ℝ) (C : ℝ), 
    u₀ > 0 ∧ w > 0 ∧ δ > 0 ∧ C > 0 ∧
    let ρ := max ((c_star + 2 * ε) * (2 : ℝ)^(β * u₀ * N₀) + (2 : ℝ)^(β * w * N₀)) ((2 : ℝ)^(-δ))
    ρ < 1 ∧
    (∫ N in survivors, V (x_plus N) ∂μ) ≤ 
      ρ * (∫ N, V N ∂μ) + C * (2 : ℝ)^(-δ * N₀)
  := by
  sorry

theorem geometric_multi_block_survival (N₀ B m : ℕ) (α : ℝ)
  (hN₀ : N₀ = 2^B)
  (hα : 1 < α ∧ α < 2 / Real.logb 2 3)
  (δ₀ : ℝ) (hδ₀ : δ₀ > 0) :
  let ball := {N : ℕ | Odd N ∧ N₀ ≤ N ∧ N ≤ ⌊(N₀ : ℝ)^α⌋₊}
  let A := fun k => (Finset.filter (fun N => 
    N ∈ ball ∧ ∀ i < k * 10, syrBlock i N > N₀
  ) (Finset.range (⌊(N₀ : ℝ)^α⌋₊ + 1))).card
  ∃ (C : ℝ) (ρ : ℝ) (δ : ℝ),
    C > 0 ∧ 0 < ρ ∧ ρ < 1 ∧ δ > 0 ∧
    ∀ k : ℕ, (A k : ℝ) ≤ C * ρ^k + C * k * (2 : ℝ)^(-δ * B)
  := by
  sorry

noncomputable def padicMetric (x y : ℕ) : ℝ :=
  (2 : ℝ)^(-(padicValNat 2 (Int.natAbs (x - y)) : ℝ))

noncomputable def hausdorffDim (S : Set ℕ) : ℝ :=
  sInf {s : ℝ | ∃ (δ : ℝ), δ > 0 ∧ 
    ∀ ε > 0, ∃ (cover : Set (Set ℕ)), 
      S ⊆ ⋃₀ cover ∧ 
      (∀ U ∈ cover, ∃ x y, x ∈ U ∧ y ∈ U ∧ padicMetric x y ≤ ε) ∧
      ∑' U : Set ℕ, (if U ∈ cover then (sSup {padicMetric x y | x ∈ U ∧ y ∈ U})^s else 0) < δ}

theorem hausdorff_dimension_drop (N₀ : ℕ) (hN₀ : N₀ ≥ 2) :
  hausdorffDim (ExceptionalSet N₀) < 1
  := by
  sorry

theorem exceptional_set_haar_null (N₀ : ℕ) (hN₀ : N₀ ≥ 2) :
  MeasureTheory.volume (ExceptionalSet N₀) = 0
  := by
  sorry
