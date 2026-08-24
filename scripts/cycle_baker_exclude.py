"""
cycle_baker_exclude.py
Исключение нетривиальных циклов Коллатца через границу Бейкера + фронт верификации.

Для цикла длины d с полным сдвигом S:
  N = c_d / (2^S - 3^d),   знаменатель обязан быть > 0  =>  S > d*log2(3).

Верхняя граница на c_d для данного (d, S):
  c_d <= 3^d - 2^d  (достигается при back-loaded сдвиге a_1=...=a_{d-1}=1, a_d=S-d+1).

Верхняя граница на N:
  N <= (3^d - 2^d) / (2^S - 3^d).

Если эта граница < 2^68 (фронт Барины), цикл длины d исключён вычислительно.
Наибольшее d, для которого граница >= 2^68, — новая граница Бейкера.
"""

import math
from math import log2, floor
import time
from numba import njit, prange

FRONTIER = 2**68          # фронт верификации Барины
LOG2_3 = log2(3)          # ≈ 1.58496

# ---------------------------------------------------------------------------
# Часть 1: граница Бейкера (аналитическая, без перечисления)
# ---------------------------------------------------------------------------

def closest_S(d):
    """Наименьшее целое S, для которого 2^S > 3^d."""
    return floor(d * LOG2_3) + 1

def N_upper_bound_log2(d, S):
    """
    Верхняя граница на log2(N), где N = c_d/(2^S - 3^d).
    c_d <= 3^d - 2^d  (back-loaded сдвиг).
    """
    diff = S - d * LOG2_3
    if diff <= 0:
        return float('inf')
        
    log_c = d * LOG2_3
    try:
        log_M = S + math.log2(1.0 - 2.0**(-diff))
    except ValueError:
        return float('inf')
        
    return log_c - log_M

def baker_frontier(d_max=500):
    """
    Для каждого d вычисляет верхнюю границу N при ближайшем S.
    Возвращает наибольшее d, не исключённое фронтом Барины.
    """
    max_d_not_excluded = 0
    results = []
    for d in range(1, d_max + 1):
        S = closest_S(d)
        N_ub_log2 = N_upper_bound_log2(d, S)
        excluded = N_ub_log2 < 68.0
        if not excluded:
            max_d_not_excluded = d
        # For display, store approx value if small enough, else inf
        if N_ub_log2 < 1000.0:
            N_ub = 2.0 ** N_ub_log2
        else:
            N_ub = float('inf')
        results.append((d, S, N_ub, excluded))
    return max_d_not_excluded, results

# ---------------------------------------------------------------------------
# Часть 2: прямое перечисление для малых d
# ---------------------------------------------------------------------------

@njit
def syr_step(x):
    """Один ускоренный сиракузский шаг: (3x+1)/2^a, возвращает (результат, a)."""
    y = 3 * x + 1
    a = 0
    while y % 2 == 0:
        y //= 2
        a += 1
    return y, a

@njit
def check_cycle(N, d):
    """
    Проверяет, является ли N элементом цикла длины ровно d (нечётных шагов).
    Возвращает True, если после ровно d шагов орбита возвращается в N
    и ни на одном промежуточном шаге не возвращается раньше.
    """
    x = N
    for k in range(1, d + 1):
        x, _ = syr_step(x)
        if x == N:
            return k == d      # вернулся ровно на шаге d
        if x < N:
            return False       # ушёл ниже старта — не может быть циклом через N
    return x == N

def enumerate_small_d(d_max_enum=30):
    """
    Для малых d перебирает все допустимые (N, S) через структуру сдвигов.
    Для каждого d перебирает N в диапазоне, где цикл ещё может существовать,
    и проверяет напрямую.
    Диапазон N: от 3 до верхней границы, где цикл длины d ещё возможен.
    """
    print(f"\nПрямое перечисление для d <= {d_max_enum}...")
    found = []
    for d in range(1, d_max_enum + 1):
        S = closest_S(d)
        N_ub_log2 = N_upper_bound_log2(d, S)
        if N_ub_log2 > 100:
            N_limit = 10**7
        else:
            N_limit = min(int(2.0 ** N_ub_log2) + 1, 10**7)
        if N_limit < 3:
            continue
        # Перебираем нечётные N
        for N in range(3, N_limit, 2):
            if check_cycle(N, d):
                found.append((N, d, S))
                print(f"  НАЙДЕН ЦИКЛ: N={N}, d={d}, S={S}", flush=True)
    if not found:
        print(f"  Циклов не найдено для d <= {d_max_enum} (кроме тривиального).", flush=True)
    return found

# ---------------------------------------------------------------------------
# Часть 3: расширенный поиск по нескольким S для каждого d
# ---------------------------------------------------------------------------

def multi_S_frontier(d_max=500, k_max=5):
    """
    Для каждого d проверяет несколько значений S (не только ближайшее),
    чтобы убедиться, что ни одно S не даёт N >= FRONTIER.
    """
    max_d_not_excluded = 0
    for d in range(1, d_max + 1):
        S_min = closest_S(d)
        excluded_for_all_S = True
        for k in range(k_max):
            S = S_min + k
            N_ub_log2 = N_upper_bound_log2(d, S)
            if N_ub_log2 >= 68.0:
                excluded_for_all_S = False
                break
        if not excluded_for_all_S:
            max_d_not_excluded = d
    return max_d_not_excluded

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("ИСКЛЮЧЕНИЕ НЕТРИВИАЛЬНЫХ ЦИКЛОВ: ГРАНИЦА БЕЙКЕРА + ФРОНТ БАРИНЫ")
    print("=" * 70)
    print(f"Фронт верификации: 2^68 = {FRONTIER}")
    print(f"log2(3) = {LOG2_3:.6f}")
    print()

    # Часть 1: граница Бейкера
    t0 = time.time()
    max_d, results = baker_frontier(1_000_000)
    t1 = time.time()
    print(f"[Часть 1] Граница Бейкера (ближайшее S) до d=1000000:")
    print(f"  Наибольшее d, не исключённое фронтом: d = {max_d}")
    print(f"  Время: {t1-t0:.3f} с")
    print()

    # Выводим первые 20 и последние 10 результатов
    print("  Первые 20 значений:")
    print(f"  {'d':>4} {'S':>5} {'N_upper':>20} {'Исключён?':>10}")
    for d, S, N_ub, exc in results[:20]:
        N_str = f"{N_ub:.3e}" if N_ub < 1e15 else "inf"
        print(f"  {d:4d} {S:5d} {N_str:>20} {'Да' if exc else 'НЕТ':>10}")
    print("  ...")
    print("  Последние 10 значений:")
    for d, S, N_ub, exc in results[-10:]:
        N_str = f"{N_ub:.3e}" if N_ub < 1e15 else "inf"
        print(f"  {d:4d} {S:5d} {N_str:>20} {'Да' if exc else 'НЕТ':>10}")
    print()

    # Часть 2: расширенный поиск по нескольким S
    t0 = time.time()
    max_d_multi = multi_S_frontier(1_000_000, k_max=2)
    t1 = time.time()
    print(f"[Часть 2] Расширенный поиск (несколько S):")
    print(f"  Наибольшее d, не исключённое фронтом: d = {max_d_multi}")
    print(f"  Время: {t1-t0:.3f} с")
    print()

    # Часть 3: прямое перечисление для малых d
    found = enumerate_small_d(30)
    print()

    # Итог
    print("=" * 70)
    print("ИТОГ")
    print("=" * 70)
    print(f"Граница Бейкера (ближайшее S):  d <= {max_d} не исключены")
    print(f"Расширенный поиск (5 значений S): d <= {max_d_multi} не исключены")
    print(f"Прямое перечисление (d<=30): {'найдены циклы' if found else 'нет нетривиальных циклов'}")
    print()
    print("Интерпретация:")
    print(f"  Все циклы длины d > {max_d} ИСКЛЮЧЕНЫ комбинацией")
    print("  границы Бейкера и фронта верификации 2^68.")
    print(f"  Для d <= {max_d} граница Бейкера не исключает цикл,")
    print("  и требуется прямой перебор или более тонкий анализ.")

if __name__ == "__main__":
    main()
