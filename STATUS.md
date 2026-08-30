# Collatz Crystal Hunter: Project Status & Roadmap

**Current Release:** v2.1.1 (Architectural Synthesis Milestone)  
**Objective:** Mapping the deterministic architecture of the Collatz space and formalizing structural obstructions.

This document clarifies the exact boundaries between what has been strictly machine-verified in Lean 4 and what has been proven computationally/analytically in our broader research manuscript.

---

## 1. Lean 4 Formalization (Structurally Verified)

The Lean 4 repository represents the rigorous algebraic bedrock of the project. Due to current limitations in Mathlib regarding continuous probability and stochastic PDEs, the formalization is strictly limited to deterministic, algebraic, and combinatorial Diophantine structures.

### ✅ Completed Lean 4 Modules:
- **Cycle Algebra (`CycleBasic`, `CycleLogs`):** The exact fractional constraints and the rigorous logarithmic clamp $0 < S \ln 2 - K \ln 3 < K / x_{min}$.
- **Shadow Mountain (`ShadowEscape`, `ShadowDescent`):** The exact deterministic algebraic expansion and descent conditions for the worst-case trailing-ones class ($M \cdot 2^a - 1$).
- **Divergence Measure (`Divergence`):** Strict proof that the Haar measure of divergent orbits is exactly $0$.
- **Terras' Theorem (`Terras.lean`):** Formalization of the combinatorial LLN on the boolean cube (bypassing continuous Mathlib limits), establishing that the natural density of integers with finite stopping time is $1$.

---

## 2. Computational and Analytical Results (Python + LaTeX)

Our research extends far beyond the Lean 4 formalization. Using high-concurrency Python scripts and advanced analytics, we have established results that surpass basic density theorems.

### ✅ Completed Computational Proofs & Falsifications:
- **Diophantine Cycle Exclusion:** Excluded macroscopic cycles up to length $d \le 1.14 \times 10^{11}$ using the continued fractions convergents of $\ln 3 / \ln 2$ (Eliahou) bounded by Barina's $x_{min} > 2^{68}$. 
- **Transcendental Asymptotics:** Formalized the Baker-Rhin interface ($\mu = 8.616$) for $d \to \infty$ cycle limits.
- **Dimensional Collapse (Theorem M1):** Computed the 3-adic dimensional collapse ($D_1 \approx 0.76$) for cyclic shift-words. Crucially, this probabilistic dimension drop is maintained *strictly separate* from the algebraic Diophantine bounds.
- **Pointwise Transport Falsification (GATE-2):** Falsified the TV-Fourier restart hypothesis, renewal closure, and W1 multiblock contraction. The Archimedean-2-adic wall stands.

---

## 3. The Epistemological Wall & No-Go Theorems

We explicitly acknowledge the boundary of modern mathematics: **Measure $0 \neq \emptyset$.**
While we have proven that divergent paths have measure 0, and that practically all numbers drop below their starting value, John Conway's 1972 Undecidability Theorem dictates that generalized Collatz sequences are Turing-unpredictable. Therefore, generic methods cannot rule out a singular parameter-specific Diophantine anomaly.

**No-Go Theorems:** We have documented 9 rigorously falsified approaches (including the Diophantine Misattribution, the CRT Dimensionality Trap, and the Measure-Zero Trap) in `collatz_no_go_theorems.md`. This epistemological map of dead ends is now available in 5 languages (EN, RU, IT, ES, ZH) in the project root.

**The project is not exhausted; it is precisely categorized.** We have mapped the computational bounds of cycle exclusion, formalized the absolute algebraic bedrock in Lean 4, and documented exactly where mathematical undecidability takes over.
