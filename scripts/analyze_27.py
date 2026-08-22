"""
analyze_27.py — Является ли n=27 мини-версией Zone 2?

Число 27 (5 бит) → peak=9232 (14 бит), ratio=2.80, d=33.
Сравниваем структуру с Zone 2 (71 бит, peak=140).

Использование:
  python analyze_27.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import collatz_peak, analyze_to_peak

LOG2_3 = math.log2(3)

# Рекордсмены Барины с bits 3–10 (из records_data.py / OEIS)
SMALL_RECORDS = {
    7:   3,   # 111
    15:  4,   # 1111
    27:  5,   # 11011
    180: 8,   # 10110100
    361: 9,   # 101101001
    795: 10,  # 1100011011
}

ZONE2_71 = 2358909599867980429759  # 71 бит, d=259, peak=140


def accelerated_trajectory(n: int, max_odd_steps: int = 500) -> list[int]:
    """Ускоренная траектория: список нечётных x_0, x_1, ..."""
    cur = n
    while cur > 1 and cur % 2 == 0:
        cur >>= 1
    traj = [cur]
    for _ in range(max_odd_steps):
        if cur <= 1:
            break
        val = 3 * cur + 1
        while val % 2 == 0:
            val >>= 1
        cur = val
        traj.append(cur)
    return traj


def extract_shifts(n: int, max_odd_steps: int = 500) -> list[int]:
    """Shift-вектор."""
    cur = n
    while cur > 1 and cur % 2 == 0:
        cur >>= 1
    shifts = []
    for _ in range(max_odd_steps):
        if cur <= 1:
            break
        val = 3 * cur + 1
        count = 0
        while val % 2 == 0:
            val >>= 1
            count += 1
        shifts.append(count)
        cur = val
    return shifts


def cumulative_gain(shifts: list[int]) -> list[float]:
    """G(k) = k·log₂3 − cumsum(shifts)."""
    result = []
    cs = 0
    for k, s in enumerate(shifts):
        cs += s
        result.append((k + 1) * LOG2_3 - cs)
    return result


def shift_distribution(shifts: list[int]) -> dict[int, int]:
    dist = defaultdict(int)
    for s in shifts:
        dist[s] += 1
    return dict(sorted(dist.items()))


def find_predecessors(m: int, a_max: int = 15, max_bits: int = 15) -> list[tuple[int, int]]:
    preds = []
    power2 = 1
    for a in range(1, a_max + 1):
        power2 <<= 1
        val = m * power2 - 1
        if val % 3 != 0:
            continue
        n = val // 3
        if n <= 0 or n % 2 == 0:
            continue
        if n.bit_length() > max_bits:
            continue
        preds.append((n, a))
    return preds


def main():
    print(f"{'=' * 78}")
    print(f"  Analyze n=27 — мини-Zone 2?")
    print(f"{'=' * 78}")

    # ── ЧАСТЬ 1: Полная траектория n=27 ───────────────────────────────────────
    print(f"\n  ЧАСТЬ 1: Ускоренная траектория n=27")
    print(f"  {'-' * 70}")

    traj_27 = accelerated_trajectory(27, max_odd_steps=100)
    print(f"  Длина: {len(traj_27)} значений (d={len(traj_27)-1} нечётных шагов)")
    print()
    print(f"  {'k':>4}  {'x_k':>15}  {'bits':>5}")
    print(f"  {'-' * 30}")
    for k, x in enumerate(traj_27):
        print(f"  {k:>4}  {x:>15}  {x.bit_length():>5}")

    # ── ЧАСТЬ 2: Shift-вектор и статистика ────────────────────────────────────
    print(f"\n  ЧАСТЬ 2: Shift-вектор n=27")
    print(f"  {'-' * 70}")

    shifts_27 = extract_shifts(27, max_odd_steps=100)
    d_27 = len(shifts_27)
    S_27 = sum(shifts_27)
    gain_27 = cumulative_gain(shifts_27)
    dist_27 = shift_distribution(shifts_27)

    print(f"  Shift-вектор: {shifts_27}")
    print(f"  d = {d_27}, S = {S_27}, S/d = {S_27/d_27:.4f}")
    print(f"  Распределение: {dist_27}")
    for v, cnt in dist_27.items():
        print(f"    {v}: {cnt} ({100*cnt/d_27:.1f}%)")
    print(f"  Кумулятивный gain G(k):")
    for k, g in enumerate(gain_27):
        bar = '+' * max(0, int(g * 2)) + '-' * max(0, int(-g * 2))
        print(f"    G({k+1:>2}) = {g:>7.3f}  {bar}")

    max_g = max(gain_27)
    max_g_k = gain_27.index(max_g) + 1
    min_g = min(gain_27)
    min_g_k = gain_27.index(min_g) + 1
    dips = sum(1 for k in range(1, len(gain_27)) if gain_27[k] < gain_27[k-1])
    print(f"\n  Max gain: {max_g:.3f} (k={max_g_k})")
    print(f"  Min gain: {min_g:.3f} (k={min_g_k})")
    print(f"  Провалов (G(k) < G(k-1)): {dips} из {d_27-1}")

    # ── ЧАСТЬ 3: Общие точки с другими рекордсменами ─────────────────────────
    print(f"\n  ЧАСТЬ 3: Общие точки с рекордсменами bits=3–10")
    print(f"  {'-' * 70}")

    traj_27_set = {x: k for k, x in enumerate(traj_27)}

    for n_rec, bits_rec in sorted(SMALL_RECORDS.items(), key=lambda x: x[1]):
        if n_rec == 27:
            continue
        traj_rec = accelerated_trajectory(n_rec, max_odd_steps=200)
        peak_rec, _, _ = collatz_peak(n_rec, max_steps=500_000)

        matches = []
        for j, x in enumerate(traj_rec):
            if x in traj_27_set:
                matches.append((traj_27_set[x], j, x))

        status = f"peak={peak_rec}, d={len(traj_rec)-1}"
        if matches:
            matches.sort(key=lambda x: x[0])
            i0, j0, x0 = matches[0]
            print(f"  n={n_rec:>4} ({bits_rec}b, {status}): "
                  f"слияние x_{i0}(27) == x_{j0}({n_rec}) = {x0} "
                  f"({x0.bit_length()} bits)")
        else:
            print(f"  n={n_rec:>4} ({bits_rec}b, {status}): нет общих точек")

    # Ищем x* для n=27: к чему сходятся несколько чисел?
    print(f"\n  Confluence-центры для n=27:")
    # Все уникальные точки слияния
    confluence_points = defaultdict(list)  # x_value -> [(n_source, step_in_source, step_in_27)]
    for n_rec, bits_rec in sorted(SMALL_RECORDS.items(), key=lambda x: x[1]):
        if n_rec == 27:
            continue
        traj_rec = accelerated_trajectory(n_rec, max_odd_steps=200)
        for j, x in enumerate(traj_rec):
            if x in traj_27_set:
                confluence_points[x].append((n_rec, j, traj_27_set[x]))

    # Точки, куда сходятся ≥2 числа (включая 27)
    for x_val, sources in sorted(confluence_points.items(),
                                  key=lambda x: -len(x[1])):
        if len(sources) >= 1:
            k_in_27 = traj_27_set[x_val]
            src_str = ", ".join(f"n={s[0]}(step {s[1]})" for s in sources)
            print(f"    x={x_val} ({x_val.bit_length()} bits), "
                  f"step {k_in_27} in traj(27): ← {src_str}")

    # ── ЧАСТЬ 4: Обратное дерево от x_7 ──────────────────────────────────────
    print(f"\n  ЧАСТЬ 4: Обратное дерево от x_7 траектории 27")
    print(f"  {'-' * 70}")

    x7 = traj_27[7] if len(traj_27) > 7 else traj_27[-1]
    print(f"  x_7 = {x7} ({x7.bit_length()} bits)")

    rev_tree: dict[int, set[int]] = {0: {x7}}
    rev_all: set[int] = {x7}

    for depth in range(5):
        current = rev_tree[depth]
        nxt: set[int] = set()
        for m in current:
            for n, a in find_predecessors(m, a_max=15, max_bits=15):
                if n not in rev_all:
                    rev_all.add(n)
                    nxt.add(n)
        rev_tree[depth + 1] = nxt
        print(f"  Depth {depth}->{depth+1}: {len(current)} -> {len(nxt)} nodes")

    total_rev = sum(len(v) for v in rev_tree.values())
    print(f"  Всего узлов (bits ≤ 15): {total_rev}")

    # Проверяем peak для всех узлов 3–10 бит
    peak_14_count = 0
    peak_14_nums = []
    info_27 = analyze_to_peak(27, max_steps=500_000)
    peak_27 = info_27['peak']
    print(f"\n  peak(27) = {peak_27}")
    print(f"  Узлы с peak={peak_27}:")

    for depth in range(6):
        for n in rev_tree[depth]:
            if n.bit_length() < 3:
                continue
            peak_n, _, _ = collatz_peak(n, max_steps=500_000)
            if peak_n == peak_27:
                peak_14_count += 1
                peak_14_nums.append((depth, n, n.bit_length()))
                print(f"    depth={depth}, n={n} ({n.bit_length()} bits)")

    print(f"\n  Всего с peak={peak_27}: {peak_14_count}")
    if peak_14_count > 1:
        print(f"  → n=27 является confluence-центром!")
    else:
        print(f"  → n=27 НЕ является confluence-центром (только само 27)")

    # ── ЧАСТЬ 5: Сравнение с Zone 2 (71 бит) ─────────────────────────────────
    print(f"\n  ЧАСТЬ 5: Сравнение структуры n=27 vs Zone 2 (71 bit)")
    print(f"  {'-' * 70}")

    shifts_z2 = extract_shifts(ZONE2_71, max_odd_steps=500)
    d_z2 = len(shifts_z2)
    S_z2 = sum(shifts_z2)
    gain_z2 = cumulative_gain(shifts_z2)
    dist_z2 = shift_distribution(shifts_z2)

    max_g_z2 = max(gain_z2)
    min_g_z2 = min(gain_z2)
    dips_z2 = sum(1 for k in range(1, len(gain_z2)) if gain_z2[k] < gain_z2[k-1])

    info_z2 = analyze_to_peak(ZONE2_71, max_steps=500_000)
    peak_z2 = info_z2['peak']
    ratio_z2 = peak_z2 / ZONE2_71.bit_length()

    ratio_27 = peak_27 / 27 .bit_length()

    # Нормированные распределения
    all_vals = sorted(set(list(dist_27.keys()) + list(dist_z2.keys())))

    print(f"  {'Параметр':<25} {'n=27':>12} {'Zone2-71':>12}")
    print(f"  {'-' * 50}")
    print(f"  {'bits':<25} {27 .bit_length():>12} {ZONE2_71.bit_length():>12}")
    print(f"  {'peak':<25} {peak_27:>12} {peak_z2:>12}")
    print(f"  {'ratio':<25} {ratio_27:>12.4f} {ratio_z2:>12.4f}")
    print(f"  {'d (odd steps)':<25} {d_27:>12} {d_z2:>12}")
    print(f"  {'S (even steps)':<25} {S_27:>12} {S_z2:>12}")
    print(f"  {'S/d':<25} {S_27/d_27:>12.4f} {S_z2/d_z2:>12.4f}")
    print(f"  {'gain = d·log₂3 − S':<25} {d_27*LOG2_3-S_27:>12.2f} {d_z2*LOG2_3-S_z2:>12.2f}")
    print(f"  {'max G(k)':<25} {max_g:>12.3f} {max_g_z2:>12.3f}")
    print(f"  {'min G(k)':<25} {min_g:>12.3f} {min_g_z2:>12.3f}")
    print(f"  {'провалов G(k)':<25} {dips:>12} {dips_z2:>12}")

    print(f"\n  Распределение сдвигов (нормированное):")
    print(f"  {'shift':<8} {'n=27':>12} {'Zone2-71':>12}")
    print(f"  {'-' * 35}")
    for v in all_vals:
        pct_27 = f"{100*dist_27.get(v, 0)/d_27:.1f}%" if v in dist_27 else "—"
        pct_z2 = f"{100*dist_z2.get(v, 0)/d_z2:.1f}%" if v in dist_z2 else "—"
        print(f"  {v:<8} {pct_27:>12} {pct_z2:>12}")

    # Вывод
    print(f"\n  Вывод:")
    if abs(S_27/d_27 - S_z2/d_z2) < 0.1:
        print(f"  → S/d близки ({S_27/d_27:.4f} vs {S_z2/d_z2:.4f}) — похожая структура!")
    else:
        print(f"  → S/d различаются ({S_27/d_27:.4f} vs {S_z2/d_z2:.4f})")

    if ratio_27 > ratio_z2:
        print(f"  → ratio(27) = {ratio_27:.4f} > ratio(Z2) = {ratio_z2:.4f} — "
              f"27 аномальнее Zone 2!")
    else:
        print(f"  → ratio(27) = {ratio_27:.4f} ≤ ratio(Z2) = {ratio_z2:.4f}")

    print(f"\n{'=' * 78}")
    print(f"  Готово.")
    print(f"{'=' * 78}")


if __name__ == '__main__':
    main()
