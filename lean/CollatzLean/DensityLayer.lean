import Mathlib

/-!
# DensityLayer: асимптотическая плотность для программы Терраса

Слой 1 маршрута 1. Определяет верхнюю асимптотическую плотность множеств
натуральных чисел и экспортирует интерфейс, в который подключается наш
счётный стек (`endpoint_card_uniform`, `endpoint_count_bounds`):

* `natUpperDensity` — определение через limsup долей по префиксам;
* монотонность по включению;
* импорт конечных границ: `∀ᶠ k, count k ≤ v * k` даёт
  `natUpperDensity s ≤ v`;
* интерфейс стремления к нулю для убывающих семейств множеств
  (`terras_eventually`) — форма, в которую собирается индукция по блокам.
-/

open Filter Finset Nat Set
open scoped ENNReal
open scoped Classical

/-! ### Определение -/

/-- Верхняя асимптотическая плотность множества натуральных чисел:
limsup доли элементов в первых `k` префиксах. -/
noncomputable def natUpperDensity (s : Set ℕ) : ℝ≥0∞ :=
  Filter.limsup
    (fun k : ℕ =>
      ((Finset.range k).filter (fun n => n ∈ s)).card / ((k : ℕ) : ℝ≥0∞))
    Filter.atTop

/-! ### Монотонность -/

/-- Верхняя плотность монотонна по включению. -/
lemma natUpperDensity_mono {s t : Set ℕ} (h : s ⊆ t) :
    natUpperDensity s ≤ natUpperDensity t := by
  unfold natUpperDensity
  refine Filter.limsup_le_limsup (Filter.Eventually.of_forall fun k => ?_)
  have hss : ((Finset.range k).filter (fun n => n ∈ s))
      ⊆ ((Finset.range k).filter (fun n => n ∈ t)) := by
    intro x hx
    simp only [Finset.mem_filter] at hx ⊢
    exact ⟨hx.1, h hx.2⟩
  refine ENNReal.div_le_div ?_ le_rfl
  exact Nat.cast_le.mpr <| Finset.card_le_card hss

/-! ### Импорт конечных границ -/

/-- Если в конце концов доля элементов не превосходит `v`, то и верхняя
плотность не превосходит `v`. -/
lemma natUpperDensity_le_of_eventually {s : Set ℕ} {v : ℝ≥0∞}
    (h : ∀ᶠ k : ℕ in Filter.atTop,
      (((Finset.range k).filter (fun n => n ∈ s)).card : ℝ≥0∞)
        / ((k : ℕ) : ℝ≥0∞) ≤ v) :
    natUpperDensity s ≤ v := by
  unfold natUpperDensity
  exact Filter.limsup_le_of_le (by isBoundedDefault) h

/-! ### Интерфейс стремления к нулю (форма Терраса) -/

/-- Если семейство множеств убывает по вложению и для каждого `ε > 0`
найдется член семейства с верхней плотностью не больше `ε`, то вдоль
семейства плотности в конце концов опускаются ниже `ε`. Это точная форма,
в которую собирается индукция по блокам из `CountBounds`. -/
lemma terras_eventually {S : ℕ → Set ℕ}
    (hmono : ∀ M N : ℕ, M ≤ N → S N ⊆ S M)
    (hvan : ∀ ε : ℝ≥0∞, 0 < ε → ∃ M : ℕ,
      natUpperDensity (S M) ≤ ε) :
    ∀ ε : ℝ≥0∞, 0 < ε → ∀ᶠ M : ℕ in Filter.atTop,
      natUpperDensity (S M) ≤ ε := by
  intro ε hε
  obtain ⟨M₀, hM₀⟩ := hvan ε hε
  filter_upwards [Filter.eventually_ge_atTop M₀] with M hM
  exact (natUpperDensity_mono (hmono M₀ M hM)).trans hM₀
