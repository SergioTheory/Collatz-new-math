#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
find_class_a_candidates.py — Поиск кандидатов в Class A confluence-центры

Ищет числа, удовлетворяющие критериям Class A (Zone 2-подобных центров):
  - Hit rate близок к 100% (например, > 95%)
  - S/d до пика близок к 1.33-1.35 (как у x* и 121)
  - d_peak (число шагов до пика) велико (например, > 50)
  - bits/peak низка (например, < 0.60)

Метод:
  1. Генерирует кандидатов через targeted sampling или перебор в узком диапазоне
  2. Для каждого кандидата вычисляет траекторию до глобального пика
  3. Проверяет метрики на соответствие Class A
  4. Сохраняет кандидатов с высоким score

Использование:
  python find_class_a_candidates.py --peak-lo 46 --peak-hi 50
  python find_class_a_candidates.py --range-bits 28 32 --samples 10000
  python find_class_a_candidates.py --seed-center 20152090995747160937051
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
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# Добавить путь к crt_solver.py
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from crt_solver import collatz_peak
except ImportError:
    print("Ошибка: не найден файл crt_solver.py в текущей директории.")
    print("Убедитесь, что скрипт запускается из папки dist.")
    sys.exit(1)

# Константы
LOG2_3 = math.log2(3)
TARGET_S_OVER_D = 1.333  # Целевое значение S/d для Class A
TARGET_HIT_RATE = 0.95
MIN_D_PEAK = 50
MAX_BITS_OVER_PEAK = 0.60
MIN_CANDIDATE_BITS = 20
MAX_CANDIDATE_BITS = 60


def trajectory_to_global_peak(n: int, max_steps: int = 2_000_000):
    """
    Полная odd-to-odd траектория. Возвращает параметры до глобального пика.
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

    d_peak = peak_idx
    S_peak = sum(shifts[:peak_idx]) if peak_idx > 0 else 0
    S_over_d = S_peak / d_peak if d_peak > 0 else 0

    return {
        "odd_values": odd_values,
        "shifts": shifts,
        "peak_bits": peak_bits,
        "peak_idx": peak_idx,
        "d_peak": d_peak,
        "S_peak": S_peak,
        "S_over_d": S_over_d,
        "d_total": len(shifts),
        "S_total": sum(shifts),
    }


def passes_mod_filter(n: int) -> bool:
    """Фильтр: n нечётное и n ≡ 2 (mod 3)"""
    return n % 2 == 1 and n % 3 == 2


def analyze_candidate(args):
    """
    Анализ одного кандидата.
    Возвращает словарь с метриками или None если не прошёл фильтры.
    """
    n, target_peak, max_samples_per_peak, max_attempts_factor = args
    t0 = time.time()

    try:
        pb, _, conv = collatz_peak(n, max_steps=2_000_000)
        if not conv or pb != target_peak:
            return None

        tr = trajectory_to_global_peak(n)
        center_bits = n.bit_length()
        hit_rate = 1.0  # Текущий кандидат сам по себе даёт 1 hit
        
        # Проверить минимальные требования к кандидату
        if tr["d_peak"] < MIN_D_PEAK:
            return None
        if tr["S_over_d"] < 1.25 or tr["S_over_d"] > 1.45:
            return None
        if center_bits / target_peak > MAX_BITS_OVER_PEAK:
            return None

        # Теперь нужно проверить confluence: найти другие числа с тем же пиком
        # и посмотреть, сколько из них сливается в одну точку
        # Это дорогостоящая операция, поэтому делаем выборку
        
        samples_with_same_peak = [n]
        attempts = 0
        max_attempts = max_attempts_factor * max_samples_per_peak  # например, 1000
        
        # Сгенерировать соседние кандидаты в том же диапазоне
        base_bits = center_bits
        lo = 1 << (base_bits - 1)
        hi = 1 << base_bits
        checked = 0
        
        while len(samples_with_same_peak) < max_samples_per_peak and attempts < max_attempts:
            attempts += 1
            # Случайное число в диапазоне битности
            candidate_n = random.randint(lo, hi - 1)
            if candidate_n % 2 == 0:
                continue
            if not passes_mod_filter(candidate_n):
                continue
                
            checked += 1
            pb2, _, conv2 = collatz_peak(candidate_n, max_steps=2_000_000)
            if conv2 and pb2 == target_peak:
                samples_with_same_peak.append(candidate_n)

        if len(samples_with_same_peak) < 5:  # Слишком мало для анализа
            return None

        # Найти точку слияния (confluence point)
        # Собираем все промежуточные нечётные значения для каждого числа
        all_intermediates = {}
        for num in samples_with_same_peak:
            tr_temp = trajectory_to_global_peak(num)
            intermediates = set(tr_temp["odd_values"])
            all_intermediates[num] = intermediates

        # Найти самые частые промежуточные точки (исключая числа из samples_with_same_peak)
        counter = Counter()
        for num, ints in all_intermediates.items():
            for val in ints:
                if val in samples_with_same_peak:
                    continue
                if val.bit_length() > target_peak + 5:  # Не выше пика + буфер
                    continue
                counter[val] += 1

        if not counter:
            return None

        best_confluence_val, best_count = counter.most_common(1)[0]
        hit_rate = best_count / len(samples_with_same_peak)

        # Финальная проверка метрик для Class A
        tr_final = trajectory_to_global_peak(best_confluence_val)
        d_peak_final = tr_final["d_peak"]
        S_over_d_final = tr_final["S_over_d"]
        bits_over_peak = best_confluence_val.bit_length() / target_peak

        # Score для сортировки кандидатов
        score = 0.0
        if hit_rate >= TARGET_HIT_RATE:
            score += 1000
        score += hit_rate * 100  # 0.95 -> 95, 1.0 -> 100
        score += (0.02 - abs(S_over_d_final - TARGET_S_OVER_D)) * 1000  # Штраф за отклонение S/d
        score -= (bits_over_peak / MAX_BITS_OVER_PEAK) * 10  # Штраф за некомпактность
        score += (d_peak_final / MIN_D_PEAK)  # Бонус за большее d_peak

        if score < 950:  # Порог для отсева
            return None

        elapsed = time.time() - t0
        return {
            "candidate_center": n,
            "confluence_center": best_confluence_val,
            "center_bits": best_confluence_val.bit_length(),
            "target_peak": target_peak,
            "hit_rate": hit_rate,
            "d_peak": d_peak_final,
            "S_peak": tr_final["S_peak"],
            "S_over_d": S_over_d_final,
            "bits_over_peak": bits_over_peak,
            "score": score,
            "samples_checked": checked,
            "time_per_candidate": elapsed
        }

    except Exception:
        return None


def generate_candidates_by_range(min_bits: int, max_bits: int, count: int) -> list:
    """Генерирует count случайных чисел в диапазоне битности с мод фильтром."""
    candidates = []
    for _ in range(count):
        bits = random.randint(min_bits, max_bits)
        lo = 1 << (bits - 1)
        hi = 1 << bits
        while True:
            n = random.randint(lo, hi - 1)
            if n % 2 == 1 and passes_mod_filter(n):
                candidates.append(n)
                break
    return candidates


def main():
    parser = argparse.ArgumentParser(description="Поиск кандидатов в Class A confluence-центры")
    parser.add_argument("--peak-lo", type=int, default=46, help="Минимальный пик для поиска")
    parser.add_argument("--peak-hi", type=int, default=60, help="Максимальный пик для поиска")
    parser.add_argument("--range-bits", nargs=2, type=int, metavar=("MIN", "MAX"), 
                        help="Диапазон битности для генерации кандидатов")
    parser.add_argument("--samples", type=int, default=10000, help="Число кандидатов для проверки на пик")
    parser.add_argument("--workers", type=int, default=12, help="Число воркеров")
    parser.add_argument("--output-json", type=str, default="class_a_candidates.json", help="Файл вывода JSON")
    
    args = parser.parse_args()

    print("=" * 80)
    print("  Find Class A Candidates")
    print(f"  Peaks: {args.peak_lo} – {args.peak_hi}")
    if args.range_bits:
        print(f"  Candidate bits: {args.range_bits[0]} – {args.range_bits[1]}")
    print(f"  Samples per peak: {args.samples}")
    print(f"  Workers: {args.workers}")
    print("=" * 80)

    all_candidates = []
    peaks_to_check = list(range(args.peak_lo, args.peak_hi + 1))

    for peak in peaks_to_check:
        print(f"\n  Обработка пика {peak}...")
        
        # Определить диапазон битности для кандидатов
        # Используем формулу из наших исследований: center_bits ≈ 0.496 * peak + 6.47
        expected_center_bits = int(0.496 * peak + 6.47)
        min_bits = max(MIN_CANDIDATE_BITS, expected_center_bits - 5)
        max_bits = min(MAX_CANDIDATE_BITS, expected_center_bits + 5)
        
        if args.range_bits:
            min_bits, max_bits = args.range_bits

        print(f"    Генерация {args.samples} кандидатов ({min_bits}-{max_bits} бит)...")
        candidates_for_peak = generate_candidates_by_range(min_bits, max_bits, args.samples)

        tasks = [(c, peak, 50, 20) for c in candidates_for_peak]  # 50 samples, 20x attempts

        peak_candidates = []
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(analyze_candidate, task): task[0] for task in tasks}
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 500 == 0:
                    print(f"      Проверено {completed}/{len(tasks)} кандидатов...")

                result = future.result()
                if result is not None:
                    peak_candidates.append(result)

        peak_candidates.sort(key=lambda x: x["score"], reverse=True)
        print(f"    Найдено {len(peak_candidates)} кандидатов для пика {peak}")

        for cand in peak_candidates:
            all_candidates.append(cand)

    all_candidates.sort(key=lambda x: x["score"], reverse=True)

    print("\n" + "=" * 80)
    print("  РЕЗУЛЬТАТЫ")
    print("=" * 80)
    print(f"  {'Peak':<4} {'Center':<20} {'Bits':<4} {'HR':<6} {'S/d':<6} {'b/p':<5} {'Score':<8} {'Time(s)':<8}")
    print("-" * 80)
    for cand in all_candidates[:20]:  # Показать топ-20
        c_str = str(cand["confluence_center"])
        if len(c_str) > 18:
            c_str = c_str[:16] + ".."
        print(f"  {cand['target_peak']:<4} {c_str:<20} {cand['center_bits']:<4} "
              f"{cand['hit_rate']:<6.3f} {cand['S_over_d']:<6.3f} {cand['bits_over_peak']:<5.3f} "
              f"{cand['score']:<8.1f} {cand['time_per_candidate']:<8.3f}")

    # Сохранить JSON
    output_data = {
        "metadata": {
            "peaks_searched": [args.peak_lo, args.peak_hi],
            "samples_per_peak": args.samples,
            "workers": args.workers,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_candidates_checked": args.samples * len(peaks_to_check),
            "total_candidates_found": len(all_candidates)
        },
        "candidates": all_candidates
    }

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n  JSON сохранён: {args.output_json}")
    print(f"  Всего кандидатов: {len(all_candidates)}")
    print("=" * 80)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
