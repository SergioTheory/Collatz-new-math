#!/usr/bin/env python3
"""
create_k385_raw_data.py
Создание CSV файла с полными данными для k=385.

Запуск:
    python create_k385_raw_data.py

Выход:
    - Файл: k385_raw_data.csv (создаётся автоматически!)
    - Содержит: m=0 до 60, степени делителей, битности N
"""

import csv

def get_divisor_power(k, m):
    """Найти максимальную степень двойки, делящую k·3^m - 1."""
    N = k * (3 ** m) - 1
    power = 0
    temp = N
    while temp % 2 == 0 and power < 30:
        temp //= 2
        power += 1
    return power

def main():
    k = 385
    
    print("=" * 80)
    print(f"СОЗДАНИЕ RAW ДАННЫХ ДЛЯ k={k}")
    print("=" * 80)
    print()
    
    rows = []
    
    # Генерация данных для m=0 до 60
    for m in range(0, 61):
        power = get_divisor_power(k, m)
        divisor = 2 ** power
        N = k * (3 ** m) - 1
        n_bits = N.bit_length()
        
        rows.append({
            'k': k,
            'm': m,
            'divisor_power': power,
            'divisor_value': divisor,
            'N_bits': n_bits,
            'is_high': 'Yes' if power >= 15 else 'No'
        })
    
    # Сохранение в CSV
    output_file = 'k385_raw_data.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['k', 'm', 'divisor_power', 'divisor_value', 'N_bits', 'is_high']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✓ Создан файл: {output_file}")
    print(f"✓ Строк данных: {len(rows)} (m=0 до 60)")
    print()
    
    # Показать высокие делители (power >= 15)
    high_divs = [r for r in rows if r['divisor_power'] >= 15]
    print(f"Высокие делители (≥ 2^15): {len(high_divs)} найдено")
    print()
    print("Топ-10 по степени делителя:")
    print("-" * 80)
    print(f"{'m':>5} | {'power':>7} | {'divisor':>12} | {'N_bits':>8}")
    print("-" * 80)
    
    for r in sorted(high_divs, key=lambda x: x['divisor_power'], reverse=True)[:10]:
        print(f"{r['m']:>5} | 2^{r['divisor_power']:<2} = {r['divisor_value']:>10} | {r['N_bits']:>8}")
    
    print("-" * 80)
    print()
    print("=" * 80)
    print("Готово! Отправьте k385_raw_data.csv Anabel для проверки.")
    print("=" * 80)

if __name__ == '__main__':
    main()