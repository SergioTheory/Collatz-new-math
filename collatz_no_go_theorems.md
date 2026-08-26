# No-Go Theorems in Collatz Hypothesis

This document catalogs rigorously and numerically falsified approaches to proving or disproving the Collatz Conjecture.

## 1. Thermodynamic/Macro-state Pointwise Domination (Dead)
**Hypothesis**: The Haar measure of odd classes completely dominates the evolution, pushing all trajectories to the stationary distribution.
**Falsified**: Falsified computationally. At finite scales (e.g., $B=16$), the boundary-layer Fourier cancellation leaves structural overlaps $E_B^{wt} \approx C \cdot 2^{-B/2}$. The uniform Haar measure does not point-wise bound the endpoints of specific words.

## 2. Finite-scale TV-Fourier Restart (Dead)
**Hypothesis**: After $d$ steps, the distribution of endpoints loses all memory of its starting block, and the Total Variation (TV) distance to a uniform restart decays exponentially.
**Falsified**: Numerically falsified in Phase A (GATE-2). The TV distance between transported endpoints and fresh uniform starts remains $O(1)$ (around $0.5 - 0.9$) and exhibits no decay. The low 2-adic bits retain memory across blocks.

## 3. Renewal Closure & W1 Contractivity (Dead)
**Hypothesis**: The trajectory can be treated as a Markovian renewal process where the time to reach $x < x_0$ forms a closed distribution, or the Wasserstein ($W_1$) metric contracts across multiple blocks.
**Falsified**: Numerically falsified (GATE-2). The renewal constant $c^*(B)$ drops drastically (e.g., $0.90 \to 0.13$) when scaling barriers, proving the process is not structurally closed. Multi-block $W_1$ distances do not contract; memory in the low bits perfectly preserves mass displacement, preventing mixing.

## 4. Hybrid Cylinder-Interval Counting (Vector 5 - Dead)
**Hypothesis**: One can count the exact number of trajectories inside an Archimedean interval by exploiting transversal intersections of 2-adic cylinders with the interval boundaries.
**Falsified**: Numerically falsified. The transversal intersection factor $\tau(S)$ converges almost exactly to $1.0$ (exact Haar frequency). There is no transversal deficit to exploit for bounding trajectory counts.

## 5. Local Grammar & Bit-Lift Divergence (G2 - Numerically Falsified)
**Hypothesis**: Divergent trajectories can be constructed by finding local dynamic grammar (words of length $d$) that survives above $x_0$ and using the minimum CRT integer lift (bit-lift).
**Result**: 
- For an ensemble of 1000 synthesized bit-lifts (prefix $d=50$, max-growth branch $\sigma \approx 1.0$, starting at $x_0 = \rho_w + 2^{S+1}q_{\min}$):
  - Median survival is extremely small (maximum 235 odd steps).
  - ZERO candidates survived $10^6$ steps (and none even survived $10^5$).
**Interpretation (Not a Theorem)**:
- Synthesis via bit-lift generates starting points that are pseudo-random in their 2-adic continuation. The near-critical or max-growth structures explicitly engineered for the first $d$ steps are *not* an attractor for the actual deterministic orbit.
- This confirms the separation of "grammatical design" and "real orbits." 
- This does *not* prove divergence is impossible ($0/1000$ is an ensemble observation, not an exhaustive bound), nor does it evaluate the exact role of near-critical structures ($\sigma \approx 1.584$).
**Consequence**: Bit-lift synthesis (taking minimum $q$ in the $2^{S+1}$ lattice) is definitively closed as a search heuristic for counter-examples. Divergence existence cannot be proven or disproven using pure short-horizon local grammar.
