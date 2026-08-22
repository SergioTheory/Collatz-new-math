#!/usr/bin/env python3
"""
Verify Septembrino's divisor prediction formulas.
Tests if her modular arithmetic correctly predicts high divisors.

Based on her tables for k=11:
- 11*3^n - 1 divisible by 2^15 when n = 8665 mod 16384
- 11*3^n - 1 divisible by 2^16 when n = 473 mod 32768
"""

import csv
from typing import List, Dict, Tuple

# ============================================================================
# Septembrino's formulas for k=11 (from her tables)
# ============================================================================

K11_PREDICTIONS = {
    15: {'n_mod': 8665, 'modulus': 16384},   # 2^15 when n = 8665 mod 16384
    16: {'n_mod': 473, 'modulus': 32768},    # 2^16 when n = 473 mod 32768
    14: {'n_mod': 4569, 'modulus': 8192},    # 2^14 when n = 4569 mod 8192
    13: {'n_mod': 2521, 'modulus': 4096},    # 2^13 when n = 2521 mod 4096
}

# ============================================================================
# Load our data
# ============================================================================

def load_trajectories(filename: str = 'septembrino_table.csv') -> List[Dict]:
    """Load trajectories from CSV."""
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

# ============================================================================
# Verification functions
# ============================================================================

def check_divisibility(k: int, m: int, target_power: int) -> bool:
    """
    Check if k*3^m - 1 is divisible by 2^target_power.
    """
    N = k * (3 ** m) - 1
    return N % (2 ** target_power) == 0

def check_septembrino_prediction(k: int, m: int, predictions: Dict) -> Dict:
    """
    Check if Septembrino's formulas predict the correct divisor.
    Returns: {'predicted_power': int, 'actual_power': int, 'match': bool}
    """
    # Find highest power of 2 that divides k*3^m - 1
    N = k * (3 ** m) - 1
    actual_power = 0
    temp = N
    while temp % 2 == 0 and actual_power < 30:
        temp //= 2
        actual_power += 1
    
    # Check predictions
    predicted_power = 0
    for power, formula in predictions.items():
        if (m - formula['n_mod']) % formula['modulus'] == 0:
            predicted_power = max(predicted_power, power)
    
    return {
        'k': k,
        'm': m,
        'predicted_power': predicted_power,
        'actual_power': actual_power,
        'match': predicted_power == actual_power,
        'N_bits': N.bit_length(),
    }

# ============================================================================
# Main verification
# ============================================================================

def main():
    print("=" * 80)
    print("VERIFYING SEPTembrino's DIVISOR PREDICTION FORMULAS")
    print("=" * 80)
    print()
    
    # Load data
    trajectories = load_trajectories()
    print(f"Loaded {len(trajectories)} trajectories")
    print()
    
    # Filter for k=11 only
    k11_trajs = [t for t in trajectories if int(t['k']) == 11]
    print(f"Testing k=11: {len(k11_trajs)} trajectories")
    print()
    
    # Verify predictions
    results = []
    for traj in k11_trajs:
        k = int(traj['k'])
        m = int(traj['m'])
        result = check_septembrino_prediction(k, m, K11_PREDICTIONS)
        results.append(result)
    
    # Statistics
    total = len(results)
    matches = sum(1 for r in results if r['match'])
    partial = sum(1 for r in results if r['predicted_power'] > 0 and not r['match'])
    unpredicted = sum(1 for r in results if r['predicted_power'] == 0)
    
    print("=" * 80)
    print("RESULTS FOR k=11:")
    print("=" * 80)
    print(f"Total trajectories: {total}")
    print(f"Exact matches (predicted = actual): {matches} ({matches/total*100:.1f}%)")
    print(f"Partial matches (predicted something, but wrong power): {partial} ({partial/total*100:.1f}%)")
    print(f"Unpredicted (formula gave no prediction): {unpredicted} ({unpredicted/total*100:.1f}%)")
    print()
    
    # Show mismatches
    mismatches = [r for r in results if not r['match'] and r['predicted_power'] > 0]
    if mismatches:
        print("MISMATCHES (predicted ≠ actual):")
        print("-" * 80)
        for r in mismatches[:10]:  # Show first 10
            print(f"  k={r['k']}, m={r['m']}: predicted 2^{r['predicted_power']}, actual 2^{r['actual_power']}")
        print()
    
    # Show unpredicted high divisors
    unpredicted_high = [r for r in results if r['predicted_power'] == 0 and r['actual_power'] >= 10]
    if unpredicted_high:
        print("UNPREDICTED HIGH DIVISORS (actual ≥ 2^10, formula gave nothing):")
        print("-" * 80)
        for r in unpredicted_high[:10]:
            print(f"  k={r['k']}, m={r['m']}: actual 2^{r['actual_power']} (N has {r['N_bits']} bits)")
        print()
    
    # Save detailed results
    with open('septembrino_verification_k11.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['k', 'm', 'predicted_power', 'actual_power', 'match', 'N_bits']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print("=" * 80)
    print("Saved detailed results to septembrino_verification_k11.csv")
    print("=" * 80)
    print()
    print("NEXT STEPS:")
    print("1. If accuracy > 80%: Her formulas work! Extend to other k.")
    print("2. If accuracy < 50%: Formulas need refinement.")
    print("3. Send results to Anabel and ask for general formula.")

if __name__ == '__main__':
    main()