import Mathlib
import CollatzLean.DensityLayer
import CollatzLean.Divergence
import CollatzLean.CycleBasic

/-!
# ReverseTree: the reverse Collatz tree from 1 is dense in ℤ₂ (Route 4)

## Chain (no new measure axioms — only the dynamic interface)

1. `nonReturning` = numbers whose accelerated orbit never reaches 1.
2. Dichotomy (dynamic interface): a number fails to reach 1 iff its orbit is
   divergent (escapes every barrier) OR it lies on a non-trivial cycle.
3. Route 2 (interface, strong Eliahou form): no non-trivial cycle exists.
   Hence `nonReturning = (⋂ N₀, divergentSet N₀)`.
4. Route 3 (`Divergence.divergent_measure_zero`): that intersection has
   Haar measure (= upper natural density) zero.
5. `cylinder_density_pos`: any 2-adic cylinder `{n | n % 2^k = r}` has
   *positive* Haar measure `1/2^(k+2)` (counting lemma + `limsup` bound).
6. Therefore no cylinder is contained in `nonReturning` (it would force
   `0 < μ(cylinder) ≤ μ(nonReturning) = 0`); every cylinder meets the
   returning set.  ⟹ **the reverse tree of 1 is dense in ℤ₂.**
-/

open Finset Nat Filter Set
open scoped Classical ENNReal

noncomputable section

/-- A 2-adic cylinder: residue class `r` modulo `2^k`. -/
noncomputable def cylinder (k r : ℕ) : Set ℕ := {n : ℕ | n % 2^k = r}

/-- The accelerating orbit of `N` eventually reaches `1`. -/
axiom reachesOne (N : ℕ) : Prop

/-- Decidability for the reaching predicate. -/
axiom reachesOne_decidable (N : ℕ) : Decidable (reachesOne N)
attribute [instance] reachesOne_decidable

/-- `N` lies on a non-trivial Collatz cycle (xmin > 1). -/
def inNonTrivialCycle (N : ℕ) : Prop :=
  ∃ (K : ℕ) (_ : NeZero K) (C : CollatzCycle K), C.xmin ≠ 1 ∧ ∃ i : Fin K, C.a i = N

/-- **Dichotomy (dynamic interface).**  A number fails to reach 1 iff its
orbit is divergent (escapes every barrier) or it lies on a non-trivial cycle.
This is the only dynamic assumption of Route 4. -/
axiom not_reachesOne_iff (N : ℕ) :
    ¬ reachesOne N ↔ N ∈ (⋂ N₀ : ℕ, divergentSet N₀) ∨ inNonTrivialCycle N

/-- **Route 2 in strong form (interface).**  No non-trivial Collatz cycle
exists (the Eliahou/Baker–Rhin conclusion: every cycle is the trivial
`1`-cycle). -/
axiom no_non_trivial_cycle (N : ℕ) : ¬ inNonTrivialCycle N

/-- The non-returning set: orbits that never reach 1. -/
noncomputable def nonReturning : Set ℕ := {N : ℕ | ¬ reachesOne N}

/-- `nonReturning` coincides with the divergent set (dichotomy + no cycles). -/
lemma nonReturning_eq_divergent :
    nonReturning = (⋂ N₀ : ℕ, divergentSet N₀) := by
  ext N
  constructor
  · intro hN
    rcases (not_reachesOne_iff N).mp hN with hDiv | hCyc
    · exact hDiv
    · exact False.elim (no_non_trivial_cycle N hCyc)
  · intro hN
    exact (not_reachesOne_iff N).mpr (Or.inl hN)

/-- The non-returning set has Haar measure zero (Route 3 + dichotomy). -/
theorem nonReturning_measure_zero : haarMeasure nonReturning = 0 := by
  rw [nonReturning_eq_divergent]
  exact divergent_measure_zero

/-! ### Cylinders have positive measure -/

/-- In the first `X` naturals, at least `X / 2^(k+1)` satisfy `n % 2^k = r`
for `r < 2^k` (blocks of length `2^(k+1)` each contain two such numbers). -/
lemma cylinder_count_lower (X k r : ℕ) (hr : r < 2^k) :
    X / 2^(k+1) ≤ ((Finset.range X).filter (fun n => n % 2^k = r)).card := by
  let B := X / 2^(k+1)
  let S : Finset ℕ := (Finset.range B).image (fun t => t * 2^(k+1) + r)
  have hS : S ⊆ (Finset.range X).filter (fun n => n % 2^k = r) := by
    intro y hy
    rw [Finset.mem_filter]
    rcases Finset.mem_image.mp hy with ⟨t, ht, rfl⟩
    have ht' : t < B := Finset.mem_range.mp ht
    have hlt : t * 2^(k+1) + r < X := by
      have h1 : (t + 1) * 2^(k+1) ≤ B * 2^(k+1) :=
        Nat.mul_le_mul_right _ (Nat.succ_le_of_lt ht')
      have h2 : B * 2^(k+1) ≤ X := Nat.div_mul_le_self X (2^(k+1))
      have htot : (t + 1) * 2^(k+1) ≤ X := le_trans h1 h2
      have hadd : t * 2^(k+1) + 2^(k+1) ≤ X := by
        rw [← Nat.succ_mul]
        exact htot
      have hle : t * 2^(k+1) ≤ X - 2^(k+1) := Nat.le_sub_of_add_le hadd
      have hrle : r < 2^(k+1) := by
        calc r < 2^k := hr
          _ ≤ 2^(k+1) := by
            apply Nat.pow_le_pow_right (by norm_num : 1 ≤ 2)
            omega
      calc t * 2^(k+1) + r ≤ (X - 2^(k+1)) + r := by
            exact Nat.add_le_add_right hle r
        _ < (X - 2^(k+1)) + 2^(k+1) := by
            exact Nat.add_lt_add_left hrle (X - 2^(k+1))
        _ = X := by
            exact Nat.sub_add_cancel (by
              exact le_trans (Nat.le_add_left (2^(k+1)) (t * 2^(k+1))) hadd)
    refine ⟨Finset.mem_range.mpr hlt, ?_⟩
    have hmod : (t * 2^(k+1) + r) % 2^k = r % 2^k := by
      rw [Nat.add_comm]
      rw [show t * 2^(k+1) = (t * 2) * 2^k by ring]
      exact Nat.add_mul_mod_self_right r (t * 2) (2^k)
    exact hmod.trans (Nat.mod_eq_of_lt hr)
  have hcard : S.card = X / 2^(k+1) := by
    dsimp [S, B]
    rw [Finset.card_image_of_injOn]
    · simp
    · intro a _ b _ h
      have hcancel : a * 2^(k+1) = b * 2^(k+1) := Nat.add_right_cancel h
      have hcomm1 : a * 2^(k+1) = 2^(k+1) * a := by ring
      have hcomm2 : b * 2^(k+1) = 2^(k+1) * b := by ring
      rw [hcomm1, hcomm2] at hcancel
      exact Nat.mul_left_cancel (pow_pos (by norm_num) (k + 1)) hcancel
  rw [← hcard]
  exact Finset.card_le_card hS

/-- The filter counting lemma, in the form needed by the density bound. -/
lemma cylinder_count_strong (X k r : ℕ) (hr : r < 2^k) (hX : 2^(k+2) ≤ X) :
    X ≤ ((Finset.range X).filter (fun n => n % 2^k = r)).card * 2^(k+2) := by
  let q := X / 2^(k+1)
  let rem := X % 2^(k+1)
  have hdiv : X = q * 2^(k+1) + rem := by
    dsimp [q, rem]
    rw [Nat.mul_comm]
    exact (Nat.div_add_mod X (2^(k+1))).symm
  have hq1 : 1 ≤ q := by
    dsimp [q]
    have hle : 2^(k+1) ≤ X := by
      calc 2^(k+1) ≤ 2^(k+2) := by
            apply Nat.pow_le_pow_right (by norm_num : 1 ≤ 2)
            omega
        _ ≤ X := hX
    exact (Nat.le_div_iff_mul_le (by positivity : 0 < 2^(k+1))).mpr (by simpa [Nat.one_mul] using hle)
  have hrem : rem < 2^(k+1) := by
    dsimp [rem]
    exact Nat.mod_lt X (by positivity : 0 < 2^(k+1))
  have hremle : rem ≤ q * 2^(k+1) := by
    have h2 : 2^(k+1) ≤ q * 2^(k+1) :=
      Nat.le_mul_of_pos_left (2^(k+1)) hq1
    exact le_trans (le_of_lt hrem) h2
  have hXle : X ≤ 2 * (q * 2^(k+1)) := by
    calc X = q * 2^(k+1) + rem := hdiv
      _ ≤ q * 2^(k+1) + q * 2^(k+1) := by exact Nat.add_le_add_left hremle _
      _ = 2 * (q * 2^(k+1)) := by ring
  have hq2 : 2 * (q * 2^(k+1)) = q * 2^(k+2) := by
    calc 2 * (q * 2^(k+1)) = (q * 2^(k+1)) * 2 := by ring
      _ = q * (2^(k+1) * 2) := by ring
      _ = q * 2^(k+2) := by
        rw [← pow_succ]
  have hqle : q * 2^(k+2) ≤ ((Finset.range X).filter (fun n => n % 2^k = r)).card * 2^(k+2) := by
    have hcl := cylinder_count_lower X k r hr
    dsimp [q]
    exact Nat.mul_le_mul_right (2^(k+2)) hcl
  omega

/-- A 2-adic cylinder has positive upper natural density (≥ 1/2^(k+2)). -/
lemma cylinder_density_pos (k r : ℕ) (hr : r < 2^k) :
    (0 : ℝ≥0∞) < haarMeasure (cylinder k r) := by
  let count (X : ℕ) := ((Finset.range X).filter (fun n => n % 2^k = r)).card
  let c : ℝ≥0∞ := (1 : ℝ≥0∞) / ((2^(k+2) : ℕ) : ℝ≥0∞)
  have hc : 0 < c := by
    dsimp [c]
    exact ENNReal.div_pos (by norm_num) (by simp)
  unfold haarMeasure natUpperDensity cylinder
  apply lt_of_lt_of_le hc
  have hlim : (c : ℝ≥0∞) ≤ Filter.limsup
      (fun X : ℕ =>
        (((Finset.range X).filter (fun n => n % 2^k = r)).card : ℝ≥0∞) /
          (X : ℝ≥0∞))
      Filter.atTop := by
    have hconst : Filter.limsup (fun _ : ℕ => c) Filter.atTop = c :=
      Filter.limsup_const c
    rw [← hconst]
    refine Filter.limsup_le_limsup (u := fun _ : ℕ => c)
      (v := fun X : ℕ =>
        (((Finset.range X).filter (fun n => n % 2^k = r)).card : ℝ≥0∞) /
          (X : ℝ≥0∞)) ?_
    filter_upwards [Filter.eventually_ge_atTop (2^(k+2))] with X hX
    have hcnt : X ≤ (count X) * 2^(k+2) := by
      dsimp [count]
      exact cylinder_count_strong X k r hr hX
    have hcntE : (X : ℝ≥0∞) ≤ (count X : ℝ≥0∞) * ((2^(k+2) : ℕ) : ℝ≥0∞) := by
      exact_mod_cast hcnt
    have hdiv : (X : ℝ≥0∞) / ((2^(k+2) : ℕ) : ℝ≥0∞) ≤ (count X : ℝ≥0∞) := by
      exact (ENNReal.div_le_iff_le_mul
        (Or.inl (by exact_mod_cast (ne_of_gt (pow_pos (by norm_num) (k + 2)))))
        (Or.inl (by simp : ((2^(k+2) : ℕ) : ℝ≥0∞) ≠ ∞))).2 hcntE
    have hcc : (c : ℝ≥0∞) * (X : ℝ≥0∞) ≤ (count X : ℝ≥0∞) := by
      dsimp [c]
      rw [one_div]
      -- goal: (2^(k+2))⁻¹ * X ≤ count, from hdiv : X / 2^(k+2) ≤ count
      simpa [ENNReal.div_eq_inv_mul, mul_comm, mul_assoc] using hdiv
    have hX0 : (X : ℝ≥0∞) ≠ 0 := by
      exact_mod_cast (ne_of_gt (lt_of_lt_of_le (pow_pos (by norm_num) (k + 2)) hX))
    rw [ENNReal.le_div_iff_mul_le (Or.inl hX0) (Or.inl (by simp : (X : ℝ≥0∞) ≠ ∞))]
    simpa [count] using hcc
  simpa [cylinder] using hlim

/-! ### Every cylinder meets the returning set -/

/-- **Route 4 Theorem: the reverse tree of 1 is dense in ℤ₂.**
Every 2-adic cylinder (odd residue class mod `2^k`) contains a number whose
accelerated orbit reaches 1. -/
theorem reverse_tree_dense (k r : ℕ) (hr : r < 2^k) :
    ∃ N : ℕ, N % 2^k = r ∧ reachesOne N := by
  --  suppose not
  by_contra h
  push Not at h
  have hcyc : cylinder k r ⊆ nonReturning := by
    intro N hN
    dsimp [cylinder] at hN
    exact h N hN
  have hle : haarMeasure (cylinder k r) ≤ haarMeasure nonReturning :=
    haarMeasure_mono hcyc
  have hzero : haarMeasure (cylinder k r) ≤ 0 := by
    rw [nonReturning_measure_zero] at hle
    exact hle
  have hpos : 0 < haarMeasure (cylinder k r) := cylinder_density_pos k r hr
  exact (not_lt_of_ge hzero) hpos