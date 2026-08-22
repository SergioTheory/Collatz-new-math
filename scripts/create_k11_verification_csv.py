#!/usr/bin/env python3
"""
Create detailed verification CSV for k=11 divisor predictions.
Tests n = 0 to 10,000 and saves all high-divisor cases to CSV.

Based on Septembrino's formulas from her tables.
"""

import csv
from typing import Dict, List

# ============================================================================
# Septembrino's formulas for k=11 (from her tables)
# ============================================================================

K11_PREDICTIONS = {
    16: {'n_mod': 473, 'modulus': 32768},       # 2^16 when n = 473 mod 32768
    15: {'n_mod': 8665, 'modulus': 16384},      # 2^15 when n = 8665 mod 16384
    14: {'n_mod': 2521, 'modulus': 4096},       # 2^14 when n = 2521 mod 4096
    13: {'n_mod': 1497, 'modulus': 2048},       # 2^13 when n = 1497 mod 2048
    12: {'n_mod': 985, 'modulus': 1024},        # 2^12 when n = 985 mod 1024
    11: {'n_mod': 217, 'modulus': 512},         # 2^11 when n = 217 mod 512
    10: {'n_mod': 217, 'modulus': 512},         # 2^10 when n = 217 mod 512
}

# ============================================================================
# Core functions
# ============================================================================

def get_actual_divisor_power(k: int, n: int) -> int:
    """Find highest power of 2 that divides k*3^n - 1."""
    N = k * (3 ** n) - 1
    power = 0
    temp = N
    while temp % 2 == 0 and power < 30:
        temp //= 2
        power += 1
    return power

def check_septembrino_prediction(k: int, n: int, predictions: Dict) -> int:
    """Get predicted divisor power from Septembrino's formulas."""
    predicted_power = 0
    for power, formula in predictions.items():
        if (n - formula['n_mod']) % formula['modulus'] == 0:
            predicted_power = max(predicted_power, power)
    return predicted_power

# ============================================================================
# Main verification
# ============================================================================

def main():
    print("=" * 80)
    print("CREATING K=11 VERIFICATION CSV")
    print("Testing n = 0 to 10,000")
    print("=" * 80)
    print()
    
    k = 11
    max_n = 10000
    results: List[Dict] = []
    high_divisor_count = 0
    
    print(f"Testing k={k}, n=0 to {max_n}...")
    print()
    
    for n in range(max_n + 1):
        actual_power = get_actual_divisor_power(k, n)
        predicted_power = check_septembrino_prediction(k, n, K11_PREDICTIONS)
        
        # Save all cases with high divisors (≥ 2^10)
        if actual_power >= 10:
            high_divisor_count += 1
            match = (predicted_power == actual_power)
            
            results.append({
                'n': n,
                'predicted_power': predicted_power,
                'actual_power': actual_power,
                'predicted_divisor': 2 ** predicted_power if predicted_power > 0 else 0,
                'actual_divisor': 2 ** actual_power,
                'match': 'Yes' if match else 'No',
                'offset': actual_power - predicted_power if predicted_power > 0 else 'N/A',
            })
            
            # Print progress for high values
            if actual_power >= 12:
                print(f"n={n:>5}: predicted 2^{predicted_power:>2}, actual 2^{actual_power:>2}, match={match}")
    
    print()
    print("=" * 80)
    print(f"RESULTS FOR k={k}, n=0 to {max_n}:")
    print("=" * 80)
    print(f"Total n values tested: {max_n + 1}")
    print(f"Values with high divisors (≥ 2^10): {high_divisor_count}")
    print()
    
    if results:
        matches = sum(1 for r in results if r['match'] == 'Yes')
        partial = sum(1 for r in results if r['predicted_power'] > 0 and r['match'] == 'No')
        unpredicted = sum(1 for r in results if r['predicted_power'] == 0)
        
        print(f"Exact matches (predicted = actual): {matches} ({matches/len(results)*100:.1f}%)")
        print(f"Partial matches (predicted something, but wrong): {partial} ({partial/len(results)*100:.1f}%)")
        print(f"Unpredicted (formula gave no prediction): {unpredicted} ({unpredicted/len(results)*100:.1f}%)")
    print()
    
    # Save to CSV
    output_file = 'septembrino_verification_k11_detailed.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['n', 'predicted_power', 'actual_power', 'predicted_divisor', 
                      'actual_divisor', 'match', 'offset']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print("=" * 80)
    print(f"Saved detailed results to {output_file}")
    print(f"Total rows: {len(results)}")
    print("=" * 80)
    print()
    print("This file can be attached to the email to Anabel (Septembrino).")

if __name__ == '__main__':
    main()