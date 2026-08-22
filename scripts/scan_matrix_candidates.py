#!/usr/bin/env python3
"""
scan_matrix_candidates.py
ЭТАП 5 ПЛАНА: Сканирование матричного пространства (k, m)
Ищет N = k*3^m - 1 с инвариантами Zone 2 / Class A.

Критерии (из Отчёт_24_03_2026.docx):
  - Zone 2: d ≈ 259, S = bits + 271, S/d ∈ [1.25, 1.40], ratio > 1.6
  - Class A: confluence к x* за ≤7 шагов, d_peak > 50, ratio > 1.585
  - Мёртвая зона: 88 ≤ bits ≤ 170 → ожидается 0 аномалий (проверка гипотезы)

Запуск:
    python scan_matrix_candidates.py
"""

import csv
import time
import math
from multiprocessing import Pool, cpu_count
from typing import Dict, List, Tuple

# ============================================================================
# КОНФИГУРАЦИЯ (строго по плану и документам)
# ============================================================================
K_MAX = 10000
M_MAX = 100
MIN_BITS = 50          # Начинаем с 50 бит, чтобы захватить подход к Zone 2
MAX_BITS = 180         # Включая границу мёртвой зоны 170 бит
OUTPUT_CSV = "matrix_candidates.csv"

# Инварианты Zone 2 (из отчёта)
ZONE2_D_TARGET = 259
ZONE2_S_OFFSET = 271   # S ≈ bits + 271
ZONE2_S_D_MIN = 1.25
ZONE2_S_D_MAX = 1.40
ZONE2_RATIO_MIN = 1.60

# ============================================================================
# ЯДРО: Быстрая симуляция + метрики
# ============================================================================
def compute_metrics(N: int, max_steps: int = 500) -> Dict:
    """Возвращает метрики траектории для N = k*3^m - 1."""
    if N <= 1:
        return None
        
    x = N
    d = 0
    S = 0
    peak = N
    shifts = []
    steps = 0
    
    while x > 1 and steps < max_steps:
        if x % 2 == 0:
            a = (x & -x).bit_length() - 1
            x >>= a
        else:
            x = 3 * x + 1
            a = (x & -x).bit_length() - 1
            x >>= a
            d += 1
            S += a
            shifts.append(a)
            
        if x > peak:
            peak = x
        steps += 1
        
    if d < 20:  # Пропускаем короткие траектории
        return None
        
    bits = N.bit_length()
    peak_bits = peak.bit_length()
    ratio = peak_bits / bits
    s_d = S / d
    
    # Профиль сдвигов
    pct1 = shifts.count(1) / d
    pct2 = shifts.count(2) / d
    pct3p = 1.0 - pct1 - pct2
    
    # Классификация
    cls = "NORMAL"
    if ZONE2_S_D_MIN <= s_d <= ZONE2_S_D_MAX and ratio >= ZONE2_RATIO_MIN and abs(d - ZONE2_D_TARGET) < 30:
        cls = "ZONE2_LIKE"
    elif ratio > 1.585 and d > 50 and s_d > 1.25:
        cls = "CLASS_A_CANDIDATE"
    elif 88 <= bits <= 170 and ratio > 1.50:
        cls = "DEAD_ZONE_ANOMALY"  # Нарушение гипотезы мёртвой зоны
        
    return {
        'k': 0, 'm': 0, 'N_bits': bits, 'peak_bits': peak_bits,
        'ratio': round(ratio, 4), 'd': d, 'S': S, 'S_d': round(s_d, 4),
        'pct1': round(pct1, 3), 'pct2': round(pct2, 3), 'pct3p': round(pct3p, 3),
        'class': cls, 'shifts_preview': str(shifts[:15])
    }

# ============================================================================
# ПАРАЛЛЕЛЬНЫЙ СКАНЕР МАТРИЦЫ
# ============================================================================
def scan_chunk(chunk: List[Tuple[int, int]]) -> List[Dict]:
    """Обрабатывает чанк пар (k, m)."""
    results = []
    for k, m in chunk:
        # N = k * 3^m - 1
        N = k * pow(3, m) - 1
        bits = N.bit_length()
        
        # Фильтр по битности (ускорение)
        if bits < MIN_BITS or bits > MAX_BITS:
            continue
            
        metrics = compute_metrics(N)
        if metrics and metrics['class'] != "NORMAL":
            metrics['k'] = k
            metrics['m'] = m
            results.append(metrics)
    return results

# ============================================================================
# ГЛАВНЫЙ ЗАПУСК
# ============================================================================
def main():
    print("="*70)
    print("ЭТАП 5: СКАНИРОВАНИЕ МАТРИЧНОГО ПРОСТРАНСТВА (k, m)")
    print(f"Диапазон: k=1..{K_MAX} (нечётные), m=0..{M_MAX}")
    print(f"Битность: {MIN_BITS}..{MAX_BITS} (Zone 2: 71-87, Dead: 88-170)")
    print(f"Критерии: Zone 2 (d≈259, S/d∈[1.25,1.40], ratio>1.6)")
    print("="*70)
    
    # Генерация пар (k, m)
    pairs = []
    for k in range(1, K_MAX + 1, 2):
        for m in range(M_MAX + 1):
            pairs.append((k, m))
            
    # Чанкирование для multiprocessing
    num_cores = min(cpu_count(), len(pairs))
    chunk_size = max(1, len(pairs) // num_cores)
    chunks = [pairs[i:i + chunk_size] for i in range(0, len(pairs), chunk_size)]
    
    print(f"\n⚡ Запуск на {num_cores} ядрах ({len(pairs)} пар)...")
    start_time = time.time()
    all_candidates = []
    
    with Pool(processes=num_cores) as pool:
        for chunk_res in pool.imap_unordered(scan_chunk, chunks):
            all_candidates.extend(chunk_res)
            
    elapsed = time.time() - start_time
    
    # Сортировка: сначала Zone 2, потом Class A, потом Dead Zone
    priority = {"ZONE2_LIKE": 0, "CLASS_A_CANDIDATE": 1, "DEAD_ZONE_ANOMALY": 2}
    all_candidates.sort(key=lambda x: (priority.get(x['class'], 3), -x['ratio']))
    
    print(f"\n✅ Сканирование завершено за {elapsed:.2f} сек.")
    print(f"🎯 Найдено кандидатов: {len(all_candidates)}")
    
    if all_candidates:
        print("\n📊 ТОП-10 кандидатов:")
        print(f"{'k':>5} | {'m':>3} | {'bits':>5} | {'class':<18} | {'ratio':>6} | {'d':>4} | {'S/d':>5} | {'1s':>4} | {'2s':>4}")
        print("-"*80)
        for c in all_candidates[:10]:
            print(f"{c['k']:>5} | {c['m']:>3} | {c['N_bits']:>5} | {c['class']:<18} | {c['ratio']:>6} | {c['d']:>4} | {c['S_d']:>5} | {c['pct1']:>4} | {c['pct2']:>4}")
            
        # Сохранение
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_candidates[0].keys())
            writer.writeheader()
            writer.writerows(all_candidates)
        print(f"\n💾 Результаты: {OUTPUT_CSV}")
        
        # Статистика по классам
        from collections import Counter
        counts = Counter(c['class'] for c in all_candidates)
        print("\n📈 Распределение:")
        for cls, cnt in counts.most_common():
            print(f"   {cls:<20}: {cnt}")
            
        print("\n💡 СЛЕДУЮЩИЙ ШАГ:")
        print("   1. ZONE2_LIKE → проверить confluence к x* через reverse_tree.py")
        print("   2. DEAD_ZONE_ANOMALY → опровергает/подтверждает гипотезу 88-170 бит")
        print("   3. CLASS_A_CANDIDATE → верификация hit rate = 100%")
    else:
        print("\n⚠️ Кандидатов не найдено. Возможные причины:")
        print("   - Zone 2 структуры крайне редки (требуют точного совпадения parity)")
        print("   - Мёртвая зона 88-170 бит действительно пуста (подтверждение гипотезы)")
        print("   - Рекомендуется расширить K_MAX до 50000 или M_MAX до 150")

if __name__ == '__main__':
    main()