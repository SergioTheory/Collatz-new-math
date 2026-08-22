import difflib

with open('Collatz_v6_en.tex', 'r', encoding='utf-8') as f1:
    v6_lines = f1.readlines()

with open('Collatz_v7_en.tex', 'r', encoding='utf-8') as f2:
    v7_lines = f2.readlines()

diff = list(difflib.unified_diff(v6_lines, v7_lines, fromfile='v6', tofile='v7'))

with open('diff_v6_v7.txt', 'w', encoding='utf-8') as fout:
    fout.writelines(diff)
