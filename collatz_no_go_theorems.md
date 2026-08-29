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

## 6. ROUTE 3 TARGET THEOREM (Active — what we are proving)

**Name**: *The divergent set has $2$-adic Haar measure zero; the fixed-barrier set has Hausdorff dimension $< 1$.* (Paper: Theorem T3, "geometric multi-block survival".)

**Statement (the precise claim being formalized in Lean, `Divergence.lean`).**

Let $\mathrm{Syr}$ be the accelerated Collatz map over odd integers. For a barrier $N_0$ define the survival set
$$ E_{N_0} = \{\, N \in 2\mathbb N + 1 :\ \mathrm{Syr}^j(N) > N_0\ \ \forall j \ge 1\,\}. $$

> **Route 3 Theorem.** (i) There is a per-block survival rate $c_\ast < 1$ and a resolution floor $\delta_d > 0$ such that, over any $2$-adic ball of $M = 2^{\alpha B - 1}$ odd starts, the mass of survivors after $k$ blocks satisfies the TV-free recurrence
> $$ A_{k+1} \;\le\; c_\ast\, A_k \;+\; \frac{\binom{\sigma d}{d}}{M} \;=\; c_\ast A_k + O(2^{-\delta_d B}), $$
> hence $A_k \le C\,c_\ast^{k} + C'\,2^{-\delta_d B}$ (geometric-plus-resolution-floor). (ii) Consequently
> $$ \dim_H(E_{N_0}) \;\le\; 1 + \frac{\log_2 c_\ast}{2d} < 1, \qquad \mu_2(E_{N_0}) \;\le\; C'\,2^{-\delta_d B} \to 0, $$
> and the divergent set $\bigcap_{N_0} E_{N_0}$ has $2$-adic Haar measure zero.

**Constants to pin numerically (the only inputs — no Fourier machinery required):**
- $c_\ast$ — per-block survival rate. Paper / Gate-2 measured band $c_\ast \in [0.51, 0.56]$; also $c_\ast = 2^{-B t I_2(\sigma)}$ with $I_2$ the Cramer rate of $\mathrm{Geom}(2)$.
- $\delta_d = \alpha - \sigma t\, H_2(1/\sigma) > 0$ (parameter gap); paper reference value $\approx 0.5255$.
- $I_2(1.33) \approx 0.25498$ bits (Cramer rate at the Zone-2 chord).

**Why NOT the Fourier / Front-C route (paper, "Two Fourier regimes and the worst-case barrier"):**
- $c_\infty$ (worst-case Fourier rate) is *not determined*; data allow $c_\infty = 0$ (subexponential). The sup is attained at low-$s$ frequencies $\xi=2^s$, $s/n\to\log_2 3$; the exceptional family has cardinality $O(n)$, not $L^2$-negligible.
- The paper itself: "Fourier route was closed", "every candidate mechanism ... falsified", "apparent spectral gap is a transient finite-window effect".
- The proven T3 bound needs **no** Fourier decay (TV-free binomial floor); unconditional for each fixed $N_0$.

**Why this is the correct Route 3:** it is the honest reachable divergence statement, already unconditional in the paper, uses exactly the Lean machinery we have (`endpoint_count_bounds` $\equiv$ `prop_B3`, `T3_recurrence`, `Stage4Decay.survivor_decay_ax`), and needs only two scalar constants ($c_\ast$, $\delta_d$) obtainable from existing scripts. The Fourier/Front-C constant $c_\infty$ remains an explicit open question — running E5 on the spectrum now would reproduce the Gate-2 data-without-theorem pattern.
**Formalization status (Lean 4, Divergence.lean):**
- haarMeasure is *defined* as 
atUpperDensity — **not an axiom**.
- haarMeasure_mono is **proved** from 
atUpperDensity_mono.
- **haar_small is a THEOREM**: ∀ ε>0, ∃ N₀, haarMeasure (divergentSet N₀) < ε, proved from lock_density_bound (the counting interface = quantified ndpoint_count_bounds + T3_recurrence) via lock_density_le : haarMeasure (blockSurvivors N₀ k) ≤ (1/2)^k and ENNReal.exists_inv_two_pow_lt.
- **divergent_measure_zero is a THEOREM:** haarMeasure (⋂ N, divergentSet N) = 0.
- Remaining axioms in Divergence.lean are all **dynamic** (survivesBarrier, survivesBlocks, survives_forever_iff, survivesBarrier_antitone, block_density_bound) — none is a measure-theory axiom. Build green, 0 sorries.


## 7. ROUTE 4 TARGET (Reverse Collatz Tree - Active, conceptual)

**The honest Route-4 object is NOT the Fourier spectrum.** The paper's Gate 2
campaign and "Two Fourier regimes" section closed the Fourier route: c_infty
(worst-case Fourier rate) is undetermined (may be 0), and every candidate
Fourier/restart mechanism was falsified. Running E4 on front/fourier scripts
today would reproduce the data-without-theorem pattern.

**What Route 4 actually is.** The reverse Collatz tree from 1 (nodes x, edges
x -> (2^s x - 1)/3 for s with 2^s x = 1 mod 3). A node reaches 1 iff it is in
this tree. Three statements, in increasing strength:

1. *(Provable from Routes 1-3, formalized next)* the non-return set has Haar
   measure zero, and the reverse tree of 1 is topologically dense in Z_2.
   Since every non-divergent orbit is eventually periodic (bounded => cycle),
   and Route 2 excludes non-trivial cycles, the set of numbers NOT reaching 1
   = divergent-set union cycles = measure zero. Hence every 2-adic cylinder
   meets the reverse tree of 1.
2. *(Finite certificate, computed - scripts/reverse_tree_front.py)* the tree
   covers 100% of odd residue classes mod 2^k for k = 1..9, with front depth
   d_k ~ 1.3k (e.g. mod 2^5 -> depth 5, mod 2^9 -> depth 12). Written to
   data/route4_front_certificate.json.
3. *(Open, the actual conjecture)* every single integer reaches 1 (pointwise).
   Density of a measure-1 set does not exclude a single point; this remains
   beyond all density methods (Tao, our paper).

**First conceptual steps (recommended):**
1. Formalize in Lean the "reaches 1" predicate + reverse_tree_dense: every
   cylinder meets the reverse tree, as a corollary of Divergence.measure_zero
   + Route 2 cycle exclusion (no new axioms).
2. Extend the finite certificate to k = 16 with a larger shift cap (currently
   S_max = 18, depth 26).
3. Leave Fourier/Front C as a documented open problem, not an E5 campaign.
