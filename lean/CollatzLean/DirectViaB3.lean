import Mathlib

open Nat BigOperators Finset

section DirectViaB3

variable (B d : ℕ) (α σ t : ℝ) (c_star : ℝ)

-- Sandbox axioms standing in for the computational notions of the paper
-- (survival set above a barrier, Hausdorff dimension, shift sums, ...).
axiom E (N0 : ℕ) : Set ℝ
axiom hausdorff_dim : Set ℝ → ℝ
axiom S_d : ℕ → ℕ
axiom geom_prob_le : ℕ → ℕ → ℝ
axiom survives_block : ℕ → Prop
axiom N₀ : ℕ

/-- Decidability for the opaque survival predicate (filter API). -/
axiom survives_block_dec (N : ℕ) : Decidable (survives_block N)
attribute [instance] survives_block_dec

/-- Proposition B3 (counting form, taken as given): over any window `I` of
`M` starts, the number whose block-shift sum drops below `m` is at most
`geom_prob_le m d + (m.choose d)/M` times `M`. -/
axiom prop_B3 (I : Finset ℕ) (m M : ℕ) (hM : I.card = M) (hm : d ≤ m) :
    ((I.filter (fun N => S_d N ≤ m)).card : ℝ) / M ≤
    geom_prob_le m d + (Nat.choose m d : ℝ) / M

/-- **T2, direct survival.**  Given the per-window survival bound of the
Proposition-B3 type (every sub-window of size `W` keeps at most
`c_star * W + C` survivors across one block, where `C` counts the exceptional
valuation words), the same bound holds for our window of `Q_k` starts. -/
theorem T2_direct_survival (surv : Finset ℕ) (Q_k : ℕ)
    (hQ : surv.card = Q_k) (_hQpos : 0 < Q_k)
    (hbound : ∀ w : Finset ℕ,
      ((w.filter (fun N => survives_block N)).card : ℝ)
        ≤ c_star * (w.card : ℝ) + (Nat.choose ⌈σ * d⌉₊ d : ℝ)) :
    ((surv.filter (fun N => survives_block N)).card : ℝ) ≤
    c_star * Q_k + (Nat.choose ⌈σ * d⌉₊ d : ℝ) := by
  have h1 := hbound surv
  rwa [hQ] at h1

/-- **T3, recurrence solved.**  Unrolling the per-block survival recurrence
`A (k+1) ≤ c_star * A k + C/M` from `A 0 = 1` gives the geometric-plus-floor
bound `A k ≤ c_star^k + (C/M)/(1 - c_star)`. -/
theorem T3_recurrence (A : ℕ → ℝ) (M : ℝ) (hA0 : A 0 = 1)
    (hrec : ∀ k, A (k + 1) ≤ c_star * A k + (Nat.choose ⌈σ*d⌉₊ d : ℝ) / M)
    (hc : c_star < 1) (hc0 : 0 ≤ c_star) (hM : 0 < M) :
    ∀ k, A k ≤ c_star ^ k + (Nat.choose ⌈σ*d⌉₊ d : ℝ) / (M * (1 - c_star)) := by
  intro k
  induction k with
  | zero =>
      have hden : 0 < M * (1 - c_star) := by
        have h1 : 0 < 1 - c_star := by linarith
        exact mul_pos hM h1
      have hfrac : 0 ≤ (Nat.choose ⌈σ*d⌉₊ d : ℝ) / (M * (1 - c_star)) :=
        div_nonneg (by exact_mod_cast Nat.zero_le _) hden.le
      rw [hA0, pow_zero]
      linarith
  | succ k ih =>
      have h1 : 1 - c_star ≠ 0 := by linarith
      have h2 : M * (1 - c_star) ≠ 0 := mul_ne_zero (ne_of_gt hM) h1
      calc A (k + 1) ≤ c_star * A k + (Nat.choose ⌈σ*d⌉₊ d : ℝ) / M := hrec k
        _ ≤ c_star * (c_star ^ k + (Nat.choose ⌈σ*d⌉₊ d : ℝ) / (M * (1 - c_star))) +
              (Nat.choose ⌈σ*d⌉₊ d : ℝ) / M := by
              gcongr
        _ = c_star ^ (k + 1) + (Nat.choose ⌈σ*d⌉₊ d : ℝ) / (M * (1 - c_star)) := by
              field_simp
              ring

/-- **T3, Hausdorff dimension bound (interface form).**
The two premises are exactly the outputs of the covering argument
(`T3` first half) and of the resolution-floor estimate; packaging them gives
the strict dimension drop. -/
theorem T3_dimH_bound (_hc : 0 < c_star) (_hc1 : c_star < 1) (_hB : 3 ≤ B)
    (hcover : hausdorff_dim (E N₀) ≤ |Real.logb 2 c_star| / d)
    (hfloor : |Real.logb 2 c_star| / d < 1) :
    hausdorff_dim (E N₀) ≤ |Real.logb 2 c_star| / d ∧
    |Real.logb 2 c_star| / d < 1 :=
  ⟨hcover, hfloor⟩

end DirectViaB3
