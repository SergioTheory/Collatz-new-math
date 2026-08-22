#!/usr/bin/env python3
"""
analyze_near_anchors.py (Multiprocessing v2)
Finds near-anchors (k*3^n - 1 = 2^a * reduced, where reduced <= 10)
Uses 18 workers for parallel computation.
"""

import os
import csv
import sys
from multiprocessing import Pool, cpu_count
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================
K_MAX = 2000
N_MAX = 60
REDUCED_THRESHOLD = 10  # "near-anchor" condition: reduced part <= 10
NUM_WORKERS = 18        # Requested worker count

# ============================================================================
# CORE COMPUTATION
# ============================================================================
def process_k_chunk(k_list):
    """Process a chunk of k values. Returns list of anchor dicts."""
    results = []
    # Precompute powers of 3 once per chunk for slight speedup
    powers_of_3 = [3 ** n for n in range(N_MAX + 1)]
    
    for k in k_list:
        for n in range(N_MAX + 1):
            N = k * powers_of_3[n] - 1
            if N <= 0:
                continue
                
            # Fast 2-adic valuation
            a = 0
            temp = N
            while temp % 2 == 0:
                temp >>= 1
                a += 1
                
            reduced = temp
            if reduced <= REDUCED_THRESHOLD:
                results.append({
                    'k': k,
                    'n': n,
                    'a': a,
                    'N_bits': N.bit_length(),
                    'k_mod_16': k % 16,
                    'k_mod_32': k % 32,
                    'residue_class': k % 16,
                    'reduced': reduced
                })
    return results

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    print("=" * 80)
    print("NEAR-ANCHOR ANALYSIS & CORRELATION WITH HIGH DIVISORS")
    print(f"Scanning k=1..{K_MAX}, n=0..{N_MAX} | Workers: {NUM_WORKERS}")
    print("=" * 80)
    print()
    
    # Prepare k values (odd numbers only)
    k_values = list(range(1, K_MAX + 1, 2))
    total_k = len(k_values)
    
    # Split into chunks for workers
    chunk_size = max(1, total_k // NUM_WORKERS)
    chunks = [k_values[i:i + chunk_size] for i in range(0, total_k, chunk_size)]
    
    all_results = []
    processed = 0
    
    print("Starting parallel computation...")
    print("-" * 80)
    
    # Use multiprocessing pool
    with Pool(processes=NUM_WORKERS) as pool:
        # imap_unordered yields results as they finish, keeping CPU busy
        for chunk_results in pool.imap_unordered(process_k_chunk, chunks):
            all_results.extend(chunk_results)
            processed += len(chunks[0]) if chunks else 0
            # Approximate progress
            current_k = min(processed, total_k)
            if current_k % 100 == 0 or current_k == total_k:
                print(f"Progress: {current_k}/{total_k} k-values processed | Anchors found: {len(all_results)}")
                
    print("-" * 80)
    print(f"\n✅ Computation complete!")
    print(f"Total near-anchors found: {len(all_results)}")
    
    # Sort results for readability
    all_results.sort(key=lambda x: (x['k'], x['n']))
    
    # Save to CSV
    output_file = 'anchors_k1_2000_n0_60.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['k', 'n', 'a', 'N_bits', 'k_mod_16', 'k_mod_32', 'residue_class', 'reduced']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
        
    print(f"💾 Saved to: {output_file}")
    print("=" * 80)
    
    # Quick summary
    if all_results:
        print("\n📊 Quick Summary:")
        print(f"  Min k: {all_results[0]['k']} | Max k: {all_results[-1]['k']}")
        print(f"  Min n: {min(r['n'] for r in all_results)} | Max n: {max(r['n'] for r in all_results)}")
        print(f"  Max a (power of 2): {max(r['a'] for r in all_results)}")
        print(f"  Most common reduced value: {max(set(r['reduced'] for r in all_results), key=lambda x: sum(1 for r in all_results if r['reduced']==x))}")

if __name__ == '__main__':
    # Windows multiprocessing safety
    import multiprocessing
    multiprocessing.freeze_support()
    main()