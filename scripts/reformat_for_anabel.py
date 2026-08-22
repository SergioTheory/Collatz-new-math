#!/usr/bin/env python3
"""
Reformat Septembrino filtered tables into Anabel's matrix format.
Converts vertical list format to matrix format (k in rows, m in columns).

Usage:
    python reformat_for_anabel.py
"""

import os
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_FILES = [
    ('septembrino_filtered_k_eq_3_mod_16.txt', '3 (mod 16)'),
    ('septembrino_filtered_k_eq_1_mod_32.txt', '1 (mod 32)'),
    ('septembrino_filtered_k_eq_17_mod_32.txt', '17 (mod 32)'),
]

MAX_M = 60  # Match the range in filtered files (m = 0 to 60)
MIN_DIVISOR = 32

# ============================================================================
# Parse filtered files
# ============================================================================

def parse_filtered_file(filename):
    """
    Parse the vertical list format.
    Each line = one (k, m) combination.
    Lines with same k are ordered by m (m=0,1,2,3...).
    
    Returns: dict[k] = {m: highest_divisor}
    """
    data = defaultdict(dict)
    
    if not os.path.exists(filename):
        print(f"WARNING: {filename} not found!")
        return data
    
    # Track m counter per k
    k_m_counter = defaultdict(int)
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and headers
            if not line:
                continue
            
            if line.startswith('DIVISORS') or line.startswith('=') or line.startswith('Range'):
                continue
            
            if ':' not in line:
                continue
            
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
            
            k_str = parts[0].strip()
            divisors_str = parts[1].strip()
            
            try:
                k = int(k_str)
            except ValueError:
                continue
            
            # Get m value (counter for this k)
            m = k_m_counter[k]
            k_m_counter[k] += 1
            
            # Parse divisors and take highest
            if divisors_str:
                divisors = divisors_str.split()
                highest = 0
                for d in divisors:
                    try:
                        divisor = int(d)
                        if divisor >= MIN_DIVISOR and divisor > highest:
                            highest = divisor
                    except ValueError:
                        continue
                
                if highest > 0:
                    data[k][m] = highest
    
    return data

# ============================================================================
# Create Anabel-style matrix table
# ============================================================================

def create_anabel_table(data, output_file, residue_class):
    """Create table in Anabel's format: k rows × m columns."""
    
    if not data:
        print(f"No data for {residue_class}, skipping...")
        return
    
    sorted_k = sorted(data.keys())
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write(f"DIVISORS k ≡ {residue_class}\n")
        f.write(f"Removing: 2, 4, 8, 16 | Showing: ≥ {MIN_DIVISOR}\n")
        f.write(f"Range: m = 0 to {MAX_M}\n")
        f.write("=" * 100 + "\n\n")
        
        # Column header (m values)
        header = f"{'k':>5} | "
        for m in range(MAX_M + 1):
            header += f"{m:>3} "
        f.write(header + "\n")
        f.write("-" * 100 + "\n")
        
        # Data rows
        for k in sorted_k:
            k_data = data[k]
            row = f"{k:>5} | "
            
            for m in range(MAX_M + 1):
                if m in k_data:
                    d = k_data[m]
                    row += f"{d:>3} "
                else:
                    row += "  . "
            
            f.write(row + "\n")
        
        f.write("\n" + "=" * 100 + "\n")
        f.write("Legend: . = no divisor ≥ 32 for that (k, m)\n")
        f.write("Each cell shows the HIGHEST divisor for that (k, m) combination\n")
    
    print(f"Created {output_file} with {len(sorted_k)} k values")

# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 80)
    print("REFORMATTING SEPTembrino FILTERED TABLES FOR ANABEL")
    print("Reading existing septembrino_filtered_*.txt files")
    print("=" * 80)
    print()
    
    for input_file, residue in INPUT_FILES:
        print(f"Processing {input_file}...")
        
        data = parse_filtered_file(input_file)
        
        if data:
            output_file = input_file.replace('septembrino_filtered_', 'anabel_table_')
            output_file = output_file.replace('.txt', '_FORMATTED.txt')
            create_anabel_table(data, output_file, residue)
        print()
    
    print("=" * 80)
    print("Done! Files ready to send to Anabel.")
    print("=" * 80)
    print()
    print("Output files:")
    for input_file, _ in INPUT_FILES:
        output_file = input_file.replace('septembrino_filtered_', 'anabel_table_')
        output_file = output_file.replace('.txt', '_FORMATTED.txt')
        print(f"  - {output_file}")

if __name__ == '__main__':
    main()