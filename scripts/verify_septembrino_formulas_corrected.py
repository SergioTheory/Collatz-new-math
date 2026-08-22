#!/usr/bin/env python3
"""
Verify Septembrino's divisor prediction formulas - CORRECTED RANGE
Tests n = 0 to 10,000 (not just 0-40!)
"""

from typing import List, Dict, Tuple

# ============================================================================
# Septembrino's formulas for k=11 (from her tables)
# ============================================================================

K11_PREDICTIONS = {
    16: {'n_mod': 473, 'modulus': 32768},      # 2^16 when n = 473 mod 32768
    15: {'n_mod': 8665, 'modulus': 16384},     # 2^15 when n = 8665 mod 16384
    14: {'n_mod': 2521, 'modulus': 4096},      # 2^14 when n = 2521 mod 4096
    13: {'n_mod': 1497, 'modulus': 2048},      # 2^13 when n = 1497 mod 2048
    12: {'n_mod': 985, 'modulus': 1024},       # 2^12 when n = 985 mod 1024
    11: {'n_mod': 217, 'modulus': 512},        # 2^11 when n = 217 mod 512
    10: {'n_mod': 217, 'modulus': 512},        # 2^10 when n = 217 mod 512
}

# ============================================================================
# Verification functions
# ============================================================================

def check_divisibility(k: int, n: int, target_power: int) -> bool:
    """Check if k*3^n - 1 is divisible by 2^target_power."""
    N = k * (3 ** n) - 1
    return N % (2 ** target_power) == 0

def get_actual_divisor_power(k: int, n: int) -> int:
    """Find highest power of 2 that divides k*3^n - 1."""
    N = k * (3 ** n) - 1
    power = 0
    temp = N
    while temp % 2 == 0 and power < 30:
        temp //= 2
        power += 1
    return power

def check_septembrino_prediction(k: int, n: int, predictions: Dict) -> Dict:
    """Check if Septembrino's formulas predict the correct divisor."""
    actual_power = get_actual_divisor_power(k, n)
    
    predicted_power = 0
    for power, formula in predictions.items():
        if (n - formula['n_mod']) % formula['modulus'] == 0:
            predicted_power = max(predicted_power, power)
    
    return {
        'k': k,
        'n': n,
        'predicted_power': predicted_power,
        'actual_power': actual_power,
        'match': predicted_power == actual_power and actual_power >= 10,
        'has_high_divisor': actual_power >= 10,
    }

# ============================================================================
# Main verification
# ============================================================================

def main():
    print("=" * 80)
    print("VERIFYING SEPTembrino's DIVISOR PREDICTION FORMULAS (CORRECTED)")
    print("Testing n = 0 to 10,000 (not just 0-40!)")
    print("=" * 80)
    print()
    
    k = 11
    max_n = 10000
    
    print(f"Testing k={k}, n=0 to {max_n}...")
    print()
    
    results = []
    high_divisor_count = 0
    
    for n in range(max_n + 1):
        result = check_septembrino_prediction(k, n, K11_PREDICTIONS)
        if result['has_high_divisor']:
            high_divisor_count += 1
            results.append(result)
            if result['actual_power'] >= 12:
                print(f"n={n:>5}: predicted 2^{result['predicted_power']:>2}, "
                      f"actual 2^{result['actual_power']:>2}, "
                      f"match={result['match']}")
    
    print()
    print("=" * 80)
    print(f"RESULTS FOR k={k}, n=0 to {max_n}:")
    print("=" * 80)
    print(f"Total n values tested: {max_n + 1}")
    print(f"Values with high divisors (≥ 2^10): {high_divisor_count}")
    print()
    
    if results:
        matches = sum(1 for r in results if r['match'])
        partial = sum(1 for r in results if r['predicted_power'] > 0 and not r['match'])
        unpredicted = sum(1 for r in results if r['predicted_power'] == 0)
        
        print(f"Exact matches (predicted = actual): {matches} ({matches/len(results)*100:.1f}%)")
        print(f"Partial matches (predicted something, but wrong): {partial} ({partial/len(results)*100:.1f}%)")
        print(f"Unpredicted (formula gave no prediction): {unpredicted} ({unpredicted/len(results)*100:.1f}%)")
    else:
        print("No high divisors found in this range!")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()