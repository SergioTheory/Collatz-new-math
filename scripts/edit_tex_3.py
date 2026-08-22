import re

with open("docs/Collatz_v8_en.tex", "r", encoding="utf-8") as f:
    tex = f.read()

footnote = r" \footnote{Note on convention: $d$ includes the transition that generates the peak spike. This shifts $S$ by the final shift amount, ensuring consistency across all formulas.}"
# Add footnote after d_{core} = 251
tex = tex.replace(r"d_{core} = 251", r"d_{core} = 251" + footnote)

table_88_90 = r"""
\begin{table}[h]
\centering
\begin{tabular}{llll}
\toprule
\textbf{Bits} & \textbf{Model Forecast ($0.395$ bit$^{-1}$)} & \textbf{Actual Reverse Tree} & \textbf{Error} \\
\midrule
88 & 287 & 272 & +5\% \\
89 & 379 & 331 & +15\% \\
90 & 497 & 343 & +45\% \\
\bottomrule
\end{tabular}
\caption{Retrospective forecast for bit lengths 88--90. The empirical entropy slope of 0.395 accurately predicts the tree size up to 88 bits, before the saturation of the finite-depth adapter layer kicks in.}
\end{table}
"""

tex = tex.replace(r"entropy of the adapters ($\sim 0.486$).", r"entropy of the adapters." + table_88_90)

with open("docs/Collatz_v8_en.tex", "w", encoding="utf-8") as f:
    f.write(tex)

print("Tex updated.")
