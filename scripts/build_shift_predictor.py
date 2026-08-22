#!/usr/bin/env python3
"""
ЭТАП 4: ПОСТРОЕНИЕ ПРЕДИКТОРА SHIFT-ВЕКТОРОВ
Генерирует shift-вектор для любого (k, m) без полной симуляции Коллатца.
Использует рекуррентную формулу R_{n+1} = (3*R_n + 2) >> a_n, подтверждённую на Этапе 3.
"""

import csv
import math
from typing import List, Tuple

def v2(x: int) -> int:
    """2-адическая валентность: степень максимальной степени 2, делящей x."""
    if x == 0: return 0
    return (x & -x).bit_length() - 1

def collatz_shifts_actual(n: int, max_steps: int = 100) -> List[int]:
    """Эталонный shift-вектор через полную симуляцию Коллатца."""
    shifts = []
    x = n
    for _ in range(max_steps):
        if x == 1: break
        if x % 2 == 0:
            a = v2(x)
            x >>= a
        else:
            x = 3 * x + 1
            a = v2(x)
            x >>= a
        shifts.append(a)
    return shifts

def predict_shifts_from_k(k: int, m: int) -> List[int]:
    """
    Предиктор shift-вектора на основе рекуррентной формулы R_{n+1} = (3*R_n + 2) >> a_n.
    Возвращает список [a_0, a_1, ..., a_{m-1}].
    """
    # Начальное состояние: N_0 = k*3^0 - 1 = k - 1
    N = k - 1
    if N <= 0: return []
    
    shifts = []
    R = N >> v2(N)  # R_0
    
    for _ in range(m):
        val = 3 * R + 2
        a = v2(val)
        shifts.append(a)
        R = val >> a  # R_{n+1}
        
    return shifts

def test_predictor():
    print("=" * 70)
    print("ЭТАП 4: ТЕСТИРОВАНИЕ ПРЕДИКТОРА SHIFT-ВЕКТОРОВ")
    print("=" * 70)
    
    # Тест 1: Zone 2 представитель (75 бит)
    zone2_k = 37742553597887686876149  # 75 бит, d=259
    m_test = 50
    actual = collatz_shifts_actual(zone2_k, m_test)
    predicted = predict_shifts_from_k(zone2_k, m_test)
    match = sum(1 for a, p in zip(actual, predicted) if a == p)
    print(f"\n🔹 Zone 2 (k={zone2_k}, m={m_test}):")
    print(f"   Совпадений: {match}/{m_test} ({match/m_test*100:.1f}%)")
    
    # Тест 2: Family A (2^b - 1)
    family_a_k = (1 << 100) - 1  # 100 бит
    actual_fa = collatz_shifts_actual(family_a_k, m_test)
    predicted_fa = predict_shifts_from_k(family_a_k, m_test)
    match_fa = sum(1 for a, p in zip(actual_fa, predicted_fa) if a == p)
    print(f"\n🔹 Family A (k=2^100-1, m={m_test}):")
    print(f"   Совпадений: {match_fa}/{m_test} ({match_fa/m_test*100:.1f}%)")
    
    # Тест 3: Случайное k
    import random
    rand_k = random.randint(10**15, 10**16)
    actual_r = collatz_shifts_actual(rand_k, m_test)
    predicted_r = predict_shifts_from_k(rand_k, m_test)
    match_r = sum(1 for a, p in zip(actual_r, predicted_r) if a == p)
    print(f"\n🔹 Случайное k ({rand_k}, m={m_test}):")
    print(f"   Совпадений: {match_r}/{m_test} ({match_r/m_test*100:.1f}%)")
    
    print("\n" + "=" * 70)
    if match == m_test and match_fa == m_test and match_r == m_test:
        print("✅ ПРЕДИКТОР РАБОТАЕТ ИДЕАЛЬНО (100% точность)")
        print("   Готов к масштабному поиску Class A центров (Этап 5)")
    else:
        print("⚠️  Обнаружены расхождения. Требуется калибровка начального R_0")
    print("=" * 70)

if __name__ == '__main__':
    test_predictor()