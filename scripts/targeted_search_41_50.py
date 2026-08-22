"""
targeted_search_41_50.py — Направленный поиск confluence-центров для peaks 41–50

Два режима:
  sampling:    50K+ кандидатов с фильтрами, быстрый (~30-60 мин)
  exhaustive:  полный перебор c ≡ 5 mod 6 в предсказанном диапазоне (~2-6 часов)

Алгебраические фильтры:
  - c нечётное, c ≡ 2 (mod 3)  →  c ≡ 5 (mod 6)
  - center_bits ≈ 0.496 * peak + 6.47 (±4 бита)
  - v2(3c+1) == 1  (быстрая проверка: (3c+1) & 3 == 2)

Использование:
  python targeted_search_41_50.py
  python targeted_search_41_50.py --mode sampling --samples 50000
  python targeted_search_41_50.py --mode exhaustive --peak-lo 41 --peak-hi 45
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

ALPHA = 0.496
BETA = 6.47
BIT_TOLERANCE = 4


# ============================================================
# Инлайн collatz_peak (быстрее для exhaustive)
# ============================================================

def _collatz_peak_fast(n: int, max_steps: int = 2_000_000) -> int:
    """Возвращает только peak_bits. Инлайн для скорости."""
    cur = n
    pb = cur.bit_length()
    s = 0
    while cur > 1 and s < max_steps:
        if cur & 1:
            cur = cur * 3 + 1
        else:
            cur >>= 1
        s += 1
        cb = cur.bit_length()
        if cb > pb:
            pb = cb
    return pb


# ============================================================
# Общие функции
# ============================================================

def odd_trajectory_to_global_peak(n: int, max_steps: int = 500_000):
    """Нечётные точки ДО глобального пика. Полная odd-to-odd до cur=1."""
    if n <= 0 or n % 2 == 0:
        return [], n.bit_length()

    cur = n
    peak_bits = cur.bit_length()
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
# Worker: exhaustive chunk
# ============================================================

def _worker_exhaustive_chunk(args):
    """
    Перебирает чанк [chunk_lo, chunk_hi) для одного target peak.
    Итерирует c ≡ 5 (mod 6), проверяет v2(3c+1)==1, считает peak.
    Возвращает список чисел с нужным peak.
    """
    chunk_lo, chunk_hi, target_peak, apply_v2_filter = args

    # Выровнять chunk_lo к первому c ≡ 5 mod 6
    r = chunk_lo % 6
    start = chunk_lo + (5 - r) % 6
    if start % 2 == 0:
        start += 3
    if start < chunk_lo:
        start += 6

    hits = []
    checked = 0

    c = start
    while c < chunk_hi:
        # Быстрый фильтр v2(3c+1)==1: (3c+1) & 3 == 2
        if apply_v2_filter and (3 * c + 1) & 3 != 2:
            c += 6
            continue

        checked += 1
        pb = _collatz_peak_fast(c, max_steps=2_000_000)
        if pb == target_peak:
            hits.append(c)

        c += 6

    return hits, checked


def _worker_exhaustive_peak(args):
    """Exhaustive перебор для одного peak, разбивая на чанки по воркерам."""
    peak, bits_lo, bits_hi, n_workers, apply_v2 = args
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

    full_lo = 1 << (bits_lo - 1)
    full_hi = 1 << bits_hi

    # Разбиваем на чанки
    total_range = full_hi - full_lo
    n_chunks = max(n_workers * 4, 16)
    chunk_size = total_range // n_chunks + 1

    chunks = []
    pos = full_lo
    while pos < full_hi:
        end = min(pos + chunk_size, full_hi)
        chunks.append((pos, end, peak, apply_v2))
        pos = end

    all_hits = []
    total_checked = 0

    with multiprocessing.Pool(n_workers) as pool:
        for hits, checked in pool.imap_unordered(
                _worker_exhaustive_chunk, chunks):
            all_hits.extend(hits)
            total_checked += checked

    result["total_checked"] = total_checked
    result["samples_found"] = len(all_hits)

    if len(all_hits) < 3:
        result["notes"] = f"{len(all_hits)} hits in {total_checked} checked"
        result["elapsed"] = time.time() - t0
        return result

    # Confluence search
    max_pb = min(80, peak + 5)
    best_center, best_count, sample_size = find_confluence(
        all_hits, peak, max_point_bits=max_pb
    )

    if best_center is None or best_count < 2:
        result["notes"] = f"{len(all_hits)} hits, no confluence"
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
# Worker: sampling
# ============================================================

def _worker_sampling_chunk(args):
    """Генерирует случайных кандидатов и возвращает те, что попали в target peak."""
    chunk_id, n_candidates, target_peak, bits_lo, bits_hi, seed = args
    rng = random.Random(seed)
    hits = []
    checked = 0

    for _ in range(n_candidates):
        b = rng.randint(bits_lo, bits_hi)
        # Генерируем c ≡ 5 mod 6 (нечётное, ≡ 2 mod 3)
        n = rng.getrandbits(b) | (1 << (b - 1)) | 1
        # Подгоняем к ≡ 5 mod 6
        r = n % 6
        if r != 5:
            n += (5 - r) % 6
        if n.bit_length() != b:
            # Переполнение битности — пропуск
            continue

        # v2 filter
        if (3 * n + 1) & 3 != 2:
            continue

        checked += 1
        pb = _collatz_peak_fast(n, max_steps=2_000_000)
        if pb == target_peak:
            hits.append(n)

    return hits, checked


def _worker_sampling_peak(args):
    """Sampling для одного peak, параллельно по чанкам."""
    peak, bits_lo, bits_hi, total_samples, n_workers = args
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

    # Также генерируем из расширенного диапазона битностей (вдруг центр далеко)
    ext_bits_lo = max(3, peak // 3)
    ext_bits_hi = peak - 1

    # Разбиваем на чанки по воркерам
    n_chunks = n_workers * 2
    per_chunk = total_samples // n_chunks + 1
    # Половина чанков в predicted range, половина в extended
    chunks = []
    for i in range(n_chunks):
        if i < n_chunks // 2:
            bl, bh = bits_lo, bits_hi
        else:
            bl, bh = ext_bits_lo, ext_bits_hi
        chunks.append((i, per_chunk, peak, bl, bh, 42 + peak * 1000 + i))

    all_hits = []
    total_checked = 0

    with multiprocessing.Pool(n_workers) as pool:
        for hits, checked in pool.imap_unordered(
                _worker_sampling_chunk, chunks):
            all_hits.extend(hits)
            total_checked += checked

    result["total_checked"] = total_checked
    result["samples_found"] = len(all_hits)

    if len(all_hits) < 5:
        result["notes"] = f"{len(all_hits)} hits in {total_checked} checked"
        result["elapsed"] = time.time() - t0
        return result

    # Confluence
    max_pb = min(80, peak + 5)
    best_center, best_count, sample_size = find_confluence(
        all_hits, peak, max_point_bits=max_pb
    )

    if best_center is None or best_count < 2:
        result["notes"] = f"{len(all_hits)} hits, no confluence"
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
        description="Targeted search for confluence centers peaks 41-50"
    )
    parser.add_argument("--mode", choices=["sampling", "exhaustive"],
                        default="sampling",
                        help="Режим поиска (default: sampling)")
    parser.add_argument("--peak-lo", type=int, default=41)
    parser.add_argument("--peak-hi", type=int, default=50)
    parser.add_argument("--samples", type=int, default=50000,
                        help="Число кандидатов на peak (sampling mode)")
    parser.add_argument("--no-v2-filter", action="store_true",
                        help="Отключить фильтр v2(3c+1)==1")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--output-json", type=str,
                        default="targeted_41_50.json")
    parser.add_argument("--output-csv", type=str,
                        default="targeted_41_50.csv")
    args = parser.parse_args()

    n_workers = args.workers if args.workers > 0 else max(1, os.cpu_count() - 1)
    peak_lo = args.peak_lo
    peak_hi = args.peak_hi
    mode = args.mode
    apply_v2 = not args.no_v2_filter

    sep = "=" * 105
    print(f"\n{sep}")
    print(f"  Targeted Search 41-50 — peaks {peak_lo}–{peak_hi}, mode={mode}")
    print(f"  Workers: {n_workers}, v2 filter: {apply_v2}")
    if mode == "sampling":
        print(f"  Samples per peak: {args.samples}")
    print(f"  Size prediction: bits ≈ {ALPHA}·peak + {BETA}")
    print(sep)

    results = []

    for p in range(peak_lo, peak_hi + 1):
        pred_bits = ALPHA * p + BETA
        bits_lo = max(3, int(pred_bits) - BIT_TOLERANCE)
        bits_hi = int(pred_bits) + BIT_TOLERANCE + 1

        range_lo = 1 << (bits_lo - 1)
        range_hi = 1 << bits_hi
        est_candidates = (range_hi - range_lo) // 6
        if apply_v2:
            est_candidates //= 2

        print(f"\n  peak={p}: pred_bits={pred_bits:.1f}, "
              f"search {bits_lo}-{bits_hi} bits, "
              f"~{est_candidates:,} candidates")

        if mode == "exhaustive":
            r = _worker_exhaustive_peak(
                (p, bits_lo, bits_hi, n_workers, apply_v2)
            )
        else:
            r = _worker_sampling_peak(
                (p, bits_lo, bits_hi, args.samples, n_workers)
            )

        c_str = r.get("center") or "—"
        if isinstance(c_str, str) and len(c_str) > 15:
            c_str = c_str[:13] + ".."
        hr = f"{r['hit_rate']:.0%}" if r['hit_rate'] > 0 else "—"
        print(f"  → samples={r['samples_found']}, checked={r['total_checked']}, "
              f"center={c_str}, hr={hr}, {r['status']} "
              f"[{r.get('elapsed', 0):.0f}s]")

        results.append(r)

    # Итоговая таблица
    print(f"\n{sep}")
    print(f"  RESULTS — peaks {peak_lo}–{peak_hi}, mode={mode}")
    print(sep)
    print(f"  {'Peak':>4}  {'PredBits':>8}  {'Method':<10}  "
          f"{'Center':>18}  {'Bits':>4}  {'Inputs':>6}  "
          f"{'HitRate':>7}  {'Status':<10}  {'Checked':>10}  "
          f"{'Samples':>7}  {'Time':>6}")
    print(f"  {'----':>4}  {'--------':>8}  {'------':<10}  "
          f"{'------':>18}  {'----':>4}  {'------':>6}  "
          f"{'-------':>7}  {'------':<10}  {'-------':>10}  "
          f"{'-------':>7}  {'----':>6}")

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
        elapsed = f"{r.get('elapsed', 0):.0f}s"

        print(f"  {r['peak']:>4}  {r['pred_bits']:>8}  "
              f"{r['method']:<10}  {c_str:>18}  {bits:>4}  "
              f"{inp:>6}  {hr:>7}  {status:<10}  "
              f"{r['total_checked']:>10}  {r['samples_found']:>7}  "
              f"{elapsed:>6}")

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
        json.dump({"metadata": {
            "peaks": [peak_lo, peak_hi],
            "mode": mode,
            "samples": args.samples if mode == "sampling" else "exhaustive",
            "v2_filter": apply_v2,
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, "results": results}, f, indent=2, default=str)
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
