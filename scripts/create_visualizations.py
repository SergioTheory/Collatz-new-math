#!/usr/bin/env python3
"""
Create high-resolution visualizations from Septembrino filtered divisor tables.
Generates heatmaps, distribution charts, and summary tables.

Usage:
    python create_visualizations.py

Requirements:
    pip install matplotlib numpy
"""

import os
import csv
from collections import defaultdict
import numpy as np

# Check if matplotlib is available
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as colors
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("WARNING: matplotlib not installed. Run: pip install matplotlib numpy")

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_FILES = [
    ('septembrino_filtered_k_eq_3_mod_16.txt', 'k ≡ 3 (mod 16)', 'red'),
    ('septembrino_filtered_k_eq_1_mod_32.txt', 'k ≡ 1 (mod 32)', 'blue'),
    ('septembrino_filtered_k_eq_17_mod_32.txt', 'k ≡ 17 (mod 32)', 'green'),
]

MAX_M = 60
MIN_DIVISOR = 32
OUTPUT_DIR = 'visualizations'

# ============================================================================
# Parse filtered files
# ============================================================================

def parse_filtered_file(filename):
    """Parse the vertical list format. Returns: dict[k] = {m: highest_divisor}"""
    data = defaultdict(dict)
    
    if not os.path.exists(filename):
        print(f"WARNING: {filename} not found!")
        return data
    
    k_m_counter = defaultdict(int)
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
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
            
            m = k_m_counter[k]
            k_m_counter[k] += 1
            
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
# Create heatmap visualization
# ============================================================================

def create_heatmap(data, title, output_file, color_scheme='red'):
    """Create heatmap of k × m with divisor values."""
    
    if not MATPLOTLIB_AVAILABLE:
        print(f"Skipping heatmap (matplotlib not available)")
        return
    
    if not data:
        print(f"No data for {title}, skipping heatmap...")
        return
    
    sorted_k = sorted(data.keys())
    k_to_idx = {k: i for i, k in enumerate(sorted_k)}
    
    # Create matrix
    matrix = np.zeros((len(sorted_k), MAX_M + 1))
    
    for k in sorted_k:
        k_idx = k_to_idx[k]
        for m in range(MAX_M + 1):
            if m in data[k]:
                matrix[k_idx, m] = data[k][m]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(20, 12))
    
    # Custom colormap
    cmap = plt.cm.RdYlGn_r
    max_val = np.max(matrix[matrix > 0]) if np.any(matrix > 0) else 65536
    norm = colors.LogNorm(vmin=32, vmax=max_val)
    
    # Plot heatmap
    im = ax.imshow(matrix, aspect='auto', cmap=cmap, norm=norm, origin='upper')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, label='Divisor Value (log scale)')
    cbar.set_ticks([32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536])
    cbar.set_ticklabels(['32', '64', '128', '256', '512', '1K', '2K', '4K', '8K', '16K', '32K', '65K'])
    
    # Labels
    ax.set_xlabel('m (power of 3)', fontsize=12, fontweight='bold')
    ax.set_ylabel('k value (sorted)', fontsize=12, fontweight='bold')
    ax.set_title(f'Divisor Heatmap: {title}\n(Removing 2, 4, 8, 16 | Showing ≥ 32)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Add grid
    ax.set_xticks(np.arange(-0.5, MAX_M + 1, 5))
    ax.set_xticklabels([str(i) for i in range(0, MAX_M + 1, 5)])
    ax.grid(which='major', color='white', linestyle='-', linewidth=0.5, alpha=0.3)
    
    # Add k value labels on y-axis (show every 5th to avoid crowding)
    step = max(1, len(sorted_k) // 20)
    y_labels = [str(sorted_k[i]) for i in range(0, len(sorted_k), step)]
    y_positions = range(0, len(sorted_k), step)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Created {output_file}")

# ============================================================================
# Create divisor distribution chart
# ============================================================================

def create_distribution_chart(all_data, output_file):
    """Create bar chart showing distribution of divisor values."""
    
    if not MATPLOTLIB_AVAILABLE:
        print(f"Skipping distribution chart (matplotlib not available)")
        return
    
    # Count divisors
    divisor_counts = defaultdict(lambda: defaultdict(int))
    
    for filename, title, _ in INPUT_FILES:
        data = parse_filtered_file(filename)
        for k in data:
            for m, d in data[k].items():
                divisor_counts[title][d] += 1
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Prepare data for plotting
    all_divisors = sorted(set(d for counts in divisor_counts.values() for d in counts.keys()))
    x = np.arange(len(all_divisors))
    width = 0.25
    
    # Plot bars for each residue class
    colors_list = ['red', 'blue', 'green']
    for i, ((filename, title, _), color) in enumerate(zip(INPUT_FILES, colors_list)):
        counts = [divisor_counts[title].get(d, 0) for d in all_divisors]
        ax.bar(x + i * width, counts, width, label=title, color=color, alpha=0.7)
    
    # Labels
    ax.set_xlabel('Divisor Value', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title('Distribution of High Divisors (≥ 32) Across Residue Classes', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x + width)
    ax.set_xticklabels([str(d) for d in all_divisors], rotation=45, ha='right')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    
    # Use log scale for y-axis if range is large
    max_count = 1
    for t in divisor_counts:
        if divisor_counts[t].values():
            max_count = max(max_count, max(divisor_counts[t].values()))
    if max_count > 1000:
        ax.set_yscale('log')
        ax.set_ylabel('Frequency (log scale)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Created {output_file}")

# ============================================================================
# Create summary table CSV
# ============================================================================

def create_summary_table(all_data, output_file):
    """Create comprehensive summary table in CSV format."""
    
    rows = []
    
    for filename, title, _ in INPUT_FILES:
        data = parse_filtered_file(filename)
        
        # Statistics
        total_k = len(data)
        total_entries = sum(len(data[k]) for k in data)
        all_divisors = [d for k in data for d in data[k].values()]
        
        if all_divisors:
            max_divisor = max(all_divisors)
            avg_divisor = sum(all_divisors) / len(all_divisors)
        else:
            max_divisor = 0
            avg_divisor = 0
        
        # Count by divisor value
        divisor_freq = defaultdict(int)
        for k in data:
            for d in data[k].values():
                divisor_freq[d] += 1
        
        # High divisor highlights (≥ 4096)
        high_divisors = [(k, m, d) for k in data for m, d in data[k].items() if d >= 4096]
        
        rows.append({
            'Residue_Class': title,
            'Total_k_Values': total_k,
            'Total_Entries': total_entries,
            'Max_Divisor': max_divisor,
            'Avg_Divisor': f"{avg_divisor:.1f}",
            'High_Divisors_≥4096': len(high_divisors),
            'Divisor_32': divisor_freq.get(32, 0),
            'Divisor_64': divisor_freq.get(64, 0),
            'Divisor_128': divisor_freq.get(128, 0),
            'Divisor_256': divisor_freq.get(256, 0),
            'Divisor_512': divisor_freq.get(512, 0),
            'Divisor_1024': divisor_freq.get(1024, 0),
            'Divisor_2048': divisor_freq.get(2048, 0),
            'Divisor_4096+': sum(v for k, v in divisor_freq.items() if k >= 4096),
        })
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Residue_Class', 'Total_k_Values', 'Total_Entries', 'Max_Divisor', 
                      'Avg_Divisor', 'High_Divisors_≥4096', 'Divisor_32', 'Divisor_64', 
                      'Divisor_128', 'Divisor_256', 'Divisor_512', 'Divisor_1024', 
                      'Divisor_2048', 'Divisor_4096+']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Created {output_file}")

# ============================================================================
# Create high divisor highlights table
# ============================================================================

def create_high_divisor_table(all_data, output_file, min_divisor=4096):
    """Create table of all high divisors (≥ min_divisor)."""
    
    rows = []
    
    for filename, title, _ in INPUT_FILES:
        data = parse_filtered_file(filename)
        
        for k in sorted(data.keys()):
            for m, d in sorted(data[k].items()):
                if d >= min_divisor:
                    rows.append({
                        'Residue_Class': title,
                        'k': k,
                        'm': m,
                        'Divisor': d,
                        'Power_of_2': f"2^{int(np.log2(d))}",
                    })
    
    # Sort by divisor (descending)
    rows.sort(key=lambda x: x['Divisor'], reverse=True)
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Residue_Class', 'k', 'm', 'Divisor', 'Power_of_2']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Created {output_file} with {len(rows)} high divisors (≥ {min_divisor})")

# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 80)
    print("CREATING VISUALIZATIONS FOR SEPTembrino DIVISOR TABLES")
    print("=" * 80)
    print()
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Parse all data
    all_data = {}
    for filename, title, _ in INPUT_FILES:
        data = parse_filtered_file(filename)
        all_data[filename] = data
        print(f"Loaded {filename}: {len(data)} k values")
    print()
    
    # Create heatmaps for each residue class
    print("Creating heatmaps...")
    for filename, title, color in INPUT_FILES:
        output_file = os.path.join(OUTPUT_DIR, f'heatmap_{filename.replace(".txt", "")}.png')
        create_heatmap(all_data[filename], title, output_file, color)
    print()
    
    # Create distribution chart
    print("Creating distribution chart...")
    create_distribution_chart(all_data, os.path.join(OUTPUT_DIR, 'divisor_distribution.png'))
    print()
    
    # Create summary table
    print("Creating summary table...")
    create_summary_table(all_data, os.path.join(OUTPUT_DIR, 'summary_table.csv'))
    print()
    
    # Create high divisor table
    print("Creating high divisor table...")
    create_high_divisor_table(all_data, os.path.join(OUTPUT_DIR, 'high_divisors_≥4096.csv'), min_divisor=4096)
    print()
    
    print("=" * 80)
    print("DONE! All visualizations saved to 'visualizations/' folder")
    print("=" * 80)
    print()
    print("Files created:")
    print("  - heatmap_septembrino_filtered_k_eq_3_mod_16.png")
    print("  - heatmap_septembrino_filtered_k_eq_1_mod_32.png")
    print("  - heatmap_septembrino_filtered_k_eq_17_mod_32.png")
    print("  - divisor_distribution.png")
    print("  - summary_table.csv")
    print("  - high_divisors_≥4096.csv")

if __name__ == '__main__':
    main()