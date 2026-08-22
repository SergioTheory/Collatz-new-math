import re

with open("docs/Collatz_v8_en.tex", "r", encoding="utf-8") as f:
    tex = f.read()

# I will replace the entirety of section 4.3 and 4.4, and insert 4.6
# I will do this via regex or string manipulation.
# For now, let's locate the sections.

print("Length:", len(tex))
