import os
import shutil

base_dir = r"c:\Users\Admin\Documents\Collatz"

# 1. Move the 9 referenced scripts back from archive/
moves = {
    "two_class_analysis.py": "analysis",
    "targeted_search_31_50.py": "src",
    "targeted_search_41_50.py": "src",
    "algebra_centers.py": "analysis",
    "family_a_spectrum.py": "analysis",
    "check_microplateau.py": "src",
    "basin_test.py": "analysis",
    "crt_solver.py": "src",
    "confluence_census.py": "src",
}

for f, d in moves.items():
    src_path = os.path.join(base_dir, "archive", f)
    dst_path = os.path.join(base_dir, d, f)
    if os.path.exists(src_path):
        shutil.move(src_path, dst_path)
        print(f"Restored {f} to {d}/")

# 2. Rename collatz_peak.py to collatz_peak_DEPRECATED.py
peak_old = os.path.join(base_dir, "src", "collatz_peak.py")
peak_new = os.path.join(base_dir, "src", "collatz_peak_DEPRECATED.py")
if os.path.exists(peak_old):
    shutil.move(peak_old, peak_new)
    print("Renamed collatz_peak.py to collatz_peak_DEPRECATED.py")

# 3. Create LICENSE (MIT)
license_text = """MIT License

Copyright (c) 2026 Collatz Crystal Hunter Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
with open(os.path.join(base_dir, "LICENSE"), "w") as f:
    f.write(license_text)
print("Created LICENSE")

# 4. Create CITATION.cff
citation_text = """cff-version: 1.2.0
message: "If you use this software or data, please cite it as below."
authors:
  - family-names: "Collatz Crystal Hunter Project"
    given-names: "Research Team"
title: "Arithmetic Chaos with Rare Islands of Order: A Computational Map of the Collatz Space"
version: 7.0
date-released: 2026-04-19
url: "https://github.com/collatz-crystal-hunter"
"""
with open(os.path.join(base_dir, "CITATION.cff"), "w") as f:
    f.write(citation_text)
print("Created CITATION.cff")

