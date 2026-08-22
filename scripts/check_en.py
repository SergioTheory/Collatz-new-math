import re

with open('C:\\Users\\Admin\\Documents\\Collatz\\docs\\Collatz_v11_en.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# I want to find the exact strings for constants in English
print("K^(1/gamma) found:", content.find(r"K^{1/\gamma}"))
print("10^-17 found:", content.find(r"10^{-17}"))
print("P - B found:", content.find(r"P - B"))
print("I_1 \\circ I_1 \\circ I_2 found:", content.find(r"I_1 \circ I_1 \circ I_2"))
print("c = 0.416 found:", content.find("0.416"))
print("c \\approx 0.55 found:", content.find("0.55"))
print("3^{-2.26n} found:", content.find(r"3^{-2.26n}"))

# Find headers for reordering
for match in re.finditer(r'\\section\{([^}]+)\}', content):
    print(match.group(0))
for match in re.finditer(r'\\section\*\{([^}]+)\}', content):
    print(match.group(0))
for match in re.finditer(r'\\subsection\{([^}]+)\}', content):
    print(match.group(0))

print("Finding centers...")
idx = content.find("34 peaks")
print(content[idx:idx+100])

print("Finding table peaks...")
idx2 = content.find("31 &")
if idx2 != -1:
    print(content[idx2-200:idx2+200])
