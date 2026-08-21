"""
two_class_analysis.py — Анализ двух классов confluence-центров

Класс A (Zone 2-подобные): 121, x* — 100% hit rate, компактные
Класс B (обычные confluence): 719, 6803, 27611... — 70-86% hit rate

Вычисляет:
  1. Правильные d, S до ГЛОБАЛЬНОГО пика (полная odd-to-odd до cur=1)
  2. Метрики: S/d, bits/peak, shift profile, energy
  3. Кластеризация по евклидовому расстоянию
  4. Почему Class A имеет 100% hit rate

Использование:
  python two_class_analysis.py
"""

from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from crt_solver import collatz_peak

log23 = math.log2(3)

# ============================================================
# Все центры
# ============================================================

ALL_CENTERS = [
    # (peak, center, label, hit_rate)
    # --- peaks 14-30 (original) ---
    (14, 121,                          "121",        1.000),
    (14, 719,                          "719",        0.805),
    (16, 6803,                         "6803",       0.846),
    (18, 27611,                        "27611",      0.862),
    (18, 10151,                        "10151-alt",  0.720),
    (19, 15977,                        "15977",      0.722),
    (21, 52487,                        "52487",      0.771),
    (22, 61823,                        "61823",      0.743),
    (23, 41471,                        "41471",      0.825),
    (24, 586115,                       "586115",     0.821),
    (25, 705307,                       "705307",     0.778),
    (26, 1085723,                      "1085723",    0.754),
    (27, 5808671,                      "5808671-alt",0.780),
    (27, 4918427,                      "4918427",    0.818),
    (30, 58595471,                     "58595471",   0.816),
    # --- peaks 31-40 (targeted_search_31_50) ---
    (31, 48427561,                     "48427561",   0.833),
    (32, 1242665,                      "1242665",    0.851),
    (33, 3538943,                      "3538943",    0.829),
    (34, 4205807,                      "4205807",    0.883),
    (35, 26658983,                     "26658983",   0.799),
    (36, 8524379,                      "8524379",    0.911),
    (37, 67625867,                     "67625867",   0.873),
    (38, 16348007,                     "16348007",   0.911),
    (39, 19351295,                     "19351295",   0.895),
    (40, 35337455,                     "35337455",   0.917),
    # --- peaks 41-45 (targeted_search_41_50) ---
    (41, 37748015,                     "37748015",   0.923),
    (42, 72481007,                     "72481007",   0.916),
    (43, 467269499,                    "467269499",  0.806),
    (44, 108893737,                    "108893737",  0.861),
    (45, 236651489,                    "236651489",  0.839),
    # --- peaks 46-50 (exhaustive search, NEW!) ---
    (46, 516844415,                    "516844415",  0.929),
    (47, 442441855,                    "442441855",  0.871),
    (48, 2303929595,                   "2303929595", 0.929),
    (49, 3830005073,                   "3830005073", 0.833),
    (50, 1396693151,                   "1396693151", 0.885),
    # --- peak 140 (Zone 2) ---
    (140, 20152090995747160937051,     "x*",         1.000),
]


# ============================================================
# Полная odd-to-odd траектория до глобального пика
# ============================================================

def trajectory_to_global_peak(n: int, max_steps: int = 2_000_000):
    """
    Полная odd-to-odd траектория. НЕ останавливается на локальном снижении.
    Идёт до cur==1 или max_steps.

    Возвращает:
      odd_values — все нечётные значения [n, v1, v2, ...]
      shifts     — shift-вектор [a1, a2, ...]  (a_i = v2 в каждом odd step)
      peak_bits  — максимальная битность на odd-to-odd траектории
      peak_idx   — индекс в odd_values где достигнут глобальный максимум
      d_total    — полное число odd-шагов до 1
      S_total    — полная сумма сдвигов до 1
    """
    cur = n
    if cur % 2 == 0:
        while cur % 2 == 0:
            cur >>= 1

    odd_values = [cur]
    shifts = []
    peak_bits = cur.bit_length()
    peak_idx = 0
    step = 0

    while cur > 1 and step < max_steps:
        nxt = cur * 3 + 1
        a = 0
        while nxt % 2 == 0:
            nxt >>= 1
            a += 1

        shifts.append(a)
        odd_values.append(nxt)
        step += 1

        if nxt.bit_length() > peak_bits:
            peak_bits = nxt.bit_length()
            peak_idx = step  # индекс в odd_values

        cur = nxt

    return {
        "odd_values": odd_values,
        "shifts": shifts,
        "peak_bits": peak_bits,
        "peak_idx": peak_idx,
        "d_total": len(shifts),
        "S_total": sum(shifts),
    }


# ============================================================
# Метрики центра
# ============================================================

def compute_metrics(peak: int, center: int, label: str,
                    hit_rate: float):
    """Все метрики для одного центра."""
    t0 = time.time()

    tr = trajectory_to_global_peak(center)

    d_total = tr["d_total"]
    S_total = tr["S_total"]
    peak_idx = tr["peak_idx"]
    shifts = tr["shifts"]

    # d, S до глобального пика
    d_peak = peak_idx
    S_peak = sum(shifts[:peak_idx]) if peak_idx > 0 else 0

    # Shift profile до пика
    shifts_to_peak = shifts[:peak_idx] if peak_idx > 0 else []
    count_1 = shifts_to_peak.count(1) if shifts_to_peak else 0
    count_2 = shifts_to_peak.count(2) if shifts_to_peak else 0
    count_ge3 = sum(1 for a in shifts_to_peak if a >= 3) if shifts_to_peak else 0

    frac_1 = count_1 / d_peak if d_peak > 0 else 0
    frac_2 = count_2 / d_peak if d_peak > 0 else 0
    frac_ge3 = count_ge3 / d_peak if d_peak > 0 else 0

    energy = (sum(a * a for a in shifts_to_peak) / d_peak
              if d_peak > 0 else 0)

    S_over_d_peak = S_peak / d_peak if d_peak > 0 else 0
    S_over_d_total = S_total / d_total if d_total > 0 else 0
    bits_over_peak = center.bit_length() / peak if peak > 0 else 0

    # Shift distribution — полное
    shift_dist = Counter(shifts_to_peak)

    # Кумулятивный gain: G(k) = k*log2(3) - sum(shifts[:k])
    # Сохраним максимальный gain и шаг где он достигнут
    max_gain = 0.0
    max_gain_step = 0
    gain_running = 0.0
    for i, a in enumerate(shifts):
        gain_running += log23 - a
        if gain_running > max_gain:
            max_gain = gain_running
            max_gain_step = i + 1

    # Первые 20 и последние 20 сдвигов до пика
    first20 = shifts_to_peak[:20]
    last20 = shifts_to_peak[-20:] if len(shifts_to_peak) >= 20 else shifts_to_peak

    elapsed = time.time() - t0

    return {
        "peak": peak,
        "center": str(center),
        "center_bits": center.bit_length(),
        "label": label,
        "hit_rate": hit_rate,
        # До глобального пика
        "d_peak": d_peak,
        "S_peak": S_peak,
        "S_over_d_peak": S_over_d_peak,
        # Полная траектория
        "d_total": d_total,
        "S_total": S_total,
        "S_over_d_total": S_over_d_total,
        # Отношения
        "bits_over_peak": bits_over_peak,
        "peak_bits_actual": tr["peak_bits"],
        # Shift profile
        "frac_1": frac_1,
        "frac_2": frac_2,
        "frac_ge3": frac_ge3,
        "energy": energy,
        "shift_dist": dict(shift_dist),
        "first20_shifts": first20,
        "last20_shifts": last20,
        # Gain
        "max_gain": max_gain,
        "max_gain_step": max_gain_step,
        # Timing
        "elapsed": elapsed,
    }


# ============================================================
# Кластеризация
# ============================================================

def normalize_metrics(metrics_list: list[dict],
                      keys: list[str]) -> list[list[float]]:
    """Нормализует метрики к [0, 1]."""
    n = len(metrics_list)
    k = len(keys)
    raw = [[m[key] for key in keys] for m in metrics_list]

    # Min-max per column
    mins = [min(raw[i][j] for i in range(n)) for j in range(k)]
    maxs = [max(raw[i][j] for i in range(n)) for j in range(k)]
    ranges = [maxs[j] - mins[j] if maxs[j] != mins[j] else 1.0
              for j in range(k)]

    normed = [[(raw[i][j] - mins[j]) / ranges[j]
               for j in range(k)]
              for i in range(n)]
    return normed


def euclidean_dist(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def distance_matrix(normed: list[list[float]]) -> list[list[float]]:
    n = len(normed)
    mat = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = euclidean_dist(normed[i], normed[j])
            mat[i][j] = d
            mat[j][i] = d
    return mat


def single_linkage_clusters(dist_mat: list[list[float]],
                            labels: list[str],
                            threshold: float = 0.5):
    """Простейшая single-linkage кластеризация."""
    n = len(labels)
    clusters = [[i] for i in range(n)]
    cluster_id = list(range(n))

    merges = []
    # Собираем все расстояния
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((dist_mat[i][j], i, j))
    pairs.sort()

    for dist, i, j in pairs:
        ci, cj = cluster_id[i], cluster_id[j]
        if ci == cj:
            continue
        if dist > threshold:
            break
        # Merge clusters
        new_id = min(ci, cj)
        old_id = max(ci, cj)
        for k in range(n):
            if cluster_id[k] == old_id:
                cluster_id[k] = new_id
        merges.append((dist, labels[i], labels[j]))

    # Group by cluster
    groups = {}
    for k in range(n):
        cid = cluster_id[k]
        if cid not in groups:
            groups[cid] = []
        groups[cid].append(labels[k])

    return list(groups.values()), merges


# ============================================================
# Анализ hit rate 100% vs <100%
# ============================================================

def analyze_hit_rate_difference(metrics_list: list[dict]):
    """Сравнивает Class A (100%) vs Class B (<100%)."""
    class_a = [m for m in metrics_list if m["hit_rate"] >= 0.99]
    class_b = [m for m in metrics_list if m["hit_rate"] < 0.99]

    if not class_a or not class_b:
        return {}

    compare_keys = [
        "S_over_d_peak", "S_over_d_total", "bits_over_peak",
        "frac_1", "frac_2", "frac_ge3", "energy",
        "d_peak", "S_peak", "max_gain",
    ]

    comparison = {}
    for key in compare_keys:
        a_vals = [m[key] for m in class_a]
        b_vals = [m[key] for m in class_b]
        a_mean = sum(a_vals) / len(a_vals)
        b_mean = sum(b_vals) / len(b_vals)
        b_std = (sum((v - b_mean) ** 2 for v in b_vals) / len(b_vals)) ** 0.5

        comparison[key] = {
            "class_a_mean": a_mean,
            "class_b_mean": b_mean,
            "class_b_std": b_std,
            "diff": a_mean - b_mean,
            "a_values": a_vals,
        }

    return comparison


# ============================================================
# Вывод
# ============================================================

def main():
    t_start = time.time()
    sep = "=" * 110

    print(f"\n{sep}")
    print(f"  Two-Class Analysis of Confluence Centers")
    print(f"  Corrected d, S to GLOBAL peak (full trajectory to 1)")
    print(sep)

    # Вычисляем метрики для всех центров
    print(f"\n  Computing trajectories for {len(ALL_CENTERS)} centers...")

    metrics = []
    for peak, center, label, hr in ALL_CENTERS:
        print(f"    {label:>20} (peak={peak})...", end="", flush=True)
        m = compute_metrics(peak, center, label, hr)
        metrics.append(m)
        print(f"  d_peak={m['d_peak']}, S_peak={m['S_peak']}, "
              f"S/d={m['S_over_d_peak']:.4f}  [{m['elapsed']:.1f}s]")

    # ==========================================
    # Таблица 1: Corrected d, S
    # ==========================================
    print(f"\n{sep}")
    print(f"  CORRECTED d, S (to global peak)")
    print(sep)
    print(f"  {'Peak':>4}  {'Center':<20}  {'d_peak':>6}  {'S_peak':>6}  "
          f"{'S/d':>7}  {'d_tot':>7}  {'S_tot':>7}  {'S/d_tot':>7}  "
          f"{'b/p':>5}  {'HR':>5}  Class")
    print(f"  {'----':>4}  {'------':<20}  {'------':>6}  {'------':>6}  "
          f"{'---':>7}  {'-----':>7}  {'-----':>7}  {'-------':>7}  "
          f"{'---':>5}  {'--':>5}  -----")

    for m in metrics:
        cls = "A" if m["hit_rate"] >= 0.99 else "B"
        lbl = m["label"]
        if len(lbl) > 18:
            lbl = lbl[:16] + ".."
        print(f"  {m['peak']:>4}  {lbl:<20}  {m['d_peak']:>6}  "
              f"{m['S_peak']:>6}  {m['S_over_d_peak']:>7.4f}  "
              f"{m['d_total']:>7}  {m['S_total']:>7}  "
              f"{m['S_over_d_total']:>7.4f}  "
              f"{m['bits_over_peak']:>5.3f}  "
              f"{m['hit_rate']:>5.0%}  {cls}")

    # ==========================================
    # Таблица 2: Shift distribution
    # ==========================================
    print(f"\n{sep}")
    print(f"  SHIFT DISTRIBUTION (to global peak)")
    print(sep)
    print(f"  {'Peak':>4}  {'Center':<16}  {'%1s':>5}  {'%2s':>5}  "
          f"{'%≥3':>5}  {'Energy':>7}  {'d_peak':>6}  Class")
    print(f"  {'----':>4}  {'------':<16}  {'---':>5}  {'---':>5}  "
          f"{'---':>5}  {'------':>7}  {'------':>6}  -----")

    for m in metrics:
        cls = "A" if m["hit_rate"] >= 0.99 else "B"
        lbl = m["label"][:14]
        print(f"  {m['peak']:>4}  {lbl:<16}  {m['frac_1']:>5.1%}  "
              f"{m['frac_2']:>5.1%}  {m['frac_ge3']:>5.1%}  "
              f"{m['energy']:>7.3f}  {m['d_peak']:>6}  {cls}")

    # ==========================================
    # Таблица 3: Первые 20 сдвигов
    # ==========================================
    print(f"\n{sep}")
    print(f"  FIRST 20 SHIFTS FROM CENTER")
    print(sep)
    for m in metrics:
        cls = "A" if m["hit_rate"] >= 0.99 else "B"
        shifts_str = ",".join(str(s) for s in m["first20_shifts"][:20])
        lbl = m["label"][:12]
        print(f"  {m['peak']:>3} {lbl:<12} [{cls}]: {shifts_str}")

    # ==========================================
    # Кластеризация
    # ==========================================
    print(f"\n{sep}")
    print(f"  CLUSTER ANALYSIS")
    print(sep)

    cluster_keys = [
        "S_over_d_peak", "S_over_d_total", "bits_over_peak",
        "frac_1", "frac_2", "frac_ge3", "energy", "hit_rate",
    ]

    labels = [m["label"] for m in metrics]
    normed = normalize_metrics(metrics, cluster_keys)
    dist_mat = distance_matrix(normed)

    # Матрица расстояний (верхний треугольник, первые 8)
    show_n = min(8, len(metrics))
    print(f"\n  Distance matrix (first {show_n}):")
    short_labels = [l[:10] for l in labels[:show_n]]
    header = "  " + " " * 12 + "  ".join(f"{l:>10}" for l in short_labels)
    print(header)
    for i in range(show_n):
        row = f"  {short_labels[i]:<12}"
        for j in range(show_n):
            if j < i:
                row += f"{'':>12}"
            elif j == i:
                row += f"{'---':>12}"
            else:
                row += f"{dist_mat[i][j]:>12.3f}"
        print(row)

    # Кластеры
    for threshold in [0.3, 0.5, 0.8, 1.0]:
        clusters, merges = single_linkage_clusters(
            dist_mat, labels, threshold=threshold
        )
        print(f"\n  Threshold={threshold}:  {len(clusters)} clusters")
        for i, cl in enumerate(clusters):
            print(f"    Cluster {i+1}: {cl}")

    # ==========================================
    # Class A vs Class B сравнение
    # ==========================================
    print(f"\n{sep}")
    print(f"  KEY DIFFERENCE: Class A (100% HR) vs Class B (<100% HR)")
    print(sep)

    comparison = analyze_hit_rate_difference(metrics)

    if comparison:
        print(f"\n  {'Metric':<20}  {'ClassA mean':>12}  {'ClassB mean':>12}  "
              f"{'ClassB std':>10}  {'Diff(A-B)':>10}  Direction")
        print(f"  {'------':<20}  {'-----------':>12}  {'-----------':>12}  "
              f"{'----------':>10}  {'---------':>10}  ---------")

        for key in sorted(comparison.keys()):
            v = comparison[key]
            direction = "A higher" if v["diff"] > 0 else "A lower"
            sig = ""
            if v["class_b_std"] > 0:
                z = abs(v["diff"]) / v["class_b_std"]
                if z > 2:
                    sig = " ***"
                elif z > 1:
                    sig = " *"

            print(f"  {key:<20}  {v['class_a_mean']:>12.4f}  "
                  f"{v['class_b_mean']:>12.4f}  {v['class_b_std']:>10.4f}  "
                  f"{v['diff']:>+10.4f}  {direction}{sig}")

    # ==========================================
    # Пара 121 vs 719 для peak=14
    # ==========================================
    print(f"\n{sep}")
    print(f"  CASE STUDY: peak=14 — 121 (100%) vs 719 (80.5%)")
    print(sep)

    m121 = next(m for m in metrics if m["label"] == "121")
    m719 = next(m for m in metrics if m["label"] == "719")

    print(f"\n  {'Metric':<20}  {'121':>12}  {'719':>12}  Difference")
    print(f"  {'------':<20}  {'---':>12}  {'---':>12}  ----------")

    compare_keys = ["d_peak", "S_peak", "S_over_d_peak",
                    "d_total", "S_total", "S_over_d_total",
                    "bits_over_peak", "frac_1", "frac_2",
                    "frac_ge3", "energy", "max_gain"]

    for key in compare_keys:
        v1 = m121[key]
        v2_ = m719[key]
        diff = v1 - v2_ if isinstance(v1, (int, float)) else "—"
        if isinstance(v1, float):
            diff_str = f"{diff:>+10.4f}" if isinstance(diff, (int, float)) else f"{'—':>10}"
            print(f"  {key:<20}  {v1:>12.4f}  {v2_:>12.4f}  {diff_str}")
        else:
            diff_str = f"{diff:>+10}" if isinstance(diff, (int, float)) else f"{'—':>10}"
            print(f"  {key:<20}  {v1:>12}  {v2_:>12}  {diff_str}")

    # Проверяем: 719 проходит через 121?
    print(f"\n  Does 719's trajectory pass through 121?")
    cur = 719
    step = 0
    found = False
    while cur > 1 and step < 100000:
        cur = cur * 3 + 1
        while cur % 2 == 0:
            cur >>= 1
        step += 1
        if cur == 121:
            found = True
            print(f"    YES! 719 reaches 121 after {step} odd steps")
            break
    if not found:
        # Обратное: 121 → 719?
        cur = 121
        step = 0
        while cur > 1 and step < 100000:
            cur = cur * 3 + 1
            while cur % 2 == 0:
                cur >>= 1
            step += 1
            if cur == 719:
                print(f"    121 reaches 719 after {step} odd steps")
                found = True
                break
        if not found:
            print(f"    Neither passes through the other")

    # ==========================================
    # Пара 5808671 vs 4918427 для peak=27
    # ==========================================
    print(f"\n  CASE STUDY: peak=27 — 5808671 (78%) vs 4918427 (81.8%)")

    m58 = next(m for m in metrics if m["label"] == "5808671-alt")
    m49 = next(m for m in metrics if m["label"] == "4918427")

    for key in ["d_peak", "S_peak", "S_over_d_peak", "bits_over_peak",
                "frac_1", "energy"]:
        v1 = m58[key]
        v2_ = m49[key]
        fmt = ".4f" if isinstance(v1, float) else ""
        print(f"    {key:<20}: 5808671={v1:{fmt}}, 4918427={v2_:{fmt}}")

    # Связь?
    cur = 5808671
    step = 0
    while cur > 1 and step < 100000:
        cur = cur * 3 + 1
        while cur % 2 == 0:
            cur >>= 1
        step += 1
        if cur == 4918427:
            print(f"    5808671 reaches 4918427 after {step} odd steps")
            break
    else:
        cur = 4918427
        step = 0
        while cur > 1 and step < 100000:
            cur = cur * 3 + 1
            while cur % 2 == 0:
                cur >>= 1
            step += 1
            if cur == 5808671:
                print(f"    4918427 reaches 5808671 after {step} odd steps")
                break
        else:
            print(f"    Neither passes through the other")

    # ==========================================
    # Итоги
    # ==========================================
    elapsed = time.time() - t_start

    print(f"\n{sep}")
    print(f"  SUMMARY")
    print(sep)

    class_a = [m for m in metrics if m["hit_rate"] >= 0.99]
    class_b = [m for m in metrics if m["hit_rate"] < 0.99]

    if class_a:
        mean_sd_a = sum(m["S_over_d_peak"] for m in class_a) / len(class_a)
        mean_bp_a = sum(m["bits_over_peak"] for m in class_a) / len(class_a)
        print(f"\n  Class A ({len(class_a)} centers, 100% hit rate):")
        print(f"    Members: {[m['label'] for m in class_a]}")
        print(f"    Mean S/d (to peak): {mean_sd_a:.4f}")
        print(f"    Mean bits/peak:     {mean_bp_a:.4f}")

    if class_b:
        mean_sd_b = sum(m["S_over_d_peak"] for m in class_b) / len(class_b)
        mean_bp_b = sum(m["bits_over_peak"] for m in class_b) / len(class_b)
        hr_range = (min(m["hit_rate"] for m in class_b),
                    max(m["hit_rate"] for m in class_b))
        print(f"\n  Class B ({len(class_b)} centers, {hr_range[0]:.0%}–"
              f"{hr_range[1]:.0%} hit rate):")
        print(f"    Members: {[m['label'] for m in class_b]}")
        print(f"    Mean S/d (to peak): {mean_sd_b:.4f}")
        print(f"    Mean bits/peak:     {mean_bp_b:.4f}")

    if class_a and class_b:
        print(f"\n  SEPARATION:")
        print(f"    S/d gap:       Class A = {mean_sd_a:.4f}, "
              f"Class B = {mean_sd_b:.4f}, diff = {mean_sd_a - mean_sd_b:+.4f}")
        print(f"    bits/peak gap: Class A = {mean_bp_a:.4f}, "
              f"Class B = {mean_bp_b:.4f}, diff = {mean_bp_a - mean_bp_b:+.4f}")

    # ==========================================
    # FIT: center_bits vs peak (linear)
    # ==========================================
    print(f"\n{sep}")
    print(f"  FIT: center_bits = α · peak + β")
    print(sep)

    # Берём по одному центру на peak (primary, не alt)
    seen_peaks = set()
    fit_points = []
    for m in metrics:
        p = m["peak"]
        if p in seen_peaks:
            continue
        if m["label"].endswith("-alt"):
            continue
        seen_peaks.add(p)
        fit_points.append((p, m["center_bits"]))

    fit_peaks = [x[0] for x in fit_points]
    fit_bits = [x[1] for x in fit_points]

    n_fit = len(fit_peaks)
    sx = sum(fit_peaks)
    sy = sum(fit_bits)
    sxx = sum(x * x for x in fit_peaks)
    sxy = sum(x * y for x, y in zip(fit_peaks, fit_bits))
    denom = n_fit * sxx - sx * sx
    if abs(denom) > 1e-30:
        alpha_fit = (n_fit * sxy - sx * sy) / denom
        beta_fit = (sy - alpha_fit * sx) / n_fit
        y_mean = sy / n_fit
        ss_res = sum((y - (alpha_fit * x + beta_fit)) ** 2
                     for x, y in zip(fit_peaks, fit_bits))
        ss_tot = sum((y - y_mean) ** 2 for y in fit_bits)
        r2_fit = 1 - ss_res / ss_tot if ss_tot > 1e-30 else 0
    else:
        alpha_fit, beta_fit, r2_fit = 0, 0, 0

    print(f"\n  On {n_fit} data points (one per peak, excl. alt):")
    print(f"    α = {alpha_fit:.6f}")
    print(f"    β = {beta_fit:.4f}")
    print(f"    R² = {r2_fit:.6f}")
    print(f"\n  Residuals:")
    print(f"  {'Peak':>4}  {'Actual':>6}  {'Predicted':>9}  {'Residual':>8}")
    for p, b in fit_points:
        pred = alpha_fit * p + beta_fit
        print(f"  {p:>4}  {b:>6}  {pred:>9.1f}  {b - pred:>+8.1f}")

    # ==========================================
    # TREND: S/d vs peak
    # ==========================================
    print(f"\n{sep}")
    print(f"  TREND: S/d (to peak) vs peak")
    print(sep)

    seen_peaks2 = set()
    trend_points = []
    for m in metrics:
        p = m["peak"]
        if p in seen_peaks2:
            continue
        if m["label"].endswith("-alt"):
            continue
        seen_peaks2.add(p)
        trend_points.append((p, m["S_over_d_peak"]))

    trend_peaks = [x[0] for x in trend_points]
    trend_sd = [x[1] for x in trend_points]

    # Linear fit S/d vs peak
    n_tr = len(trend_peaks)
    sx2 = sum(trend_peaks)
    sy2 = sum(trend_sd)
    sxx2 = sum(x * x for x in trend_peaks)
    sxy2 = sum(x * y for x, y in zip(trend_peaks, trend_sd))
    denom2 = n_tr * sxx2 - sx2 * sx2
    if abs(denom2) > 1e-30:
        a_sd = (n_tr * sxy2 - sx2 * sy2) / denom2
        b_sd = (sy2 - a_sd * sx2) / n_tr
    else:
        a_sd, b_sd = 0, 0

    mean_sd_all = sy2 / n_tr if n_tr > 0 else 0
    # Excluding x* (peak=140)
    sd_no_xstar = [s for p, s in trend_points if p < 140]
    mean_sd_no_xstar = (sum(sd_no_xstar) / len(sd_no_xstar)
                        if sd_no_xstar else 0)

    print(f"\n  Mean S/d (all):         {mean_sd_all:.4f}")
    print(f"  Mean S/d (peaks<140):   {mean_sd_no_xstar:.4f}")
    print(f"  Linear trend: S/d ≈ {a_sd:+.6f} · peak + {b_sd:.4f}")
    print(f"\n  {'Peak':>4}  {'S/d':>8}  {'Trend':>8}")
    for p, sd in trend_points:
        print(f"  {p:>4}  {sd:>8.4f}  {a_sd * p + b_sd:>8.4f}")

    # ==========================================
    # TREND: hit_rate vs peak
    # ==========================================
    print(f"\n{sep}")
    print(f"  TREND: hit_rate vs peak (Class B only)")
    print(sep)

    hr_points = [(m["peak"], m["hit_rate"]) for m in metrics
                 if m["hit_rate"] < 0.99 and not m["label"].endswith("-alt")]
    # Remove duplicate peaks (keep first)
    hr_seen = set()
    hr_unique = []
    for p, h in hr_points:
        if p not in hr_seen:
            hr_seen.add(p)
            hr_unique.append((p, h))

    if len(hr_unique) >= 3:
        hr_peaks_v = [x[0] for x in hr_unique]
        hr_vals = [x[1] for x in hr_unique]
        n_hr = len(hr_peaks_v)
        sx3 = sum(hr_peaks_v)
        sy3 = sum(hr_vals)
        sxx3 = sum(x * x for x in hr_peaks_v)
        sxy3 = sum(x * y for x, y in zip(hr_peaks_v, hr_vals))
        denom3 = n_hr * sxx3 - sx3 * sx3
        if abs(denom3) > 1e-30:
            a_hr = (n_hr * sxy3 - sx3 * sy3) / denom3
            b_hr = (sy3 - a_hr * sx3) / n_hr
        else:
            a_hr, b_hr = 0, 0
        print(f"  Linear trend: hit_rate ≈ {a_hr:+.6f} · peak + {b_hr:.4f}")
        print(f"  (positive slope = hit rate increases with peak)")
        for p, h in hr_unique:
            print(f"    peak={p:>3}: hr={h:.3f}, trend={a_hr * p + b_hr:.3f}")

    print(f"\n  Time: {time.time() - t_start:.1f}s")
    print(sep)

    # JSON
    out_path = "two_class_analysis.json"
    # Убираем невыгружаемые поля
    export = []
    for m in metrics:
        e = dict(m)
        e.pop("odd_values", None)
        export.append(e)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"metrics": export,
                   "comparison": {k: {kk: vv for kk, vv in v.items()
                                      if kk != "a_values"}
                                  for k, v in comparison.items()},
                   }, f, indent=2, default=str)
    print(f"\n  JSON: {out_path}")


if __name__ == "__main__":
    main()
