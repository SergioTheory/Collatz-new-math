import Mathlib.Data.Nat.Basic

def is_monotone_trajectory (x : ℕ → ℕ → ℕ) (d : ℕ) : Prop :=
  ∀ k ≤ d, ∀ q₁ q₂, q₁ ≤ q₂ → x k q₁ ≤ x k q₂

lemma surviving_q_is_interval (d N₀ : ℕ) (x : ℕ → ℕ → ℕ)
    (h_mono : is_monotone_trajectory x d)
    (h_nonempty : ∃ q, ∀ k ≤ d, x k q > N₀) :
    ∃ q_min : ℕ, ∀ q, (∀ k ≤ d, x k q > N₀) ↔ q_min ≤ q := by
  set q_min := Nat.find h_nonempty
  refine ⟨q_min, fun q ↦ ⟨?surv_to_ge, fun hge ↦ ?ge_to_surv⟩⟩
  · intro hq_surv
    exact Nat.find_min' h_nonempty hq_surv
  · intro hge
    have h_min_surv : ∀ k ≤ d, x k q_min > N₀ := Nat.find_spec h_nonempty
    intro k hkd
    exact lt_of_lt_of_le (h_min_surv k hkd) (h_mono k hkd q_min q hge)
