import os
import shutil

base_dir = r"c:\Users\Admin\Documents\Collatz"

# Define directories
dirs = ["src", "data", "analysis", "docs", "archive"]
for d in dirs:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

# Define move mapping (source filename or glob -> target directory)
# Let's specify direct filenames first to avoid matching errors
moves = {
    # Docs
    "Collatz_v7_en.tex": "docs",
    "Collatz_v6_en.pdf": "docs",
    "Collatz_v5.docx": "archive",  # old versions to archive
    "Collatz_v5_extracted.txt": "archive",
    "Collatz_v6.md": "archive",
    "Collatz_v6_en.tex": "archive",
    "math_extraction.md": "docs", # Wait, I don't see math_extraction.md in list_dir output, but Qwen mentioned it. If it doesn't exist, ignore.
    "Алгоритмическая_формализация.md": "docs",
    "SEPTembrino_MATRIX_THEORY.md": "docs",
    
    # Data
    "expand_913.json": "data",
    "targeted_41_50.csv": "data",
    "targeted_41_50.json": "data",
    "targeted_31_50.csv": "data",
    "targeted_31_50.json": "data",
    "confluence_census.json": "data",
    "confluence_census.csv": "data",
    "algebra_centers.json": "data",
    "extra_seeds.json": "data",
    "zone2_shifts.csv": "data",
    
    # Analysis
    "analyze_records_gain.py": "analysis",
    "plot_v7_figures.py": "analysis", # To be created later if needed
}

# Add all verify*, check*, test*, etc., that are old to archive, EXCEPT the new verify_ scripts we will create.
# Actually, it's safer to move EVERYTHING except a whitelist to archive, 
# but that might break imports right now. I will just move some obvious old files to archive.

archive_files = [
    "patch_v6.py", "patch_v6_2.py", "diff.py", "diff_v6_v7.txt", "calc_stats.py", "test_27.py",
    "generate_913.py", "build_v6.py", "translate_to_latex.py", "read_docx.py"
]
for f in archive_files:
    moves[f] = "archive"

for f, d in moves.items():
    src = os.path.join(base_dir, f)
    dst = os.path.join(base_dir, d, f)
    if os.path.exists(src):
        # Handle case where file might already be in target
        if not os.path.exists(dst):
            shutil.move(src, dst)
            print(f"Moved {f} to {d}/")
        else:
            print(f"File {f} already in {d}/")
    else:
        print(f"Skipped {f} - not found in root.")

print("Restructuring stage 1 complete.")
