import re

with open('C:\\Users\\Admin\\Documents\\Collatz\\docs\\Collatz_v12_en.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update text and constants
content = content.replace(r'K^{1/\gamma} \approx e^{10.3} \approx 3 \times 10^4', r'K^{1/\gamma} \approx 10^{7.7}')
content = content.replace(r'\approx 1 - 2.5 \times 10^{-17}', r'\approx 1 - 2.5 \times 10^{-9}')
content = content.replace(r'P - B \approx 68.4', r'P - B \approx 63.8')
content = content.replace(r'I_1 \circ I_1 \circ I_2', r'I_2 \circ I_1 \circ I_1')
content = content.replace(r'(conjugate to the direct pattern (2,1,1))', r'(applying $I_1$, then $I_1$, then $I_2$, which is conjugate to the direct pattern (2,1,1))')
content = content.replace(r'c = 0.416 (verified computationally for $n \le 14$ across frequencies', r'c = 0.416 (strict conservative bound, verified computationally for $n \le 14$ across frequencies')
content = content.replace(r'c \approx 0.55)', r'c \approx 0.55, empirical spectral gap)')
content = content.replace(r'which is stronger than the theoretical bound $3^{-2.26n}$', r'which is stronger than the theoretical bound $3^{-2.26n}$ (since $2n-3 < 2.26n$ for large $n$, the empirical lower bound is larger and therefore stronger)')

# Peaks replace
old_peaks = '34 peaks (checked for all integer peaks from 14 to 50, confirmed for peaks 14, 16, 18, 19, 21--27, 30--34, 36, 38--40, 42--50)'
new_peaks = '39 peaks (checked for all integer peaks from 14 to 51, confirmed for peaks 14--51 except 35, 37, 41)'
content = content.replace(old_peaks, new_peaks)

# Expedition D
content = content.replace('Data for Peak 51 has been added', 'Data for peaks 15, 17, 20, 28, 29 (from Expedition D), and Peak 51 have been added')

# Fix math delimiter typo if it exists (I didn't introduce it this time, but just in case it existed before)
content = content.replace('after $ odd steps', 'after $d$ odd steps')

# 4. Structural Reordering
sections = re.split(r'(?=\\section\{|\\section\*\{|\\subsection\{|\\appendix)', content)

new_parts = {
    'main': [],
    'branching': [],
    'effective': [],
    'conclusion': [],
    'appendix_start': [],
    'app_a': [],
    'app_b': [],
    'bib': []
}

current_group = 'main'
for sec in sections:
    if sec.startswith(r'\subsection{The Branching Balance: the Center as a Caustic (Model T1)}'):
        current_group = 'branching'
    elif sec.startswith(r'\section{Effective Almost-All Bounds for Collatz Orbits}'):
        current_group = 'effective'
    elif sec.startswith(r'\section{Conclusion: Crystals Cannot Be Grown}'):
        current_group = 'conclusion'
    elif sec.startswith(r'\section*{Glossary and Constants}'):
        current_group = 'conclusion'
    elif sec.startswith(r'\section*{Data Availability and Supplementary Material}'):
        current_group = 'conclusion'
    elif sec.startswith(r'\appendix'):
        current_group = 'appendix_start'
    elif sec.startswith(r'\section*{Appendix A. Main Project Scripts}'):
        current_group = 'app_a'
    elif sec.startswith(r'\section{Nature of the Instanton (Expedition B)}'):
        current_group = 'app_b'
    elif sec.startswith(r'\begin{thebibliography}'):
        current_group = 'bib'
    
    new_parts[current_group].append(sec)
    
    if current_group == 'branching':
        current_group = 'main'
    if current_group == 'effective':
        current_group = 'main'

final_content = ''.join(new_parts['main']) + \
                ''.join(new_parts['branching']) + \
                ''.join(new_parts['effective']) + \
                ''.join(new_parts['conclusion']) + \
                ''.join(new_parts['appendix_start']) + \
                ''.join(new_parts['app_a']) + \
                ''.join(new_parts['app_b']) + \
                ''.join(new_parts['bib'])

with open('C:\\Users\\Admin\\Documents\\Collatz\\docs\\Collatz_v12_en.tex', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Done building Collatz_v12_en.tex")
