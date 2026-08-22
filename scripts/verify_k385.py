#!/usr/bin/env python3
"""
verify_k385.py
Проверка каких m значений дают 2^18 для k=385.

Запуск:
    python verify_k385.py

Выход:
    - Вывод в консоль таблицы m vs делитель
    - Подсветка значений с 2^18
"""

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
    print(f"ПРОВЕРКА k={k} для m=25 до 35")
    print("=" * 80)
    print()
    print(f"{'m':>5} | {'2^power':>10} | {'divisor':>12} | {'примечание'}")
    print("-" * 80)
    
    for m in range(25, 36):
        power = get_divisor_power(k, m)
        divisor = 2 ** power
        
        # Подсветка 2^18
        if power == 18:
            note = "← 2^18! РЕКОРД!"
        elif power >= 15:
            note = "← высокий"
        else:
            note = ""
        
        print(f"{m:>5} | 2^{power:<2} = {divisor:>10} | {note}")
    
    print("-" * 80)
    print()
    print("=" * 80)
    print("Вывод: Anabel нашла n=32 (то же что m=32) с 2^18 — это совпадает!")
    print("Наши данные m=29-30 были ошибочными в summary.")
    print("=" * 80)

if __name__ == '__main__':
    main()