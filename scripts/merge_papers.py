import re

# Read Part 1
with open('part1_user.tex', 'r', encoding='utf8') as f:
    part1_code = f.read()

# Read Part 2
with open('../papers/part2_large_deviation_theory.tex', 'r', encoding='utf8') as f:
    part2_code = f.read()

# Merge Logic

# Extract Preamble from part 1 up to \title
m_preamble = re.search(r'(.*?)\\title\{', part1_code, re.DOTALL)
preamble = m_preamble.group(1)

# Extract Part 2 Abstract
m_abs2 = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', part2_code, re.DOTALL)
abstract2 = m_abs2.group(1).strip() if m_abs2 else ""
# Remove the first sentence from part 2 abstract since we are merging ("This paper develops...")
# Or just keep it as the second paragraph of the combined abstract.
abstract2_clean = abstract2.replace("This paper develops the rigorous theory", "Part II develops the rigorous theory")

# Extract Part 1 Abstract
m_abs1 = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', part1_code, re.DOTALL)
abstract1 = m_abs1.group(1).strip() if m_abs1 else ""

# Remove the "Companion paper" and "Supplementary Material" blocks from Part 1 abstract as they will be at the end or integrated.
abstract1_clean = re.sub(r'\\smallskip\s*\\noindent\\textit\{Companion paper:\}.*?(?=\\smallskip)', '', abstract1, flags=re.DOTALL)

combined_abstract = f"\\begin{{abstract}}\n{abstract1_clean}\n\n\\smallskip\n\\noindent\\textbf{{Theoretical framework (Part II):}} {abstract2}\n\\end{{abstract}}"

# Build Author Block
author_block = "\\author{Collatz Crystal Hunter Project \\\\[0.5em] \\small with AI Assistance}\n\\date{August 2026}"

# Build Title
title_block = "\\title{The Architecture of the Collatz Space:\\\\Computational Mapping and Large-Deviation Theory}"

# Extract Part 1 Body (from \section*{Glossary and Constants} up to \section*{Data Availability})
m_body1 = re.search(r'(\\section\*\{Glossary and Constants\}.*?)\\section\*\{Data Availability\}', part1_code, re.DOTALL)
body1 = m_body1.group(1).strip() if m_body1 else ""

# Extract Part 2 Body (from \section{Introduction} up to \section{Conclusion)
m_body2 = re.search(r'(\\section\{Introduction\}.*?)\\begin\{thebibliography\}', part2_code, re.DOTALL)
body2 = m_body2.group(1).strip() if m_body2 else ""

# Extract Part 2 Bibliography
m_bib2 = re.search(r'\\begin\{thebibliography\}\{99\}(.*?)\\end\{thebibliography\}', part2_code, re.DOTALL)
bib2 = m_bib2.group(1).strip() if m_bib2 else ""

# Combine Bibliographies (removing duplicates ideally, but simple concat works if we just deduplicate by label)
bib_combined_lines = []
seen_labels = set()

# Part 1 Bib (from user's code)
m_bib1 = re.search(r'\\begin\{thebibliography\}\{99\}(.*?)\\end\{thebibliography\}', part1_code, re.DOTALL)
bib1 = m_bib1.group(1).strip() if m_bib1 else ""

for bib_str in [bib1, bib2]:
    for line in bib_str.split('\n'):
        line = line.strip()
        if not line: continue
        m_label = re.search(r'\\bibitem\{([^}]+)\}', line)
        if m_label:
            label = m_label.group(1)
            if label not in seen_labels and label != "PartII" and label != "PartI":
                seen_labels.add(label)
                bib_combined_lines.append(line)
        else:
            if line not in bib_combined_lines:
                bib_combined_lines.append(line)

combined_bib = "\\begin{thebibliography}{99}\n" + "\n".join(bib_combined_lines) + "\n\\end{thebibliography}"

# Data Availability section (combined)
data_avail = """\\section*{Data Availability and Formalization}
The full Zone 2 catalog (913 entries, \\texttt{zone2\\_shifts\\_full.csv}), 39-center census, KL derivation, beam-search death logs, algorithmic pseudocodes, and Python verification scripts are available in the project GitHub repository. The Lean 4 formalization of the exact conditional transport (Theorem~\\ref{thm:exact_conditional_transport}) and the CRT dimensionality obstruction (Theorem~M1) are also provided in the repository."""


# Assemble the full document
full_doc = f"""{preamble.strip()}
{title_block}
{author_block}
\\begin{{document}}
\\maketitle
{combined_abstract}

\\newpage
\\tableofcontents
\\newpage

\\part{{The Computational Map}}
{body1}

\\part{{Large-Deviation Theory}}
{body2}

{data_avail}

{combined_bib}
\\end{{document}}
"""

with open('../papers/Collatz_Architecture_Full.tex', 'w', encoding='utf8') as f:
    f.write(full_doc)

print("Merged successfully!")
