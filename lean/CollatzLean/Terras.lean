import Mathlib
import CollatzLean.DensityLayer
import CollatzLean.CountBounds

/-!
# Terras (1976): The Stopping Time Theorem
Formalization of the combinatorial proof that for almost all $n$ 
(in terms of natural density) there exists $k$ such that $Col^k(n) < n$.

This proof DOES NOT require continuous probability or stochastic equations.
It relies solely on:
1. Affine structure of the Collatz map modulo $2^k$.
2. Combinatorial fact (LLN for boolean cube): the proportion of parity vectors with $3^d \ge 2^k$ 
   tends to 0 as $k \to \infty$, since average $d = k/2 < k \log_3 2$.
3. Infrastructure of `DensityLayer` (lemma `terras_eventually`).
-/

open Finset Nat Filter Set
open scoped ENNReal Classical

namespace Terras1976

/- Abstract function of Collatz iteration. -/
variable (Col_iter : ℕ → ℕ → ℕ) 

/-- Number of odd steps in the first `k` iterations for starting `n`. -/
axiom odd_steps (k n : ℕ) : ℕ

/-- Affine offset $c(v)$ such that $Col^k(n) = \frac{3^d}{2^k} n + c$. -/
axiom affine_offset (k n : ℕ) : ℕ

/-- Collatz affine formula for $k$ steps. -/
axiom col_affine_eq (k n : ℕ) : 
  (2 ^ k : ℚ) * Col_iter k n = 3 ^ (odd_steps k n) * n + affine_offset k n

/-- "Bad" starting values where the multiplier $\ge 1$ (descent not guaranteed). -/
def is_bad_vector (k n : ℕ) : Prop :=
  3 ^ (odd_steps k n) ≥ 2 ^ k

/-- **Combinatorial core (LLN for boolean cube):**
The proportion of "bad" parity vectors tends to zero. -/
axiom bad_vectors_density_tendsto_zero :
  ∀ ε > 0, ∃ k : ℕ, 
    ((Finset.range (2^k)).filter (fun n => is_bad_vector k n)).card < ε * 2^k

/-- Maximum threshold $N_k$ for "good" vectors. 
For $n > N_k$ the affine map strictly compresses $n$. -/
axiom max_good_threshold (k : ℕ) : ℕ

/-- **Terras Lemma (Finite step):** 
For fixed $k$, the set of numbers that DO NOT descend below $n$ in $k$ steps 
is contained in the union of the finite set $[0, N_k]$ and the "bad" residue classes. -/
axiom terras_finite_step_bound (k : ℕ) :
  {n : ℕ | Col_iter k n ≥ n} ⊆ 
    (Set.Iic (max_good_threshold k)) ∪ 
    {n : ℕ | is_bad_vector k n}

/-- **Main Theorem (Terras 1976):**
The upper natural density of numbers that never descend below 
their starting value (infinite stopping time) is zero. -/
theorem terras_density_zero :
  natUpperDensity {n : ℕ | ∀ k, Col_iter k n ≥ n} = 0 := by
  -- Тактический план доказательства:
  -- 1. Используем le_antisymm
  -- 2. Нижняя граница тривиальна (zero_le для ENNReal)
  -- 3. Верхняя граница (≤ 0) доказывается через ε-δ предел:
  --    Для любого ε > 0 находим шаг k, где доля плохих векторов < ε.
  --    Затем используем terras_finite_step_bound и монотонность верхней плотности
  --    (natUpperDensity_mono), чтобы показать, что итоговая плотность < ε.
  sorry

end Terras1976
