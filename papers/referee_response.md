# Statement for the Referees: The Boundary of Rigor

To assist the review process, we wish to explicitly clarify the boundary between the rigorously proven theorems in our manuscript and the conditional components, addressing a common concern in the literature regarding heuristic leaps in Collatz proofs.

Our work intentionally avoids conflating empirical observation with mathematical proof. We have drawn a strict line between the properties of the 3-adic topology and the integer arithmetic.

**1. What is rigorously proven:**
In Section 3 (Steps A and B), all claims regarding the 3-adic model are strict mathematical theorems. We establish the uniform spectral gap of the tilted 3-adic reverse operator on compact sets, construct the Doob $h$-transformed Markov kernel, and rigorously prove both the Law of Large Numbers (LLN) and the upper large-deviation bound for the conditioned 3-adic process. The thermodynamic variables, such as the empirical rate $I_{\mathrm{rev}}(1.33) \approx 0.2532$ (in bits), are mathematically well-defined properties of this ensemble.

**2. What is conditional:**
Transferring these rigorous 3-adic large-deviation properties to actual integer Collatz orbits is an open problem, which we explicitly formulate as the **Shadowing Hypothesis** (Corollary B3). This is an LDP-level generalization of Terence Tao's Proposition 1.9 (2019). The integer Collatz flow exhibits "architectural dilution" (the spacing between divisions by 2), which introduces a gap that prevents a strictly unconditional proof.

**3. The conclusion:**
By clearly isolating the shadowing hypothesis, we demonstrate exactly what follows if the hypothesis holds. Section 4 shows that conditional on this transfer, we achieve an explicit bound of $\gamma \approx 1$ for the logarithmic density of the exceptional set, yielding a residual density of $<10^{-15}$ at the current $2^{68}$ computational frontier. 

We submit that this transparent delineation—proving the 3-adic thermodynamics rigorously while keeping the integer transfer explicitly conditional—is the most intellectually honest and mathematically productive way to advance the structural understanding of the Collatz conjecture.
