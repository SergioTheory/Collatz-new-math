#!/usr/bin/env python3
"""
ЭТАП 3: СОПОСТАВЛЕНИЕ REDUCED С ДИНАМИКОЙ КОЛЛАТЦА
Проверяет математическую связь между строками n и n+1 матрицы.
"""

import csv

def v2(x):
    """2-адическая валентность (степень двойки в разложении)."""
    if x == 0: return 0
    return (x & -x).bit_length() - 1

def analyze_k(k, max_n=60):
    print(f"\n🔍 Анализ k = {k}")
    print("-" * 60)
    rows = []
    matches = 0
    total = 0

    for n in range(max_n):
        N = k * (3 ** n) - 1
        a = v2(N)
        R = N >> a  # reduced top row

        N_next = k * (3 ** (n+1)) - 1
        a_next = v2(N_next)
        R_next = N_next >> a_next

        # Математический переход: N_{n+1} = 3*N_n + 2
        # Если a == 1: N_{n+1} = 2*(3R + 1) → Collatz-подобный переход
        # Если a > 1:  N_{n+1} = 2*(нечётное) → линейный сдвиг
        if a == 1:
            expected_a_next = 1 + v2(3 * R + 1)
            expected_R_next = (3 * R + 1) >> v2(3 * R + 1)
            case = "a=1 (Collatz-step)"
        else:
            expected_a_next = 1
            expected_R_next = 3 * R * (2 ** (a - 1)) + 1
            case = f"a={a} (Linear-shift)"

        match = (a_next == expected_a_next) and (R_next == expected_R_next)
        total += 1
        if match:
            matches += 1

        rows.append({
            'k': k, 'n': n, 'a': a, 'R': R,
            'a_next': a_next, 'R_next': R_next,
            'expected_a': expected_a_next, 'expected_R': expected_R_next,
            'match': match, 'case': case
        })

    # Сохранение
    filename = f'reduced_collatz_k{k}.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"  📊 Совпадений (формула → факт): {matches}/{total} ({matches/total*100:.1f}%)")
    print(f"  📈 Макс. R: {max(r['R'] for r in rows):,}")
    print(f"  💾 Сохранено в {filename}")
    return rows

def main():
    print("=" * 70)
    print("ЭТАП 3: СОПОСТАВЛЕНИЕ REDUCED С ДИНАМИКОЙ КОЛЛАТЦА")
    print("Проверка: эволюционирует ли R_n по правилу Коллатца?")
    print("=" * 70)

    for k in [11, 5, 7, 385]:
        analyze_k(k)

    print("\n" + "=" * 70)
    print("📊 ВЫВОДЫ ЭТАПА 3:")
    print("1. Если match ≈ 100%: Матрица полностью детерминирована формулой N_{n+1}=3N_n+2.")
    print("2. Переход делится на два режима: a=1 (Collatz) и a>1 (Linear).")
    print("3. CSV-файлы содержат полную карту переходов для Этапа 4.")
    print("=" * 70)

if __name__ == '__main__':
    main()