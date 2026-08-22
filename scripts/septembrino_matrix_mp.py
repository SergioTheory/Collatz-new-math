#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
septembrino_matrix_mp.py — Генерация матрицы делителей Коллатца
Формула Septembrino: N = k · 3^m - 1
Анализ shift-векторов и распределения делителей (2^a)
"""

import os
import csv
import json
from multiprocessing import Pool, cpu_count
from functools import partial
from datetime import datetime
from typing import List, Dict, Tuple

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================
CONFIG = {
    'K_MIN': 1,
    'K_MAX': 2000,
    'K_STEP': 2,              # Только нечётные k
    'M_MIN': 0,
    'M_MAX': 60,
    'MAX_STEPS': 500,         # Максимум шагов Коллатца
    'MAX_DIVISORS': 100,      # Максимум делителей на траекторию
    'MIN_DIVISOR': 32,        # Минимальный делитель для вывода (2^5)
    'OUTPUT_DIR': os.path.dirname(os.path.abspath(__file__)),
    'CSV_FILE': 'septembrino_raw_data.csv',
    'SUMMARY_FILE': 'septembrino_summary.json',
}

# ============================================================================
# ЯДРО: СИМУЛЯЦИЯ КОЛЛАТЦА
# ============================================================================

def count_trailing_zeros(n: int) -> int:
    """Безопасный подсчёт количества нулей в конце (valuation v2(n))"""
    if n == 0:
        return 0
    count = 0
    while n & 1 == 0:
        n >>= 1
        count += 1
    return count

def get_shift_vector(n: int, max_steps: int = CONFIG['MAX_STEPS']) -> List[int]:
    """
    Извлечение shift-вектора из траектории Коллатца.
    Возвращает список a_k где x_{k+1} = (3·x_k + 1) / 2^{a_k}
    """
    shifts = []
    current = n
    steps = 0
    
    while current > 1 and steps < max_steps:
        if current & 1:  # Нечётное
            current = 3 * current + 1
            a = count_trailing_zeros(current)
            current >>= a
            shifts.append(a)
        else:  # Чётное
            a = count_trailing_zeros(current)
            current >>= a
            shifts.append(a)
        
        steps += 1
        
        if len(shifts) >= CONFIG['MAX_DIVISORS']:
            break
    
    return shifts

def shifts_to_divisors(shifts: List[int]) -> List[int]:
    """Конвертация shift-вектора в делители (2^a)"""
    return [2 ** s for s in shifts]

def filter_divisors(divisors: List[int], min_div: int = CONFIG['MIN_DIVISOR']) -> List[int]:
    """Фильтрация: оставляем только делители >= min_div"""
    return [d for d in divisors if d >= min_div]

# ============================================================================
# ФОРМУЛА SEPTEMBRINO
# ============================================================================

def generate_k_sequence(k: int, m_min: int = CONFIG['M_MIN'], 
                        m_max: int = CONFIG['M_MAX']) -> List[Dict]:
    """
    Генерация чисел по формуле Septembrino: N = k · 3^m - 1
    Для каждого m вычисляется траектория и shift-вектор
    """
    results = []
    
    for m in range(m_min, m_max + 1):
        N = k * (3 ** m) - 1
        if N <= 0:
            continue
            
        bits = N.bit_length()
        shifts = get_shift_vector(N)
        divisors = shifts_to_divisors(shifts)
        divisors_filtered = filter_divisors(divisors)
        
        # Статистика
        d = len(shifts)  # Число нечётных шагов
        S = sum(shifts)  # Сумма сдвигов
        S_d = S / d if d > 0 else 0
        
        # Распределение делителей
        divisor_counts = {}
        for div in divisors:
            divisor_counts[div] = divisor_counts.get(div, 0) + 1
        
        results.append({
            'k': k,
            'm': m,
            'N': N,
            'bits': bits,
            'shifts': shifts,
            'divisors': divisors,
            'divisors_filtered': divisors_filtered,
            'd': d,
            'S': S,
            'S_d': round(S_d, 4),
            'divisor_counts': divisor_counts,
            'k_mod_16': k % 16,
            'k_mod_32': k % 32,
            'residue_class': k % 32,
        })
    
    return results

# ============================================================================
# MULTIPROCESSING
# ============================================================================

def process_k_value(k: int, config: dict = CONFIG) -> List[Dict]:
    """Воркер для обработки одного значения k"""
    try:
        results = generate_k_sequence(
            k, 
            m_min=config['M_MIN'], 
            m_max=config['M_MAX']
        )
        return results
    except Exception as e:
        print(f"ERROR k={k}: {e}")
        return []

def run_multiprocessing():
    """Запуск параллельной обработки всех k"""
    k_values = list(range(CONFIG['K_MIN'], CONFIG['K_MAX'] + 1, CONFIG['K_STEP']))
    num_cores = cpu_count()
    num_workers = min(num_cores, len(k_values))
    
    print(f"=" * 80)
    print(f"Septembrino Matrix Generator")
    print(f"=" * 80)
    print(f"K range: {CONFIG['K_MIN']} to {CONFIG['K_MAX']} (step {CONFIG['K_STEP']})")
    print(f"M range: {CONFIG['M_MIN']} to {CONFIG['M_MAX']}")
    print(f"Total K values: {len(k_values)}")
    print(f"CPU cores: {num_cores}, Workers: {num_workers}")
    print(f"Output dir: {CONFIG['OUTPUT_DIR']}")
    print(f"=" * 80)
    print()
    
    all_results = []
    start_time = datetime.now()
    
    with Pool(processes=num_workers) as pool:
        worker_func = partial(process_k_value, config=CONFIG)
        
        for idx, result in enumerate(pool.imap(worker_func, k_values)):
            all_results.extend(result)
            if (idx + 1) % 10 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = (idx + 1) / elapsed if elapsed > 0 else 0
                print(f"✓ Completed k={k_values[idx]} ({idx+1}/{len(k_values)}) - {rate:.1f} k/sec")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print()
    print(f"=" * 80)
    print(f"Generation complete: {len(all_results)} trajectories in {elapsed:.1f}s")
    print(f"=" * 80)
    
    return all_results, k_values

# ============================================================================
# ВЫВОД ДАННЫХ
# ============================================================================

def save_to_csv(results: List[Dict], filename: str):
    """Сохранение основных данных в CSV"""
    filepath = os.path.join(CONFIG['OUTPUT_DIR'], filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'k', 'm', 'N', 'bits', 'd', 'S', 'S_d', 
            'k_mod_16', 'k_mod_32', 'residue_class',
            'divisors_str', 'max_divisor', 'high_divisors_count'
        ])
        
        for r in results:
            divisors_str = ' '.join(map(str, r['divisors_filtered']))
            max_div = max(r['divisors']) if r['divisors'] else 0
            high_div_count = sum(1 for d in r['divisors'] if d >= 4096)
            
            writer.writerow([
                r['k'], r['m'], r['N'], r['bits'], r['d'], r['S'], r['S_d'],
                r['k_mod_16'], r['k_mod_32'], r['residue_class'],
                divisors_str, max_div, high_div_count
            ])
    
    print(f"✓ Saved CSV: {filepath}")

def save_divisor_tables(results: List[Dict], k_values: List[int]):
    """Сохранение таблиц делителей по residue classes"""
    filepath = os.path.join(CONFIG['OUTPUT_DIR'], 'septembrino_divisor_tables.txt')
    
    # Группировка по residue class
    by_class = {}
    for r in results:
        rc = r['residue_class']
        if rc not in by_class:
            by_class[rc] = []
        by_class[rc].append(r)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("SEPTembrino DIVISOR TABLES\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"K range: {CONFIG['K_MIN']} to {CONFIG['K_MAX']}, M: {CONFIG['M_MIN']} to {CONFIG['M_MAX']}\n")
        f.write(f"Showing divisors >= {CONFIG['MIN_DIVISOR']}\n")
        f.write("=" * 120 + "\n\n")
        
        for rc in sorted(by_class.keys()):
            class_data = by_class[rc]
            f.write(f"\nResidue Class: k ≡ {rc} (mod 32)\n")
            f.write(f"Total entries: {len(class_data)}\n")
            f.write("-" * 120 + "\n")
            f.write(f"{'k':>6} | {'m':>3} | {'bits':>5} | {'d':>4} | {'S':>5} | {'S/d':>6} | Divisors (>= 32)\n")
            f.write("-" * 120 + "\n")
            
            for r in class_data[:100]:  # Первые 100 для каждого класса
                div_str = ' '.join(map(str, r['divisors_filtered'][:20]))
                f.write(f"{r['k']:>6} | {r['m']:>3} | {r['bits']:>5} | {r['d']:>4} | {r['S']:>5} | {r['S_d']:>6.3f} | {div_str}\n")
            
            if len(class_data) > 100:
                f.write(f"... and {len(class_data) - 100} more entries\n")
            
            f.write("\n")
    
    print(f"✓ Saved divisor tables: {filepath}")

def save_summary(results: List[Dict], k_values: List[int]):
    """Сохранение сводной статистики"""
    filepath = os.path.join(CONFIG['OUTPUT_DIR'], CONFIG['SUMMARY_FILE'])
    
    # Статистика по residue classes
    by_class = {}
    for r in results:
        rc = r['residue_class']
        if rc not in by_class:
            by_class[rc] = {'count': 0, 'total_divisors': 0, 'max_divisor': 0, 'high_divisors': 0}
        by_class[rc]['count'] += 1
        by_class[rc]['total_divisors'] += len(r['divisors'])
        by_class[rc]['max_divisor'] = max(by_class[rc]['max_divisor'], max(r['divisors']) if r['divisors'] else 0)
        by_class[rc]['high_divisors'] += sum(1 for d in r['divisors'] if d >= 4096)
    
    # Распределение делителей
    all_divisors = []
    for r in results:
        all_divisors.extend(r['divisors'])
    
    divisor_dist = {}
    for d in all_divisors:
        divisor_dist[d] = divisor_dist.get(d, 0) + 1
    
    summary = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'config': CONFIG,
        'total_trajectories': len(results),
        'total_k_values': len(k_values),
        'total_divisors': len(all_divisors),
        'divisor_distribution': divisor_dist,
        'by_residue_class': by_class,
        'avg_S_d': sum(r['S_d'] for r in results) / len(results) if results else 0,
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved summary: {filepath}")
    
    # Печать краткой статистики
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total trajectories: {len(results)}")
    print(f"Total divisors analyzed: {len(all_divisors)}")
    print(f"Average S/d: {summary['avg_S_d']:.4f}")
    print("\nDivisor distribution (top 10):")
    sorted_dist = sorted(divisor_dist.items(), key=lambda x: x[1], reverse=True)[:10]
    for div, count in sorted_dist:
        pct = 100 * count / len(all_divisors)
        print(f"  {div:>6}: {count:>7} ({pct:5.2f}%)")
    print("=" * 80)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Создаем директорию если нет
    os.makedirs(CONFIG['OUTPUT_DIR'], exist_ok=True)
    
    # Генерация данных
    results, k_values = run_multiprocessing()
    
    # Сохранение
    save_to_csv(results, CONFIG['CSV_FILE'])
    save_divisor_tables(results, k_values)
    save_summary(results, k_values)
    
    print("\n✓ All done! Check output files in:", CONFIG['OUTPUT_DIR'])