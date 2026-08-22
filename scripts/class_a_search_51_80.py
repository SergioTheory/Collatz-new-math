"""
class_a_search_51_80.py — Поиск Class A confluence-центров для peaks 51–80

Двухфазная стратегия:
  Фаза 1: Найти центр (exhaustive для 51-55, sampling для 56-80)
  Фаза 2: Классифицировать (d_peak, S/d, hit_rate → Class A или B)

Class A критерии: hit_rate=100%, d_peak >> 50, S/d ≈ 1.33

Использование:
  python class_a_search_51_80.py
  python class_a_search_51_80.py --peak-lo 51 --peak-hi 55 --mode exhaustive
  python class_a_search_51_80.py --peak-lo 56 --peak-hi 80 --mode sampling --samples 500000
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

# Формула размера центра (обновлённая на 32 точках)
ALPHA = 0.498
BETA = 6.29
BIT_TOLERANCE = 3


# ============================================================
# Инлайн fast_peak — пик по ПОЛНОЙ траектории (стандарт Collatz)
# Пик = max bit_length на ПОЛНОЙ траектории включая чётные шаги
# ============================================================

def _fast_peak(n: int, max_steps: int = 2_000_000) -> int:
    """Peak bit-length по полной траектории. Инлайн для скорости."""
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
# Odd-to-odd trajectory до ГЛОБАЛЬНОГО пика (полная, до cur=1)
# ============================================================

def trajectory_to_global_peak(n: int, max_steps: int = 2_000_000):
    """
    Полная odd-to-odd траектория. НЕ останавливается на локальном снижении.
    Идёт до cur==1 или max_steps.
    Возвращает dict с d_peak, S_peak, shifts, peak_bits, d_total, S_total.
    """
    cur = n
    if cur % 2 == 0:
        while cur % 2 == 0:
            cur >>= 1

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
        step += 1

        if nxt.bit_length() > peak_bits:
            peak_bits = nxt.bit_length()
            peak_idx = step

        cur = nxt

    d_peak = peak_idx
    S_peak = sum(shifts[:peak_idx]) if peak_idx > 0 else 0
    shifts_to_peak = shifts[:peak_idx] if peak_idx > 0 else []

    # Shift profile
    d = d_peak if d_peak > 0 else 1
    frac_1 = shifts_to_peak.count(1) / d if shifts_to_peak else 0
    frac_2 = shifts_to_peak.count(2) / d if shifts_to_peak else 0
    frac_ge3 = sum(1 for a in shifts_to_peak if a >= 3) / d if shifts_to_peak else 0

    return {
        "d_peak": d_peak,
        "S_peak": S_peak,
        "S_over_d": S_peak / d_peak if d_peak > 0 else 0,
        "d_total": len(shifts),
        "S_total": sum(shifts),
        "peak_bits": peak_bits,
        "frac_1": frac_1,
        "frac_2": frac_2,
        "frac_ge3": frac_ge3,
    }


# ============================================================
# Confluence + reverse tree
# ============================================================

def odd_trajectory_before_peak(n: int, max_steps: int = 500_000):
    """Нечётные точки ДО глобального пика (полная odd-to-odd до cur=1)."""
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
    """Самая частая общая нечётная точка в траекториях ДО пика."""
    if len(samples) < 3:
        return None, 0, len(samples)

    counter = Counter()
    used = samples[:150]

    for n in used:
        points, _ = odd_trajectory_before_peak(n, max_steps=200_000)
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
    """Reverse tree verification. Возвращает (inputs, total, hit_rate, tree_size)."""
    max_bits = target_peak + 10
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
# Classify center
# ============================================================

def classify_center(center: int, peak: int):
    """Полная классификация: trajectory + reverse tree → Class A/B."""
    t0 = time.time()

    # Trajectory
    tr = trajectory_to_global_peak(center)

    # Reverse tree
    inputs, total, hr, tree_sz = verify_center(center, peak)

    # Classification
    if hr >= 0.99 and tr["d_peak"] > 50 and tr["S_over_d"] < 1.50:
        cls = "CLASS_A"
    elif hr >= 0.80 and inputs >= 10:
        cls = "CONFIRMED_B"
    elif hr >= 0.50 and inputs >= 5:
        cls = "CANDIDATE_B"
    elif hr >= 0.30 or inputs >= 2:
        cls = "WEAK"
    else:
        cls = "NONE"

    return {
        "peak": peak,
        "center": str(center),
        "center_bits": center.bit_length(),
        "inputs": inputs,
        "total_in_range": total,
        "hit_rate": hr,
        "d_peak": tr["d_peak"],
        "S_peak": tr["S_peak"],
        "S_over_d": tr["S_over_d"],
        "d_total": tr["d_total"],
        "frac_1": tr["frac_1"],
        "frac_2": tr["frac_2"],
        "frac_ge3": tr["frac_ge3"],
        "cls": cls,
        "elapsed": time.time() - t0,
    }


# ============================================================
# Workers — exhaustive
# ============================================================

def _worker_exhaust_chunk(args):
    """Перебирает чанк c ≡ 5 mod 6 для одного target peak."""
    chunk_lo, chunk_hi, target_peak = args

    # Выровнять к c ≡ 5 mod 6
    r = chunk_lo % 6
    start = chunk_lo + (5 - r) % 6
    if start < chunk_lo:
        start += 6

    hits = []
    checked = 0
    c = start
    while c < chunk_hi:
        checked += 1
        pb = _fast_peak(c, max_steps=2_000_000)
        if pb == target_peak:
            hits.append(c)
        c += 6

    return hits, checked


def run_exhaustive(peak: int, bits_lo: int, bits_hi: int,
                   n_workers: int):
    """Exhaustive перебор для одного peak."""
    full_lo = 1 << (bits_lo - 1)
    full_hi = 1 << bits_hi

    total_range = full_hi - full_lo
    n_chunks = max(n_workers * 4, 16)
    chunk_size = total_range // n_chunks + 1

    chunks = []
    pos = full_lo
    while pos < full_hi:
        end = min(pos + chunk_size, full_hi)
        chunks.append((pos, end, peak))
        pos = end

    all_hits = []
    total_checked = 0

    with multiprocessing.Pool(n_workers) as pool:
        for hits, checked in pool.imap_unordered(
                _worker_exhaust_chunk, chunks):
            all_hits.extend(hits)
            total_checked += checked

    return all_hits, total_checked


# ============================================================
# Workers — sampling
# ============================================================

def _worker_sample_chunk(args):
    """Генерирует случайных кандидатов c ≡ 5 mod 6, проверяет peak."""
    chunk_id, n_candidates, target_peak, bits_lo, bits_hi, seed = args
    rng = random.Random(seed)
    hits = []
    checked = 0

    for _ in range(n_candidates):
        b = rng.randint(bits_lo, bits_hi)
        n = rng.getrandbits(b) | (1 << (b - 1)) | 1
        # Подгоняем к ≡ 5 mod 6
        r = n % 6
        if r != 5:
            n += (5 - r) % 6
        if n.bit_length() != b:
            continue

        checked += 1
        pb = _fast_peak(n, max_steps=2_000_000)
        if pb == target_peak:
            hits.append(n)

    return hits, checked


def run_sampling(peak: int, bits_lo: int, bits_hi: int,
                 total_samples: int, n_workers: int):
    """Sampling поиск для одного peak."""
    # Также пробуем расширенный диапазон битностей
    ext_bits_lo = max(3, peak // 3)
    ext_bits_hi = peak - 1

    n_chunks = n_workers * 2
    per_chunk = total_samples // n_chunks + 1

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
                _worker_sample_chunk, chunks):
            all_hits.extend(hits)
            total_checked += checked

    return all_hits, total_checked


# ============================================================
# Process one peak (full pipeline)
# ============================================================

def process_peak(peak: int, mode: str, n_workers: int,
                 n_samples: int = 500_000):
    """Полный пайплайн для одного peak: search → confluence → classify."""
    t0 = time.time()
    pred_bits = ALPHA * peak + BETA
    bits_lo = max(3, int(pred_bits) - BIT_TOLERANCE)
    bits_hi = int(pred_bits) + BIT_TOLERANCE + 1

    result = {
        "peak": peak,
        "method": mode,
        "pred_bits": round(pred_bits, 1),
        "center": None,
        "center_bits": None,
        "inputs": 0,
        "hit_rate": 0.0,
        "d_peak": 0,
        "S_over_d": 0.0,
        "cls": "NONE",
        "samples_found": 0,
        "total_checked": 0,
        "notes": "",
    }

    # Фаза 1: Найти числа с данным peak
    if mode == "exhaustive":
        hits, total_checked = run_exhaustive(peak, bits_lo, bits_hi, n_workers)
    else:
        hits, total_checked = run_sampling(peak, bits_lo, bits_hi,
                                           n_samples, n_workers)
        # Если мало — добавить попытки
        if len(hits) < 10 and n_samples < 2_000_000:
            hits2, tc2 = run_sampling(peak, bits_lo, bits_hi,
                                       1_000_000, n_workers)
            hits.extend(hits2)
            total_checked += tc2

    result["samples_found"] = len(hits)
    result["total_checked"] = total_checked

    if len(hits) < 5:
        result["notes"] = f"{len(hits)} hits in {total_checked} checked"
        result["elapsed"] = time.time() - t0
        return result

    # Фаза 1b: Confluence search
    max_pb = min(80, peak + 5)
    best_center, best_count, sample_size = find_confluence(
        hits, peak, max_point_bits=max_pb
    )

    if best_center is None or best_count < 2:
        result["notes"] = f"{len(hits)} hits, no confluence"
        result["elapsed"] = time.time() - t0
        return result

    # Фаза 2: Classify
    cr = classify_center(best_center, peak)

    result["center"] = cr["center"]
    result["center_bits"] = cr["center_bits"]
    result["inputs"] = cr["inputs"]
    result["hit_rate"] = cr["hit_rate"]
    result["d_peak"] = cr["d_peak"]
    result["S_peak"] = cr.get("S_peak", 0)
    result["S_over_d"] = cr["S_over_d"]
    result["d_total"] = cr.get("d_total", 0)
    result["frac_1"] = cr.get("frac_1", 0)
    result["frac_2"] = cr.get("frac_2", 0)
    result["frac_ge3"] = cr.get("frac_ge3", 0)
    result["cls"] = cr["cls"]
    result["confluence_hits"] = best_count
    result["confluence_sample"] = sample_size
    result["elapsed"] = time.time() - t0

    return result


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Class A search for confluence centers peaks 51-80"
    )
    parser.add_argument("--peak-lo", type=int, default=51)
    parser.add_argument("--peak-hi", type=int, default=80)
    parser.add_argument("--mode", choices=["exhaustive", "sampling", "auto"],
                        default="auto",
                        help="auto: exhaustive 51-55, sampling 56-80")
    parser.add_argument("--samples", type=int, default=500_000,
                        help="Samples per peak in sampling mode")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--bit-window", type=int, default=None,
                        help="Override BIT_TOLERANCE (default: 3)")
    parser.add_argument("--output-json", type=str,
                        default="class_a_search_51_80.json")
    parser.add_argument("--output-csv", type=str,
                        default="class_a_search_51_80.csv")
    args = parser.parse_args()

    # Override global BIT_TOLERANCE if --bit-window given
    global BIT_TOLERANCE
    if args.bit_window is not None:
        BIT_TOLERANCE = args.bit_window

    n_workers = args.workers if args.workers > 0 else max(1, os.cpu_count() - 1)
    peak_lo = args.peak_lo
    peak_hi = args.peak_hi

    sep = "=" * 115
    print(f"\n{sep}")
    print(f"  Class A Search — peaks {peak_lo}–{peak_hi}")
    print(f"  Workers: {n_workers}, mode: {args.mode}, samples: {args.samples}")
    print(f"  Bit window: ±{BIT_TOLERANCE} from prediction")
    print(f"  Size prediction: bits ≈ {ALPHA}·peak + {BETA}")
    print(sep)

    results = []

    for p in range(peak_lo, peak_hi + 1):
        # Determine mode
        if args.mode == "auto":
            mode = "exhaustive" if p <= 55 else "sampling"
        else:
            mode = args.mode

        pred_bits = ALPHA * p + BETA
        bits_lo = max(3, int(pred_bits) - BIT_TOLERANCE)
        bits_hi = int(pred_bits) + BIT_TOLERANCE + 1

        if mode == "exhaustive":
            est = (1 << bits_hi) - (1 << (bits_lo - 1))
            est_filtered = est // 6
            print(f"\n  peak={p}: pred={pred_bits:.1f}b, "
                  f"exhaustive {bits_lo}-{bits_hi}b (~{est_filtered:,} cands)")
        else:
            print(f"\n  peak={p}: pred={pred_bits:.1f}b, "
                  f"sampling {args.samples:,} cands")

        r = process_peak(p, mode, n_workers, args.samples)

        c_str = r.get("center") or "—"
        if isinstance(c_str, str) and len(c_str) > 15:
            c_str = c_str[:13] + ".."
        hr = f"{r['hit_rate']:.0%}" if r['hit_rate'] > 0 else "—"
        cls = r.get("cls", "NONE")
        sd = f"{r['S_over_d']:.3f}" if r['S_over_d'] > 0 else "—"
        dp = r.get("d_peak", 0)

        star = " *** CLASS A CANDIDATE! ***" if cls == "CLASS_A" else ""
        print(f"  -> samples={r['samples_found']}, center={c_str}, "
              f"hr={hr}, d_peak={dp}, S/d={sd}, {cls} "
              f"[{r.get('elapsed', 0):.0f}s]{star}")

        results.append(r)

    # Итоговая таблица
    print(f"\n{sep}")
    print(f"  RESULTS — peaks {peak_lo}–{peak_hi}")
    print(sep)
    print(f"  {'Peak':>4}  {'Method':<9}  {'Center':>16}  {'Bits':>4}  "
          f"{'Inp':>5}  {'HR':>6}  {'d_pk':>5}  {'S/d':>6}  "
          f"{'%1':>5}  {'%2':>5}  {'Cls':<13}  {'Time':>5}")
    print(f"  {'----':>4}  {'------':<9}  {'------':>16}  {'----':>4}  "
          f"{'---':>5}  {'--':>6}  {'----':>5}  {'---':>6}  "
          f"{'--':>5}  {'--':>5}  {'---':<13}  {'----':>5}")

    class_a_list = []

    for r in results:
        c_str = r.get("center") or "—"
        if isinstance(c_str, str) and len(c_str) > 14:
            c_str = c_str[:12] + ".."
        bits = str(r.get("center_bits") or "—")
        inp = str(r.get("inputs") or "—")
        hr = f"{r['hit_rate']:.1%}" if r['hit_rate'] > 0 else "—"
        dp = str(r.get("d_peak") or "—")
        sd = f"{r['S_over_d']:.3f}" if r.get('S_over_d', 0) > 0 else "—"
        f1 = f"{r.get('frac_1', 0):.1%}" if r.get('frac_1', 0) > 0 else "—"
        f2 = f"{r.get('frac_2', 0):.1%}" if r.get('frac_2', 0) > 0 else "—"
        cls = r.get("cls", "NONE")
        elapsed = f"{r.get('elapsed', 0):.0f}s"

        marker = " *" if cls == "CLASS_A" else ""
        print(f"  {r['peak']:>4}  {r['method']:<9}  {c_str:>16}  "
              f"{bits:>4}  {inp:>5}  {hr:>6}  {dp:>5}  {sd:>6}  "
              f"{f1:>5}  {f2:>5}  {cls:<13}  {elapsed:>5}{marker}")

        if cls == "CLASS_A":
            class_a_list.append(r)

    # Class A summary
    print(f"\n{sep}")
    if class_a_list:
        print(f"  CLASS A CANDIDATES FOUND: {len(class_a_list)}")
        for r in class_a_list:
            print(f"    peak={r['peak']}: center={r['center']}, "
                  f"d_peak={r['d_peak']}, S/d={r['S_over_d']:.4f}, "
                  f"hit_rate={r['hit_rate']:.1%}")
    else:
        print(f"  No Class A candidates found in peaks {peak_lo}–{peak_hi}")
        print(f"  All centers are Class B (hit_rate < 100%)")

    # Trend: d_peak vs peak
    with_centers = [r for r in results if r.get("d_peak", 0) > 0]
    if with_centers:
        print(f"\n  TREND: d_peak vs peak")
        for r in with_centers:
            bar = "#" * min(r["d_peak"], 80)
            print(f"    peak={r['peak']:>3}: d_peak={r['d_peak']:>5}  "
                  f"S/d={r['S_over_d']:.3f}  {bar}")

    # Trend: S/d vs peak
    if with_centers:
        sd_vals = [r["S_over_d"] for r in with_centers]
        mean_sd = sum(sd_vals) / len(sd_vals)
        min_sd = min(sd_vals)
        max_sd = max(sd_vals)
        min_r = min(with_centers, key=lambda x: x["S_over_d"])
        print(f"\n  S/d stats: mean={mean_sd:.4f}, min={min_sd:.4f} "
              f"(peak={min_r['peak']}), max={max_sd:.4f}")
        print(f"  Closest to Class A (S/d≈1.33): peak={min_r['peak']}, "
              f"S/d={min_sd:.4f}")

    # Statistics
    confirmed = sum(1 for r in results
                    if r["cls"] in ("CONFIRMED_B", "CLASS_A"))
    candidate = sum(1 for r in results if r["cls"] == "CANDIDATE_B")
    weak = sum(1 for r in results if r["cls"] == "WEAK")
    none_c = sum(1 for r in results if r["cls"] == "NONE")
    print(f"\n  TOTALS: {confirmed} confirmed, {candidate} candidate, "
          f"{weak} weak, {none_c} none, "
          f"{len(class_a_list)} Class A")
    print(sep)

    # JSON
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump({"metadata": {
            "peaks": [peak_lo, peak_hi],
            "mode": args.mode,
            "samples": args.samples,
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, "results": results}, f, indent=2, default=str)
    print(f"\n  JSON: {args.output_json}")

    # CSV
    fields = ["peak", "method", "pred_bits", "center", "center_bits",
              "inputs", "hit_rate", "d_peak", "S_peak", "S_over_d",
              "frac_1", "frac_2", "frac_ge3", "cls",
              "samples_found", "total_checked", "notes"]
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
