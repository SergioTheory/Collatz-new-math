"""
check_residues.py — Анализ остатков Zone 2 чисел, FFT спектр, таблица records
"""

import ast
import csv
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from crt_solver import collatz_peak, analyze_to_peak
from zone_parity_search import extract_shifts
from records_data import PATH_RECORDS_BINARY

Z2_CORE = int('111111111100000011100100110011100001010100011011100111100111001101111110', 2)
MODULI = [3, 9, 27, 81, 243, 7, 5, 13]


def first_shift(n):
    """Максимальная степень 2, на которую делится 3n+1"""
    v = 3 * n + 1
    s = 0
    while v % 2 == 0:
        v >>= 1
        s += 1
    return s


# ============================================================
# ЧАСТЬ 1: Остатки Zone 2 чисел
# ============================================================

def part1_residues():
    print("=" * 80)
    print("  ЧАСТЬ 1: Остатки Zone 2 чисел по малым модулям")
    print("=" * 80)

    # Загружаем из CSV
    numbers = []
    with open('zone2_shifts.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row['n'])
            bits = int(row['input_bits'])
            numbers.append((n, bits, f"Zone2-{bits}b"))

    # Добавляем Z2_CORE
    numbers.append((Z2_CORE, Z2_CORE.bit_length(), "Z2_CORE"))

    # Заголовок
    hdr = f"  {'name':<12} {'bits':>4}"
    for m in MODULI:
        hdr += f" {'%'+str(m):>5}"
    hdr += f" {'s1':>3}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    for n, bits, name in numbers:
        row = f"  {name:<12} {bits:>4}"
        for m in MODULI:
            row += f" {n % m:>5}"
        row += f" {first_shift(n):>3}"
        print(row)

    print()


# ============================================================
# ЧАСТЬ 2: FFT спектр shift-вектора 87 бит
# ============================================================

def part2_fft():
    print("=" * 80)
    print("  ЧАСТЬ 2: FFT спектр shift-вектора (87 бит)")
    print("=" * 80)

    # Загружаем shift-вектор для 87 бит
    shifts_87 = None
    with open('zone2_shifts.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row['input_bits']) == 87:
                shifts_87 = ast.literal_eval(row['blocks'])
                break

    if shifts_87 is None:
        print("  Ошибка: не найден shift-вектор для 87 бит!")
        return

    arr = np.array(shifts_87, dtype=float)
    print(f"  Длина вектора: {len(arr)}, сумма: {int(arr.sum())}")
    print(f"  Среднее: {arr.mean():.4f}, std: {arr.std():.4f}")

    # FFT
    spectrum = np.fft.rfft(arr)
    amplitudes = np.abs(spectrum)
    freqs = np.fft.rfftfreq(len(arr))

    # Топ-10 (кроме DC, индекс 0)
    indices = np.argsort(amplitudes[1:])[::-1][:10] + 1  # +1 чтобы пропустить DC

    print(f"\n  {'rank':>4}  {'freq':>8}  {'period':>8}  {'amplitude':>10}")
    print(f"  {'-' * 40}")
    for rank, idx in enumerate(indices, 1):
        freq = freqs[idx]
        period = 1.0 / freq if freq > 0 else float('inf')
        amp = amplitudes[idx]
        print(f"  {rank:>4}  {freq:>8.5f}  {period:>8.2f}  {amp:>10.4f}")

    # График
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    ax1.stem(freqs[1:], amplitudes[1:], linefmt='b-', markerfmt='bo', basefmt='k-')
    ax1.set_xlabel('Частота (1/шаг)')
    ax1.set_ylabel('Амплитуда')
    ax1.set_title('FFT спектр shift-вектора Zone 2 (87 бит, d=258)')
    ax1.grid(True, alpha=0.3)

    # Топ-10 точек подписываем
    for idx in indices[:5]:
        freq = freqs[idx]
        amp = amplitudes[idx]
        period = 1.0 / freq if freq > 0 else float('inf')
        ax1.annotate(f'T={period:.1f}', (freq, amp),
                     textcoords="offset points", xytext=(5, 5), fontsize=8)

    # Сам shift-вектор
    ax2.bar(range(len(arr)), arr, width=1.0, color='steelblue', alpha=0.7)
    ax2.set_xlabel('Шаг (odd step index)')
    ax2.set_ylabel('Shift (делений на 2)')
    ax2.set_title('Shift-вектор Zone 2 (87 бит)')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('fft_zone2.png', dpi=150)
    print(f"\n  График сохранён: fft_zone2.png")
    print()


# ============================================================
# ЧАСТЬ 3: Таблица records из records_data.py
# ============================================================

def part3_records():
    print("=" * 80)
    print("  ЧАСТЬ 3: Анализ PATH_RECORDS_BINARY")
    print("=" * 80)

    rows = []
    for bstr in PATH_RECORDS_BINARY:
        n = int(bstr, 2)
        bits = n.bit_length()
        peak, steps, conv = collatz_peak(n, max_steps=2_000_000)
        ratio = peak / bits
        shifts = extract_shifts(n, max_steps=2_000_000)

        # d и S до пика: d = кол-во odd steps, S = сумма shifts
        # Используем analyze_to_peak для точных значений
        info = analyze_to_peak(n)
        d = info['total_o']
        S = info['total_e']
        s_d = S / d if d > 0 else 0

        first10 = shifts[:10]

        rows.append({
            'bits': bits,
            'peak': peak,
            'ratio': ratio,
            'd': d,
            'S': S,
            'S_d': s_d,
            'first10': first10,
        })

    # Сортировка по битности
    rows.sort(key=lambda r: r['bits'])

    print(f"\n  {'bits':>5}  {'peak':>5}  {'ratio':>7}  {'d':>5}  {'S':>5}  {'S/d':>6}  first 10 shifts")
    print(f"  {'-' * 75}")

    for r in rows:
        shifts_str = str(r['first10'])
        print(f"  {r['bits']:>5}  {r['peak']:>5}  {r['ratio']:>7.4f}  "
              f"{r['d']:>5}  {r['S']:>5}  {r['S_d']:>6.3f}  {shifts_str}")

    print(f"\n  Всего записей: {len(rows)}")
    print()


# ============================================================

if __name__ == '__main__':
    part1_residues()
    part2_fft()
    part3_records()
