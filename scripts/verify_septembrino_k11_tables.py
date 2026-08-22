#!/usr/bin/env python3
"""
Verify Septembrino's k=11 divisor prediction tables.
Tests her modular conditions against computed data.

Based on her tables:
- 11*3^n - 1 divisible by 2^p when n ≡ n_mod (mod modulus)
"""

import csv
from typing import Dict, List, Tuple

# ============================================================================
# Septembrino's k=11 prediction table (from her PDF files)
# ============================================================================

K11_PREDICTIONS = {
    3:  {'n_mod': 3,    'modulus': 4},      # 2^3 = 8
    4:  {'n_mod': 5,    'modulus': 8},      # 2^4 = 16
    5:  {'n_mod': 1,    'modulus': 16},     # 2^5 = 32
    6:  {'n_mod': 9,    'modulus': 32},     # 2^6 = 64
    7:  {'n_mod': 57,   'modulus': 64},     # 2^7 = 128
    8:  {'n_mod': 25,   'modulus': 128},    # 2^8 = 256
    9:  {'n_mod': 89,   'modulus': 256},    # 2^9 = 512
    10: {'n_mod': 217,  'modulus': 512},    # 2^10 = 1024
    11: {'n_mod': 985,  'modulus': 1024},   # 2^11 = 2048
    12: {'n_mod': 1497, 'modulus': 2048},   # 2^12 = 4096
    13: {'n_mod': 2521, 'modulus': 4096},   # 2^13 = 8192
    16: {'n_mod': 473,  'modulus': 32768},  # 2^16 = 65536
}

# ============================================================================
# Core functions
# ============================================================================

def get_divisor_power(k: int, n: int) -> int:
    """Find highest power of 2 that divides k*3^n - 1."""
    N = k * (3 ** n) - 1
    power = 0
    temp = N
    while temp % 2 == 0 and power < 30:
        temp //= 2
        power += 1
    return power

def verify_prediction(power: int, n_mod: int, modulus: int, k: int = 11, 
                      max_n: int = 10000) -> Dict:
    """
    Verify a single prediction.
    Returns: {'predicted_n': [...], 'actual_n': [...], 'matches': [...]}
    """
    # Find all n in range that match the modular condition
    predicted_n = [n for n in range(max_n + 1) if (n - n_mod) % modulus == 0]
    
    # Find all n in range where actual divisor >= 2^power
    actual_n = [n for n in range(max_n + 1) 
                if get_divisor_power(k, n) >= power]
    
    # Check which predicted n actually have the divisor
    matches = [n for n in predicted_n if n in actual_n]
    
    return {
        'power': power,
        'divisor': 2 ** power,
        'n_mod': n_mod,
        'modulus': modulus,
        'predicted_n': predicted_n[:10],  # First 10
        'actual_n': actual_n[:10],
        'matches': matches[:10],
        'total_predicted': len(predicted_n),
        'total_actual': len(actual_n),
        'total_matches': len(matches),
        'accuracy': len(matches) / len(predicted_n) * 100 if predicted_n else 0,
    }

# ============================================================================
# Main verification
# ============================================================================

def main():
    print("=" * 80)
    print("VERIFYING SEPTembrino's k=11 DIVISOR PREDICTION TABLES")
    print("=" * 80)
    print()
    
    k = 11
    max_n = 10000
    
    results = []
    
    for power, formula in sorted(K11_PREDICTIONS.items()):
        result = verify_prediction(
            power=power,
            n_mod=formula['n_mod'],
            modulus=formula['modulus'],
            k=k,
            max_n=max_n
        )
        results.append(result)
        
        print(f"2^{power:>2} = {result['divisor']:>6}:")
        print(f"  Condition: n ≡ {formula['n_mod']} (mod {formula['modulus']})")
        print(f"  Predicted n (first 10): {result['predicted_n']}")
        print(f"  Actual n with divisor ≥ 2^{power} (first 10): {result['actual_n']}")
        print(f"  Matches: {result['total_matches']} / {result['total_predicted']} ({result['accuracy']:.1f}%)")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    
    total_predictions = sum(r['total_predicted'] for r in results)
    total_matches = sum(r['total_matches'] for r in results)
    overall_accuracy = total_matches / total_predictions * 100 if total_predictions else 0
    
    print(f"Total predictions tested: {total_predictions}")
    print(f"Total matches: {total_matches}")
    print(f"Overall accuracy: {overall_accuracy:.1f}%")
    print()
    
    # Save to CSV
    with open('septembrino_k11_verification.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['power', 'divisor', 'n_mod', 'modulus', 'total_predicted', 
                      'total_actual', 'total_matches', 'accuracy']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                'power': r['power'],
                'divisor': r['divisor'],
                'n_mod': r['n_mod'],
                'modulus': r['modulus'],
                'total_predicted': r['total_predicted'],
                'total_actual': r['total_actual'],
                'total_matches': r['total_matches'],
                'accuracy': r['accuracy'],
            })
    
    print("Saved detailed results to septembrino_k11_verification.csv")
    print()
    print("NEXT STEPS:")
    print("1. If accuracy > 90%: Her formulas are correct! Extend to higher powers.")
    print("2. Search for 2^17, 2^18, 2^19... automatically.")
    print("3. Generate similar tables for k=5, 7, 13, 385, 433...")

if __name__ == '__main__':
    main()