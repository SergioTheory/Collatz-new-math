#!/usr/bin/env python3
"""
extract_anchors.py
ЭТАП 1 ПЛАНА: Извлечение якорных точек и проверка гипотезы 2

Собирает все пары (k, n), где k*3^n - 1 = 2^a (reduced top row = 1).
Проверяет модулярную структуру (решётку), ищет закономерности в n и a,
сопоставляет с Class A/B центрами (x*, 121, 6803...).

Запуск:
    python extract_anchors.py

Выход:
    anchors_k1_2000_n0_60.csv
    Консольный анализ гипотезы 2
"""

import csv
import os

def is_power_of_two(x: int) -> bool:
    """Быстрая проверка: является ли число точной степенью двойки."""
    return x > 0 and (x & (x - 1)) == 0

def main():
    K_MAX = 2000
    N_MAX = 60
    OUTPUT_FILE = 'anchors_k1_2000_n0_60.csv'
    
    anchors = []
    total_checks = 0
    
    print(f"🔍 Поиск якорных точек (k*3^n - 1 = 2^a)")
    print(f"📏 Диапазон: k=1..{K_MAX} (нечётные), n=0..{N_MAX}")
    print("-" * 60)
    
    for k in range(1, K_MAX + 1, 2):
        for n in range(N_MAX + 1):
            total_checks += 1
            N = k * (3 ** n) - 1
            
            if is_power_of_two(N):
                a = N.bit_length() - 1  # N = 2^a => битность = a+1
                N_bits = a + 1
                
                k_mod_16 = k % 16
                k_mod_32 = k % 32
                residue = "Regular" if k % 8 in (5, 7) else "Non-Regular"
                
                anchors.append({
                    'k': k,
                    'n': n,
                    'a': a,
                    'N_bits': N_bits,
                    'k_mod_16': k_mod_16,
                    'k_mod_32': k_mod_32,
                    'residue_class': residue
                })
    
    # Сохранение в CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['k', 'n', 'a', 'N_bits', 'k_mod_16', 'k_mod_32', 'residue_class']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(anchors)
        
    print(f"✅ Проверено комбинаций: {total_checks}")
    print(f"🎯 Найдено якорных точек: {len(anchors)}")
    print(f"💾 Сохранено в: {OUTPUT_FILE}")
    
    # 📊 АНАЛИЗ ГИПОТЕЗЫ 2 (Решётка и модулярные правила)
    if anchors:
        print("\n" + "=" * 60)
        print("📐 АНАЛИЗ ГИПОТЕЗЫ 2: Структура решётки")
        print("=" * 60)
        
        # 1. Распределение по k mod 32
        mod32_dist = {}
        for a in anchors:
            m32 = a['k_mod_32']
            mod32_dist[m32] = mod32_dist.get(m32, 0) + 1
        print(f"🔹 Распределение по k mod 32: {dict(sorted(mod32_dist.items()))}")
        
        # 2. Проверка на линейные/модулярные зависимости n от k
        print("\n🔹 Первые 10 якорей (k, n, a, N_bits):")
        for a in anchors[:10]:
            print(f"   k={a['k']:>4}, n={a['n']:>2}, a={a['a']:>2}, bits={a['N_bits']:>3} | mod32={a['k_mod_32']:>2} | {a['residue_class']}")
            
        # 3. Сопоставление с Class A/B центрами
        known_centers = {
            '121 (Class A)': 7,
            'x* (Class A)': 75,
            '6803 (Class B)': 13,
            '27611 (Class B)': 15,
            '15977 (Class B)': 14
        }
        print("\n🔹 Сопоставление с известными confluence-центрами:")
        anchor_bits = set(a['N_bits'] for a in anchors)
        for name, bits in known_centers.items():
            if bits in anchor_bits:
                print(f"   ✅ {name} ({bits} бит) -> СОВПАДАЕТ с якорем!")
            else:
                # Проверяем близость (±2 бита)
                close = [ab for ab in anchor_bits if abs(ab - bits) <= 2]
                if close:
                    print(f"   ⚠️  {name} ({bits} бит) -> Близко к якорям: {close}")
                else:
                    print(f"   ❌ {name} ({bits} бит) -> Не совпадает с якорями")
                    
        print("\n💡 Вывод по Гипотезе 2:")
        if len(mod32_dist) <= 4:
            print("   Якоря концентрируются в узком наборе классов вычетов -> подтверждает модулярную решётку.")
        else:
            print("   Якоря распределены широко -> требуется анализ периодичности n(k).")
            
    else:
        print("\n⚠️ Якорные точки не найдены в заданном диапазоне.")

if __name__ == '__main__':
    main()