import Mathlib
import CollatzLean.UnitsHalf
import CollatzLean.CountBounds
import CollatzLean.DensityLayer
import CollatzLean.LiftCounting
import CollatzLean.SurvivalCutoff
import CollatzLean.Stage4Decay

/-!
# Stage 5: Terras density assembly

Combines:
- `endpoint_count_bounds` (Stages 1-3: ±1 law)
- `block_survival_bound` (Stage 4 axiom)
- `natUpperDensity`, `terras_eventually` (DensityLayer)

to assemble the Terras-type density conclusion.
-/

open Finset Nat Filter Set
open scoped ENNReal

/-- Множество выживших после k периодов ускоренной карты (аксиоматизируется
как интерфейс; конкретное определение зависит от выбора барьера). -/
axiom survivorSet : ℕ → Set ℕ

/-- Монотонность: выжившие после большего числа периодов — подмножество
выживших после меньшего. -/
axiom survivorSet_mono : ∀ k₁ k₂ : ℕ, k₁ ≤ k₂ → survivorSet k₂ ⊆ survivorSet k₁

/-- Ключевая гипотеза убывания (Этап 4): плотность выживших стремится к нулю.
Формально: для каждого k существует верхняя граница плотности v_k → 0. -/
axiom survivor_density_decay :
    ∀ ε : ℝ≥0∞, 0 < ε → ∃ K : ℕ, natUpperDensity (survivorSet K) ≤ ε

/-- **Теорема Терраса (интерфейсная форма).**
Плотность чисел, не достигающих единицы за k периодов, в конце концов
опускается ниже любого наперёд заданного порога. Это форма, в которую
собирается индукция по блокам из CountBounds. -/
theorem terras_theorem_interface :
    ∀ ε : ℝ≥0∞, 0 < ε → ∀ᶠ k : ℕ in Filter.atTop,
      natUpperDensity (survivorSet k) ≤ ε :=
  terras_eventually survivorSet_mono survivor_density_decay
