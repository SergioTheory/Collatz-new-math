#!/usr/bin/env python3
"""
targeted_zone2_search.py
Целевой поиск Zone 2 в матрице Septembrino

Стратегия:
1. Для Zone 2 нужна битность 71-87
2. N = k·3^m - 1, bits ≈ log2(k) + m·log2(3)
3. Для bits=71-87: m ≈ (71 - log2(k)) / log2(3) ≈ 20-55 для k=1-10000
"""

import multiprocessing as mp
from multiprocessing import Pool, cpu_count
from collections import defaultdict
import time
import math

def count_trailing_zeros(n):
    if n == 0:
        return 0
    return (n & -n).bit_length() - 1

def collatz_peak(n, max_steps=5000):
    if n <= 1:
        return (n.bit_length(), 0, 0, [])
    
    current = n
    peak_bits = n.bit_length()
    shifts = []
    d = 0
    S = 0
    
    for _ in range(max_steps):
        if current == 1:
            break
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
        
        current_bits = current.bit_length()
        if current_bits > peak_bits:
            peak_bits = current_bits
    
    return (peak_bits, d, S, shifts)

def search_zone2_candidate(args):
    k, m_min, m_max = args
    candidates = []
    
    for m in range(m_min, m_max + 1):
        N = k * (3 ** m) - 1
        bits = N.bit_length()
        
        # Целевой диапазон Zone 2
        if 71 <= bits <= 87:
            peak_bits, d, S, shifts = collatz_peak(N, max_steps=3000)
            s_d = S / d if d > 0 else 0
            ratio = peak_bits / bits if bits > 0 else 0
            
            # Zone 2 критерии
            if 1.25 <= s_d <= 1.40 and ratio > 1.60:
                candidates.append({
                    'k': k,
                    'm': m,
                    'bits': bits,
                    'peak_bits': peak_bits,
                    'd': d,
                    'S': S,
                    's_d': round(s_d, 4),
                    'ratio': round(ratio, 4),
                    'shifts_preview': shifts[:20]
                })
    
    return candidates

def main():
    print("=" * 80)
    print("ЦЕЛЕВОЙ ПОИСК ZONE 2 В МАТРИЦЕ SEPTembrino")
    print("=" * 80)
    
    # Для битности 71-87: m ≈ 20-55 для k=1-10000
    K_MAX = 10000
    M_MIN = 20
    M_MAX = 55
    
    k_values = list(range(1, K_MAX + 1, 2))
    worker_args = [(k, M_MIN, M_MAX) for k in k_values]
    
    print(f"K: 1-{K_MAX}, M: {M_MIN}-{M_MAX} (целевой диапазон для 71-87 бит)")
    print(f"Всего k: {len(k_values)}")
    print()
    
    start_time = time.time()
    all_candidates = []
    
    with Pool(processes=cpu_count()) as pool:
        for result in pool.imap(search_zone2_candidate, worker_args):
            all_candidates.extend(result)
    
    elapsed = time.time() - start_time
    
    print(f"Время: {elapsed:.2f} сек")
    print(f"Найдено Zone 2 кандидатов: {len(all_candidates)}")
    
    if all_candidates:
        print("\n📊 Топ-10 по близости к S/d=1.33:")
        sorted_candidates = sorted(all_candidates, key=lambda x: abs(x['s_d'] - 1.33))[:10]
        for c in sorted_candidates:
            print(f"  k={c['k']:>5}, m={c['m']:>3}, bits={c['bits']:>2}, "
                  f"peak={c['peak_bits']:>3}, d={c['d']:>3}, S/d={c['s_d']:.4f}, ratio={c['ratio']:.4f}")
    else:
        print("\n⚠️  ZONE 2 НЕ НАЙДЕН В МАТРИЦЕ SEPTembrino!")
        print("   Это означает, что Zone 2 — это НЕ свойство матрицы N=k·3^m-1,")
        print("   а отдельная структура, требующая других методов генерации (CRT, peak_hunter).")

if __name__ == '__main__':
    mp.freeze_support()
    main()