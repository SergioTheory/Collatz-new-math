"""
find_intermediate_centers.py — Поиск иерархии confluence-центров

Проверяет, существует ли серия confluence-центров между:
  Mini-Z2 (peak=14, center=121) и Zone 2 (peak=140, center=x*).

Алгоритм:
  1. Берём все рекордсмены из records_data.py с bits 3–70 и ratio > 1.2.
  2. Группируем по peak.
  3. Для каждой группы ≥ 2 числа — ищем общие точки в ускоренных траекториях.
  4. Для каждого рекордсмена строим обратное дерево от x_7 и считаем
     предшественников с тем же peak.

Использование:
  python find_intermediate_centers.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from crt_solver import collatz_peak, analyze_to_peak
from records_data import PATH_RECORDS_BINARY

LOG2_3 = math.log2(3)


def accel_trajectory(n: int, max_steps: int = 500) -> list[int]:
    """Ускоренная траектория: список нечётных x_0, x_1, ..."""
    cur = n
    while cur > 1 and cur % 2 == 0:
        cur >>= 1
    traj = [cur]
    for _ in range(max_steps):
        if cur <= 1:
            break
        val = 3 * cur + 1
        while val % 2 == 0:
            val >>= 1
        cur = val
        traj.append(cur)
    return traj


def extract_shifts_local(n: int, max_steps: int = 500) -> list[int]:
    """Shift-вектор."""
    cur = n
    while cur > 1 and cur % 2 == 0:
        cur >>= 1
    shifts = []
    for _ in range(max_steps):
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


def find_predecessors(m: int, a_max: int = 10, max_bits: int = 150) -> list[tuple[int, int]]:
    """Нечётные предшественники m с bits ≤ max_bits."""
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


def build_reverse_tree(root: int, depth: int, a_max: int, max_bits: int) -> set[int]:
    """Обратное дерево от root, возвращает все узлы."""
    tree_levels = {0: {root}}
    all_nodes = {root}
    for d in range(depth):
        nxt = set()
        for m in tree_levels[d]:
            for n, a in find_predecessors(m, a_max=a_max, max_bits=max_bits):
                if n not in all_nodes:
                    all_nodes.add(n)
                    nxt.add(n)
        tree_levels[d + 1] = nxt
    return all_nodes


def main():
    print(f"{'=' * 80}")
    print(f"  Find Intermediate Confluence Centers")
    print(f"  Mini-Z2 (peak=14, center=121)  →  ???  →  Zone 2 (peak=140, center=x*)")
    print(f"{'=' * 80}")
    print()

    # ── ЧАСТЬ 1: Загрузка и фильтрация рекордсменов ─────────────────────────
    print(f"  ЧАСТЬ 1: Загрузка рекордсменов (bits 3–70, ratio > 1.2)")
    print(f"  {'-' * 70}")

    records = []  # (n, bits, peak, ratio)
    seen_n = set()

    for bstr in PATH_RECORDS_BINARY:
        n = int(bstr, 2)
        bits = n.bit_length()
        if bits < 3 or bits > 70:
            continue
        if n in seen_n:
            continue
        seen_n.add(n)

        peak, steps, conv = collatz_peak(n, max_steps=500_000)
        ratio = peak / bits
        if ratio > 1.2:
            records.append((n, bits, peak, ratio))

    records.sort(key=lambda x: x[1])
    print(f"  Загружено: {len(records)} рекордсменов")

    # ── ЧАСТЬ 2: Группировка по peak ─────────────────────────────────────────
    print(f"\n  ЧАСТЬ 2: Группировка по peak")
    print(f"  {'-' * 70}")

    by_peak = defaultdict(list)  # peak -> [(n, bits, ratio), ...]
    for n, bits, peak, ratio in records:
        by_peak[peak].append((n, bits, ratio))

    print(f"  {'peak':>5}  {'count':>5}  bits")
    print(f"  {'-' * 40}")
    for peak in sorted(by_peak.keys()):
        members = by_peak[peak]
        bits_list = sorted(set(m[1] for m in members))
        bits_str = ', '.join(str(b) for b in bits_list[:8])
        if len(bits_list) > 8:
            bits_str += '...'
        print(f"  {peak:>5}  {len(members):>5}  [{bits_str}]")

    # ── ЧАСТЬ 3: Поиск общих точек в группах ≥ 2 ────────────────────────────
    print(f"\n  ЧАСТЬ 3: Поиск confluence-центров (общие точки в группах)")
    print(f"  {'-' * 70}")

    confluence_centers = []  # (peak, center_value, center_bits, num_inputs,
                             #  bits_range, sd_center, method)

    for peak in sorted(by_peak.keys()):
        members = by_peak[peak]
        if len(members) < 2:
            continue

        # Вычисляем траектории для всех членов группы
        trajs = {}  # n -> trajectory
        for n, bits, ratio in members:
            trajs[n] = accel_trajectory(n, max_steps=500)

        # Ищем общие точки между ВСЕМИ парами
        # Для эффективности: строим индекс значений → (n, step)
        val_index = defaultdict(list)  # x_value -> [(n, step), ...]
        for n, bits, ratio in members:
            for k, x in enumerate(trajs[n]):
                val_index[x].append((n, k))

        # Общая точка — значение, встречающееся у ≥ 2 разных n
        common_points = []
        for x_val, sources in val_index.items():
            unique_n = set(s[0] for s in sources)
            if len(unique_n) >= 2:
                # Берём минимальный шаг для каждого n
                steps_per_n = {}
                for n_src, k_src in sources:
                    if n_src not in steps_per_n or k_src < steps_per_n[n_src]:
                        steps_per_n[n_src] = k_src
                common_points.append((x_val, len(unique_n), steps_per_n))

        if not common_points:
            continue

        # Ищем самую раннюю общую точку (минимальная сумма шагов)
        # и точку, общую для МАКСИМАЛЬНОГО числа входов
        common_points.sort(key=lambda x: -x[1])
        best = common_points[0]
        x_center, num_sources, steps_dict = best

        # Может быть несколько точек с одинаковым num_sources
        # Берём ту, у которой минимальная сумма шагов
        best_by_count = [cp for cp in common_points if cp[1] == num_sources]
        best_by_count.sort(key=lambda cp: sum(cp[2].values()))
        x_center, num_sources, steps_dict = best_by_count[0]

        # S/d для центра
        info_center = analyze_to_peak(x_center, max_steps=500_000)
        d_c = info_center['total_o']
        S_c = info_center['total_e']
        sd_c = round(S_c / d_c, 4) if d_c > 0 else None

        bits_range_list = sorted(set(m[1] for m in members))
        bits_range_str = f"{min(bits_range_list)}-{max(bits_range_list)}"

        confluence_centers.append((
            peak, x_center, x_center.bit_length(), num_sources,
            bits_range_str, sd_c, "trajectory_intersection",
            steps_dict
        ))

        # Выводим детали
        print(f"\n  PEAK={peak}: confluence-центр найден!")
        print(f"    center = {x_center}")
        print(f"    center_bits = {x_center.bit_length()}")
        print(f"    sources = {num_sources} из {len(members)}")
        print(f"    S/d = {sd_c}")
        steps_str = ", ".join(f"{n_s}({bits}b)->step {steps_dict[n_s]}"
                              for n_s, bits, _ in members if n_s in steps_dict)
        print(f"    merge steps: {steps_str[:120]}")

    # ── ЧАСТЬ 4: Обратные деревья от x_7 ─────────────────────────────────────
    print(f"\n  ЧАСТЬ 4: Обратные деревья от x_7 (depth=3)")
    print(f"  {'-' * 70}")

    # Для каждого уникального peak — берём одного представителя
    peak_representatives = {}
    for n, bits, peak, ratio in records:
        if peak not in peak_representatives or bits < peak_representatives[peak][1]:
            peak_representatives[peak] = (n, bits, peak, ratio)

    reverse_centers = []

    for peak in sorted(peak_representatives.keys()):
        n, bits, pk, ratio = peak_representatives[peak]
        traj = accel_trajectory(n, max_steps=500)

        # Берём x_7 (или последний доступный)
        pivot_k = min(7, len(traj) - 1)
        x_pivot = traj[pivot_k]

        # Обратное дерево
        max_bits_tree = pk + 10
        tree_nodes = build_reverse_tree(x_pivot, depth=3, a_max=10,
                                        max_bits=max_bits_tree)

        # Считаем, сколько узлов имеют тот же peak
        same_peak_count = 0
        same_peak_nodes = []

        for node in tree_nodes:
            if node.bit_length() < 3:
                continue
            node_peak, _, _ = collatz_peak(node, max_steps=500_000)
            if node_peak == pk:
                same_peak_count += 1
                same_peak_nodes.append(node)

        if same_peak_count > 1:
            # Это confluence-центр!
            info_piv = analyze_to_peak(x_pivot, max_steps=500_000)
            d_piv = info_piv['total_o']
            S_piv = info_piv['total_e']
            sd_piv = round(S_piv / d_piv, 4) if d_piv > 0 else None

            bits_list = sorted(set(nd.bit_length() for nd in same_peak_nodes))
            bits_range_str = f"{min(bits_list)}-{max(bits_list)}"

            already_found = any(c[0] == pk for c in confluence_centers)
            if not already_found:
                confluence_centers.append((
                    pk, x_pivot, x_pivot.bit_length(), same_peak_count,
                    bits_range_str, sd_piv, "reverse_tree",
                    {}
                ))

            reverse_centers.append((pk, x_pivot, same_peak_count,
                                    len(tree_nodes)))

            print(f"  peak={pk:>4}: x_7={x_pivot} ({x_pivot.bit_length()}b), "
                  f"tree={len(tree_nodes)} nodes, "
                  f"same_peak={same_peak_count}, "
                  f"bits=[{bits_range_str}]")
        else:
            print(f"  peak={pk:>4}: x_7={x_pivot} ({x_pivot.bit_length()}b), "
                  f"tree={len(tree_nodes)} nodes, "
                  f"same_peak={same_peak_count} — NOT a center")

    # ══════════════════════════════════════════════════════════════════════════
    # ИТОГОВАЯ ТАБЛИЦА
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n{'=' * 80}")
    print(f"  ИТОГОВАЯ ТАБЛИЦА CONFLUENCE-ЦЕНТРОВ")
    print(f"{'=' * 80}")

    # Добавляем известные центры для полноты
    # Mini-Z2
    traj_27 = accel_trajectory(27, max_steps=100)
    x7_27 = traj_27[7] if len(traj_27) > 7 else traj_27[-1]
    info_27 = analyze_to_peak(x7_27, max_steps=500_000)
    d_27 = info_27['total_o']
    S_27 = info_27['total_e']
    sd_27 = round(S_27 / d_27, 4) if d_27 > 0 else None

    # Zone 2
    X_STAR = 20152090995747160937051
    info_xs = analyze_to_peak(X_STAR, max_steps=500_000)
    d_xs = info_xs['total_o']
    S_xs = info_xs['total_e']
    sd_xs = round(S_xs / d_xs, 4) if d_xs > 0 else None

    # Собираем все центры
    all_centers = []

    # Добавляем Mini-Z2 если не найден автоматически
    if not any(c[0] == 14 for c in confluence_centers):
        all_centers.append((14, x7_27, x7_27.bit_length(), 27,
                           "5-13", sd_27, "known"))

    # Добавляем найденные
    for pk, xc, xc_bits, nsrc, br, sd, method, _ in confluence_centers:
        all_centers.append((pk, xc, xc_bits, nsrc, br, sd, method))

    # Добавляем Zone 2 если не найден
    if not any(c[0] == 140 for c in confluence_centers):
        all_centers.append((140, X_STAR, X_STAR.bit_length(), 913,
                           "71-87", sd_xs, "known"))

    all_centers.sort(key=lambda x: x[0])

    print(f"\n  {'peak':>5}  {'center':>25}  {'c_bits':>6}  {'inputs':>7}  "
          f"{'src_bits':>10}  {'S/d':>7}  {'method'}")
    print(f"  {'-' * 80}")

    for pk, xc, xc_bits, nsrc, br, sd, method in all_centers:
        xc_str = str(xc)
        if len(xc_str) > 22:
            xc_str = xc_str[:10] + '..' + xc_str[-10:]
        sd_str = f"{sd:.4f}" if sd is not None else "—"
        print(f"  {pk:>5}  {xc_str:>25}  {xc_bits:>6}  {nsrc:>7}  "
              f"{br:>10}  {sd_str:>7}  {method}")

    # ══════════════════════════════════════════════════════════════════════════
    # АНАЛИЗ ЛЕСТНИЦЫ
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n{'=' * 80}")
    print(f"  АНАЛИЗ ЛЕСТНИЦЫ CONFLUENCE-ЦЕНТРОВ")
    print(f"{'=' * 80}")

    if len(all_centers) >= 3:
        print(f"\n  Найдено {len(all_centers)} центров. Проверяем закономерности:")
        print()

        peaks = [c[0] for c in all_centers]
        cbits = [c[2] for c in all_centers]
        sds = [c[5] for c in all_centers if c[5] is not None]

        for i in range(len(all_centers) - 1):
            pk1, _, cb1 = all_centers[i][0], all_centers[i][1], all_centers[i][2]
            pk2, _, cb2 = all_centers[i+1][0], all_centers[i+1][1], all_centers[i+1][2]
            ratio_peaks = pk2 / pk1 if pk1 > 0 else 0
            ratio_cbits = cb2 / cb1 if cb1 > 0 else 0
            print(f"  peak {pk1} → {pk2}: "
                  f"peak ratio = {ratio_peaks:.3f}, "
                  f"center_bits ratio = {ratio_cbits:.3f}")

        # Проверяем log-линейность
        if len(peaks) >= 3:
            import numpy as np
            log_peaks = [math.log(p) for p in peaks if p > 0]
            log_cbits = [math.log(c) for c in cbits if c > 0]
            if len(log_peaks) == len(log_cbits) and len(log_peaks) >= 3:
                # Корреляция
                mean_lp = sum(log_peaks) / len(log_peaks)
                mean_lc = sum(log_cbits) / len(log_cbits)
                cov = sum((a - mean_lp) * (b - mean_lc)
                          for a, b in zip(log_peaks, log_cbits))
                var_lp = sum((a - mean_lp) ** 2 for a in log_peaks)
                var_lc = sum((b - mean_lc) ** 2 for b in log_cbits)
                if var_lp > 0 and var_lc > 0:
                    corr = cov / (var_lp ** 0.5 * var_lc ** 0.5)
                    print(f"\n  Корреляция log(peak) vs log(center_bits): {corr:.4f}")
    else:
        print(f"\n  Найдено только {len(all_centers)} центра. "
              f"Недостаточно для анализа лестницы.")

    # ── Проверяем связность: проходит ли центр уровня k через центр уровня k+1?
    print(f"\n  Проверка связности: проходит ли центр через следующий?")
    print(f"  {'-' * 70}")

    for i in range(len(all_centers) - 1):
        pk1, xc1 = all_centers[i][0], all_centers[i][1]
        pk2, xc2 = all_centers[i+1][0], all_centers[i+1][1]

        traj1 = accel_trajectory(xc1, max_steps=500)
        found = False
        for k, x in enumerate(traj1):
            if x == xc2:
                print(f"  center(peak={pk1}) → center(peak={pk2}): "
                      f"CONNECTED at step {k}!")
                found = True
                break
        if not found:
            # Проверяем, есть ли вообще общие точки
            traj2_set = set(accel_trajectory(xc2, max_steps=500))
            traj1_set = set(traj1)
            common = traj1_set & traj2_set
            if common:
                smallest = min(common, key=lambda x: x.bit_length())
                print(f"  center(peak={pk1}) → center(peak={pk2}): "
                      f"NOT direct, but {len(common)} common points "
                      f"(smallest: {smallest.bit_length()} bits)")
            else:
                print(f"  center(peak={pk1}) → center(peak={pk2}): "
                      f"NO connection")

    print(f"\n{'=' * 80}")
    print(f"  Готово.")
    print(f"{'=' * 80}")


if __name__ == '__main__':
    main()
