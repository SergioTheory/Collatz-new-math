"""
family_a_spectrum.py — Спектр Family A: характеристики 2^b-1 для b=71..310
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import analyze_to_peak

def main():
    rows = []

    print(f"  Вычисляю характеристики 2^b-1 для b=71..310...", flush=True)

    for b in range(71, 311):
        n = (1 << b) - 1
        info = analyze_to_peak(n)
        d = info['total_o']
        S = info['total_e']
        peak = info['peak']
        ratio = peak / b
        s_d = S / d if d > 0 else 0

        rows.append({
            'b': b,
            'peak': peak,
            'ratio': round(ratio, 5),
            'd': d,
            'S': S,
            'S_d': round(s_d, 5),
        })

        if b % 20 == 0:
            print(f"  b={b} done", flush=True)

    # Полная таблица
    print()
    print("=" * 70)
    print("  Family A спектр: 2^b - 1, b = 71..310")
    print("=" * 70)
    print(f"  {'b':>4}  {'peak':>5}  {'ratio':>7}  {'d':>5}  {'S':>6}  {'S/d':>7}")
    print(f"  {'-' * 42}")
    for r in rows:
        print(f"  {r['b']:>4}  {r['peak']:>5}  {r['ratio']:>7.4f}  "
              f"{r['d']:>5}  {r['S']:>6}  {r['S_d']:>7.4f}")

    # Нетривиальные аккорды
    nontrivial = [r for r in rows if r['S_d'] > 1.05]
    print()
    print("=" * 70)
    print(f"  Нетривиальные аккорды (S/d > 1.05): {len(nontrivial)} из {len(rows)}")
    print("=" * 70)
    print(f"  {'b':>4}  {'peak':>5}  {'ratio':>7}  {'d':>5}  {'S':>6}  {'S/d':>7}")
    print(f"  {'-' * 42}")
    for r in nontrivial:
        print(f"  {r['b']:>4}  {r['peak']:>5}  {r['ratio']:>7.4f}  "
              f"{r['d']:>5}  {r['S']:>6}  {r['S_d']:>7.4f}")

    # CSV
    with open('family_a_spectrum.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['b', 'peak', 'ratio', 'd', 'S', 'S_d'])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n  Сохранено: family_a_spectrum.csv")


if __name__ == '__main__':
    main()
