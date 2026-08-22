import os

tex_path = os.path.join("docs", "Collatz_v7_en.tex")

with open(tex_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add to the end of abstract
abstract_old = r"(\textbf{Class A}), organized around the irrationality $\log_2 3$."
abstract_new = abstract_old + "\n\n" + r"\noindent\textit{Supplementary Material: All computational data, the full Zone 2 catalog (913 entries), algorithmic pseudocodes, and detailed mathematical derivations are available in the Supplementary Material (\texttt{Collatz\_v7\_Supplementary.pdf}).}"
if abstract_old in content and abstract_new not in content:
    content = content.replace(abstract_old, abstract_new)

# Add before References
refs_old = r"\begin{thebibliography}{99}"
refs_new = r"\section*{Data Availability and Supplementary Material}" + "\n" + r"The full catalog of \textbf{Zone 2} (913 entries), detailed derivation of the KL-divergence for Sanov's Theorem, and explicit algorithmic pseudocodes used for verification are provided in the Supplementary Material accompanying this article." + "\n\n" + refs_old

if refs_old in content and refs_new not in content:
    content = content.replace(refs_old, refs_new)

with open(tex_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched Collatz_v7_en.tex with Supplementary mentions.")
