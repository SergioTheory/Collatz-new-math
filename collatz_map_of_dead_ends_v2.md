# Collatz Map of Dead Ends v2: Closure of Local Grammar Models

This document formalizes the definitive closure of local grammatical and $\sigma$-class structural searches for Collatz divergence, establishing the precise boundaries of where divergence *cannot* exist and isolating the single remaining theoretical frontier.

## 1. The Universal F1 Decay Law (Mean Drift)
**Finding**: Synthetic bit-lifts (trajectories artificially engineered to survive for $d$ steps with a specific density $\sigma = S/d$) do not survive indefinitely. Once the constructed prefix ends, the trajectory succumbs to the standard statistical drag of pseudo-random continuations.
**Quantitative Rule**: The maximum lifetime $T_{\max}$ of an orbit starting from an optimized bit-lift is governed by the predictive formula for the mean:
$$T_{\max}(d, \sigma) \approx d + \frac{(\lambda - \sigma)d}{0.415} + \epsilon(d)$$
where $\lambda = \log_2 3 \approx 1.58496$, and $0.415$ bits/step is the universal drag (F1 gradient) of a typical random tail. The excess $\epsilon(d)$ corresponds to $2\sigma-3\sigma$ positive variance fluctuations of the random walk.
**Status**: Numerically verified across $\sigma \in [1.30, 1.584]$.

## 2. Clarification of Zone 2 & Structured Cores
**Hypothesis**: Specific grammatical structures (e.g., the Zone-2 repeating core `(1, 1, 2)` with $\sigma \approx 1.333$) possess anomalous resilience that bypasses standard statistical decay.
**Falsified**: The real lifetime of the Zone-2 core perfectly matches the predicted F1 decay rate for its density (falling right between random words of similar $\sigma$). 
**Nuance**: This falsifies the myth that "structure $\implies$ survival". However, it does *not* touch the true mystery of Zone 2, which is **confluence/capture**. Zone-2 acts as a fixed point of the reverse map $R(x)=(16x-29)/27$, capturing trajectories and funneling them toward the peak. The audit proves Zone 2 is not a lifetime-record holder, but its structural role as a convergence node for cascading descent remains untested and intact.

## 3. The Empirical Boundary and The Open Ergodic Question (Vector B)

After exhaustive empirical testing (D3-D8), we have hit the strict limit of what numerical simulation can prove regarding divergence. Every attempt to empirically "falsify" divergence using the F1 decay law or 2-adic mixing revealed a fundamental methodological limit: **one cannot use the properties of typical (converging) orbits to rule out the existence of exceptional (diverging) orbits.**

### The Empirical Ledger (What is Actually Proven)

| Experiment | Target Phenomenon | Actual Mathematical Content (The Truth) | Status for Divergence |
| :--- | :--- | :--- | :--- |
| **D3** | Zone-2 Cascade Capture | Found exact 1/16 independent probability. | **Neutral**: No anomalous global capture, just standard Haar density. |
| **D5** | 2-adic Memory | ensemble $a_{k+1}$ measure given $2^S$ is exactly Geom(2). | **Neutral**: Proves 1-step stationarity, says nothing of long-time path ergodicity. |
| **D6** | Time-Ergodicity (Birkhoff) | A massive falling orbit (100k bits) achieves TV $\to 0$. | **Neutral**: Confirms Tao's theorem for typical orbits ($E[a]=2$), misses exceptional orbits. |
| **D7/D8**| TV of Near-Critical Orbits | TV is strictly $> 0$ for orbits forced to $S/d \approx 1.585$. | **Neutral**: Tautology of conditional geometry. Forcing a mean shift $<2$ mathematically requires skewed modular visits. |

### The True Open Question: Ergodic Decomposition
The impossibility of divergence cannot be proven by pointing out that a divergent orbit would have to break 2-adic uniform mixing (TV $> 0$). **It is an arithmetic requirement that it breaks mixing** to maintain $S/d \le \lambda$. 

The central, formally open question is exactly this:
**Does there exist an invariant measure $\mu$ on the 2-adic integers such that for $\mu$-almost all $x$:**
1. $\lim S_d/d = \sigma \le \log_2 3$ (Survival)
2. The Diophantine error $\delta = |d \log_2 3 - S_d| \le \mathcal{O}(d^c), c < 1$ (Resonance tracking)

If the only invariant measure is the Haar measure (Tao's typical case), then $\sigma = 2$, TV $\to 0$, and divergence is impossible. If a "strange attractor" measure exists that supports the skewed conditional geometry required for $\sigma \le \lambda$, divergence exists. This reduces the Collatz Conjecture to a pure question of **ergodic decomposition of the 2-adic map**.

**Final Consensus**: The empirical phase is closed. The structural impossibility of divergence remains strictly unproven. Future work must shift to formalizing the exact 2-adic transport and Hausdorff dimension drops (e.g., in Lean), leaving the Diophantine/Ergodic gap honestly acknowledged.
