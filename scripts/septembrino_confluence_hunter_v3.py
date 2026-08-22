#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
septembrino_confluence_hunter_v3.py
РАСШИРЕННЫЙ ПОИСК ZONE 2

Изменения v3:
- K_MAX = 10000 (было 2000)
- M_MAX = 100 (было 60)
- Ожидаемая битность: до ~175 бит (покрывает Zone 2: 71-87, Dead Zone: 88-170)
- Оптимизированная проверка confluence (кэширование центров)

Авторы: Collatz Crystal Hunter Team
Дата: 2 апреля 2026
Версия: 3.0 (Zone 2 search)
"""

import multiprocessing as mp
from multiprocessing import Pool, cpu_count
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import json
import time
from pathlib import Path
from datetime import datetime
import csv
import sys

# ──────────────────────────────────────────────────────────────────────────
# КОНФИГУРАЦИЯ (РАСШИРЕННАЯ!)
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class Config:
    # Диапазоны Septembrino (РАСШИРЕНО!)
    K_MIN: int = 1
    K_MAX: int = 10000         # ⬆️ Было 2000
    M_MIN: int = 0
    M_MAX: int = 100           # ⬆️ Было 60
    
    # Параметры траектории
    MAX_STEPS: int = 5000
    MAX_DIVISORS: int = 100
    
    # Фильтры Zone 2
    SD_TARGET: float = 1.33
    SD_TOLERANCE: float = 0.08
    
    # Диапазоны битности
    DEAD_ZONE_MIN: int = 88
    DEAD_ZONE_MAX: int = 170
    ZONE2_MIN: int = 71
    ZONE2_MAX: int = 87
    
    # Целевые пики
    TARGET_PEAKS: List[int] = field(default_factory=lambda: [140, 233, 240, 280, 483])
    
    # Confluence центры (из Collatz_v5.docx)
    CONFLUENCE_CENTERS: Dict[int, int] = field(default_factory=lambda: {
        14: 121,
        140: 20152090995747160937051,  # x*
        32: 1242665,
        35: 26658983,
        37: 67625867,
        41: 37748015,
        50: 1396693151
    })
    
    # Вывод
    OUTPUT_DIR: Path = Path("septembrino_results_v3")
    SAVE_INTERVAL: int = 1000

config = Config()

# ──────────────────────────────────────────────────────────────────────────
# ЯДРО: ДИНАМИКА КОЛЛАТЦА
# ──────────────────────────────────────────────────────────────────────────

def count_trailing_zeros(n: int) -> int:
    if n == 0:
        return 0
    return (n & -n).bit_length() - 1

def collatz_peak(n: int, max_steps: int = 5000) -> Tuple[int, int, int, List[int]]:
    if n <= 1:
        return (n.bit_length(), 0, 0, [])
    
    current = n
    peak = n
    peak_bits = n.bit_length()
    shifts = []
    d = 0
    S = 0
    steps = 0
    
    while current > 1 and steps < max_steps:
        if current & 1:
            current = 3 * current + 1
            a = count_trailing_zeros(current)
            current >>= a
            shifts.append(a)
            S += a
            d += 1
        else:
            a = count_trailing_zeros(current)
            current >>= a
            shifts.append(a)
            S += a
        
        if current.bit_length() > peak_bits:
            peak_bits = current.bit_length()
            peak = current
        
        steps += 1
    
    return (peak_bits, d, S, shifts)

def generate_septembrino_number(k: int, m: int) -> int:
    return k * (3 ** m) - 1

def analyze_trajectory(k: int, m: int, confluence_centers: Dict[int, int]) -> Optional[Dict]:
    N = generate_septembrino_number(k, m)
    if N <= 0:
        return None
    
    bits = N.bit_length()
    peak_bits, d, S, shifts = collatz_peak(N, max_steps=config.MAX_STEPS)
    
    if d == 0:
        return None
    
    ratio = peak_bits / bits if bits > 0 else 0.0
    s_d_ratio = S / d if d > 0 else 0.0
    
    pct_1 = shifts.count(1) / len(shifts) if shifts else 0.0
    pct_2 = shifts.count(2) / len(shifts) if shifts else 0.0
    pct_3p = 1.0 - pct_1 - pct_2
    
    # Проверка confluence (оптимизировано: только для бит 5-90)
    confluence_center = None
    confluence_peak = None
    if 5 <= bits <= 90:  # Оптимизация: не проверять для очень больших чисел
        for peak, center in confluence_centers.items():
            if passes_through_center_fast(N, center, max_steps=15):
                confluence_center = center
                confluence_peak = peak
                break
    
    # Классификация
    class_label = "NORMAL"
    
    # Zone 2: 71-87 бит, S/d ≈ 1.33
    if config.ZONE2_MIN <= bits <= config.ZONE2_MAX:
        if abs(s_d_ratio - config.SD_TARGET) < config.SD_TOLERANCE:
            class_label = "ZONE2_LIKE"
    
    # Class A: S/d > 1.25, ratio > 1.60, d > 50
    if ratio > 1.60 and s_d_ratio > 1.25 and d > 50:
        class_label = "CLASS_A_CANDIDATE"
    
    # Dead Zone аномалия
    if config.DEAD_ZONE_MIN <= bits <= config.DEAD_ZONE_MAX:
        if ratio > 1.585:
            class_label = "DEAD_ZONE_ANOMALY"
    
    # Confluence подтверждено
    if confluence_center is not None:
        if class_label == "NORMAL":
            class_label = "CONFLUENCE_CONFIRMED"
        else:
            class_label = f"{class_label}+CONFLUENCE"
    
    return {
        'k': k,
        'm': m,
        'N': N,
        'N_hex': hex(N),
        'bits': bits,
        'peak_bits': peak_bits,
        'ratio': round(ratio, 4),
        'd': d,
        'S': S,
        's_d_ratio': round(s_d_ratio, 4),
        'pct_1': round(pct_1, 3),
        'pct_2': round(pct_2, 3),
        'pct_3p': round(pct_3p, 3),
        'shifts_preview': shifts[:20],
        'confluence_center': confluence_center,
        'confluence_peak': confluence_peak,
        'class': class_label,
        'residue_class': k % 8,
        'timestamp': datetime.now().isoformat(),
    }

def passes_through_center_fast(n: int, center: int, max_steps: int = 15) -> bool:
    """Быстрая проверка confluence (до 15 шагов)"""
    current = n
    steps = 0
    
    while current > 1 and steps < max_steps:
        if current == center:
            return True
        if current < center:  # Оптимизация: если уже меньше центра, не догонит
            return False
        if current & 1:
            current = 3 * current + 1
            a = count_trailing_zeros(current)
            current >>= a
        else:
            a = count_trailing_zeros(current)
            current >>= a
        steps += 1
    
    return False

# ──────────────────────────────────────────────────────────────────────────
# ВОРОКЕР (НА УРОВНЕ МОДУЛЯ!)
# ──────────────────────────────────────────────────────────────────────────

def process_k_worker(args: Tuple[int, int, Dict[int, int]]) -> List[Dict]:
    k, max_m, confluence_centers = args
    results = []
    
    try:
        for m in range(max_m + 1):
            result = analyze_trajectory(k, m, confluence_centers)
            if result and result['class'] != "NORMAL":
                results.append(result)
    except Exception as e:
        print(f"ERROR k={k}: {e}", file=sys.stderr)
    
    return results

# ──────────────────────────────────────────────────────────────────────────
# СОХРАНЕНИЕ
# ──────────────────────────────────────────────────────────────────────────

def save_results(results: List[Dict], filename: str):
    config.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    
    json_path = config.OUTPUT_DIR / f"{filename}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    csv_path = config.OUTPUT_DIR / f"{filename}.csv"
    if results:
        keys = ['k', 'm', 'bits', 'peak_bits', 'ratio', 'd', 'S', 's_d_ratio', 
                'pct_1', 'pct_2', 'class', 'confluence_center', 'confluence_peak']
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            for r in results:
                writer.writerow({k: r.get(k, '') for k in keys})
    
    print(f"✓ Saved: {json_path}, {csv_path}")

def save_summary_report(summary: Dict):
    config.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    report_path = config.OUTPUT_DIR / "summary_report.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✓ Summary: {report_path}")

# ──────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("SEPTembrino Confluence Hunter v3.0")
    print("РАСШИРЕННЫЙ ПОИСК ZONE 2 (K=1-10000, M=0-100)")
    print("=" * 80)
    print(f"Дата: {datetime.now().isoformat()}")
    print(f"Диапазон k: {config.K_MIN}–{config.K_MAX} (нечётные)")
    print(f"Диапазон m: {config.M_MIN}–{config.M_MAX}")
    print(f"Ожидаемая битность: {config.ZONE2_MIN}–175+ бит")
    print(f"Ядра CPU: {cpu_count()}")
    print("=" * 80)
    
    start_time = time.time()
    all_results = []
    
    k_values = list(range(config.K_MIN, config.K_MAX + 1, 2))
    print(f"Всего k значений: {len(k_values)}")
    
    # Подготовка аргументов (включаем confluence_centers в каждый кортеж)
    worker_args = [(k, config.M_MAX, config.CONFLUENCE_CENTERS) for k in k_values]
    
    num_workers = min(cpu_count(), len(k_values))
    print(f"Запуск {num_workers} воркеров...")
    
    with Pool(processes=num_workers) as pool:
        for idx, results in enumerate(pool.imap(process_k_worker, worker_args)):
            all_results.extend(results)
            
            if (idx + 1) % config.SAVE_INTERVAL == 0:
                elapsed = time.time() - start_time
                rate = (idx + 1) / elapsed if elapsed > 0 else 0
                print(f"✓ Обработано k={k_values[idx]} ({idx+1}/{len(k_values)}) - {rate:.1f} k/sec")
    
    elapsed = time.time() - start_time
    print(f"\n✓ Завершено за {elapsed:.2f} секунд")
    print(f"Всего траекторий: {len(all_results)}")
    
    # ──────────────────────────────────────────────────────────────────────
    # АНАЛИЗ
    # ──────────────────────────────────────────────────────────────────────
    
    print("\n" + "=" * 80)
    print("АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("=" * 80)
    
    # Статистика по битности
    all_bits = [r['bits'] for r in all_results]
    print(f"\nБитность: мин={min(all_bits)}, макс={max(all_bits)}, среднее={sum(all_bits)/len(all_results):.1f}")
    
    # Zone 2
    print("\n1. Zone 2 кандидаты (71-87 бит, S/d ≈ 1.33):")
    zone2 = [r for r in all_results if r['class'] in ["ZONE2_LIKE", "ZONE2_LIKE+CONFLUENCE"]]
    print(f"   Найдено: {len(zone2)}")
    if zone2:
        print("   Топ-5:")
        zone2_sorted = sorted(zone2, key=lambda x: abs(x['s_d_ratio'] - 1.33))[:5]
        for z in zone2_sorted:
            cf = f"→ {z['confluence_center']}" if z['confluence_center'] else ""
            print(f"     k={z['k']:>5}, m={z['m']:>3}, bits={z['bits']:>3}, "
                  f"peak={z['peak_bits']:>3}, S/d={z['s_d_ratio']:.4f} {cf}")
    
    # Class A
    print("\n2. Class A кандидаты:")
    class_a = [r for r in all_results if "CLASS_A" in r['class']]
    print(f"   Найдено: {len(class_a)}")
    
    # Dead Zone
    print("\n3. Dead Zone аномалии (88-170 бит, ratio > 1.585):")
    dead = [r for r in all_results if r['class'] in ["DEAD_ZONE_ANOMALY", "DEAD_ZONE_ANOMALY+CONFLUENCE"]]
    print(f"   Найдено: {len(dead)}")
    if dead:
        print("   ⚠️  АНОМАЛИИ В МЁРТВОЙ ЗОНЕ!")
        for d in dead[:5]:
            print(f"     k={d['k']}, m={d['m']}, bits={d['bits']}, ratio={d['ratio']}")
    
    # Confluence
    print("\n4. Confluence-центры:")
    confluence = [r for r in all_results if r['confluence_center']]
    print(f"   Проходят через центры: {len(confluence)}")
    center_counts = defaultdict(int)
    for r in confluence:
        center_counts[r['confluence_center']] += 1
    for center, count in sorted(center_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"     Центр {center}: {count} траекторий")
    
    # Сводный отчёт
    summary = {
        'timestamp': datetime.now().isoformat(),
        'config': asdict(config),
        'total_trajectories': len(all_results),
        'elapsed_seconds': elapsed,
        'bitness_range': {'min': min(all_bits), 'max': max(all_bits)},
        'zone2_found': len(zone2),
        'class_a_found': len(class_a),
        'dead_zone_anomalies': len(dead),
        'confluence_found': len(confluence),
        'top_zone2': zone2_sorted[:10] if zone2 else [],
        'center_counts': dict(center_counts),
    }
    
    save_results(all_results, "full_results_v3")
    save_summary_report(summary)
    
    print("\n" + "=" * 80)
    print("ИССЛЕДОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    
    return summary

# ──────────────────────────────────────────────────────────────────────────
# ЗАПУСК
# ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mp.freeze_support()
    summary = main()
    print("\n✅ Все результаты сохранены в папке:", config.OUTPUT_DIR.absolute())