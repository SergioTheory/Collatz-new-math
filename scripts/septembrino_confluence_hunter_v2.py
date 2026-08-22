#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
septembrino_confluence_hunter_v2.py
─────────────────────────────────────────────────────────────────────────────
Интеграция матричной теории Septembrino с Collatz Crystal Hunter

Исправления v2:
- Worker-функция на уровне модуля (не внутри main)
- Правильный guard if __name__ == '__main__'
- freeze_support() для Windows совместимости
- Передача кортежей вместо lambda

Цели:
1. Генерация кандидатов по формуле Septembrino: N = k·3^m - 1
2. Поиск Zone 2-подобных профилей (S/d ≈ 1.33, d ≈ 259)
3. Проверка confluence через x* и Class A/B центры
4. Верификация мёртвой зоны 88–170 бит
5. Поиск новых Class A центров

Авторы: Collatz Crystal Hunter Team
Дата: 2 апреля 2026
Версия: 2.0 (исправлена multiprocessing ошибка Windows)
─────────────────────────────────────────────────────────────────────────────
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
# КОНФИГУРАЦИЯ
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class Config:
    # Диапазоны Septembrino
    K_MIN: int = 1
    K_MAX: int = 2000          # k от 1 до 2000 (нечётные)
    M_MIN: int = 0
    M_MAX: int = 60            # степени 3^m
    
    # Параметры траектории
    MAX_STEPS: int = 5000      # максимум шагов Коллатца
    MAX_DIVISORS: int = 100    # максимум делителей для анализа
    
    # Фильтры Zone 2-подобных профилей (из Collatz_v5.docx)
    SD_TARGET: float = 1.33    # целевое S/d для Zone 2 / Class A
    SD_TOLERANCE: float = 0.08 # допуск ±0.08
    
    # Диапазоны битности
    DEAD_ZONE_MIN: int = 88    # мёртвая зона старт
    DEAD_ZONE_MAX: int = 170   # мёртвая зона финиш
    ZONE2_MIN: int = 71        # Zone 2 старт
    ZONE2_MAX: int = 87        # Zone 2 финиш
    
    # Целевые пики (из extra_seeds.json)
    TARGET_PEAKS: List[int] = field(default_factory=lambda: [140, 233, 240, 280, 483])
    
    # Confluence центры (из Collatz_v5.docx, раздел 9)
    # Class A: 121 (peak 14), x* (peak 140)
    # Class B: центры для peaks 14-50
    CONFLUENCE_CENTERS: Dict[int, int] = field(default_factory=lambda: {
        14: 121,              # Class A, 7 бит, hit rate 100%
        140: 20152090995747160937051,  # x* Class A, 75 бит, hit rate 100%
        32: 1242665,          # Class B, 21 бит
        35: 26658983,         # Class B transitional, 25 бит
        37: 67625867,         # Class B transitional, 27 бит
        41: 37748015,         # Class B transitional, 26 бит
        50: 1396693151,       # Class B, 31 бит
    })
    
    # Вывод
    OUTPUT_DIR: Path = Path("septembrino_results")
    SAVE_INTERVAL: int = 500   # сохранять каждые N кандидатов
    
config = Config()

# ──────────────────────────────────────────────────────────────────────────
# ЯДРО: ДИНАМИКА КОЛЛАТЦА
# ──────────────────────────────────────────────────────────────────────────

def count_trailing_zeros(n: int) -> int:
    """Безопасный подсчёт a_k (число делений на 2)"""
    if n == 0:
        return 0
    return (n & -n).bit_length() - 1

def collatz_peak(n: int, max_steps: int = 5000) -> Tuple[int, int, int, List[int]]:
    """
    Полный прогон траектории Коллатца.
    
    Returns:
        (peak_bits, d, S, shift_vector)
        - peak_bits: пиковая битность
        - d: число нечётных шагов до пика
        - S: сумма чётных сдвигов до пика
        - shift_vector: вектор сдвигов [a_0, a_1, ..., a_{d-1}]
    """
    if n <= 1:
        return (n.bit_length(), 0, 0, [])
    
    current = n
    peak = n
    peak_bits = n.bit_length()
    shifts = []
    d = 0  # нечётные шаги
    S = 0  # сумма сдвигов
    steps = 0
    
    while current > 1 and steps < max_steps:
        if current & 1:  # нечётное
            current = 3 * current + 1
            a = count_trailing_zeros(current)
            current >>= a
            shifts.append(a)
            S += a
            d += 1
        else:  # чётное
            a = count_trailing_zeros(current)
            current >>= a
            shifts.append(a)
            S += a
        
        if current.bit_length() > peak_bits:
            peak_bits = current.bit_length()
            peak = current
        
        steps += 1
    
    return (peak_bits, d, S, shifts)

def get_shift_vector(n: int, max_steps: int = 500) -> List[int]:
    """Извлечение shift-вектора (ускоренная динамика)"""
    shifts = []
    current = n
    steps = 0
    
    while current > 1 and steps < max_steps:
        if current & 1:
            current = 3 * current + 1
            a = count_trailing_zeros(current)
            current >>= a
            shifts.append(a)
        else:
            a = count_trailing_zeros(current)
            current >>= a
            shifts.append(a)
        steps += 1
    
    return shifts

def shifts_to_divisors(shifts: List[int]) -> List[int]:
    """Конвертация shift-вектора в делители (нотация Septembrino)"""
    return [2**s for s in shifts if s > 0]

# ──────────────────────────────────────────────────────────────────────────
# СЕПТЕМБРИНО: ГЕНЕРАЦИЯ ЧИСЕЛ
# ──────────────────────────────────────────────────────────────────────────

def generate_septembrino_number(k: int, m: int) -> int:
    """Формула Septembrino: N = k·3^m - 1"""
    return k * (3 ** m) - 1

def analyze_trajectory(k: int, m: int) -> Optional[Dict]:
    """
    Анализирует одну траекторию N = k·3^m - 1.
    Возвращает Dict с метриками или None если не интересно.
    """
    N = generate_septembrino_number(k, m)
    if N <= 0:
        return None
    
    bits = N.bit_length()
    peak_bits, d, S, shifts = collatz_peak(N, max_steps=config.MAX_STEPS)
    
    if d == 0:
        return None
    
    ratio = peak_bits / bits if bits > 0 else 0.0
    s_d_ratio = S / d if d > 0 else 0.0
    
    # Профиль сдвигов
    pct_1 = shifts.count(1) / len(shifts) if shifts else 0.0
    pct_2 = shifts.count(2) / len(shifts) if shifts else 0.0
    pct_3p = 1.0 - pct_1 - pct_2
    
    # Проверка confluence через известные центры
    confluence_center = None
    confluence_peak = None
    for peak, center in config.CONFLUENCE_CENTERS.items():
        if passes_through_center(N, center, max_steps=100):
            confluence_center = center
            confluence_peak = peak
            break
    
    # Классификация по критериям из Collatz_v5.docx
    class_label = "NORMAL"
    
    # Zone 2: 71-87 бит, S/d ≈ 1.33
    if config.ZONE2_MIN <= bits <= config.ZONE2_MAX:
        if abs(s_d_ratio - config.SD_TARGET) < config.SD_TOLERANCE:
            class_label = "ZONE2_LIKE"
    
    # Class A: S/d > 1.25, ratio > 1.60, d > 50
    if ratio > 1.60 and s_d_ratio > 1.25 and d > 50:
        class_label = "CLASS_A_CANDIDATE"
    
    # Dead Zone аномалия: 88-170 бит, ratio > 1.585
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

def passes_through_center(n: int, center: int, max_steps: int = 100) -> bool:
    """Проверка, проходит ли траектория n через confluence-центр"""
    current = n
    steps = 0
    
    while current > 1 and steps < max_steps:
        if current == center:
            return True
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
# ВОРОКЕР ДЛЯ MULTIPROCESSING (НА УРОВНЕ МОДУЛЯ!)
# ──────────────────────────────────────────────────────────────────────────

def process_k_worker(args: Tuple[int, int]) -> List[Dict]:
    """
    Воркер для обработки одного k.
    args = (k, max_m)
    
    ВАЖНО: Эта функция должна быть на уровне модуля для Windows multiprocessing!
    """
    k, max_m = args
    results = []
    
    try:
        for m in range(max_m + 1):
            result = analyze_trajectory(k, m)
            if result and result['class'] != "NORMAL":
                results.append(result)
    except Exception as e:
        print(f"ERROR k={k}: {e}", file=sys.stderr)
    
    return results

# ──────────────────────────────────────────────────────────────────────────
# АНАЛИЗ МЁРТВОЙ ЗОНЫ
# ──────────────────────────────────────────────────────────────────────────

def verify_dead_zone(results: List[Dict]) -> Dict:
    """Верификация мёртвой зоны 88–170 бит"""
    dead_zone_candidates = []
    anomalies = []
    
    for r in results:
        bits = r['bits']
        ratio = r['ratio']
        
        if config.DEAD_ZONE_MIN <= bits <= config.DEAD_ZONE_MAX:
            dead_zone_candidates.append(r)
            
            # Family A baseline ≈ 1.585
            if ratio > 1.59:  # выше Family A
                anomalies.append({
                    'k': r['k'],
                    'm': r['m'],
                    'bits': bits,
                    'peak': r['peak_bits'],
                    'ratio': ratio,
                    's_d_ratio': r['s_d_ratio'],
                })
    
    return {
        'total_in_dead_zone': len(dead_zone_candidates),
        'anomalies_found': len(anomalies),
        'anomalies': anomalies,
        'dead_zone_confirmed': len(anomalies) == 0,
    }

# ──────────────────────────────────────────────────────────────────────────
# СТАТИСТИКА ДЕЛИТЕЛЕЙ (SEPTembrino)
# ──────────────────────────────────────────────────────────────────────────

def analyze_divisor_distribution(results: List[Dict]) -> Dict:
    """Анализ распределения делителей по Septembrino"""
    divisor_counts = defaultdict(int)
    total_divisors = 0
    
    for r in results:
        shifts = r.get('shifts_preview', [])
        for s in shifts:
            div = 2 ** s
            divisor_counts[div] += 1
            total_divisors += 1
    
    # Ожидаемое распределение Septembrino: P(div=2^a) = 1/2^a
    expected = {
        2: 0.50,
        4: 0.25,
        8: 0.125,
        16: 0.0625,
        32: 0.03125,
        64: 0.015625,
        128: 0.0078125,
    }
    
    actual = {}
    for div, count in divisor_counts.items():
        actual[div] = count / total_divisors if total_divisors > 0 else 0.0
    
    # Отклонения
    deviations = {}
    for div in expected:
        exp = expected[div]
        act = actual.get(div, 0.0)
        deviations[div] = abs(act - exp) / exp * 100 if exp > 0 else 0.0
    
    return {
        'total_divisors': total_divisors,
        'actual_distribution': actual,
        'expected_distribution': expected,
        'deviations_percent': deviations,
        'septembrino_confirmed': all(d < 10.0 for d in deviations.values()),
    }

# ──────────────────────────────────────────────────────────────────────────
# СОХРАНЕНИЕ РЕЗУЛЬТАТОВ
# ──────────────────────────────────────────────────────────────────────────

def save_results(results: List[Dict], filename: str):
    """Сохранение результатов в JSON и CSV"""
    config.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    
    # JSON
    json_path = config.OUTPUT_DIR / f"{filename}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # CSV
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
    """Сохранение сводного отчёта"""
    config.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    report_path = config.OUTPUT_DIR / "summary_report.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✓ Summary: {report_path}")

# ──────────────────────────────────────────────────────────────────────────
# ОСНОВНОЙ ЗАПУСК
# ──────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("SEPTembrino Confluence Hunter v2.0")
    print("Интеграция матричной теории Septembrino с Collatz Crystal Hunter")
    print("=" * 80)
    print(f"Дата: {datetime.now().isoformat()}")
    print(f"Диапазон k: {config.K_MIN}–{config.K_MAX} (нечётные)")
    print(f"Диапазон m: {config.M_MIN}–{config.M_MAX}")
    print(f"Ядра CPU: {cpu_count()}")
    print("=" * 80)
    
    start_time = time.time()
    all_results = []
    
    # Генерация списка нечётных k
    k_values = list(range(config.K_MIN, config.K_MAX + 1, 2))
    print(f"Всего k значений: {len(k_values)}")
    
    # Подготовка аргументов для воркеров (k, max_m)
    worker_args = [(k, config.M_MAX) for k in k_values]
    
    # Multiprocessing — ИСПРАВЛЕННАЯ ВЕРСИЯ
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
    
    # 1. Распределение делителей (Septembrino)
    print("\n1. Распределение делителей (Septembrino):")
    divisor_stats = analyze_divisor_distribution(all_results)
    print(f"   Всего делителей: {divisor_stats['total_divisors']}")
    print(f"   Septembrino подтверждён: {divisor_stats['septembrino_confirmed']}")
    for div, dev in divisor_stats['deviations_percent'].items():
        status = "✓" if dev < 10.0 else "✗"
        print(f"   {status} 2^{div}: отклонение {dev:.2f}%")
    
    # 2. Мёртвая зона
    print("\n2. Верификация мёртвой зоны 88–170 бит:")
    dead_zone = verify_dead_zone(all_results)
    print(f"   Кандидатов в мёртвой зоне: {dead_zone['total_in_dead_zone']}")
    print(f"   Аномалий найдено: {dead_zone['anomalies_found']}")
    print(f"   Мёртвая зона подтверждена: {dead_zone['dead_zone_confirmed']}")
    if dead_zone['anomalies']:
        print("   ⚠️ АНОМАЛИИ:")
        for a in dead_zone['anomalies'][:5]:
            print(f"     k={a['k']}, m={a['m']}, bits={a['bits']}, ratio={a['ratio']:.4f}")
    
    # 3. Zone 2-подобные профили
    print("\n3. Zone 2-подобные профили (S/d ≈ 1.33):")
    zone2_like = [r for r in all_results if r['class'] in ["ZONE2_LIKE", "ZONE2_LIKE+CONFLUENCE"]]
    print(f"   Найдено: {len(zone2_like)}")
    if zone2_like:
        print("   Топ-5 по близости к Zone 2:")
        zone2_sorted = sorted(zone2_like, key=lambda x: abs(x['s_d_ratio'] - config.SD_TARGET))[:5]
        for z in zone2_sorted:
            cf = f"→ центр {z['confluence_center']}" if z['confluence_center'] else ""
            print(f"     k={z['k']}, m={z['m']}, bits={z['bits']}, S/d={z['s_d_ratio']:.4f} {cf}")
    
    # 4. Class A кандидаты
    print("\n4. Class A кандидаты (ratio > 1.60, S/d > 1.25, d > 50):")
    class_a = [r for r in all_results if "CLASS_A" in r['class']]
    print(f"   Найдено: {len(class_a)}")
    if class_a:
        print("   Топ-5 по ratio:")
        class_a_sorted = sorted(class_a, key=lambda x: x['ratio'], reverse=True)[:5]
        for c in class_a_sorted:
            print(f"     k={c['k']}, m={c['m']}, bits={c['bits']}, ratio={c['ratio']:.4f}, S/d={c['s_d_ratio']:.4f}")
    
    # 5. Confluence-центры
    print("\n5. Confluence-центры:")
    confluence_found = [r for r in all_results if r['confluence_center'] is not None]
    print(f"   Проходят через центры: {len(confluence_found)}")
    center_counts = defaultdict(int)
    for r in confluence_found:
        center_counts[r['confluence_center']] += 1
    for center, count in sorted(center_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"     Центр {center}: {count} траекторий")
    
    # 6. Распределение по residue классам
    print("\n6. Распределение по residue классам (k mod 8):")
    residue_counts = defaultdict(int)
    for r in all_results:
        residue_counts[r['residue_class']] += 1
    for residue, count in sorted(residue_counts.items(), key=lambda x: -x[1]):
        print(f"     k ≡ {residue} (mod 8): {count} траекторий")
    
    # ──────────────────────────────────────────────────────────────────────
    # СВОДНЫЙ ОТЧЁТ
    # ──────────────────────────────────────────────────────────────────────
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'config': asdict(config),
        'total_trajectories': len(all_results),
        'elapsed_seconds': elapsed,
        'divisor_analysis': divisor_stats,
        'dead_zone_verification': dead_zone,
        'zone2_like_profiles': len(zone2_like),
        'class_a_candidates': len(class_a),
        'confluence_found': len(confluence_found),
        'top_zone2_like': zone2_sorted[:10] if zone2_like else [],
        'top_class_a': class_a_sorted[:10] if class_a else [],
        'center_counts': dict(center_counts),
        'residue_distribution': dict(residue_counts),
    }
    
    save_results(all_results, "full_results")
    save_summary_report(summary)
    
    print("\n" + "=" * 80)
    print("ИССЛЕДОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    
    return summary

# ──────────────────────────────────────────────────────────────────────────
# ЗАПУСК (Windows-safe)
# ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Для Windows multiprocessing
    mp.freeze_support()
    
    # Запуск main
    summary = main()
    
    print("\n✅ Все результаты сохранены в папке:", config.OUTPUT_DIR.absolute())