import sys

def update_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
        else:
            print(f'WARNING: Could not find snippet in {path}:\n{repr(old)}')
            
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

v1_fixes = [
    ('$2187$ states', '$1458$ states'),
    ('up to $M=10^5$', 'up to $M \le 10^4$'),
    ('Anomalous suppression (such as $\\theta \\to 0.20$ observed in unrestricted phase sums) is exclusively a consequence of \emph{inter-layer} destructive interference, which is irrelevant for isolated buckets defined at fixed length $d$. Thus, the decay in $\Delta_b$ is not driven by the endpoint distribution becoming artificially smooth, but rather by its sharp peaks systematically avoiding the structural resonances of the bad set.',
     'Thus, the decay in $\Delta_b$ is not driven by the endpoint distribution becoming artificially smooth, but rather by its sharp peaks systematically avoiding the structural resonances of the bad set.')
]

update_file(r'C:\Users\Admin\Documents\Collatz_NewMath\docs\Collatz_NewMath_v1.tex', v1_fixes)

note_fixes = [
    ('up to $M=10^5$', 'up to $M \le 10^4$'),
    ('Anomalous suppression (such as $\\theta \\to 0.20$ observed in unrestricted phase sums) is exclusively a consequence of \emph{inter-layer} destructive interference, which is irrelevant for isolated buckets defined at fixed length $d$. Thus, the decay in $\Delta_b$ is not driven by the endpoint distribution becoming artificially smooth, but rather by its sharp peaks systematically avoiding the structural resonances of the bad set.',
     'Thus, the decay in $\Delta_b$ is not driven by the endpoint distribution becoming artificially smooth, but rather by its sharp peaks systematically avoiding the structural resonances of the bad set.'),
    ('\\frac{S_d}{d}<\\log_2 3+\\frac{\\log_2(N/N_0)}d+O(N_0^{-1})\n>\\log_2 3,',
     '\\frac{S_d}{d}<\\log_2 3+\\frac{\\log_2(N/N_0)}d+O(N_0^{-1}) \\qquad \\text{(which is } > \\log_2 3\\text{)},')
]

update_file(r'C:\Users\Admin\Documents\Collatz_NewMath\docs\Collatz_Shadowing_Note.tex', note_fixes)
print('Done')
