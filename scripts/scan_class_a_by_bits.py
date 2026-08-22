#!/usr/bin/env python3
"""
scan_class_a_by_bits.py
Целевой поиск Class A / Zone 2 кандидатов по битности входа.
Использует CRT-восстановление из Zone 2 parity-шаблона + верификацию.
"""

import sys
import time
from multiprocessing import Pool, cpu_count

# ============================================================================
# ЗОНА 2 PARITY-ШАБЛОН (первые 90 элементов shift-вектора)
# Извлечён из analyze_zone2.py / zone2_shifts.csv
# ============================================================================
ZONE2_PARITY_PREFIX = [
    2, 1, 2, 1, 1, 2, 1, 1, 1, 2, 3, 1, 1, 2, 1, 2, 1, 1, 1, 1,
    1, 2, 1, 1, 1, 2, 2, 1, 2, 1, 1, 2, 1, 1, 1, 2, 3, 1, 1, 2,
    1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 2, 1, 2, 1, 1, 2, 1, 1,
    1, 2, 3, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 2, 1,
    2, 1, 1, 2, 1, 1
]

# ============================================================================
# CRT-ВОССТАНОВЛЕНИЕ ЧИСЛА ИЗ PARITY-СТРОКИ
# ============================================================================
def crt_from_parity(parity, target_bits=None):
    """
    Восстанавливает число n из parity-строки через CRT.
    parity = [a_0, a_1, ..., a_{k-1}]
    Возвращает (n, bits, d, S, ratio) или None.
    """
    n = 0
    mod = 1
    S = 0
    
    for a in parity:
        # x_{k+1} = (3*x_k + 1) / 2^a
        # Обратное: x_k ≡ (2^a * x_{k+1} - 1) * inv(3) mod 2^{S+a}
        # Для простоты используем прямое восстановление:
        n = (n * 2**a - 1) // 3
        if n < 0:
            # Корректировка для отрицательных значений
            n += 2**(S + a)
        S += a
        mod = 2**S
        
    if target_bits:
        # Подгоняем под целевую битность
        current_bits = n.bit_length()
        if current_bits < target_bits:
            shift = target_bits - current_bits
            n += (1 << (S - 1)) * (1 << shift)
        elif current_bits > target_bits:
            n &= (1 << target_bits) - 1
            
    if n <= 0:
        return None
        
    bits = n.bit_length()
    # Быстрая оценка пика (приближённая)
    ratio_est = 1.0 + (S / len(parity) - 1.585) * 0.3  # Эвристика
    return n, bits, len(parity), S, ratio_est

# ============================================================================
# ВЕРИФИКАЦИЯ КАНДИДАТА
# ============================================================================
def verify_candidate(n, min_ratio=1.6, min_s_d=1.25, min_d=50):
    """Полный прогон траектории для верификации."""
    x = n
    d = 0
    S = 0
    peak = n
    shifts = []
    
    while x > 1 and d < 500:
        if x % 2 == 0:
            a = (x & -x).bit_length() - 1
            x >>= a
        else:
            x = 3 * x + 1
            a = (x & -x).bit_length() - 1
            x >>= a
            d += 1
            S += a
            shifts.append(a)
        if x > peak:
            peak = x
            
    if d < min_d:
        return None
        
    ratio = peak.bit_length() / n.bit_length()
    s_d = S / d if d > 0 else 0
    pct1 = shifts.count(1) / d if d > 0 else 0
    pct2 = shifts.count(2) / d if d > 0 else 0
    
    if ratio >= min_ratio and s_d >= min_s_d and pct1 >= 0.65 and pct2 >= 0.2:
        return {
            'n': n, 'bits': n.bit_length(), 'peak_bits': peak.bit_length(),
            'ratio': ratio, 'd': d, 'S': S, 'S_d': s_d,
            'pct1': pct1, 'pct2': pct2, 'shifts': shifts[:20]
        }
    return None

# ============================================================================
# ГЛАВНЫЙ ПОИСК
# ============================================================================
def search_by_bits(target_bits, attempts=1000):
    """Ищет кандидатов в диапазоне битности target_bits ± 2."""
    candidates = []
    for _ in range(attempts):
        # Генерируем число из Zone 2 шаблона + случайный хвост
        parity = ZONE2_PARITY_PREFIX + [1] * (target_bits // 10)
        res = crt_from_parity(parity, target_bits)
        if not res:
            continue
        n, bits, d, S, _ = res
        cand = verify_candidate(n)
        if cand:
            candidates.append(cand)
    return candidates

def main():
    print("="*70)
    print("ЦЕЛЕВОЙ ПОИСК CLASS A / ZONE 2 ПО БИТНОСТИ")
    print("Метод: CRT-восстановление из Zone 2 parity-шаблона")
    print("="*70)
    
    # Диапазон битности, где живёт Zone 2 / Class A
    BIT_RANGES = [71, 75, 80, 85, 87]
    all_candidates = []
    
    for bits in BIT_RANGES:
        print(f"\n🔍 Сканирование битности ~{bits}...")
        cands = search_by_bits(bits, attempts=200)
        all_candidates.extend(cands)
        print(f"   Найдено: {len(cands)}")
        
    print("\n" + "="*70)
    print(f"✅ ВСЕГО НАЙДЕНО КАНДИДАТОВ: {len(all_candidates)}")
    print("="*70)
    
    for i, c in enumerate(all_candidates, 1):
        print(f"\n🎯 Кандидат #{i}:")
        print(f"   n (hex): {hex(c['n'])[:30]}...")
        print(f"   bits: {c['bits']}, peak: {c['peak_bits']}, ratio: {c['ratio']:.3f}")
        print(f"   d: {c['d']}, S: {c['S']}, S/d: {c['S_d']:.3f}")
        print(f"   shift profile: 1s={c['pct1']:.2%}, 2s={c['pct2']:.2%}")
        print(f"   first shifts: {c['shifts']}")

if __name__ == '__main__':
    main()