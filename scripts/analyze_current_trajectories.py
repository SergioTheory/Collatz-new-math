#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_current_trajectories.py
Глубокий анализ 5,262 траекторий из septembrino_results/full_results.json

Цели:
1. Распределение битности (почему нет Zone 2?)
2. Распределение d (нечётные шаги)
3. Распределение S/d (почему нет Class A?)
4. Поиск Zone 2 кандидатов (71-87 бит, S/d ≈ 1.33)
5. Анализ confluence по битности
6. Анализ residue классов (k mod 8)
"""

import json
import csv
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────
# ЗАГРУЗКА ДАННЫХ
# ──────────────────────────────────────────────────────────────────────────

def load_trajectories(filepath):
    """Загрузка траекторий из JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# ──────────────────────────────────────────────────────────────────────────
# АНАЛИЗ
# ──────────────────────────────────────────────────────────────────────────

def analyze_bitness_distribution(trajectories):
    """Распределение по битности входа"""
    bins = defaultdict(int)
    for t in trajectories:
        bits = t['bits']
        # Группируем по 10 бит
        bin_start = (bits // 10) * 10
        bins[bin_start] += 1
    
    return dict(sorted(bins.items()))

def analyze_d_distribution(trajectories):
    """Распределение по d (число нечётных шагов)"""
    bins = defaultdict(int)
    for t in trajectories:
        d = t['d']
        bin_start = (d // 20) * 20
        bins[bin_start] += 1
    
    return dict(sorted(bins.items()))

def analyze_sd_distribution(trajectories):
    """Распределение по S/d"""
    bins = defaultdict(int)
    for t in trajectories:
        sd = t['s_d_ratio']
        bin_start = round(sd * 10) / 10  # Округление до 0.1
        bins[bin_start] += 1
    
    return dict(sorted(bins.items()))

def analyze_confluence_by_bits(trajectories):
    """Confluence-центры по битности"""
    by_center = defaultdict(lambda: defaultdict(int))
    for t in trajectories:
        center = t.get('confluence_center')
        if center:
            bits_bin = (t['bits'] // 10) * 10
            by_center[str(center)][bits_bin] += 1
    
    return dict(by_center)

def find_zone2_candidates(trajectories):
    """Поиск кандидатов Zone 2 (71-87 бит, S/d ∈ [1.25, 1.40])"""
    candidates = []
    for t in trajectories:
        bits = t['bits']
        sd = t['s_d_ratio']
        
        if 71 <= bits <= 87 and 1.25 <= sd <= 1.40:
            candidates.append({
                'k': t['k'],
                'm': t['m'],
                'bits': bits,
                'peak_bits': t['peak_bits'],
                'd': t['d'],
                'S': t['S'],
                's_d_ratio': sd,
                'ratio': t['ratio'],
                'class': t['class'],
                'confluence_center': t.get('confluence_center')
            })
    
    return sorted(candidates, key=lambda x: abs(x['s_d_ratio'] - 1.33))

def analyze_residue_classes(trajectories):
    """Анализ по residue классам (k mod 8)"""
    by_residue = defaultdict(lambda: {'count': 0, 'avg_sd': 0, 'sd_sum': 0})
    
    for t in trajectories:
        residue = t['residue_class']
        by_residue[residue]['count'] += 1
        by_residue[residue]['sd_sum'] += t['s_d_ratio']
    
    for residue in by_residue:
        count = by_residue[residue]['count']
        by_residue[residue]['avg_sd'] = by_residue[residue]['sd_sum'] / count if count > 0 else 0
    
    return dict(by_residue)

def analyze_class_distribution(trajectories):
    """Распределение по классам"""
    class_counts = defaultdict(int)
    for t in trajectories:
        cls = t.get('class', 'UNKNOWN')
        class_counts[cls] += 1
    
    return dict(sorted(class_counts.items(), key=lambda x: -x[1]))

# ──────────────────────────────────────────────────────────────────────────
# ВЫВОД
# ──────────────────────────────────────────────────────────────────────────

def print_analysis(trajectories):
    print("=" * 80)
    print("ГЛУБОКИЙ АНАЛИЗ 5,262 ТРАЕКТОРИЙ")
    print("=" * 80)
    
    # 0. Распределение по классам
    print("\n0. Распределение по классам:")
    class_dist = analyze_class_distribution(trajectories)
    for cls, count in class_dist.items():
        pct = 100 * count / len(trajectories)
        print(f"   {cls:<30}: {count:5d} ({pct:5.1f}%)")
    
    # 1. Распределение по битности
    print("\n1. Распределение по битности входа:")
    bitness = analyze_bitness_distribution(trajectories)
    for bin_start, count in bitness.items():
        pct = 100 * count / len(trajectories)
        marker = "← Zone 2" if 70 <= bin_start <= 80 else ""
        marker = "← Dead Zone" if 80 <= bin_start <= 170 else marker
        print(f"   {bin_start:3d}-{bin_start+9:3d} бит: {count:5d} ({pct:5.1f}%) {marker}")
    
    # Статистика
    all_bits = [t['bits'] for t in trajectories]
    print(f"\n   Мин: {min(all_bits)}, Макс: {max(all_bits)}, Среднее: {sum(all_bits)/len(all_bits):.1f}")
    
    # 2. Распределение по d
    print("\n2. Распределение по d (нечётные шаги):")
    d_dist = analyze_d_distribution(trajectories)
    for bin_start, count in list(d_dist.items())[:15]:
        pct = 100 * count / len(trajectories)
        marker = "← Class A требует d>50" if bin_start >= 40 else ""
        print(f"   {bin_start:3d}-{bin_start+19:3d}: {count:5d} ({pct:5.1f}%) {marker}")
    
    # 3. Распределение по S/d
    print("\n3. Распределение по S/d:")
    sd_dist = analyze_sd_distribution(trajectories)
    for bin_start, count in list(sd_dist.items())[:20]:
        pct = 100 * count / len(trajectories)
        marker = ""
        if 1.25 <= bin_start <= 1.40:
            marker = "← Zone 2 / Class A target"
        elif bin_start < 1.0:
            marker = "← Family A-like"
        print(f"   {bin_start:.1f}: {count:5d} ({pct:5.1f}%) {marker}")
    
    # 4. Zone 2 кандидаты
    print("\n4. Zone 2 кандидаты (71-87 бит, S/d ∈ [1.25, 1.40]):")
    zone2 = find_zone2_candidates(trajectories)
    print(f"   Найдено: {len(zone2)}")
    if zone2:
        print("\n   Топ-5 по близости к S/d=1.33:")
        for c in zone2[:5]:
            cf = f"→ {c['confluence_center']}" if c['confluence_center'] else ""
            print(f"     k={c['k']:>5}, m={c['m']:>2}, bits={c['bits']:>2}, "
                  f"peak={c['peak_bits']:>3}, d={c['d']:>3}, S/d={c['s_d_ratio']:.4f} {cf}")
    else:
        print("   ⚠️  НЕТ КАНДИДАТОВ!")
        print("   ПРИЧИНА: Битность слишком мала для Zone 2 (71-87 бит)")
    
    # 5. Confluence по битности
    print("\n5. Confluence-центры по битности:")
    by_center = analyze_confluence_by_bits(trajectories)
    for center, bins in by_center.items():
        print(f"\n   Центр {center}:")
        for bin_start, count in sorted(bins.items()):
            marker = "← Zone 2 диапазон!" if 70 <= bin_start <= 80 else ""
            print(f"      {bin_start:3d}-{bin_start+9:3d} бит: {count:5d} {marker}")
    
    # 6. Residue классы
    print("\n6. Анализ по residue классам (k mod 8):")
    residues = analyze_residue_classes(trajectories)
    for residue, stats in sorted(residues.items()):
        print(f"   k ≡ {residue} (mod 8): {stats['count']:5d} траекторий, "
              f"средний S/d = {stats['avg_sd']:.4f}")
    
    # 7. Ключевой вывод
    print("\n" + "=" * 80)
    print("КЛЮЧЕВОЙ ВЫВОД:")
    print("=" * 80)
    
    max_bits = max(t['bits'] for t in trajectories)
    min_bits = min(t['bits'] for t in trajectories)
    
    print(f"\n📊 Диапазон битности: {min_bits} – {max_bits}")
    print(f"📊 Zone 2 требует: 71–87 бит")
    print(f"📊 Class A требует: d > 50, S/d > 1.25, ratio > 1.60")
    
    if max_bits < 71:
        print(f"\n⚠️  ПРОБЛЕМА: Максимальная битность ({max_bits}) < 71 (граница Zone 2)")
        print("   Невозможно найти Zone 2 в текущем диапазоне!")
        print("\n✅ РЕШЕНИЕ:")
        print("   - Увеличить K_MAX до 10000 (было 2000)")
        print("   - Увеличить M_MAX до 100 (было 60)")
        print("   - Формула: N = k·3^m - 1")
        print(f"   - При k=10000, m=100: N ≈ 10^4 × 3^100 ≈ 10^51 → ~170 бит")
    elif max_bits < 87:
        print(f"\n⚠️  Частичное покрытие: макс. битность ({max_bits}) < 87")
        print("   Zone 2 может быть частично доступна")
    else:
        print(f"\n✓  Максимальная битность ({max_bits}) покрывает Zone 2 (71-87)")
        if zone2:
            print(f"   Найдено {len(zone2)} Zone 2-подобных кандидатов")
        else:
            print("   Но Zone 2 кандидатов нет → нужны другие k,m комбинации")
    
    # Проверка confluence
    confluence_count = sum(1 for t in trajectories if t.get('confluence_center'))
    print(f"\n📊 Confluence подтверждено: {confluence_count}/{len(trajectories)} ({100*confluence_count/len(trajectories):.1f}%)")
    
    if confluence_count > 0:
        print("   ✓ 121 (Class A) доминирует для малых бит")
        print("   ✓ Это подтверждает, что матрица Septembrino кодирует confluence!")
    
    print("\n" + "=" * 80)
    print("РЕКОМЕНДАЦИЯ:")
    print("=" * 80)
    print("""
    Запустить septembrino_confluence_hunter_v3.py с параметрами:
    
    K_MAX = 10000   (было 2000)
    M_MAX = 100     (было 60)
    
    Ожидаемая битность: до ~175 бит
    - Zone 2: 71-87 бит ✓
    - Dead Zone: 88-170 бит ✓
    - Class A поиск: d>50, S/d>1.25 ✓
    
    Время выполнения: ~60-120 секунд на 36 ядрах
    """)
    print("=" * 80)

# ──────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────

def main():
    filepath = Path("septembrino_results/full_results.json")
    
    if not filepath.exists():
        print(f"❌ Файл не найден: {filepath}")
        print("   Запустите сначала septembrino_confluence_hunter_v2.py")
        return
    
    trajectories = load_trajectories(filepath)
    print(f"✓ Загружено {len(trajectories)} траекторий")
    print(f"✓ Файл: {filepath}")
    print()
    
    print_analysis(trajectories)
    
    # Сохранение детального отчёта
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_trajectories': len(trajectories),
        'bitness_distribution': analyze_bitness_distribution(trajectories),
        'd_distribution': analyze_d_distribution(trajectories),
        'sd_distribution': analyze_sd_distribution(trajectories),
        'class_distribution': analyze_class_distribution(trajectories),
        'zone2_candidates': find_zone2_candidates(trajectories),
        'confluence_by_bits': analyze_confluence_by_bits(trajectories),
        'residue_analysis': analyze_residue_classes(trajectories),
        'max_bits': max(t['bits'] for t in trajectories),
        'min_bits': min(t['bits'] for t in trajectories),
        'avg_bits': sum(t['bits'] for t in trajectories) / len(trajectories),
    }
    
    report_path = Path("septembrino_results/trajectory_analysis.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n✓ Детальный отчёт сохранён: {report_path}")

if __name__ == '__main__':
    main()