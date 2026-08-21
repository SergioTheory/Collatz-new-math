"""
targeted_search_31_50.py — Направленный поиск confluence-центров для peaks 31–50

Использует алгебраические фильтры из census:
  - center_bits ≈ 0.496 * peak + 6.47
  - c ≡ 2 (mod 3)  (92% центров)
  - c нечётное
  - v2(3c+1) == 1  (87% центров)

Для peaks 31–40: exhaustive перебор (предсказанный центр 20–26 бит)
Для peaks 41–50: sampling (27–31 бит)

Использование:
  python targeted_search_31_50.py
  python targeted_search_31_50.py --peak-lo 31 --peak-hi 40
  python targeted_search_31_50.py --peak-lo 41 --peak-hi 50 --samples 50000
"""

from __future__ import annotations

import argparse
import csv
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

TRIVIAL = frozenset({1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21})

# Алгебраическая формула для предсказания размера центра
ALPHA = 0.496
BETA = 6.47
BIT_TOLERANCE = 5  # допуск ±5 бит


# ============================================================
# Базовые функции
# ============================================================

def v2(n: int) -> int:
    if n == 0:
        return -1
    c = 0
    while n % 2 == 0:
        c += 1
        n //= 2
    return c


def passes_algebraic_filter(n: int) -> bool:
    """Алгебраические фильтры: нечётное, ≡2 mod 3, v2(3n+1)==1."""
    if n % 2 == 0:
        return False
    if n % 3 != 2:
        return False
    # v2(3n+1) == 1 фильтр (87%, не строгий — ослабим)
    return True


def odd_trajectory_to_global_peak(n: int, max_steps: int = 500_000):
    """
    Нечётные точки ДО глобального пика. НЕ останавливаемся на локальном.
    Идём до cur==1 или max_steps, записываем peak_idx.
    Возвращает (odd_before_peak, peak_bits).
    odd_before_peak — список нечётных значений ДО момента пика.
    """
    if n <= 0 or n % 2 == 0:
        return [], n.bit_length()

    cur = n
    peak_bits = cur.bit_length()
    # Полная odd-to-odd до конца, записываем все нечётные
    odd_vals = [cur]
    peak_idx = 0
    step = 0

    while cur > 1 and step < max_steps:
        cur = cur * 3 + 1
        while cur % 2 == 0:
            cur >>= 1
        step += 1
        odd_vals.append(cur)
        if cur.bit_length() > peak_bits:
            peak_bits = cur.bit_length()
            peak_idx = step

    # Возвращаем только точки ДО пика (не включая саму пиковую)
    return odd_vals[:peak_idx], peak_bits


def find_confluence(samples: list[int], peak: int,
                    max_point_bits: int = 80) -> tuple:
    """Ищет самую частую общую точку в траекториях ДО пика."""
    if len(samples) < 3:
        return None, 0, len(samples)

    counter = Counter()
    used = samples[:100]

    for n in used:
        points, _ = odd_trajectory_to_global_peak(n, max_steps=200_000)
        for p in points:
            if p != n and p not in TRIVIAL and p.bit_length() <= max_point_bits:
                counter[p] += 1

    if not counter:
        return None, 0, len(used)

    best_val, best_count = counter.most_common(1)[0]
    return best_val, best_count, len(used)


def reverse_step(x: int, a_max: int = 15, max_bits: int = 200):
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


def verify_center(center: int, target_peak: int, depth: int = 5,
                  a_max: int = 15):
    """Reverse tree verification."""
    max_bits = target_peak + 15
    visited = {center}
    frontier = {center}
    all_nodes = set()

    for d in range(depth):
        nxt = set()
        for m in frontier:
            for y in reverse_step(m, a_max=a_max, max_bits=max_bits):
                if y not in visited:
                    visited.add(y)
                    nxt.add(y)
                    all_nodes.add(y)
        frontier = nxt

    hit = 0
    total = 0
    for n in all_nodes:
        if n.bit_length() < target_peak:
            total += 1
            pb, _, conv = collatz_peak(n, max_steps=2_000_000)
            if pb == target_peak:
                hit += 1

    hr = hit / total if total > 0 else 0.0
    return hit, total, hr, len(all_nodes)


# ============================================================
# Workers
# ============================================================

def _worker_exhaustive(args):
    """Exhaustive перебор для одного peak. Модуль-уровень."""
    peak, bits_lo, bits_hi = args
    t0 = time.time()

    result = {
        "peak": peak,
        "method": "exhaustive",
        "pred_bits": round(ALPHA * peak + BETA, 1),
        "search_range": f"{bits_lo}-{bits_hi}",
        "center": None,
        "center_bits": None,
        "inputs": 0,
        "hit_rate": 0.0,
        "status": "NONE",
        "samples_found": 0,
        "total_checked": 0,
        "notes": "",
    }

    # Собираем ВСЕ числа с данным peak в диапазоне битности
    samples = []
    total_checked = 0

    for b in range(bits_lo, bits_hi + 1):
        lo = 1 << (b - 1)
        hi = 1 << b

        # Перебираем нечётные c ≡ 2 mod 3 (т.е. c ≡ 5 mod 6)
        start = lo | 1  # первое нечётное >= lo
        # Найти первое c >= start с c % 6 == 5
        r = start % 6
        if r <= 5:
            start = start + (5 - r) % 6
        if start % 2 == 0:
            start += 3
        # Теперь start ≡ 5 mod 6, нечётное
        # Шаг 6: следующее 5 mod 6

        c = start
        while c < hi:
            total_checked += 1
            pb, _, conv = collatz_peak(c, max_steps=2_000_000)
            if pb == peak and conv:
                samples.append(c)
            c += 6

    result["total_checked"] = total_checked
    result["samples_found"] = len(samples)

    if len(samples) < 3:
        result["notes"] = f"{len(samples)} samples in {total_checked} checked"
        result["elapsed"] = time.time() - t0
        return result

    # Confluence search
    max_pb = min(80, peak + 5)
    best_center, best_count, sample_size = find_confluence(
        samples, peak, max_point_bits=max_pb
    )

    if best_center is None or best_count < 2:
        result["notes"] = (f"{len(samples)} samples, no confluence, "
                           f"{total_checked} checked")
        result["elapsed"] = time.time() - t0
        return result

    # Verify
    inputs, total, hr, tree_sz = verify_center(best_center, peak)
    result["center"] = str(best_center)
    result["center_bits"] = best_center.bit_length()
    result["inputs"] = inputs
    result["hit_rate"] = hr
    result["confluence_hits"] = best_count
    result["confluence_sample"] = sample_size

    if hr >= 0.80 and inputs >= 10:
        result["status"] = "CONFIRMED"
    elif hr >= 0.50 and inputs >= 5:
        result["status"] = "CANDIDATE"
    elif hr >= 0.30 or inputs >= 2:
        result["status"] = "WEAK"

    result["elapsed"] = time.time() - t0
    return result


def _worker_sampling(args):
    """Sampling для одного peak. Модуль-уровень."""
    peak, bits_lo, bits_hi, n_samples, seed = args
    rng = random.Random(seed)
    t0 = time.time()

    result = {
        "peak": peak,
        "method": "sampling",
        "pred_bits": round(ALPHA * peak + BETA, 1),
        "search_range": f"{bits_lo}-{bits_hi}",
        "center": None,
        "center_bits": None,
        "inputs": 0,
        "hit_rate": 0.0,
        "status": "NONE",
        "samples_found": 0,
        "total_checked": 0,
        "notes": "",
    }

    samples = []
    total_checked = 0
    max_attempts = n_samples * 50  # Больше попыток т.к. фильтрация

    while total_checked < max_attempts and len(samples) < 200:
        b = rng.randint(max(3, peak // 3), peak - 1)
        n = rng.getrandbits(b) | (1 << (b - 1)) | 1
        if n < 3:
            continue
        # Фильтр mod 3
        if n % 3 != 2:
            n += (5 - n % 6) % 6  # сдвиг к ближайшему 5 mod 6
            if n.bit_length() != b:
                continue
        total_checked += 1
        pb, _, conv = collatz_peak(n, max_steps=2_000_000)
        if pb == peak and conv:
            samples.append(n)

    # Также генерируем в предсказанном диапазоне битности (фокусированно)
    attempts2 = 0
    while attempts2 < n_samples * 10 and len(samples) < 200:
        b = rng.randint(bits_lo, bits_hi)
        n = rng.getrandbits(b) | (1 << (b - 1)) | 1
        if n % 3 != 2:
            n += (5 - n % 6) % 6
            if n.bit_length() != b:
                attempts2 += 1
                continue
        attempts2 += 1
        total_checked += 1
        pb, _, conv = collatz_peak(n, max_steps=2_000_000)
        if pb == peak and conv:
            samples.append(n)

    result["total_checked"] = total_checked
    result["samples_found"] = len(samples)

    if len(samples) < 5:
        result["notes"] = f"{len(samples)} samples in {total_checked} checked"
        result["elapsed"] = time.time() - t0
        return result

    # Confluence search
    max_pb = min(80, peak + 5)
    best_center, best_count, sample_size = find_confluence(
        samples, peak, max_point_bits=max_pb
    )

    if best_center is None or best_count < 2:
        result["notes"] = (f"{len(samples)} samples, no confluence")
        result["elapsed"] = time.time() - t0
        return result

    # Verify
    inputs, total, hr, tree_sz = verify_center(best_center, peak)
    result["center"] = str(best_center)
    result["center_bits"] = best_center.bit_length()
    result["inputs"] = inputs
    result["hit_rate"] = hr
    result["confluence_hits"] = best_count
    result["confluence_sample"] = sample_size

    if hr >= 0.80 and inputs >= 10:
        result["status"] = "CONFIRMED"
    elif hr >= 0.50 and inputs >= 5:
        result["status"] = "CANDIDATE"
    elif hr >= 0.30 or inputs >= 2:
        result["status"] = "WEAK"

    result["elapsed"] = time.time() - t0
    return result


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Targeted search for confluence centers peaks 31-50"
    )
    parser.add_argument("--peak-lo", type=int, default=31)
    parser.add_argument("--peak-hi", type=int, default=50)
    parser.add_argument("--exhaustive-limit", type=int, default=40,
                        help="Peaks <= this use exhaustive (default: 40)")
    parser.add_argument("--samples", type=int, default=50000,
                        help="Sample budget per peak for sampling mode")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--output-json", type=str,
                        default="targeted_31_50.json")
    parser.add_argument("--output-csv", type=str,
                        default="targeted_31_50.csv")
    args = parser.parse_args()

    n_workers = args.workers if args.workers > 0 else max(1, os.cpu_count() - 1)
    peak_lo = args.peak_lo
    peak_hi = args.peak_hi

    sep = "=" * 100
    print(f"\n{sep}")
    print(f"  Targeted Search for Confluence Centers — peaks {peak_lo}–{peak_hi}")
    print(f"  Workers: {n_workers}, exhaustive limit: peak<={args.exhaustive_limit}")
    print(f"  Algebraic filter: c odd, c ≡ 2 (mod 3)")
    print(f"  Size prediction: bits ≈ {ALPHA}·peak + {BETA}")
    print(sep)

    # Подготовка задач
    tasks_ex = []
    tasks_samp = []

    for p in range(peak_lo, peak_hi + 1):
        pred_bits = ALPHA * p + BETA
        bits_lo = max(3, int(pred_bits) - BIT_TOLERANCE)
        bits_hi = int(pred_bits) + BIT_TOLERANCE

        if p <= args.exhaustive_limit:
            tasks_ex.append((p, bits_lo, bits_hi))
        else:
            tasks_samp.append((p, bits_lo, bits_hi, args.samples, 42 + p))

    results = []

    # Exhaustive
    if tasks_ex:
        print(f"\n  --- Exhaustive search (peaks {tasks_ex[0][0]}–"
              f"{tasks_ex[-1][0]}) ---")
        done = 0
        total = len(tasks_ex)
        with multiprocessing.Pool(n_workers) as pool:
            for r in pool.imap_unordered(_worker_exhaustive, tasks_ex):
                done += 1
                c_str = r.get("center") or "—"
                if isinstance(c_str, str) and len(c_str) > 15:
                    c_str = c_str[:13] + ".."
                hr = f"{r['hit_rate']:.0%}" if r['hit_rate'] > 0 else "—"
                print(f"  [{done}/{total}] peak={r['peak']:>3}  "
                      f"samples={r['samples_found']:>5}  "
                      f"center={c_str:<16}  hr={hr:<6}  "
                      f"{r['status']:<10}  [{r.get('elapsed',0):.0f}s]")
                results.append(r)

    # Sampling
    if tasks_samp:
        print(f"\n  --- Sampling search (peaks {tasks_samp[0][0]}–"
              f"{tasks_samp[-1][0]}) ---")
        done = 0
        total = len(tasks_samp)
        with multiprocessing.Pool(n_workers) as pool:
            for r in pool.imap_unordered(_worker_sampling, tasks_samp):
                done += 1
                c_str = r.get("center") or "—"
                if isinstance(c_str, str) and len(c_str) > 15:
                    c_str = c_str[:13] + ".."
                hr = f"{r['hit_rate']:.0%}" if r['hit_rate'] > 0 else "—"
                print(f"  [{done}/{total}] peak={r['peak']:>3}  "
                      f"samples={r['samples_found']:>5}  "
                      f"center={c_str:<16}  hr={hr:<6}  "
                      f"{r['status']:<10}  [{r.get('elapsed',0):.0f}s]")
                results.append(r)

    # Сортируем по peak
    results.sort(key=lambda x: x["peak"])

    # Итоговая таблица
    print(f"\n{sep}")
    print(f"  RESULTS")
    print(sep)
    print(f"  {'Peak':>4}  {'PredBits':>8}  {'Method':<10}  "
          f"{'Center':>18}  {'Bits':>4}  {'Inputs':>6}  "
          f"{'HitRate':>7}  {'Status':<10}  {'Samples':>7}")
    print(f"  {'----':>4}  {'--------':>8}  {'------':<10}  "
          f"{'------':>18}  {'----':>4}  {'------':>6}  "
          f"{'-------':>7}  {'------':<10}  {'-------':>7}")

    confirmed = 0
    candidate = 0
    weak = 0

    for r in results:
        c_str = r.get("center") or "—"
        if isinstance(c_str, str) and len(c_str) > 16:
            c_str = c_str[:14] + ".."
        bits = str(r.get("center_bits") or "—")
        inp = str(r.get("inputs") or "—")
        hr = f"{r['hit_rate']:.1%}" if r['hit_rate'] > 0 else "—"
        status = r["status"]

        print(f"  {r['peak']:>4}  {r['pred_bits']:>8}  "
              f"{r['method']:<10}  {c_str:>18}  {bits:>4}  "
              f"{inp:>6}  {hr:>7}  {status:<10}  "
              f"{r['samples_found']:>7}")

        if status == "CONFIRMED":
            confirmed += 1
        elif status == "CANDIDATE":
            candidate += 1
        elif status == "WEAK":
            weak += 1

    none_count = len(results) - confirmed - candidate - weak
    print(f"\n  ИТОГО: {confirmed} confirmed, {candidate} candidates, "
          f"{weak} weak, {none_count} none")
    print(sep)

    # JSON
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump({"metadata": {"peaks": [peak_lo, peak_hi],
                                "date": time.strftime("%Y-%m-%d %H:%M:%S")},
                   "results": results}, f, indent=2, default=str)
    print(f"\n  JSON: {args.output_json}")

    # CSV
    fields = ["peak", "method", "pred_bits", "center", "center_bits",
              "inputs", "hit_rate", "status", "samples_found",
              "total_checked", "notes"]
    with open(args.output_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in results:
            row = dict(r)
            row["hit_rate"] = f"{r['hit_rate']:.4f}" if r['hit_rate'] else ""
            w.writerow(row)
    print(f"  CSV:  {args.output_csv}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
