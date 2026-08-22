#!/usr/bin/env python3
"""
Generate data in Septembrino's filtered table format.
- Filter by residue class (k ≡ r mod m)
- Remove low divisors (2, 8, 16)
- Output high divisors only (32, 64, 128, 256, 512, 1024, 2048, 4096...)
"""

import csv
from typing import List, Dict

# ============================================================================
# CONFIGURATION
# ============================================================================

# Residue classes to extract (from her tables)
RESIDUE_CLASSES = [
    {'mod': 16, 'residue': 3, 'name': 'k_eq_3_mod_16'},
    {'mod': 32, 'residue': 1, 'name': 'k_eq_1_mod_32'},
    {'mod': 32, 'residue': 17, 'name': 'k_eq_17_mod_32'},
]

# Divisors to REMOVE (low divisors)
REMOVE_DIVISORS = [2, 4, 8, 16]

# Minimum divisor to KEEP
MIN_DIVISOR = 32

# Data range
K_MAX = 2000  # Extend from 999 to 2000
M_MAX = 60    # Extend from 40 to 60

# ============================================================================
# Load and process data
# ============================================================================

def load_trajectories(filename: str = 'septembrino_table.csv') -> List[Dict]:
    """Load trajectories from CSV."""
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def filter_by_residue(trajs: List[Dict], mod: int, residue: int) -> List[Dict]:
    """Filter trajectories by k ≡ residue (mod mod)."""
    return [t for t in trajs if int(t['k']) % mod == residue]

def remove_low_divisors(trajs: List[Dict], remove: List[int]) -> List[Dict]:
    """Remove low divisors from trajectories."""
    filtered = []
    for t in trajs:
        new_t = t.copy()
        for i in range(1, 41):
            col = f'div_{i}'
            if col in new_t and new_t[col]:
                d = int(new_t[col])
                if d in remove:
                    new_t[col] = ''  # Remove this divisor
        filtered.append(new_t)
    return filtered

def extract_high_divisors(trajs: List[Dict], min_div: int) -> Dict[int, List[Dict]]:
    """Group trajectories by k, keeping only high divisors."""
    by_k = {}
    for t in trajs:
        k = int(t['k'])
        if k not in by_k:
            by_k[k] = []
        
        high_divs = []
        for i in range(1, 41):
            col = f'div_{i}'
            if col in t and t[col]:
                d = int(t[col])
                if d >= min_div:
                    high_divs.append({'position': i, 'divisor': d})
        
        if high_divs:  # Only include k that have high divisors
            by_k[k].append({
                'm': int(t['m']),
                'high_divisors': high_divs
            })
    
    return by_k

# ============================================================================
# Output in Septembrino's table format
# ============================================================================

def create_filtered_table(by_k: Dict[int, List[Dict]], output_file: str, 
                          residue_name: str):
    """Create table in Septembrino's format (k, then high divisors in columns)."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"DIVISORS {residue_name} (removing 2's, 8's, 16's)\n")
        f.write("=" * 80 + "\n\n")
        
        # Sort by k
        sorted_k = sorted(by_k.keys())
        
        for k in sorted_k:
            entries = by_k[k]
            for entry in entries:
                m = entry['m']
                high_divs = entry['high_divisors']
                
                # Format: k: div1 div2 div3 ...
                div_str = ' '.join(f"{d['divisor']}" for d in high_divs)
                f.write(f"{k:>4}: {div_str}\n")
        
        f.write("\n" + "=" * 80 + "\n")

# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 80)
    print("GENERATING DATA IN SEPTembrino's FILTERED TABLE FORMAT")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading trajectories...")
    trajs = load_trajectories()
    print(f"Loaded {len(trajs)} trajectories")
    print()
    
    # Process each residue class
    for rc in RESIDUE_CLASSES:
        print(f"Processing {rc['name']}...")
        
        # Filter by residue
        filtered = filter_by_residue(trajs, rc['mod'], rc['residue'])
        print(f"  {len(filtered)} trajectories match k ≡ {rc['residue']} (mod {rc['mod']})")
        
        # Remove low divisors
        cleaned = remove_low_divisors(filtered, REMOVE_DIVISORS)
        
        # Extract high divisors
        by_k = extract_high_divisors(cleaned, MIN_DIVISOR)
        print(f"  {len(by_k)} k values have high divisors (≥ {MIN_DIVISOR})")
        
        # Create table
        output_file = f"septembrino_filtered_{rc['name']}.txt"
        create_filtered_table(by_k, output_file, rc['name'])
        print(f"  Saved to {output_file}")
        print()
    
    print("=" * 80)
    print("Done! Files ready to send to Anabel.")
    print("=" * 80)

if __name__ == '__main__':
    main()