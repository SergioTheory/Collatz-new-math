import Mathlib

/-!
# SurvivalCutoff: Bridge B — монотонность и суффикс выживания

Аффинное отображение блока по слову `x ↦ (3^d·x + c) / 2^S` монотонно
по старту; следовательно, внутри цилиндра слова (позиции `q` с лифтом
`x₀ = ρ + 2^S·q`) множество выживающих над барьером является суффиксом
по `q`: больший старт выживает, если выжил меньший.
-/

/-- Аффинный блочный отображение по слову. -/
noncomputable def wordMap (d S c x : ℕ) : ℕ := (3 ^ d * x + c) / 2 ^ S

/-- Монотонность блочного отображения по старту. -/
lemma wordMap_mono {d S c x₁ x₂ : ℕ} (h : x₁ ≤ x₂) :
    wordMap d S c x₁ ≤ wordMap d S c x₂ := by
  unfold wordMap
  exact Nat.div_le_div_right <|
    Nat.add_le_add (Nat.mul_le_mul_left _ h) (le_refl c)

/-- Выживание над барьером для данного слова. -/
def survivesWord (d S c B x : ℕ) : Prop := B ≤ wordMap d S c x

/-- Выживающие образуют суффикс по лифтам: если выжил меньший старт,
то выживает и больший. -/
lemma survival_suffix_lift {d S c B q₁ q₂ : ℕ} (hle : q₁ ≤ q₂)
    (hsurv : survivesWord d S c B q₁) :
    survivesWord d S c B q₂ :=
  le_trans hsurv (wordMap_mono hle)
