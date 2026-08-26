import Mathlib

/-!
# LiftCounting: Bridge A — аффинная параметризация лифтов слова

Старты с данным словом валентностей образуют арифметическую прогрессию
с шагом `M`; число позиций `q`, чьи старты `x₀ = ρ + M·q` попадают в
префикс `[0, X)`, ограничено величиной `X / M + 1`.
-/

open Finset Nat

/-- Позиционная оценка: среди первых `N` лифтов ниже границы `X` лежит
не больше `X / M + 1`. -/
lemma lift_positions_le {ρ M X N : ℕ} (hM : 0 < M) :
    ((Finset.range N).filter (fun q => ρ + M * q < X)).card ≤ X / M + 1 := by
  have hsub : (Finset.range N).filter (fun q => ρ + M * q < X) ⊆
      Finset.range (X / M + 1) := by
    intro q hq
    simp only [Finset.mem_filter, Finset.mem_range] at hq ⊢
    obtain ⟨_, hlt⟩ := hq
    have hmq : M * q < X := by linarith
    have hqle : q ≤ X / M :=
      (Nat.le_div_iff_mul_le hM).mpr (by linarith)
    exact Nat.lt_succ_of_le hqle
  refine le_trans (Finset.card_le_card hsub) ?_
  rw [Finset.card_range]
