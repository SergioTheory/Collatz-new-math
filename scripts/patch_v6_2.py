import re

with open('Collatz_v6_en.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix Tao Reference
tao_old = r"""Tao, T. (2019). \textit{Almost all orbits of the Collatz map attain almost bounded values}. Forum of Mathematics, Pi, 10, e12."""
tao_new = r"""Tao, T. (2022). \textit{Almost all orbits of the Collatz map attain almost bounded values}. arXiv:1909.03562 (2019); Forum of Mathematics, Sigma, 10 (2022), e12."""
content = content.replace(tao_old, tao_new)

# 2. Section 13 Scaling Hypothesis fix
scaling_old = r"""\item Scaling Hypothesis $\times 10$: Does the Class A hierarchy continue? If so, what is the next Class A center (predicted peak $\approx 1400$)? This hypothesis justifies why we did not find deep funnels of Class A between peaks 14 and 140."""
scaling_new = r"""\item \textbf{Scaling Hypothesis $\times 10$:} Does Class A follow a logarithmic scale (14 $\to$ 140 $\to$ 1400...)? If so, what are the parameters of the hypothetical next Class A center (predicted peak $\approx 1400$, center $\approx 703$ bits)?"""
content = content.replace(scaling_old, scaling_new)

# Just in case it was the original text:
scaling_orig = r"""\item We formulate the \textbf{Scaling Hypothesis $\times 10$}: \textbf{Class A} centers follow a logarithmic scale ($14 \to 140 \to 1400$). This justifies why we did not find deep funnels of \textbf{Class A} between peaks 14 and 140, and contrasts the dense continuous archipelago of \textbf{Class B} with the sparse hierarchy of macro-attractors of \textbf{Class A}."""
content = content.replace(scaling_orig, scaling_new)

# 3. Peak 51 inputs
peak51_old = r"51 & 6572463707 & 33 & — & 88.0\% & 56 & 1.29 \\"
peak51_new = r"51 & 6572463707 & 33 & $\approx$400\footnote{Inputs not computed due to time constraints, value estimated based on trend.} & 88.0\% & 56 & 1.29 \\"
content = content.replace(peak51_old, peak51_new)

# 4. KL Divergence
kl_old = r"""(where the coefficient $0.084$ is the KL-divergence between the target shift distribution and the uniform distribution)"""
kl_new = r"""(KL-divergence $D_{KL}(q \| p)$ where $q$ is the \textbf{Zone~2} shift distribution with $\approx 75\%$ ones and $p$ is the geometric distribution $P(a=k) = 2^{-k}$)"""
content = content.replace(kl_old, kl_new)

# 5. center\_bits
content = content.replace(r"center\_bits", r"\mathrm{center\_bits}")

# 6. Add \endhead to longtables
# First table (Zone 2)
z2_table_old = r"""\begin{longtable}{lllll}
\toprule
\textbf{Bits} & \textbf{Number $n$} & \textbf{Peak} & \textbf{Ratio} & \textbf{Steps to $x^*$} \\
\midrule"""
z2_table_new = r"""\begin{longtable}{lllll}
\toprule
\textbf{Bits} & \textbf{Number $n$} & \textbf{Peak} & \textbf{Ratio} & \textbf{Steps to $x^*$} \\
\midrule
\endhead"""
content = content.replace(z2_table_old, z2_table_new)

# Second table (Reverse tree $x^*$)
xstar_table_old = r"""\begin{longtable}{llll}
\toprule
\textbf{Bits} & \textbf{Nodes in Tree} & \textbf{With Peak 140} & \textbf{Fraction} \\
\midrule"""
xstar_table_new = r"""\begin{longtable}{llll}
\toprule
\textbf{Bits} & \textbf{Nodes in Tree} & \textbf{With Peak 140} & \textbf{Fraction} \\
\midrule
\endhead"""
content = content.replace(xstar_table_old, xstar_table_new)

# Third table (Census)
census_table_old = r"""\begin{longtable}{lllllll}
\toprule
\textbf{Peak} & \textbf{Center} & \textbf{Bits} & \textbf{Inputs} & \textbf{Hit rate} & $d_{peak}$ & $S/d$ \\
\midrule"""
census_table_new = r"""\begin{longtable}{lllllll}
\toprule
\textbf{Peak} & \textbf{Center} & \textbf{Bits} & \textbf{Inputs} & \textbf{Hit rate} & $d_{peak}$ & $S/d$ \\
\midrule
\endhead"""
content = content.replace(census_table_old, census_table_new)

# Fourth table (Summary map)
summary_table_old = r"""\begin{longtable}{lllllll}
\toprule
\textbf{Type} & \textbf{Input Bits} & \textbf{Peak} & $d$ & $S/d$ & \textbf{Class} & \textbf{Status} \\
\midrule"""
summary_table_new = r"""\begin{longtable}{lllllll}
\toprule
\textbf{Type} & \textbf{Input Bits} & \textbf{Peak} & $d$ & $S/d$ & \textbf{Class} & \textbf{Status} \\
\midrule
\endhead"""
content = content.replace(summary_table_old, summary_table_new)

# 7. Add Algorithmic Primitives to Appendix A
primitives = r"""\subsection*{Key Algorithmic Primitives}
\begin{enumerate}
\item \textbf{Confluence Search Filter:} candidate $c$ is accepted iff
  $c \equiv 1 \pmod{2}$, $c \equiv 2 \pmod{3}$, $v_2(3c+1) = 1$, 
  $|\mathrm{bits}(c) - (0.498 \cdot P + 6.29)| \le 3$.
\item \textbf{Reverse Step:} $T^{-1}(x, a) = \{(x \cdot 2^a - 1)/3\}$ 
  if $(x \cdot 2^a - 1) \equiv 0 \pmod{3}$ and result is odd.
\item \textbf{Hit Rate:} $HR(c, P) = |\{y \in V_d : \mathrm{peak}(y) = P\}| / 
  |\{y \in V_d : \mathrm{bits}(y) < P\}|$ where $V_d$ is the reverse tree of $c$ at depth $d$.
\end{enumerate}

\begin{thebibliography}{99}"""
content = content.replace(r"\begin{thebibliography}{99}", primitives)


with open('Collatz_v6_en.tex', 'w', encoding='utf-8') as f:
    f.write(content)
