import re

with open('Collatz_v6_en.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Abstract & Glossary
content = content.replace("Dense archipelago (Peaks 15–51)", "Dense archipelago (Peaks 14–51)")
content = content.replace("dense archipelago (Peaks 15–51)", "dense archipelago (Peaks 14–51)")

# 2. Section 4.2: d=259 vs 258
content = content.replace("All 17 numbers have $d = 259$ odd steps to the peak", 
                          "All 17 numbers have $d = 259$ odd steps to the peak (or equivalently 258 transitions in the shift-vector)")

# 3. Section 6: Number 27
content = content.replace("The trajectory of number 27 has $d = 41$ odd steps, $S/d = 1.707$, a shift-vector with 58.5\\% ones, 24.4\\% twos, 7.3\\% threes",
                          "The trajectory of number 27 has $d_{peak} = 28$ odd steps to the peak, $S/d_{to\_peak} \\approx 1.36$, a shift-vector with 58.5\\% ones, 24.4\\% twos, 7.3\\% threes")
content = content.replace("$S/d$ (to peak) & $\\sim 1.22$ & $\\sim 1.33$ \\\\",
                          "$S/d_{to\_peak}$ & $\\sim 1.36$ & $\\sim 1.33$ \\\\")
content = content.replace("Number 27 & 1.33 & 67\\% & 11 & 5 bits \\\\",
                          "Number 27 & 1.36 & 67\\% & 11 & 5 bits \\\\")

# 4. Section 9.3: 31 centers -> 34 centers
content = content.replace("31 centers", "34 centers")
content = content.replace("on 33 points", "on 34 points")

# 5. Section 9.4: Transitional centers (add 48, 49)
table_to_replace = r"""35 & 26658983 & 61 & 1.459 & 80\% & 66\% & 28\% & Transitional \\
37 & 67625867 & 69 & 1.464 & 87\% & 70\% & 17\% & Transitional \\
41 & 37748015 & 81 & 1.420 & 92\% & 67\% & 26\% & Transitional \\"""

new_table = r"""35 & 26658983 & 61 & 1.459 & 80\% & 66\% & 28\% & Transitional \\
37 & 67625867 & 69 & 1.464 & 87\% & 70\% & 17\% & Transitional \\
41 & 37748015 & 81 & 1.420 & 92\% & 67\% & 26\% & Transitional \\
48 & 2303929595 & 111 & 1.450 & 93\% & 68\% & 25\% & Transitional \\
49 & 3830005073 & 73 & 1.384 & 83\% & 69\% & 22\% & Transitional \\"""
content = content.replace(table_to_replace, new_table)

content = content.replace("Three centers occupy an intermediate position", "Five centers occupy an intermediate position")

# 6. Section 12: Scaling Hypothesis duplication
sec12_scaling = r"""We formulate the \textbf{Scaling Hypothesis \times 10}: \textbf{Class A} centers follow a logarithmic scale ($14 \to 140 \to 1400$). This justifies why we did not find deep \textbf{Class A} funnels between peaks 14 and 140, and contrasts the dense continuous \textbf{Class B} archipelago with the sparse hierarchy of \textbf{Class A} macro-attractors.

The Collatz space is structured more complexly than ``chaos with rare islands''"""

new_sec12_scaling = r"""The Collatz space is structured more complexly than ``chaos with rare islands''"""
content = content.replace(sec12_scaling, new_sec12_scaling)

sec13_scaling_q = r"""We formulate the \textbf{Scaling Hypothesis \times 10}: \textbf{Class A} centers follow a logarithmic scale ($14 \to 140 \to 1400$). This justifies why we did not find deep funnels of \textbf{Class A} between peaks 14 and 140, and contrasts the dense continuous archipelago of \textbf{Class B} with the sparse hierarchy of macro-attractors of \textbf{Class A}."""

new_sec13_scaling_q = r"""Scaling Hypothesis $\times 10$: Does the Class A hierarchy continue? If so, what is the next Class A center (predicted peak $\approx 1400$)? This hypothesis justifies why we did not find deep funnels of Class A between peaks 14 and 140."""
content = content.replace(sec13_scaling_q, new_sec13_scaling_q)


# 9. FA-88b
content = content.replace("The number FA-88b ($2^{88} - 1$)", "The number $2^{88} - 1$")

# 10. Section 7.1 Sanov coefficient
content = content.replace("falls exponentially as $2^{-d \cdot 0.084}$.",
                          "falls exponentially as $2^{-d \cdot 0.084}$ (where the coefficient $0.084$ is the KL-divergence between the target shift distribution and the uniform distribution).")

# 11. Add Computational Complexity section before Open Questions
complexity_section = r"""\section{Computational Complexity}
The computational verification of the Collatz space was achieved using a hybrid array of algorithms, with complexity scaling heavily dependent on the chosen method:
\begin{itemize}
    \item \textbf{Exhaustive Parity Scan} (\texttt{zone\_parity\_search.py}): Reconstructing numbers from shift-vectors requires evaluating $2^{bits}$ parity combinations. Time complexity is $\mathcal{O}(2^{bits})$, making it strictly unfeasible for $bits > 90$ without aggressive pruning.
    \item \textbf{Reverse Tree Generation} (\texttt{reverse\_tree\_xstar.py}): Building predecessors from a known center $x^*$. Complexity scales as $\mathcal{O}(B^{depth})$, where $B \approx 2$ is the average branching factor per odd step. This allowed deep exploration of \textbf{Zone 2} (913 inputs) in milliseconds.
    \item \textbf{Residue Beam Search} (\texttt{residue\_search.py}): Heuristic exploration of the $\mathbb{Z}_2$ space by pruning branches with $S/d < 1.05$. Reduced the search space exponentially, enabling checks up to 170 bits.
    \item \textbf{Confluence Census} (\texttt{targeted\_search\_31\_50.py}): To find \textbf{Class B} centers for peak=51, $22.9 \times 10^9$ candidates were processed using the algebraic filter $c \equiv 2 \pmod 3$, reducing operations by a factor of 3.
\end{itemize}

"""
content = content.replace("\\section{Open Questions}", complexity_section + "\\section{Open Questions}")

# 8. Appendix A: class_a_search_51_80.py
content = content.replace(r"\item \texttt{residue\_search.py} — beam search over residue classes with 3 filters and niching",
                          r"\item \texttt{residue\_search.py} — beam search over residue classes with 3 filters and niching" + "\n    " + r"\item \texttt{class\_a\_search\_51\_80.py} — search for Class A candidates")

# 7. Add References at the end
references = r"""
\begin{thebibliography}{99}
\bibitem{Lagarias1985}
Lagarias, J.C. (1985). \textit{The 3x+1 problem and its generalizations}. The American Mathematical Monthly, 92(1), 3-23.

\bibitem{Tao2019}
Tao, T. (2019). \textit{Almost all orbits of the Collatz map attain almost bounded values}. Forum of Mathematics, Pi, 10, e12.

\bibitem{Barina2021}
Barina, D. (2021). \textit{Convergence verification of the Collatz problem}. The Journal of Supercomputing, 77, 2681-2688.

\bibitem{Kontorovich2005}
Kontorovich, A., Miller, S.J. (2005). \textit{Benford's law, values of L-functions and the 3x+1 problem}. Acta Arithmetica, 120, 269-297.
\end{thebibliography}

\end{document}
"""
content = content.replace(r"\end{document}", references)

with open('Collatz_v6_en.tex', 'w', encoding='utf-8') as f:
    f.write(content)
