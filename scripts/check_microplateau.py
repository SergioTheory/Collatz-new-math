"""
check_microplateau.py — Проверка микро-плато (пик 183 при b=113-114, пик 190 при b=117-118)
Ищем другие числа с таким же пиком через CRT-конструирование и случайный поиск.
"""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import collatz_peak, analyze_to_peak
from zone_parity_search import extract_shifts, shifts_to_parity, construct_for_bitlength


def extract_parity_from_fa(b):
    """Извлекает shift-вектор и parity для 2^b-1, обрезанные до пика"""
    n = (1 << b) - 1
    info = analyze_to_peak(n)
    d = info['total_o']
    S = info['total_e']
    peak = info['peak']

    shifts = extract_shifts(n)
    shifts_to_peak = shifts[:d]
    parity = shifts_to_parity(shifts_to_peak)

    return n, peak, d, S, shifts_to_peak, parity


def crt_search(label, source_b, target_peak, bits_lo, bits_hi):
    """Конструирует числа через CRT из shift-вектора Family A"""
    print(f"\n{'=' * 70}")
    print(f"  CRT-поиск: {label}")
    print(f"  Источник: 2^{source_b}-1, целевой пик: {target_peak}")
    print(f"  Битности: {bits_lo}–{bits_hi}")
    print(f"{'=' * 70}")

    n_src, peak_src, d, S, shifts, parity = extract_parity_from_fa(source_b)
    print(f"  Источник: bits={source_b}, peak={peak_src}, d={d}, S={S}, len(parity)={len(parity)}")

    results = []

    for tb in range(bits_lo, bits_hi + 1):
        n = construct_for_bitlength(parity, tb)
        if n is None:
            continue

        actual_bits = n.bit_length()
        peak, steps, conv = collatz_peak(n, max_steps=2_000_000)
        ratio = peak / actual_bits

        hit = "  <<<< HIT!" if peak == target_peak else ""
        print(f"  tb={tb:>4}, bits={actual_bits:>4}, peak={peak:>4}, "
              f"ratio={ratio:.4f}{hit}")

        if peak == target_peak:
            results.append({
                'n': n,
                'bits': actual_bits,
                'peak': peak,
                'ratio': ratio,
            })

    print(f"\n  Найдено с пиком {target_peak}: {len(results)}")
    return results


def random_search(label, target_peak, bits_list, n_trials=100_000):
    """Случайный поиск чисел с высокой плотностью единиц"""
    print(f"\n{'=' * 70}")
    print(f"  Случайный поиск: {label}")
    print(f"  Целевой пик: {target_peak}, битности: {bits_list}")
    print(f"  Попыток: {n_trials:,}")
    print(f"{'=' * 70}")

    results = []
    best_by_peak = {}  # peak -> best ratio

    for trial in range(n_trials):
        b = random.choice(bits_list)

        # Генерируем число с высокой плотностью единиц (80-100%)
        density = random.uniform(0.80, 1.00)
        bits_str = '1'  # MSB всегда 1
        for i in range(b - 1):
            bits_str += '1' if random.random() < density else '0'

        n = int(bits_str, 2)
        peak, steps, conv = collatz_peak(n, max_steps=500_000)
        ratio = peak / b

        if peak == target_peak:
            results.append({
                'n': n,
                'bits': b,
                'peak': peak,
                'ratio': ratio,
                'density': bin(n).count('1') / b,
            })

        # Трекинг лучших по пику (для общей статистики)
        if peak not in best_by_peak or ratio > best_by_peak[peak]['ratio']:
            best_by_peak[peak] = {'bits': b, 'ratio': ratio, 'trial': trial}

        if (trial + 1) % 20000 == 0:
            print(f"  [{trial + 1:>7d}] найдено с пиком {target_peak}: {len(results)}", flush=True)

    print(f"\n  Итого с пиком {target_peak}: {len(results)}")

    if results:
        results.sort(key=lambda r: -r['ratio'])
        print(f"\n  Топ-10:")
        print(f"  {'bits':>5}  {'peak':>5}  {'ratio':>7}  {'density':>7}")
        print(f"  {'-' * 30}")
        for r in results[:10]:
            print(f"  {r['bits']:>5}  {r['peak']:>5}  {r['ratio']:>7.4f}  {r['density']:>7.3f}")

    # Статистика пиков
    nearby_peaks = {p: v for p, v in best_by_peak.items()
                    if abs(p - target_peak) <= 5}
    if nearby_peaks:
        print(f"\n  Пики в окрестности {target_peak}±5:")
        for p in sorted(nearby_peaks):
            v = nearby_peaks[p]
            marker = " <<<" if p == target_peak else ""
            print(f"    peak={p}: best ratio={v['ratio']:.4f} (bits={v['bits']}){marker}")

    return results


def main():
    print("=" * 70)
    print("  Проверка микро-плато")
    print("=" * 70)

    # ── Микро-плато 183 (b=113-114) ──────────────────────────────────────
    crt_183 = crt_search(
        label="Микро-плато 183",
        source_b=113,
        target_peak=183,
        bits_lo=100,
        bits_hi=120,
    )

    rand_183 = random_search(
        label="Микро-плато 183",
        target_peak=183,
        bits_list=[113, 114],
        n_trials=100_000,
    )

    # ── Микро-плато 190 (b=117-118) ──────────────────────────────────────
    crt_190 = crt_search(
        label="Микро-плато 190",
        source_b=117,
        target_peak=190,
        bits_lo=105,
        bits_hi=125,
    )

    rand_190 = random_search(
        label="Микро-плато 190",
        target_peak=190,
        bits_list=[117, 118],
        n_trials=100_000,
    )

    # ── Итоги ────────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"  ИТОГИ")
    print(f"{'=' * 70}")
    print(f"  Микро-плато 183: CRT={len(crt_183)}, random={len(rand_183)}")
    print(f"  Микро-плато 190: CRT={len(crt_190)}, random={len(rand_190)}")


if __name__ == '__main__':
    main()
