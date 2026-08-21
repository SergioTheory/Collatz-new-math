"""
verify_census_centers.py — Верификация confluence-центров через обратное дерево

Части:
  A. Reverse-tree верификация каждого кандидата (depth=7)
  B. Сравнение census vs known центров (кто предшественник кого)
  C. Поиск "лучшего" центра для каждого peak (точка слияния)
  D. Расширенный поиск для peaks 31–60

Использование:
  python verify_census_centers.py
  python verify_census_centers.py --peaks 14 18 27
  python verify_census_centers.py --extended --peak-lo 31 --peak-hi 60
  python verify_census_centers.py --no-extended
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from crt_solver import collatz_peak

log23 = math.log2(3)

# ============================================================
# Данные
# ============================================================

KNOWN_CENTERS = {
    14: 121,
    16: 6803,
    18: 27611,
    22: 61823,
    27: 5808671,
}

CENSUS_CENTERS = {
    14: 719,
    18: 10151,
    19: 15977,
    21: 52487,
    23: 41471,
    24: 586115,
    25: 705307,
    26: 1085723,
    27: 4918427,
    30: 58595471,
}

# Тривиальные точки — исключаем
TRIVIAL = frozenset({1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21})

REVERSE_DEPTH = 7
A_MAX = 15
MAX_STEPS = 2_000_000
PEAK_TIMEOUT = 120  # секунд на один peak (мягкий лимит)


# ============================================================
# Базовые функции
# ============================================================

def reverse_step(x: int, a_max: int = A_MAX, max_bits: int = 200):
    """Предшественники x по ускоренной odd-to-odd динамике."""
    preds = []
    pw = 1
    for a in range(1, a_max + 1):
        pw <<= 1
        y_num = x * pw - 1
        if y_num % 3 != 0:
            continue
        y = y_num // 3
        if y > 0 and y & 1 and y != x and y.bit_length() <= max_bits:
            preds.append(y)
    return preds


def build_reverse_tree(root: int, depth: int, a_max: int,
                       max_bits: int) -> list[set]:
    """BFS обратного дерева. Возвращает список множеств по уровням."""
    layers = [set() for _ in range(depth + 1)]
    layers[0].add(root)
    visited = {root}

    for d in range(depth):
        for m in layers[d]:
            for y in reverse_step(m, a_max=a_max, max_bits=max_bits):
                if y not in visited:
                    visited.add(y)
                    layers[d + 1].add(y)

    return layers


def odd_trajectory_to_peak(n: int, max_steps: int = 50000):
    """Нечётные значения траектории ДО пика (+ несколько шагов после)."""
    if n <= 0 or n % 2 == 0:
        return [], n.bit_length()

    cur = n
    peak_bits = cur.bit_length()
    trajectory = [cur]
    steps_past_peak = 0

    for _ in range(max_steps):
        if cur <= 1:
            break
        cur = cur * 3 + 1
        while cur % 2 == 0:
            cur >>= 1

        cb = cur.bit_length()
        if cb > peak_bits:
            peak_bits = cb
            steps_past_peak = 0
        else:
            steps_past_peak += 1

        trajectory.append(cur)

        if steps_past_peak > 8:
            break

    return trajectory, peak_bits


def trajectory_before_peak(n: int, max_steps: int = 50000):
    """Нечётные точки строго ДО достижения пика."""
    if n <= 0 or n % 2 == 0:
        return []

    cur = n
    peak_bits = cur.bit_length()
    points = []

    # Сначала пройдём до пика, запоминая odd-шаги
    all_odd = [cur]
    for _ in range(max_steps):
        if cur <= 1:
            break
        cur = cur * 3 + 1
        while cur % 2 == 0:
            cur >>= 1
        all_odd.append(cur)

        if cur.bit_length() > peak_bits:
            peak_bits = cur.bit_length()

        # Далеко за пиком — стоп
        if cur.bit_length() < peak_bits - 10 and len(all_odd) > 10:
            break

    # Теперь отбираем те, что ДО пика
    running_max = n.bit_length()
    for val in all_odd:
        nxt = val * 3 + 1
        nxt_bits = nxt.bit_length()
        if nxt_bits >= peak_bits:
            # val — последняя точка перед пиком
            points.append(val)
            break
        points.append(val)
        if nxt_bits > running_max:
            running_max = nxt_bits

    return points


def check_passes_through(n: int, target: int, max_steps: int = 50000):
    """Проверяет, проходит ли odd-trajectory n через target."""
    cur = n
    for _ in range(max_steps):
        if cur == target:
            return True
        if cur <= 1:
            return False
        cur = cur * 3 + 1
        while cur % 2 == 0:
            cur >>= 1
    return False


def steps_to_reach(n: int, target: int, max_steps: int = 50000):
    """Сколько odd-шагов от n до target. -1 если не достигнут."""
    cur = n
    for step in range(max_steps):
        if cur == target:
            return step
        if cur <= 1:
            return -1
        cur = cur * 3 + 1
        while cur % 2 == 0:
            cur >>= 1
    return -1


# ============================================================
# Часть A: Верификация через обратное дерево
# ============================================================

def verify_center_via_tree(center: int, target_peak: int,
                           depth: int = REVERSE_DEPTH,
                           a_max: int = A_MAX):
    """
    Строит обратное дерево от center, считает hit rate.
    Возвращает dict с результатами.
    """
    max_bits = target_peak + 15
    layers = build_reverse_tree(center, depth, a_max, max_bits)

    total_nodes = sum(len(lay) for lay in layers)

    # Собираем узлы с bits < target_peak (это потенциальные inputs)
    target_nodes = []
    for lay in layers:
        for n in lay:
            if n.bit_length() < target_peak and n != center:
                target_nodes.append(n)

    # Проверяем peak для каждого
    hit_nodes = 0
    for n in target_nodes:
        pb, _, conv = collatz_peak(n, max_steps=MAX_STEPS)
        if pb == target_peak:
            hit_nodes += 1

    hit_rate = hit_nodes / len(target_nodes) if target_nodes else 0.0

    if hit_rate >= 0.80 and hit_nodes >= 10:
        status = "CONFIRMED"
    elif hit_rate >= 0.50 and hit_nodes >= 5:
        status = "CANDIDATE"
    elif hit_rate >= 0.30 or hit_nodes >= 2:
        status = "WEAK"
    else:
        status = "NONE"

    return {
        "center": str(center),
        "center_bits": center.bit_length(),
        "peak": target_peak,
        "tree_nodes": total_nodes,
        "target_nodes": len(target_nodes),
        "hit_nodes": hit_nodes,
        "hit_rate": hit_rate,
        "status": status,
        "depth": depth,
    }


# ============================================================
# Часть C: Поиск лучшего центра через точки слияния
# ============================================================

def find_best_center(numbers: list[int], peak: int,
                     max_point_bits: int = 80):
    """
    Для списка чисел с одинаковым peak находит самую частую
    общую нечётную точку в траекториях ДО пика.
    """
    if len(numbers) < 3:
        return None, 0, len(numbers)

    point_counter = Counter()
    sample = numbers[:100]

    for n in sample:
        points = trajectory_before_peak(n)
        for p in points:
            if p != n and p not in TRIVIAL and p.bit_length() <= max_point_bits:
                point_counter[p] += 1

    if not point_counter:
        return None, 0, len(sample)

    best_val, best_count = point_counter.most_common(1)[0]
    return best_val, best_count, len(sample)


# ============================================================
# Workers для multiprocessing
# ============================================================

def _worker_verify_pair(args):
    """Верифицирует пару (center, peak). Модуль-уровень для pickle."""
    center, peak, label = args
    t0 = time.time()
    result = verify_center_via_tree(center, peak)
    result["label"] = label
    result["elapsed"] = time.time() - t0
    return result


def _worker_extended_peak(args):
    """Ищет и верифицирует центр для одного peak (31-60)."""
    peak, seed = args
    rng = random.Random(seed)
    t0 = time.time()

    result = {
        "peak": peak,
        "center": None,
        "center_bits": None,
        "hit_nodes": 0,
        "hit_rate": 0.0,
        "status": "NONE",
        "sample_size": 0,
        "notes": "",
    }

    # Генерируем случайные числа и ищем с peak == P
    bit_lo = max(3, peak // 3)
    bit_hi = peak - 1
    samples = []
    attempts = 0
    max_attempts = 500_000

    while len(samples) < 80 and attempts < max_attempts:
        b = rng.randint(bit_lo, bit_hi)
        n = rng.getrandbits(b) | (1 << (b - 1)) | 1
        if n < 3:
            attempts += 1
            continue
        pb, _, conv = collatz_peak(n, max_steps=MAX_STEPS)
        attempts += 1
        if pb == peak and conv:
            samples.append(n)

    result["sample_size"] = len(samples)

    if len(samples) < 5:
        # Альтернативный метод: обратное дерево от 2^ceil(peak/log23)-1
        b_fa = round(peak / log23)
        fa_num = (1 << b_fa) - 1
        pb_fa, _, _ = collatz_peak(fa_num, max_steps=MAX_STEPS)

        if pb_fa == peak:
            # Family A точно накрывает этот peak
            max_bits_tree = peak + 10
            layers = build_reverse_tree(fa_num, depth=4, a_max=A_MAX,
                                        max_bits=max_bits_tree)
            for lay in layers:
                for n in lay:
                    if n.bit_length() < peak:
                        pb2, _, conv2 = collatz_peak(n, max_steps=MAX_STEPS)
                        if pb2 == peak and conv2:
                            samples.append(n)

            result["sample_size"] = len(samples)
            if len(samples) < 5:
                result["status"] = "FAMILY_A"
                result["notes"] = f"only Family A (2^{b_fa}-1)"
                result["elapsed"] = time.time() - t0
                return result

    if len(samples) < 5:
        result["notes"] = f"{len(samples)} samples in {attempts} attempts"
        result["elapsed"] = time.time() - t0
        return result

    # Ищем точку слияния
    best_center, best_count, sample_size = find_best_center(
        samples, peak, max_point_bits=min(80, peak + 5)
    )

    if best_center is None or best_count < 2:
        result["notes"] = f"{len(samples)} samples, no confluence"
        result["elapsed"] = time.time() - t0
        return result

    # Верифицируем через reverse tree
    vr = verify_center_via_tree(best_center, peak, depth=6, a_max=A_MAX)

    result["center"] = str(best_center)
    result["center_bits"] = best_center.bit_length()
    result["hit_nodes"] = vr["hit_nodes"]
    result["hit_rate"] = vr["hit_rate"]
    result["status"] = vr["status"]
    result["tree_nodes"] = vr["tree_nodes"]
    result["confluence_hits"] = best_count
    result["elapsed"] = time.time() - t0

    return result


# ============================================================
# Часть B: Сравнение census vs known
# ============================================================

def compare_census_vs_known():
    """Проверяет связь между census и known центрами."""
    common_peaks = sorted(set(CENSUS_CENTERS) & set(KNOWN_CENTERS))
    comparisons = []

    for peak in common_peaks:
        census_c = CENSUS_CENTERS[peak]
        known_c = KNOWN_CENTERS[peak]

        # census → known? (проходит ли траектория census через known)
        c_to_k_steps = steps_to_reach(census_c, known_c)
        # known → census?
        k_to_c_steps = steps_to_reach(known_c, census_c)

        comparisons.append({
            "peak": peak,
            "census_center": census_c,
            "known_center": known_c,
            "census_reaches_known": c_to_k_steps >= 0,
            "census_to_known_steps": c_to_k_steps,
            "known_reaches_census": k_to_c_steps >= 0,
            "known_to_census_steps": k_to_c_steps,
        })

    return comparisons


# ============================================================
# Вывод
# ============================================================

def print_part_a(results: list[dict]):
    """Таблица верификации Part A."""
    sep = "=" * 100
    print(f"\n{sep}")
    print("  Part A: Verification of Centers via Reverse Tree (depth=7)")
    print(sep)
    print(f"  {'Peak':>4}  {'Label':<12}  {'Center':>22}  {'Bits':>4}  "
          f"{'TreeN':>6}  {'TgtN':>5}  {'HitN':>5}  {'HitRate':>7}  "
          f"{'Status':<10}  {'Time':>5}")
    print(f"  {'----':>4}  {'-----':<12}  {'------':>22}  {'----':>4}  "
          f"{'-----':>6}  {'----':>5}  {'----':>5}  {'-------':>7}  "
          f"{'------':<10}  {'----':>5}")

    for r in sorted(results, key=lambda x: (x["peak"], x["label"])):
        c_str = r["center"]
        if len(c_str) > 20:
            c_str = c_str[:18] + ".."
        hr_str = f"{r['hit_rate']:.1%}"
        t_str = f"{r['elapsed']:.0f}s"
        print(f"  {r['peak']:>4}  {r['label']:<12}  {c_str:>22}  "
              f"{r['center_bits']:>4}  {r['tree_nodes']:>6}  "
              f"{r['target_nodes']:>5}  {r['hit_nodes']:>5}  "
              f"{hr_str:>7}  {r['status']:<10}  {t_str:>5}")


def print_part_b(comparisons: list[dict]):
    """Таблица сравнений Part B."""
    sep = "=" * 100
    print(f"\n{sep}")
    print("  Part B: Comparison — Census center vs Known center")
    print(sep)
    print(f"  {'Peak':>4}  {'Census':>12}  {'Known':>12}  "
          f"{'Census→Known':>14}  {'Known→Census':>14}  {'Relation':<30}")
    print(f"  {'----':>4}  {'------':>12}  {'-----':>12}  "
          f"{'------------':>14}  {'------------':>14}  {'--------':<30}")

    for c in comparisons:
        c2k = (f"YES ({c['census_to_known_steps']} steps)"
               if c["census_reaches_known"] else "NO")
        k2c = (f"YES ({c['known_to_census_steps']} steps)"
               if c["known_reaches_census"] else "NO")

        if c["census_reaches_known"] and not c["known_reaches_census"]:
            relation = "census is PREDECESSOR of known"
        elif c["known_reaches_census"] and not c["census_reaches_known"]:
            relation = "known is PREDECESSOR of census"
        elif c["census_center"] == c["known_center"]:
            relation = "SAME center"
        elif c["census_reaches_known"] and c["known_reaches_census"]:
            relation = "MUTUAL (cycle?!)"
        else:
            relation = "INDEPENDENT branches"

        print(f"  {c['peak']:>4}  {c['census_center']:>12}  "
              f"{c['known_center']:>12}  {c2k:>14}  {k2c:>14}  "
              f"{relation:<30}")


def print_part_c(best_centers: list[dict]):
    """Таблица лучших центров Part C."""
    sep = "=" * 100
    print(f"\n{sep}")
    print("  Part C: Best Center per Peak (via trajectory merging)")
    print(sep)
    print(f"  {'Peak':>4}  {'BestCenter':>22}  {'Bits':>4}  "
          f"{'MergeHits':>9}  {'SampleSize':>10}  "
          f"{'MatchCensus':>12}  {'MatchKnown':>11}")
    print(f"  {'----':>4}  {'----------':>22}  {'----':>4}  "
          f"{'--------':>9}  {'----------':>10}  "
          f"{'-----------':>12}  {'----------':>11}")

    for r in best_centers:
        c_str = str(r["best_center"]) if r["best_center"] else "—"
        if len(c_str) > 20:
            c_str = c_str[:18] + ".."
        bits = str(r["best_bits"]) if r["best_bits"] else "—"
        mh = str(r["merge_hits"]) if r["merge_hits"] else "—"
        ss = str(r["sample_size"])

        match_c = "YES" if r.get("matches_census") else "no"
        match_k = "YES" if r.get("matches_known") else "no"
        if r["best_center"] is None:
            match_c = "—"
            match_k = "—"

        print(f"  {r['peak']:>4}  {c_str:>22}  {bits:>4}  "
              f"{mh:>9}  {ss:>10}  {match_c:>12}  {match_k:>11}")


def print_part_d(results: list[dict]):
    """Таблица Part D."""
    sep = "=" * 100
    print(f"\n{sep}")
    print("  Part D: Extended Search — peaks 31–60")
    print(sep)
    print(f"  {'Peak':>4}  {'Center':>22}  {'Bits':>4}  {'HitN':>5}  "
          f"{'HitRate':>7}  {'Status':<10}  {'Samples':>7}  Notes")
    print(f"  {'----':>4}  {'------':>22}  {'----':>4}  {'----':>5}  "
          f"{'-------':>7}  {'------':<10}  {'-------':>7}  -----")

    for r in sorted(results, key=lambda x: x["peak"]):
        c_str = r.get("center") or "—"
        if isinstance(c_str, str) and len(c_str) > 20:
            c_str = c_str[:18] + ".."
        bits = str(r.get("center_bits") or "—")
        hit_n = str(r.get("hit_nodes", "—"))
        hr = f"{r['hit_rate']:.1%}" if r.get("hit_rate", 0) > 0 else "—"
        status = r.get("status", "NONE")
        samples = str(r.get("sample_size", 0))
        notes = r.get("notes", "")

        print(f"  {r['peak']:>4}  {c_str:>22}  {bits:>4}  {hit_n:>5}  "
              f"{hr:>7}  {status:<10}  {samples:>7}  {notes}")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Verify census confluence centers via reverse tree"
    )
    parser.add_argument("--peaks", type=int, nargs="+", default=None,
                        help="Конкретные peaks для верификации (Part A-C)")
    parser.add_argument("--extended", action="store_true", default=False,
                        help="Включить Part D (peaks 31-60)")
    parser.add_argument("--no-extended", action="store_true", default=False,
                        help="Отключить Part D")
    parser.add_argument("--peak-lo", type=int, default=31,
                        help="Нижняя граница для extended (default: 31)")
    parser.add_argument("--peak-hi", type=int, default=60,
                        help="Верхняя граница для extended (default: 60)")
    parser.add_argument("--workers", type=int, default=0,
                        help="Число worker-процессов (0=auto)")
    parser.add_argument("--output-json", type=str,
                        default="verify_census_results.json")
    args = parser.parse_args()

    n_workers = (args.workers if args.workers > 0
                 else max(1, os.cpu_count() - 1))
    run_extended = args.extended or not args.no_extended

    # Если --peaks задан, работаем только с ними
    if args.peaks:
        target_peaks = set(args.peaks)
    else:
        target_peaks = set(CENSUS_CENTERS.keys()) | set(KNOWN_CENTERS.keys())

    print(f"\n{'=' * 100}")
    print(f"  Verify Census Centers — Reverse Tree Verification")
    print(f"  Peaks: {sorted(target_peaks)}, workers: {n_workers}")
    print(f"{'=' * 100}")

    all_results = {}
    t_global = time.time()

    # ===========================================================
    # Part A: Верификация каждого центра через обратное дерево
    # ===========================================================
    print(f"\n  --- Part A: Building reverse trees (depth={REVERSE_DEPTH}) ---")

    verify_tasks = []
    for peak in sorted(target_peaks):
        if peak in CENSUS_CENTERS:
            verify_tasks.append(
                (CENSUS_CENTERS[peak], peak, "census")
            )
        if peak in KNOWN_CENTERS:
            verify_tasks.append(
                (KNOWN_CENTERS[peak], peak, "known")
            )

    part_a_results = []
    done = 0
    total = len(verify_tasks)

    with multiprocessing.Pool(n_workers) as pool:
        for r in pool.imap_unordered(_worker_verify_pair, verify_tasks):
            done += 1
            print(f"  [{done}/{total}] peak={r['peak']:>3} "
                  f"{r['label']:<8} → {r['status']:<10} "
                  f"hit={r['hit_nodes']}/{r['target_nodes']} "
                  f"({r['hit_rate']:.1%})  [{r['elapsed']:.0f}s]")
            part_a_results.append(r)

    print_part_a(part_a_results)
    all_results["part_a"] = part_a_results

    # ===========================================================
    # Part B: Сравнение census vs known
    # ===========================================================
    print(f"\n  --- Part B: Comparing census vs known centers ---")
    comparisons = compare_census_vs_known()
    print_part_b(comparisons)
    all_results["part_b"] = [
        {k: (str(v) if isinstance(v, int) and v > 10**15 else v)
         for k, v in c.items()}
        for c in comparisons
    ]

    # ===========================================================
    # Part C: Лучший центр для каждого peak
    # ===========================================================
    print(f"\n  --- Part C: Finding best center per peak ---")

    part_c_results = []
    for peak in sorted(target_peaks):
        # Собираем числа с данным peak из обратных деревьев Part A
        numbers_with_peak = []

        # Берём узлы из ВСЕХ деревьев для данного peak
        centers_for_peak = []
        if peak in CENSUS_CENTERS:
            centers_for_peak.append(CENSUS_CENTERS[peak])
        if peak in KNOWN_CENTERS:
            centers_for_peak.append(KNOWN_CENTERS[peak])

        for center in centers_for_peak:
            max_bits = peak + 15
            layers = build_reverse_tree(center, depth=5, a_max=A_MAX,
                                        max_bits=max_bits)
            for lay in layers:
                for n in lay:
                    if n.bit_length() < peak:
                        pb, _, conv = collatz_peak(n, max_steps=MAX_STEPS)
                        if pb == peak:
                            numbers_with_peak.append(n)

        # Убираем дубли
        numbers_with_peak = list(set(numbers_with_peak))

        best_center, merge_hits, sample_size = find_best_center(
            numbers_with_peak, peak, max_point_bits=min(80, peak + 5)
        )

        entry = {
            "peak": peak,
            "best_center": best_center,
            "best_bits": best_center.bit_length() if best_center else None,
            "merge_hits": merge_hits,
            "sample_size": len(numbers_with_peak),
            "matches_census": (best_center == CENSUS_CENTERS.get(peak)),
            "matches_known": (best_center == KNOWN_CENTERS.get(peak)),
        }
        part_c_results.append(entry)

        bc_str = str(best_center) if best_center else "—"
        match_info = ""
        if entry["matches_known"]:
            match_info = " ← matches KNOWN"
        elif entry["matches_census"]:
            match_info = " ← matches CENSUS"
        print(f"    peak={peak:>3}: best={bc_str}, "
              f"merge_hits={merge_hits}/{len(numbers_with_peak)}{match_info}")

    print_part_c(part_c_results)
    all_results["part_c"] = [
        {k: (str(v) if isinstance(v, int) and abs(v) > 10**15 else v)
         for k, v in r.items()}
        for r in part_c_results
    ]

    # ===========================================================
    # Part D: Расширенный поиск peaks 31–60
    # ===========================================================
    if run_extended:
        ext_lo = args.peak_lo
        ext_hi = args.peak_hi
        print(f"\n  --- Part D: Extended search peaks {ext_lo}–{ext_hi} ---")

        ext_tasks = [(p, 42 + p) for p in range(ext_lo, ext_hi + 1)]

        part_d_results = []
        done = 0
        total_d = len(ext_tasks)

        with multiprocessing.Pool(n_workers) as pool:
            for r in pool.imap_unordered(_worker_extended_peak, ext_tasks):
                done += 1
                c_str = r.get("center") or "—"
                if isinstance(c_str, str) and len(c_str) > 15:
                    c_str = c_str[:13] + ".."
                hr = (f"{r['hit_rate']:.0%}"
                      if r.get("hit_rate", 0) > 0 else "—")
                print(f"  [{done}/{total_d}] peak={r['peak']:>3} "
                      f"→ {r['status']:<10} center={c_str} "
                      f"hr={hr}  samples={r['sample_size']}")
                part_d_results.append(r)

        print_part_d(part_d_results)
        all_results["part_d"] = part_d_results
    else:
        print(f"\n  Part D skipped (use --extended to enable)")

    # ===========================================================
    # Итоги
    # ===========================================================
    elapsed_total = time.time() - t_global

    sep = "=" * 100
    print(f"\n{sep}")
    print("  SUMMARY")
    print(sep)

    # Part A summary: для каждого peak — какой центр лучше
    peaks_seen = sorted(target_peaks)
    for peak in peaks_seen:
        a_for_peak = [r for r in part_a_results if r["peak"] == peak]
        if not a_for_peak:
            continue
        best = max(a_for_peak, key=lambda x: (x["hit_rate"], x["hit_nodes"]))
        others = [r for r in a_for_peak if r is not best]
        other_str = ""
        if others:
            o = others[0]
            other_str = (f"  (vs {o['label']}={o['center']}: "
                         f"{o['hit_rate']:.0%})")
        print(f"  peak={peak:>3}: BEST={best['label']} "
              f"center={best['center']} "
              f"hit_rate={best['hit_rate']:.1%} "
              f"inputs={best['hit_nodes']} "
              f"[{best['status']}]{other_str}")

    # Part D summary
    if run_extended and 'part_d' in all_results:
        d_confirmed = [r for r in all_results["part_d"]
                       if r["status"] in ("CONFIRMED", "CANDIDATE")]
        d_family_a = [r for r in all_results["part_d"]
                      if r["status"] == "FAMILY_A"]
        print(f"\n  Extended {args.peak_lo}–{args.peak_hi}: "
              f"{len(d_confirmed)} confirmed/candidate, "
              f"{len(d_family_a)} family_a")
        for r in sorted(d_confirmed, key=lambda x: x["peak"]):
            print(f"    peak={r['peak']}: center={r['center']}, "
                  f"hr={r['hit_rate']:.0%}, inputs={r['hit_nodes']}")

        # Ответ на вопрос: где заканчивается архипелаг?
        last_found = max((r["peak"] for r in d_confirmed), default=0)
        if last_found > 0:
            print(f"\n  Архипелаг простирается как минимум до peak={last_found}")
        else:
            print(f"\n  Архипелаг заканчивается на peak≤30 (ничего не найдено "
                  f"в {args.peak_lo}–{args.peak_hi})")

    print(f"\n  Общее время: {elapsed_total:.1f}s")
    print(sep)

    # Сохранение JSON
    # Конвертируем большие int в str для JSON
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  JSON сохранён: {args.output_json}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
