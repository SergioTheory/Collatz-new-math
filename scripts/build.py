#!/usr/bin/env python3
"""
build.py — Collatz Crystal Hunter  (Console-only build)
Run from the source folder:  python build.py
"""
import os, sys, subprocess, shutil
from pathlib import Path

SRC  = Path(__file__).parent.resolve()
DIST = SRC / "dist"
BLD  = SRC / "build"

def run(cmd, **kw):
    print(f"\n> {' '.join(str(c) for c in cmd)}\n")
    r = subprocess.run(cmd, **kw)
    return r.returncode == 0

def check(label, ok):
    print(f"  {'[OK]  ' if ok else '[FAIL]'} {label}")
    return ok

DIST.mkdir(exist_ok=True)
BLD.mkdir(exist_ok=True)

print("\n" + "="*62)
print("  Collatz Crystal Hunter  --  Console Build")
print("="*62)
print(f"  Source : {SRC}")
print(f"  Python : {sys.version.split()[0]}")

# -- verify / install pyinstaller -------------------------------------
r = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                   capture_output=True, text=True)
if r.returncode != 0:
    print("  PyInstaller not found, installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

r = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                   capture_output=True, text=True)
print(f"  PyInstaller: {r.stdout.strip()}")

# -- dependencies -----------------------------------------------------
print("\n[1/3] Installing dependencies...")
subprocess.run([sys.executable, "-m", "pip", "install",
                "pyyaml", "numpy", "--quiet"], check=True)
print("  [OK]  pyyaml, numpy")

# -- Console ----------------------------------------------------------
print("\n" + "="*62)
print("[2/3] Building Console  (CrystalHunter_Console.exe)")
print("      Approx 2-4 minutes...")
print("="*62)

con_ok = run([
    sys.executable, "-m", "PyInstaller",
    "--clean", "--noconfirm",
    "--onefile", "--console",
    "--name", "CrystalHunter_Console",
    "--distpath", str(DIST),
    "--workpath", str(BLD / "console"),
    "--specpath", str(BLD),
    "--add-data", f"{SRC / 'config.yaml'};.",
    "--add-data", f"{SRC / 'records_data.py'};.",
    "--hidden-import", "multiprocessing.pool",
    "--hidden-import", "multiprocessing.managers",
    "--hidden-import", "concurrent.futures",
    "--hidden-import", "concurrent.futures.process",
    "--hidden-import", "queue",
    "--collect-all", "yaml",
    "--collect-all", "numpy",
    str(SRC / "main.py"),
])

if con_ok:
    print("\n  [OK]  dist/CrystalHunter_Console.exe")
else:
    print("\n  [FAIL] Build failed -- see errors above")

# -- copy resources ---------------------------------------------------
print("\n[3/3] Copying resources to dist/...")
shutil.copy2(SRC / "config.yaml", DIST / "config.yaml")
(DIST / "crystal_records").mkdir(exist_ok=True)
(DIST / "logs").mkdir(exist_ok=True)
(DIST / "stats").mkdir(exist_ok=True)

# -- summary ----------------------------------------------------------
print("\n" + "="*62)
print("  Build Summary")
print("="*62)
check("dist/CrystalHunter_Console.exe", con_ok)
print("\n  Files in dist/:")
for f in sorted(DIST.iterdir()):
    print(f"    {f.name}")
print()
print("  NOTE: config.yaml must stay next to the EXE!")
print()
print("  Console flags:")
print("    --bits 80 120    custom bit range")
print("    --workers 16     override worker count")
print("    --resume         continue from snapshot")
print()
input("  Press Enter to exit...")
