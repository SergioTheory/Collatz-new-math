#!/usr/bin/env python3
"""
diagnose_bitness.py
Проверка: какие битности реально генерируются формулой N = k·3^m - 1
"""

import multiprocessing as mp
from multiprocessing import Pool, cpu_count
from collections import defaultdict
import time
from datetime import datetime

def compute_bitness(args):
    k, m_max = args
    bitness_dist = defaultdict(int)
    max_bits = 0
    
    for m in range(m_max + 1):
        N = k * (3 ** m) - 1
        bits = N.bit_length()
        bin_start = (bits // 10) * 10
        bitness_dist[bin_start] += 1
        if bits > max_bits:
            max_bits = bits
    
    return {
        'k': k,
        'max_bits': max_bits,
        'bitness_dist': dict(bitness_dist),
        'total': sum(bitness_dist.values())
    }

def main():
    print("=" * 80)
    print("ДИАГНОСТИКА БИТНОСТИ для N = k·3^m - 1")
    print("=" * 80)
    
    K_MAX = 10000
    M_MAX = 100
    
    k_values = list(range(1, K_MAX + 1, 2))
    worker_args = [(k, M_MAX) for k in k_values]
    
    print(f"K: 1-{K_MAX} (нечётные), M: 0-{M_MAX}")
    print(f"Всего k: {len(k_values)}")
    print()
    
    start_time = time.time()
    
    with Pool(processes=cpu_count()) as pool:
        results = list(pool.imap(compute_bitness, worker_args))
    
    elapsed = time.time() - start_time
    
    # Агрегация
    total_bitness_dist = defaultdict(int)
    global_max_bits = 0
    total_trajectories = 0
    
    for r in results:
        global_max_bits = max(global_max_bits, r['max_bits'])
        total_trajectories += r['total']
        for bin_start, count in r['bitness_dist'].items():
            total_bitness_dist[bin_start] += count
    
    print(f"Время: {elapsed:.2f} сек")
    print(f"Всего траекторий: {total_trajectories}")
    print(f"\n📊 Распределение битности:")
    print("-" * 60)
    
    for bin_start in sorted(total_bitness_dist.keys()):
        count = total_bitness_dist[bin_start]
        pct = 100 * count / total_trajectories
        marker = ""
        if 70 <= bin_start <= 80:
            marker = "← ZONE 2!"
        elif 80 <= bin_start <= 170:
            marker = "← DEAD ZONE!"
        print(f"  {bin_start:3d}-{bin_start+9:3d} бит: {count:7d} ({pct:5.1f}%) {marker}")
    
    print("-" * 60)
    print(f"\nМин бит: {min(total_bitness_dist.keys())}")
    print(f"Макс бит: {global_max_bits}")
    print(f"Среднее: {sum(k*v for k,v in total_bitness_dist.items()) / total_trajectories:.1f}")
    
    # Примеры для конкретных (k, m)
    print("\n" + "=" * 80)
    print("ПРИМЕРЫ БИТНОСТИ для конкретных (k, m):")
    print("=" * 80)
    
    test_cases = [
        (1, 10), (1, 50), (1, 100),
        (1000, 10), (1000, 50), (1000, 100),
        (10000, 10), (10000, 50), (10000, 100),
    ]
    
    for k, m in test_cases:
        N = k * (3 ** m) - 1
        bits = N.bit_length()
        print(f"  k={k:>5}, m={m:>3}: N.bit_length() = {bits:>3} бит")

if __name__ == '__main__':
    mp.freeze_support()
    main()