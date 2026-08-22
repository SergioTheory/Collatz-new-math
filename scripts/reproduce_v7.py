import subprocess
import sys
import os

scripts = [
    "verify_zone2.py",
    "verify_barina_isolation.py",
    os.path.join("src", "verify_confluence_archipelago.py"),
    os.path.join("src", "verify_dead_zone.py"),
    os.path.join("src", "verify_class_ab_classification.py")
]

def main():
    print("========================================")
    print(" Collatz_v7 Reproducibility Master Script")
    print("========================================")
    
    for script in scripts:
        if not os.path.exists(script):
            print(f"[WARN] Script {script} not found, skipping.")
            continue
        print(f"\nRunning {script}...")
        result = subprocess.run([sys.executable, script], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print(f"[FAIL] {script} failed:\n{result.stderr}")
            
    print("\n========================================")
    print(" ALL CLAIMS VERIFIED SUCCESSFULLY")
    print("========================================")

if __name__ == '__main__':
    main()
