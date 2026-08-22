#!/usr/bin/env python3
"""
Extract high divisors (≥ 128) from Septembrino matrix data.
Creates table showing position, k, m, and k mod 8 classification.

Version: 1.0
Date: March 2026
Project: Collatz Crystal Hunter + Septembrino Collaboration
"""

import csv
import json
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================

HIGH_DIVISOR_THRESHOLD = 128
INPUT_FILE = 'septembrino_table.csv'
OUTPUT_FILE = 'high_divisors_table.csv'

# ============================================================================
# LOAD DATA
# ============================================================================

print("=" * 80)
print("EXTRACTING HIGH DIVISORS FROM SEPTembrino MATRIX DATA")
print("=" * 80)
print()

try:
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        trajectories = list(reader)
    print(f"Loaded {len(trajectories)} trajectories from {INPUT_FILE}")
except FileNotFoundError:
    print(f"ERROR: {INPUT_FILE} not found!")
    print("Run septembrino_matrix_mp.py first to generate the data.")
    exit(1)

print()

# ============================================================================
# EXTRACT HIGH DIVISORS
# ============================================================================

high_divisors = []

for traj in trajectories:
    k = int(traj['k'])
    m = int(traj['m'])
    k_mod_8 = k % 8
    is_regular = k_mod_8 in [5, 7]
    
    for i in range(1, 41):  # Columns 1-40
        col_name = f'div_{i}'
        if col_name in traj and traj[col_name]:
            try:
                d = int(traj[col_name])
                if d >= HIGH_DIVISOR_THRESHOLD:
                    high_divisors.append({
                        'k': k,
                        'm': m,
                        'k_mod_8': k_mod_8,
                        'is_regular': 'Yes' if is_regular else 'No',
                        'position': i,
                        'divisor': d,
                        'log2_divisor': d.bit_length() - 1,  # 128=7, 256=8, etc.
                    })
            except (ValueError, KeyError):
                continue

# Sort by divisor (largest first)
high_divisors.sort(key=lambda x: x['divisor'], reverse=True)

# ============================================================================
# SAVE TO CSV
# ============================================================================

with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['k', 'm', 'k_mod_8', 'is_regular', 'position', 'divisor', 'log2_divisor']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(high_divisors)

# ============================================================================
# PRINT SUMMARY
# ============================================================================

print(f"Total high divisors (≥ {HIGH_DIVISOR_THRESHOLD}): {len(high_divisors)}")
print()

# Summary by divisor value
divisor_counts = defaultdict(int)
for hd in high_divisors:
    divisor_counts[hd['divisor']] += 1

print("Distribution by divisor value:")
print("-" * 60)
for d in sorted(divisor_counts.keys(), reverse=True):
    count = divisor_counts[d]
    pct = count / len(high_divisors) * 100 if high_divisors else 0
    bar = '█' * int(pct / 2)  # Visual bar
    print(f"  {d:>6}: {count:>6} ({pct:>5.1f}%) {bar}")

print()

# Summary by Regular vs Non-Regular
regular_count = sum(1 for hd in high_divisors if hd['is_regular'] == 'Yes')
non_regular_count = len(high_divisors) - regular_count

print("Distribution by matrix type:")
print("-" * 60)
print(f"  Regular matrices    (k ≡ 5,7 mod 8): {regular_count:>6} ({regular_count/len(high_divisors)*100:>5.1f}%)")
print(f"  Non-Regular matrices (k ≡ 1,3 mod 8): {non_regular_count:>6} ({non_regular_count/len(high_divisors)*100:>5.1f}%)")

print()

# Top 20 highest divisors
print("Top 20 highest divisors found:")
print("-" * 60)
print(f"{'k':>6} | {'m':>3} | {'pos':>3} | {'k mod 8':>7} | {'Regular':>7} | {'Divisor':>10}")
print("-" * 60)
for hd in high_divisors[:20]:
    print(f"{hd['k']:>6} | {hd['m']:>3} | {hd['position']:>3} | {hd['k_mod_8']:>7} | {hd['is_regular']:>7} | {hd['divisor']:>10}")

print()
print("=" * 80)
print(f"Saved to {OUTPUT_FILE}")
print("=" * 80)