"""
Spine Collapse v2: Чистая карта долгожителей.

Исправления:
1. Исключён r=1 (тривиальная неподвижная точка Syr(1)=1)
2. Трекинг УНИКАЛЬНЫХ значений выживших через все k
3. Ключевой вопрос: стабилизируется ли множество профилей?
"""

import math
import json
import time
from multiprocessing import Pool, cpu_count

def syr(x):
    """Ускоренное отображение: (3x+1)/2^v2(3x+1)"""
    y = 3 * x + 1
    while y % 2 == 0:
        y //= 2
    return y

def trailing_ones(r):
    """Число последовательных 1-бит с младшего конца."""
    count = 0
    while r & 1:
        count += 1
        r >>= 1
    return count

def analyze_orbit(r, d_max):
    """Анализирует орбиту r: выживание, пик, профиль сдвигов."""
    x = r
    peak = r
    shifts = []
    for j in range(d_max):
        y = 3 * x + 1
        s = 0
        while y % 2 == 0:
            y //= 2
            s += 1
        shifts.append(s)
        x = y
        peak = max(peak, x)
        if x < r:  # упал ниже старта
            return None
    return {
        'r': r,
        'trailing_ones': trailing_ones(r),
        'peak': peak,
        'peak_ratio': peak / r if r > 0 else 0,
        'total_shift': sum(shifts),
        'avg_shift': sum(shifts) / len(shifts) if shifts else 0,
        'shifts': shifts,
    }

def check_residue(args):
    r, d_max = args
    if r == 1:  # исключаем тривиальную неподвижную точку
        return None
    return analyze_orbit(r, d_max)

def run_for_k(k):
    d_max = math.ceil(1.3 * k)
    mod = 1 << k
    residues = list(range(3, mod, 2))  # нечётные от 3 (исключаем 1)

    tasks = [(r, d_max) for r in residues]
    survivors = []

    if k <= 16:
        for task in tasks:
            result = check_residue(task)
            if result is not None:
                survivors.append(result)
    else:
        with Pool(processes=min(30, cpu_count())) as pool:
            for result in pool.imap_unordered(check_residue, tasks, chunksize=1024):
                if result is not None:
                    survivors.append(result)

    survivors.sort(key=lambda s: s['r'])
    return {
        'k': k,
        'd_max': d_max,
        'total_residues': len(residues),
        'num_survivors': len(survivors),
        'survivor_values': [s['r'] for s in survivors],
        'survivors_detail': survivors[:30],
        'spine_2k_minus1': (mod - 1) in [s['r'] for s in survivors],
    }

if __name__ == '__main__':
    print("=" * 80)
    print("SPINE COLLAPSE v2: Чистая карта долгожителей (r=1 исключён)")
    print("=" * 80)

    results = []
    all_unique_survivors = set()
    new_per_k = {}
    t0 = time.time()

    for k in range(4, 21):
        tk = time.time()
        row = run_for_k(k)
        elapsed = time.time() - tk

        current_set = set(row['survivor_values'])
        new_values = current_set - all_unique_survivors
        all_unique_survivors |= current_set
        new_per_k[k] = sorted(new_values)

        spine_ok = "Y" if row['spine_2k_minus1'] else "N"
        print(f"k={k:2d}  d_max={row['d_max']:2d}  "
              f"survivors={row['num_survivors']:5d}  "
              f"new_unique={len(new_values):4d}  "
              f"total_unique={len(all_unique_survivors):5d}  "
              f"spine={spine_ok}  [{elapsed:.2f}s]")

        if new_values and len(new_values) <= 10:
            print(f"    NEW: {sorted(new_values)}")
        elif new_values:
            nv = sorted(new_values)
            print(f"    NEW (first 10): {nv[:10]}...")

        results.append(row)

    total_time = time.time() - t0

    # Стабильное ядро: значения, присутствующие при ВСЕХ k >= 5
    stable_core = None
    for row in results:
        if row['k'] < 5:
            continue
        s = set(row['survivor_values'])
        if stable_core is None:
            stable_core = s
        else:
            stable_core &= s

    print(f"\nОбщее время: {total_time:.2f}s")
    print(f"\nВсего уникальных долгожителей (k=4..20): {len(all_unique_survivors)}")
    print(f"Стабильное ядро (присутствует при всех k>=5): {sorted(stable_core) if stable_core else 'пусто'}")

    # Рост числа новых значений по k
    print("\n" + "=" * 80)
    print("КЛЮЧЕВОЙ ВОПРОС: стабилизируется ли множество?")
    print(f"{'k':>3} {'new':>5} {'total':>6}  {'trend':>10}")
    print("-" * 40)
    cumulative = 0
    prev_new = 0
    for k in range(4, 21):
        n_new = len(new_per_k[k])
        cumulative += n_new
        trend = ""
        if prev_new > 0:
            ratio = n_new / prev_new
            trend = f"x{ratio:.2f}"
        prev_new = n_new
        print(f"{k:3d} {n_new:5d} {cumulative:6d}  {trend:>10}")

    print("-" * 40)
    if len(new_per_k.get(20, [])) > len(new_per_k.get(19, [])):
        print("ВЕРДИКТ: Множество РАСТЁТ — профили НЕ стабилизируются")
    elif len(new_per_k.get(20, [])) == 0:
        print("ВЕРДИКТ: Множество СТАБИЛИЗИРОВАЛОСЬ — конечное число профилей!")
    else:
        print("ВЕРДИКТ: Множество растёт, но темп замедляется — неясно")

    # Детали стабильного ядра
    if stable_core:
        print(f"\nДетали стабильного ядра ({len(stable_core)} значений):")
        for row in results:
            if row['k'] == 20:
                for s in row['survivors_detail']:
                    if s['r'] in stable_core:
                        print(f"  r={s['r']:6d}  trailing_ones={s['trailing_ones']}  "
                              f"peak_ratio={s['peak_ratio']:.1f}  "
                              f"avg_shift={s['avg_shift']:.2f}")

    # Сохранение
    outpath = r"C:\Users\Admin\Documents\Collatz\data\spine_v2_results.json"
    import os
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    save_data = {
        'all_unique_survivors': sorted(all_unique_survivors),
        'stable_core': sorted(stable_core) if stable_core else [],
        'new_per_k': {str(k): v for k, v in new_per_k.items()},
        'summary': [
            {'k': r['k'], 'd_max': r['d_max'],
             'num_survivors': r['num_survivors'],
             'survivor_values': r['survivor_values']}
            for r in results
        ],
    }
    with open(outpath, 'w') as f:
        json.dump(save_data, f, indent=2)
    print(f"\nРезультаты: {outpath}")
