"""
Congruence Survival Depth v2:
Индивидуальный анализ выживания чисел n по уровням k.

Вопрос: как быстро число n "выпадает" из выживших классов при росте k?
"""

import math
import json
import time

def syr(x):
    """Ускоренное отображение: (3x+1)/2^v2(3x+1)"""
    y = 3 * x + 1
    while y % 2 == 0:
        y //= 2
    return y

def steps_to_descent(n, max_steps=10000):
    """Считает число нечётных шагов Syr(x) до первого значения < n."""
    x = n
    peak = n
    for j in range(1, max_steps + 1):
        x = syr(x)
        if x > peak:
            peak = x
        if x < n:
            return j, peak
    return -1, peak  # не упал за max_steps

def analyze_number(n, k_max=50):
    descent_steps, peak = steps_to_descent(n)
    
    # n выживает на уровне k <=> d_max(k) = ceil(1.3*k) <= descent_steps (или descent_steps == -1)
    survival_levels = []
    for k in range(2, k_max + 1):
        d_max = math.ceil(1.3 * k)
        if descent_steps == -1 or descent_steps > d_max:
            survival_levels.append(k)
            
    max_k = max(survival_levels) if survival_levels else 0
    return {
        'n': n,
        'descent_steps': descent_steps,
        'peak': peak,
        'peak_ratio': peak / n if n > 0 else 0,
        'max_k': max_k,
        'survival_levels': survival_levels,
    }

if __name__ == '__main__':
    print("=" * 80)
    print("CONGRUENCE SURVIVAL DEPTH: Анализ долгожителей")
    print("=" * 80)

    # Загружаем выживших из spine_v2_results.json
    try:
        with open(r"C:\Users\Admin\Documents\Collatz\data\spine_v2_results.json") as f:
            prev = json.load(f)
        survivors = prev['all_unique_survivors']
    except Exception:
        survivors = []

    test_set = set(survivors[:200])
    test_set.update([3, 7, 15, 27, 31, 47, 63, 71, 91, 103, 111, 127, 155, 159, 167, 
                     223, 239, 251, 255, 283, 319, 447, 495, 511, 639, 703, 871, 991, 1023,
                     2047, 4095, 8191, 16383, 32767, 65535, 131071, 262143, 524287])
    test_set.discard(1)
    
    test_list = sorted(test_set)
    print(f"Тестируем {len(test_list)} чисел...")
    
    results = [analyze_number(n, k_max=50) for n in test_list]
    results.sort(key=lambda r: (-r['descent_steps'], -r['n']))
    
    print(f"\n{'n':>10} {'steps_desc':>12} {'max_k (d<=desc)':>16} {'peak':>15} {'peak_ratio':>12}")
    print("-" * 75)
    for r in results[:40]:
        desc_str = str(r['descent_steps']) if r['descent_steps'] != -1 else "NEVER (>10k)"
        print(f"{r['n']:10d} {desc_str:>12} {r['max_k']:16d} {r['peak']:15d} {r['peak_ratio']:12.1f}")
        
    print("\n" + "=" * 80)
    print("АНАЛИЗ ЗАВИСИМОСТИ МАКСИМАЛЬНОЙ ГЛУБИНЫ k ОТ n:")
    print("=" * 80)
    
    # Проверим формулу связи descent_steps и max_k
    # descent_steps = d_max(k) = ceil(1.3 * k) => k_max ~ descent_steps / 1.3
    # А как descent_steps зависит от n?
    for r in [res for res in results if res['n'] in [27, 31, 71, 127, 255, 511, 1023, 32767, 131071, 524287]]:
        print(f"n = {r['n']:<8} (log2 ≈ {math.log2(r['n']):.1f} бит): descent_steps = {r['descent_steps']:4d}, max_k = {r['max_k']:3d}, max_k / log2(n) = {r['max_k']/math.log2(r['n']):.2f}")
