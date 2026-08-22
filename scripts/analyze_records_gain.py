"""
analyze_records_gain.py — Кумулятивный gain G(k) и распределение сдвигов
для выбранных records из records_data.py
"""

import math
import sys
from pathlib import Path
from collections import Counter

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from crt_solver import collatz_peak, analyze_to_peak
from zone_parity_search import extract_shifts
from records_data import PATH_RECORDS_BINARY

LOG2_3 = math.log2(3)

# ── Числа для анализа ───────────────────────────────────────────────────────

# Специальные числа (не из PATH_RECORDS_BINARY)
SPECIAL = {
    'n=27': 27,
}

# 71-битные (оба из records_data, строки 62-63)
Z2_71a = "10111111011101000101101010111101101011101101000001010000111010011101111"
Z2_71b = "11111111110000001110010011001110000101010001101110011110011100110111111"

# Family A числа по битности (из records_data: "1" * bits)
FA_BITS = [83, 103, 109, 113, 117]

# 114-битное число (не Family A — чередование)
REC_114 = "101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101001"


def analyze_one(n, label):
    """Полный анализ одного числа"""
    bits = n.bit_length()
    peak, steps, conv = collatz_peak(n, max_steps=2_000_000)
    ratio = peak / bits
    shifts = extract_shifts(n, max_steps=2_000_000)

    info = analyze_to_peak(n)
    d = info['total_o']
    S = info['total_e']
    s_d = S / d if d > 0 else 0

    # Shift-вектор до пика (первые d элементов)
    shifts_to_peak = shifts[:d]

    # Распределение сдвигов
    cnt = Counter(shifts_to_peak)

    # Кумулятивный gain G(k) = k·log₂3 − cumsum(shifts)
    cs = np.cumsum(shifts_to_peak)
    ks = np.arange(1, len(shifts_to_peak) + 1)
    G = ks * LOG2_3 - cs

    # Монотонность: сколько раз G(k) < G(k-1) (провалов)
    dips = 0
    for i in range(1, len(G)):
        if G[i] < G[i - 1]:
            dips += 1

    # Проценты
    total_shifts = len(shifts_to_peak)
    pct1 = 100 * cnt.get(1, 0) / total_shifts if total_shifts > 0 else 0
    pct2 = 100 * cnt.get(2, 0) / total_shifts if total_shifts > 0 else 0
    pct3 = 100 * cnt.get(3, 0) / total_shifts if total_shifts > 0 else 0
    pct_hi = 100 * sum(v for k, v in cnt.items() if k >= 4) / total_shifts if total_shifts > 0 else 0

    return {
        'label': label,
        'bits': bits,
        'peak': peak,
        'ratio': ratio,
        'd': d,
        'S': S,
        'S_d': s_d,
        'pct1': pct1,
        'pct2': pct2,
        'pct3': pct3,
        'pct_hi': pct_hi,
        'dips': dips,
        'G': G,
        'dist': dict(sorted(cnt.items())),
    }


def main():
    # Собираем все числа для анализа
    targets = []

    # n=27
    targets.append((27, 'n=27 (5b)'))

    # Оба 71-битных
    targets.append((int(Z2_71a, 2), 'Z2-71a (Barina)'))
    targets.append((int(Z2_71b, 2), 'Z2-71b (core)'))

    # Family A
    for b in FA_BITS:
        targets.append((2**b - 1, f'FA-{b}b'))

    # 114-битное
    targets.append((int(REC_114, 2), 'Rec-114b'))

    # Анализ
    results = []
    for n, label in targets:
        print(f"  Анализирую {label}...", flush=True)
        r = analyze_one(n, label)
        results.append(r)

    # ── Таблица ──────────────────────────────────────────────────────────────
    print()
    print("=" * 100)
    print("  Кумулятивный gain и распределение сдвигов")
    print("=" * 100)

    hdr = (f"  {'label':<18} {'bits':>4} {'peak':>4} {'d':>5} {'S':>5} {'S/d':>6}"
           f"  {'%1':>5} {'%2':>5} {'%3':>5} {'%4+':>5} {'dips':>5}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    for r in results:
        print(f"  {r['label']:<18} {r['bits']:>4} {r['peak']:>4} {r['d']:>5} {r['S']:>5} "
              f"{r['S_d']:>6.3f}  {r['pct1']:>5.1f} {r['pct2']:>5.1f} {r['pct3']:>5.1f} "
              f"{r['pct_hi']:>5.1f} {r['dips']:>5}")

    # Распределения
    print()
    print("  Распределения сдвигов:")
    for r in results:
        print(f"  {r['label']:<18} {r['dist']}")

    # ── График ───────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, 8))

    cmap = plt.cm.tab10
    for i, r in enumerate(results):
        G = r['G']
        color = cmap(i % 10)
        ax.plot(range(1, len(G) + 1), G, label=r['label'], color=color, alpha=0.8, linewidth=1.2)

    ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
    ax.set_xlabel('Odd step k')
    ax.set_ylabel('Cumulative gain G(k) = k·log₂3 − Σshifts')
    ax.set_title('Cumulative gain G(k) для выбранных record numbers')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('records_gain.png', dpi=150)
    print(f"\n  График сохранён: records_gain.png")


if __name__ == '__main__':
    main()
