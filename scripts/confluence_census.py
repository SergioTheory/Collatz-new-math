"""
confluence_census.py — Систематический поиск confluence-центров для peaks 10–200

Алгоритм:
  1. Для каждого peak P генерируем выборку чисел с collatz_peak == P
  2. Строим odd-траектории до пика, ищем общие точки (confluence)
  3. Верифицируем лучших кандидатов через обратное дерево
  4. Классифицируем: CONFIRMED / CANDIDATE / WEAK / NONE / FAMILY_A

Использование:
  python confluence_census.py
  python confluence_census.py --peak-lo 10 --peak-hi 200 --workers 8
  python confluence_census.py --peak-lo 14 --peak-hi 14   # один пик
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
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from crt_solver import collatz_peak

log23 = math.log2(3)

# Известные центры для аннотации
KNOWN_CENTERS = {
    14: 121,
    16: 6803,
    18: 27611,
    22: 61823,
    27: 5808671,
    140: 20152090995747160937051,
}

# Тривиальные точки — исключаем из кандидатов
TRIVIAL = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21}


# ============================================================
# Ускоренная odd-to-odd динамика
# ============================================================

def odd_trajectory_to_peak(n: int, max_odd_steps: int = 50000):
    """
    Возвращает список нечётных значений на траектории n ДО пика (фаза роста).
    Останавливается как только битность начинает падать после пика.
    """
    if n <= 0 or n % 2 == 0:
        return [], n.bit_length()

    trajectory = []
    cur = n
    peak_bits = cur.bit_length()
    peak_reached = False
    steps_after_peak = 0

    for _ in range(max_odd_steps):
        if cur <= 1:
            break

        if cur & 1:
            trajectory.append(cur)
            cur = cur * 3 + 1
            # cur теперь чётное, снимаем все двойки
            while cur > 0 and cur % 2 == 0:
                cur >>= 1
            cb = cur.bit_length()
            if cb > peak_bits:
                peak_bits = cb
                peak_reached = False
                steps_after_peak = 0
            else:
                if not peak_reached:
                    peak_reached = True
                steps_after_peak += 1
                # Даём несколько шагов после пика чтобы не обрезать слишком рано
                if steps_after_peak > 5:
                    break
        else:
            # Не должно случиться при odd-to-odd, но на всякий случай
            while cur > 0 and cur % 2 == 0:
                cur >>= 1

    return trajectory, peak_bits


def odd_points_before_peak(n: int, max_odd_steps: int = 50000,
                           max_point_bits: int = 80):
    """
    Возвращает set нечётных точек на траектории n строго ДО пика.
    Фильтрует по битности <= max_point_bits (центры не бывают огромными).
    Не включает само n.
    """
    if n <= 0 or n % 2 == 0:
        return set(), 0

    points = set()
    cur = n
    peak_bits = cur.bit_length()
    peak_val = cur
    # Сначала пройдём полную траекторию до пика, запоминая odd-точки
    trajectory_odd = []
    step = 0

    while cur > 1 and step < max_odd_steps:
        if cur & 1:
            nxt = cur * 3 + 1
            while nxt % 2 == 0:
                nxt >>= 1
            cb_nxt = nxt.bit_length()

            # nxt — следующая нечётная точка
            trajectory_odd.append((cur, cur.bit_length()))

            cur = nxt
            step += 1

            if cur.bit_length() > peak_bits:
                peak_bits = cur.bit_length()
        else:
            while cur % 2 == 0:
                cur >>= 1

    # Теперь отбираем точки СТРОГО до пика
    # Идём по trajectory_odd и останавливаемся когда следующая точка дала бы пик
    running_max = n.bit_length()
    for val, vbits in trajectory_odd:
        if val == n:
            continue
        if val.bit_length() <= max_point_bits and val not in TRIVIAL:
            points.add(val)
        # Проверяем, достиг ли пик уже максимума
        nxt_val = val * 3 + 1
        nxt_bits = nxt_val.bit_length()
        if nxt_bits >= peak_bits:
            break

    return points, peak_bits


# ============================================================
# Шаг 1: Генерация выборки чисел с данным peak
# ============================================================

def _find_samples_small(peak: int, max_numbers: int = 200):
    """Для малых peak (<=30): полный перебор нечётных до 2^peak."""
    samples = []
    limit = 1 << peak  # 2^peak
    # Числа с битностью >= peak уже >= 2^(peak-1), их peak >= peak
    # Перебираем нечётные от 1 до 2^peak
    for n in range(1, min(limit, 1 << 22), 2):  # до 4M для скорости
        pb, _, conv = collatz_peak(n, max_steps=500_000)
        if pb == peak and conv:
            samples.append(n)
            if len(samples) >= max_numbers:
                break
    return samples


def _find_samples_random(peak: int, rng: random.Random,
                         target_count: int = 80,
                         max_attempts: int = 300_000):
    """Для средних/больших peak: случайная выборка."""
    samples = []
    attempts = 0
    bit_lo = max(3, peak // 2 - 5)
    bit_hi = peak - 1

    while len(samples) < target_count and attempts < max_attempts:
        # Выбираем случайную битность
        b = rng.randint(bit_lo, bit_hi)
        # Генерируем случайное нечётное число с b битами
        n = rng.getrandbits(b) | (1 << (b - 1)) | 1
        if n < 3:
            attempts += 1
            continue

        pb, _, conv = collatz_peak(n, max_steps=2_000_000)
        attempts += 1

        if pb == peak and conv:
            samples.append(n)

    return samples


def _is_family_a_peak(peak: int):
    """Проверяет, является ли peak типичным Family A пиком для 2^b-1."""
    # Family A: n = 2^b - 1, peak ≈ b * log2(3) ≈ b * 1.585
    # Обратно: b ≈ peak / 1.585
    b_approx = peak / log23
    b_lo = max(2, int(b_approx) - 1)
    b_hi = int(b_approx) + 2
    for b in range(b_lo, b_hi + 1):
        n = (1 << b) - 1
        if n < 3:
            continue
        pb, _, conv = collatz_peak(n, max_steps=2_000_000)
        if pb == peak:
            return True, n
    return False, None


# ============================================================
# Шаг 2: Поиск confluence-точки
# ============================================================

def find_confluence_point(samples: list[int], peak: int,
                          max_point_bits: int = 80):
    """
    Для списка чисел с одинаковым peak находит общие точки в траекториях.
    Возвращает (best_center, hit_count, sample_size, all_candidates).
    """
    if not samples:
        return None, 0, 0, []

    point_counter = Counter()
    sample_size = min(len(samples), 100)  # Не больше 100 для скорости
    used_samples = samples[:sample_size]

    for n in used_samples:
        points, _ = odd_points_before_peak(n, max_point_bits=max_point_bits)
        for p in points:
            point_counter[p] += 1

    if not point_counter:
        return None, 0, sample_size, []

    # Сортируем по частоте, берём топ
    top = point_counter.most_common(20)

    # Фильтруем: кандидат должен быть меньше 2^peak и не тривиальный
    candidates = []
    for val, count in top:
        if val.bit_length() < peak and count >= 2:
            candidates.append((val, count))

    if not candidates:
        return None, 0, sample_size, []

    best_val, best_count = candidates[0]
    return best_val, best_count, sample_size, candidates


# ============================================================
# Шаг 3: Верификация через обратное дерево
# ============================================================

def find_predecessors(m: int, a_max: int = 15, max_bits: int = 200):
    """Предшественники m по ускоренной odd-to-odd динамике."""
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
        preds.append(n)
    return preds


def verify_center(center: int, peak: int, tree_depth: int = 5,
                  a_max: int = 15):
    """
    Строит обратное дерево от center и считает сколько предшественников
    имеют collatz_peak == peak.
    """
    max_bits = peak + 10  # Центр и предшественники не должны быть слишком большими

    # BFS обратного дерева
    visited = {center}
    frontier = {center}
    all_nodes = set()

    for d in range(tree_depth):
        next_frontier = set()
        for m in frontier:
            for n in find_predecessors(m, a_max=a_max, max_bits=max_bits):
                if n not in visited:
                    visited.add(n)
                    next_frontier.add(n)
                    all_nodes.add(n)
        frontier = next_frontier

    # Проверяем peak для всех узлов с битностью < peak
    inputs_with_peak = 0
    total_in_range = 0

    for n in all_nodes:
        if n.bit_length() < peak:
            total_in_range += 1
            pb, _, conv = collatz_peak(n, max_steps=2_000_000)
            if pb == peak:
                inputs_with_peak += 1

    hit_rate = inputs_with_peak / total_in_range if total_in_range > 0 else 0.0

    return inputs_with_peak, total_in_range, hit_rate, len(all_nodes)


# ============================================================
# Worker для multiprocessing
# ============================================================

def _process_peak(args):
    """Worker: обрабатывает один peak. Модуль-уровень для pickle."""
    peak, seed = args
    rng = random.Random(seed)
    result = {
        "peak": peak,
        "center": None,
        "center_bits": None,
        "inputs": 0,
        "hit_rate": 0.0,
        "status": "NONE",
        "sample_size": 0,
        "tree_depth": 0,
        "tree_size": 0,
        "notes": "",
        "candidates_top3": [],
    }

    t0 = time.time()

    # Проверяем Family A
    is_fa, fa_num = _is_family_a_peak(peak)

    # Шаг 1: Генерируем выборку
    if peak <= 30:
        samples = _find_samples_small(peak, max_numbers=200)
    else:
        samples = _find_samples_random(peak, rng, target_count=80,
                                       max_attempts=300_000)

    result["sample_size"] = len(samples)

    if not samples:
        if is_fa:
            result["status"] = "FAMILY_A"
            result["notes"] = f"only 2^{round(peak/log23)}-1"
        else:
            result["notes"] = "no samples found"
        return result

    # Если только 1-2 числа и все = 2^b-1 → Family A
    if len(samples) <= 2 and is_fa:
        all_fa = all(s == (1 << s.bit_length()) - 1 for s in samples)
        if all_fa:
            result["status"] = "FAMILY_A"
            result["notes"] = f"only 2^{samples[0].bit_length()}-1"
            return result

    # Шаг 2: Поиск confluence
    max_point_bits = min(80, peak + 5)
    best_center, hit_count, sample_size, candidates = find_confluence_point(
        samples, peak, max_point_bits=max_point_bits
    )

    if candidates:
        result["candidates_top3"] = [
            {"value": str(v), "bits": v.bit_length(), "hits": c}
            for v, c in candidates[:3]
        ]

    if best_center is None or hit_count < 2:
        # Нет confluence
        if is_fa and len(samples) <= 5:
            result["status"] = "FAMILY_A"
            result["notes"] = f"Family A vicinity, {len(samples)} samples"
        else:
            result["notes"] = (f"{len(samples)} samples, no confluence"
                               if samples else "no samples")
        return result

    confluence_rate = hit_count / sample_size
    result["center"] = str(best_center)
    result["center_bits"] = best_center.bit_length()

    # Шаг 3: Верификация через обратное дерево (если confluence_rate >= 20%)
    if confluence_rate >= 0.20 and best_center.bit_length() <= 80:
        depth = 6 if peak <= 50 else 5
        inputs, total, hr, tree_sz = verify_center(
            best_center, peak, tree_depth=depth, a_max=15
        )
        result["inputs"] = inputs
        result["hit_rate"] = hr
        result["tree_depth"] = depth
        result["tree_size"] = tree_sz
    else:
        result["inputs"] = hit_count
        result["hit_rate"] = confluence_rate
        result["notes"] += f"sampling only ({confluence_rate:.0%})"

    # Шаг 4: Классификация
    hr = result["hit_rate"]
    inp = result["inputs"]

    if hr >= 0.80 and inp >= 10:
        result["status"] = "CONFIRMED"
    elif hr >= 0.50 and inp >= 5:
        result["status"] = "CANDIDATE"
    elif hr >= 0.30 or (inp >= 2 and hr >= 0.20):
        result["status"] = "WEAK"
    elif is_fa and len(samples) <= 5:
        result["status"] = "FAMILY_A"
        result["notes"] = f"Family A, {len(samples)} samples"
    else:
        result["status"] = "NONE"

    # Аннотации для известных центров
    if peak in KNOWN_CENTERS:
        known = KNOWN_CENTERS[peak]
        if best_center == known:
            result["notes"] = "known center"
        else:
            result["notes"] += f" (known: {known})"

    elapsed = time.time() - t0
    if elapsed > 30:
        result["notes"] += f" [{elapsed:.0f}s]"

    return result


# ============================================================
# Вывод результатов
# ============================================================

def print_results(results: list[dict], peak_lo: int, peak_hi: int):
    """Красивая таблица в консоль."""
    sep = "=" * 90
    print(f"\n{sep}")
    print(f"  Confluence Census — систематический поиск центров для "
          f"peaks {peak_lo}–{peak_hi}")
    print(sep)
    print()
    print(f"  {'Peak':>5}  {'Center':>22}  {'Bits':>4}  {'Inputs':>6}  "
          f"{'HitRate':>7}  {'Status':<10}  Notes")
    print(f"  {'----':>5}  {'------':>22}  {'----':>4}  {'------':>6}  "
          f"{'-------':>7}  {'------':<10}  -----")

    confirmed = 0
    candidate = 0
    weak = 0
    none_count = 0
    family_a = 0

    for r in results:
        peak = r["peak"]
        center = r["center"] if r["center"] else "—"
        if isinstance(center, str) and len(center) > 20:
            center = center[:18] + ".."
        bits = str(r["center_bits"]) if r["center_bits"] else "—"
        inputs = str(r["inputs"]) if r["inputs"] else "—"
        hr = f"{r['hit_rate']:.0%}" if r["hit_rate"] > 0 else "—"
        status = r["status"]
        notes = r.get("notes", "")

        print(f"  {peak:>5}  {center:>22}  {bits:>4}  {inputs:>6}  "
              f"{hr:>7}  {status:<10}  {notes}")

        if status == "CONFIRMED":
            confirmed += 1
        elif status == "CANDIDATE":
            candidate += 1
        elif status == "WEAK":
            weak += 1
        elif status == "FAMILY_A":
            family_a += 1
        else:
            none_count += 1

    print()
    print(sep)
    print(f"  ИТОГО: {confirmed} confirmed, {candidate} candidates, "
          f"{weak} weak, {family_a} family_a, {none_count} none")
    print(sep)


def save_json(results: list[dict], peak_lo: int, peak_hi: int,
              filepath: str):
    """Сохраняет результаты в JSON."""
    data = {
        "metadata": {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "peaks_range": [peak_lo, peak_hi],
            "method": "random_sampling + reverse_tree",
            "total_peaks": len(results),
        },
        "results": results,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON сохранён: {filepath}")


def save_csv(results: list[dict], filepath: str):
    """Сохраняет результаты в CSV."""
    fields = ["peak", "center", "center_bits", "inputs", "hit_rate",
              "status", "sample_size", "tree_depth", "tree_size", "notes"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            row = dict(r)
            row["hit_rate"] = f"{r['hit_rate']:.4f}" if r["hit_rate"] else ""
            writer.writerow(row)
    print(f"  CSV сохранён:  {filepath}")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Confluence Census — поиск центров для peaks 10-200"
    )
    parser.add_argument("--peak-lo", type=int, default=10,
                        help="Нижняя граница диапазона peak (default: 10)")
    parser.add_argument("--peak-hi", type=int, default=200,
                        help="Верхняя граница диапазона peak (default: 200)")
    parser.add_argument("--workers", type=int, default=0,
                        help="Число worker-процессов (0 = auto)")
    parser.add_argument("--output-json", type=str,
                        default="confluence_census.json",
                        help="Путь к JSON-файлу")
    parser.add_argument("--output-csv", type=str,
                        default="confluence_census.csv",
                        help="Путь к CSV-файлу")
    parser.add_argument("--sequential", action="store_true",
                        help="Запуск без multiprocessing (для отладки)")
    args = parser.parse_args()

    peak_lo = args.peak_lo
    peak_hi = args.peak_hi
    n_workers = args.workers if args.workers > 0 else max(1, os.cpu_count() - 1)

    print(f"\n{'=' * 90}")
    print(f"  Confluence Census")
    print(f"  Peaks: {peak_lo}–{peak_hi}, workers: {n_workers}")
    print(f"{'=' * 90}\n")

    # Подготавливаем задачи: (peak, seed)
    base_seed = 42
    tasks = [(p, base_seed + p) for p in range(peak_lo, peak_hi + 1)]

    t_start = time.time()

    if args.sequential:
        results = []
        for i, task in enumerate(tasks):
            p = task[0]
            print(f"  [{i+1}/{len(tasks)}] Processing peak={p}...",
                  end="", flush=True)
            r = _process_peak(task)
            print(f"  → {r['status']}"
                  f"{'  center=' + str(r['center']) if r['center'] else ''}")
            results.append(r)
    else:
        # Parallel
        results = []
        done = 0
        total = len(tasks)
        with multiprocessing.Pool(n_workers) as pool:
            for r in pool.imap_unordered(_process_peak, tasks):
                done += 1
                status_str = r["status"]
                c_str = (f"center={r['center']}" if r["center"]
                         else "")
                print(f"  [{done}/{total}] peak={r['peak']:>3}  "
                      f"{status_str:<10}  {c_str}")
                results.append(r)

    # Сортируем по peak
    results.sort(key=lambda x: x["peak"])

    elapsed = time.time() - t_start
    print(f"\n  Время: {elapsed:.1f}s")

    # Вывод
    print_results(results, peak_lo, peak_hi)

    # Сохранение
    save_json(results, peak_lo, peak_hi, args.output_json)
    save_csv(results, args.output_csv)

    # Анализ: есть ли центры между peak=27 и peak=140?
    gap_centers = [r for r in results
                   if 27 < r["peak"] < 140
                   and r["status"] in ("CONFIRMED", "CANDIDATE")]
    print(f"\n  Центры в разрыве peak 28–139: {len(gap_centers)}")
    for r in gap_centers:
        print(f"    peak={r['peak']}, center={r['center']}, "
              f"hit_rate={r['hit_rate']:.0%}, status={r['status']}")

    # Тренд: размер центра vs peak
    with_centers = [r for r in results if r["center_bits"] and r["center_bits"] > 0]
    if len(with_centers) >= 3:
        print(f"\n  Тренд center_bits vs peak:")
        for r in with_centers[:15]:
            bar = "#" * r["center_bits"]
            print(f"    peak={r['peak']:>3}, center_bits={r['center_bits']:>3}  {bar}")
        if len(with_centers) > 15:
            print(f"    ... и ещё {len(with_centers) - 15}")

    print(f"\n{'=' * 90}")
    print(f"  Готово.")
    print(f"{'=' * 90}\n")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
