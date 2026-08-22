import os
import shutil
import glob

base_dir = r"c:\Users\Admin\Documents\Collatz"

# Ensure directories exist
for d in ["src", "data", "analysis", "docs", "archive"]:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

# 1. Move verify scripts to src/
verify_scripts = ["verify_zone2.py", "verify_barina_isolation.py"]
for f in verify_scripts:
    src_path = os.path.join(base_dir, f)
    dst_path = os.path.join(base_dir, "src", f)
    if os.path.exists(src_path):
        shutil.move(src_path, dst_path)

# 2. Update reproduce_v7.py to point to src/
reproduce_path = os.path.join(base_dir, "reproduce_v7.py")
if os.path.exists(reproduce_path):
    with open(reproduce_path, 'r') as f:
        content = f.read()
    content = content.replace('"verify_zone2.py"', 'os.path.join("src", "verify_zone2.py")')
    content = content.replace('"verify_barina_isolation.py"', 'os.path.join("src", "verify_barina_isolation.py")')
    with open(reproduce_path, 'w') as f:
        f.write(content)

# 3. Aggressive move to archive/
keep_in_root = {
    "reproduce_v7.py",
    "requirements.txt",
    "README.md",
    "CrystalHunter_Console.exe",
    "cleanup.py"
}

# Iterate over all files in root
for item in os.listdir(base_dir):
    item_path = os.path.join(base_dir, item)
    if os.path.isfile(item_path):
        if item in keep_in_root:
            continue
        
        # We also have folders src, data, analysis, docs, archive, stats, logs, etc. They are dirs, so isfile is False.
        # Move the file to archive/
        dst_path = os.path.join(base_dir, "archive", item)
        # Handle overwriting or just pass
        if not os.path.exists(dst_path):
            shutil.move(item_path, dst_path)
            print(f"Moved {item} to archive/")
        else:
            try:
                os.remove(item_path)
                print(f"Deleted duplicate {item} in root")
            except:
                pass

print("Deep cleanup complete.")
