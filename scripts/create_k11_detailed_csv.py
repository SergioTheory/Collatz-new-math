#!/usr/bin/env python3
"""
Create detailed CSV with ALL n values for k=11.
Shows predicted vs actual divisor for each n from 0 to 10,000.
"""

import csv

# ============================================================================
# Septembrino's formulas for k=11
# ============================================================================

K11_PREDICTIONS = {
    16: {'n_mod': 473, 'modulus': 32768},
    15: {'n_mod': 8665, 'modulus': 16384},
    14: {'n_mod': 2521, 'modulus': 4096},
    13: {'n_mod': 1497, 'modulus': 2048},
    12: {'n_mod': 985, 'modulus': 1024},
    11: {'n_mod': 217, 'modulus': 512},
    10: {'n_mod': 217, 'modulus': 512},
    9: {'n_mod': 89, 'modulus': 256},
    8: {'n_mod': 25, 'modulus': 128},
    7: {'n_mod': 57, 'modulus': 64},
    6: {'n_mod': 9, 'modulus': 32},
    5: {'n_mod': 1, 'modulus': 16},
    4: {'n_mod': 5, 'modulus': 8},
    3: {'n_mod': 3, 'modulus': 4},
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

def get_predicted_power(n: int, predictions: dict) -> int:
    """Get predicted divisor power from Septembrino's formulas."""
    predicted_power = 0
    for power, formula in predictions.items():
        if (n - formula['n_mod']) % formula['modulus'] == 0:
            predicted_power = max(predicted_power, power)
    return predicted_power

# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 80)
    print("CREATING DETAILED K=11 VERIFICATION CSV")
    print("Testing n = 0 to 10,000")
    print("=" * 80)
    print()
    
    k = 11
    max_n = 10000
    rows = []
    
    print(f"Processing {max_n + 1} values...")
    
    for n in range(max_n + 1):
        actual_power = get_divisor_power(k, n)
        predicted_power = get_predicted_power(n, K11_PREDICTIONS)
        
        # Only save n with high divisors (>= 2^10) to keep file manageable
        if actual_power >= 10:
            match = (predicted_power == actual_power)
            rows.append({
                'n': n,
                'predicted_power': predicted_power,
                'actual_power': actual_power,
                'predicted_divisor': 2 ** predicted_power if predicted_power > 0 else 0,
                'actual_divisor': 2 ** actual_power,
                'match': 'Yes' if match else 'No',
                'offset': actual_power - predicted_power if predicted_power > 0 else 'N/A',
            })
    
    # Save to CSV
    output_file = 'septembrino_k11_detailed.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['n', 'predicted_power', 'actual_power', 'predicted_divisor', 
                      'actual_divisor', 'match', 'offset']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print()
    print("=" * 80)
    print(f"Saved {len(rows)} rows to {output_file}")
    print("(Only n with actual divisor >= 2^10 are included)")
    print("=" * 80)
    print()
    
    # Show sample
    print("Sample rows (first 10):")
    print("-" * 80)
    for row in rows[:10]:
        print(f"n={row['n']:>5}: predicted 2^{row['predicted_power']:>2}, "
              f"actual 2^{row['actual_power']:>2}, match={row['match']}")

if __name__ == '__main__':
    main()