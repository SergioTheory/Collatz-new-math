#!/usr/bin/env python3
"""
scan_class_a_centers.py
Сканирует диапазон нечётных k для поиска кандидатов в Class A центры.

Критерии Class A (из Collatz_v5.docx, раздел 9.3):
  - S/d ≈ 1.33 (медленный набор gain, нетривиальный shift-вектор)
  - d_peak >> 10 (длинный путь до пика)
  - ratio > 1.585 (существенно выше Family A baseline)
  - Shift-профиль: ~70% единиц, ~25% двоек, ~5% троек+
  - Примечание: hit_rate = 100% проверяется отдельно через reverse_tree.py

Запуск:
    python scan_class_a_centers.py
"""

import csv
import time
from multiprocessing import Pool, cpu_count
from typing import Dict, List

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================
K_START = 1
K_END = 10000
MAX_STEPS = 5000          # Достаточно для достижения пика в этом диапазоне
MIN_RATIO = 1.60          # Выше Family A (1.585)
MIN_S_D = 1.25            # Близко к Zone 2 / Class A (~1.33)
MIN_D = 50                # d_peak >> 10
MIN_PCT_1 = 0.65          # ~70% единиц
MIN_PCT_2 = 0.20          # ~25% двоек
OUTPUT_FILE = "class_a_candidates.csv"

# ============================================================================
# ЯДРО: Ускоренная динамика + анализ
# ============================================================================
def get_trajectory_metrics(n: int, max_steps: int = MAX_STEPS) -> Dict:
    """
    Ускоренная траектория по нечётным числам.
    Возвращает метрики: d, S, peak, shift_vector, ratios.
    """
    x = n
    d = 0
    S = 0
    peak = n
    shifts = []

    for _ in range(max_steps):
        if x == 1:
            break
        val = 3 * x + 1
        # Подсчёт a_k = v2(3x+1)
        a = 0
        temp = val
        while temp % 2 == 0:
            temp //= 2
            a += 1
            
        shifts.append(a)
        S += a
        d += 1
        x = temp
        if x > peak:
            peak = x

    if d == 0:
        return None

    input_bits = n.bit_length()
    peak_bits = peak.bit_length()
    ratio = peak_bits / input_bits
    s_d = S / d

    # Профиль сдвигов
    pct_1 = shifts.count(1) / d
    pct_2 = shifts.count(2) / d
    pct_3plus = 1.0 - pct_1 - pct_2

    # Флаг Class A кандидата
    is_class_a = (
        ratio > MIN_RATIO and
        s_d > MIN_S_D and
        d > MIN_D and
        pct_1 > MIN_PCT_1 and
        pct_2 > MIN_PCT_2
    )

    return {
        'k': n,
        'input_bits': input_bits,
        'peak_bits': peak_bits,
        'ratio': round(ratio, 4),
        'd': d,
        'S': S,
        'S_d': round(s_d, 4),
        'pct_1': round(pct_1, 3),
        'pct_2': round(pct_2, 3),
        'pct_3plus': round(pct_3plus, 3),
        'is_class_a': is_class_a
    }

# ============================================================================
# ПАРАЛЛЕЛЬНАЯ ОБРАБОТКА
# ============================================================================
def worker_chunk(k_list: List[int]) -> List[Dict]:
    """Обработка чанка чисел. Возвращает только Class A кандидатов."""
    candidates = []
    for k in k_list:
        res = get_trajectory_metrics(k)
        if res and res['is_class_a']:
            candidates.append(res)
    return candidates

# ============================================================================
# ГЛАВНЫЙ ЗАПУСК
# ============================================================================
def main():
    print("="*70)
    print("СКАНИРОВАНИЕ CLASS A ЦЕНТРОВ")
    print(f"Диапазон: k = {K_START}..{K_END} (нечётные)")
    print(f"Критерии: ratio > {MIN_RATIO}, S/d > {MIN_S_D}, d > {MIN_D}")
    print(f"Shift-профиль: 1s > {MIN_PCT_1}, 2s > {MIN_PCT_2}")
    print("="*70)

    # Подготовка чанков
    k_values = list(range(K_START, K_END + 1, 2))
    num_cores = min(cpu_count(), len(k_values))
    chunk_size = max(1, len(k_values) // num_cores)
    chunks = [k_values[i:i + chunk_size] for i in range(0, len(k_values), chunk_size)]

    start_time = time.time()
    all_candidates = []

    print(f"\n⚡ Запуск на {num_cores} ядрах...")
    with Pool(processes=num_cores) as pool:
        for chunk_res in pool.imap_unordered(worker_chunk, chunks):
            all_candidates.extend(chunk_res)

    elapsed = time.time() - start_time

    # Сортировка по ratio (убывание)
    all_candidates.sort(key=lambda x: x['ratio'], reverse=True)

    print(f"\n✅ Сканирование завершено за {elapsed:.2f} сек.")
    print(f"🎯 Найдено Class A кандидатов: {len(all_candidates)}")

    if all_candidates:
        print("\n📊 ТОП-10 кандидатов:")
        print(f"{'k':>8} | {'bits':>5} | {'peak':>5} | {'ratio':>6} | {'d':>4} | {'S/d':>5} | {'1s':>4} | {'2s':>4} | {'3+':>4}")
        print("-"*70)
        for c in all_candidates[:10]:
            print(f"{c['k']:>8} | {c['input_bits']:>5} | {c['peak_bits']:>5} | {c['ratio']:>6} | {c['d']:>4} | {c['S_d']:>5} | {c['pct_1']:>4} | {c['pct_2']:>4} | {c['pct_3plus']:>4}")

        # Сохранение в CSV
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_candidates[0].keys())
            writer.writeheader()
            writer.writerows(all_candidates)
        print(f"\n💾 Все кандидаты сохранены в {OUTPUT_FILE}")
        print("📌 Примечание: hit_rate = 100% требует верификации через reverse_tree.py")
    else:
        print("\n⚠️ Кандидатов не найдено. Попробуйте:")
        print("   - Расширить диапазон (K_END)")
        print("   - Смягчить критерии (MIN_RATIO, MIN_S_D, MIN_D)")

if __name__ == '__main__':
    main()