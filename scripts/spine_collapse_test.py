"""
Spine Collapse Experiment: тест гипотезы хребтового сжатия.

Гипотеза: для всех k <= 20, всякий нечётный r mod 2^k,
доживающий до глубины ceil(1.3*k) без падения ниже старта,
имеет r ≡ -1 (mod 2^a) для a >= k/2 (т.е. >= k/2 единиц в хвосте).

Ускоренное отображение: Syr(x) = (3x+1) / 2^{v_2(3x+1)}
Критерий «выжил»: Syr^j(r) >= r для всех j = 1..d_max
"""

import math
import json
import time
from multiprocessing import Pool, cpu_count

def syr(x):
    """Ускоренное отображение Сиракуз: (3x+1)/2^v2(3x+1)"""
    y = 3 * x + 1
    # Делим на 2 пока чётное
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

def check_residue(args):
    """Проверяет один остаток r: выживает ли до глубины d_max,
    и если да — сколько trailing ones."""
    r, d_max = args
    x = r
    for j in range(d_max):
        x = syr(x)
        if x < r:  # упал ниже старта — «умер»
            return None  # не выжил
    # Выжил! Возвращаем (r, trailing_ones)
    return (r, trailing_ones(r))

def run_for_k(k):
    """Запускает проверку для одного значения k."""
    d_max = math.ceil(1.3 * k)
    # Все нечётные r в [1, 2^k - 1]
    mod = 1 << k
    residues = list(range(1, mod, 2))  # нечётные от 1 до 2^k - 1
    
    tasks = [(r, d_max) for r in residues]
    
    survivors = []
    counterexamples = []
    threshold = k / 2
    
    # Для k <= 16 — однопоточно (быстрее из-за overhead пула)
    # Для k > 16 — используем пул
    if k <= 16:
        for task in tasks:
            result = check_residue(task)
            if result is not None:
                r_val, t_ones = result
                survivors.append((r_val, t_ones))
                if t_ones < threshold:
                    counterexamples.append((r_val, t_ones))
    else:
        with Pool(processes=min(30, cpu_count())) as pool:
            for result in pool.imap_unordered(check_residue, tasks, chunksize=1024):
                if result is not None:
                    r_val, t_ones = result
                    survivors.append((r_val, t_ones))
                    if t_ones < threshold:
                        counterexamples.append((r_val, t_ones))
    
    return {
        'k': k,
        'd_max': d_max,
        'total_odd_residues': len(residues),
        'num_survivors': len(survivors),
        'num_counterexamples': len(counterexamples),
        'counterexamples': counterexamples[:20],  # первые 20 для анализа
        'survivors_sample': survivors[:10],  # первые 10 для контроля
        # Контрольная проверка: 2^k - 1 (все единицы) выживает?
        'spine_control': (mod - 1) in [s[0] for s in survivors],
    }

if __name__ == '__main__':
    print("=" * 70)
    print("SPINE COLLAPSE EXPERIMENT")
    print("Гипотеза: выжившие до глубины ceil(1.3k) имеют >= k/2 trailing ones")
    print("=" * 70)
    
    results = []
    t0 = time.time()
    
    for k in range(4, 21):
        tk = time.time()
        row = run_for_k(k)
        elapsed = time.time() - tk
        
        status = "✅ ЧИСТО" if row['num_counterexamples'] == 0 else "❌ КОНТРПРИМЕР"
        spine_ok = "✓" if row['spine_control'] else "✗"
        
        print(f"k={k:2d}  d_max={row['d_max']:2d}  "
              f"residues={row['total_odd_residues']:7d}  "
              f"survivors={row['num_survivors']:5d}  "
              f"counter={row['num_counterexamples']:3d}  "
              f"spine={spine_ok}  "
              f"{status}  [{elapsed:.2f}s]")
        
        if row['num_counterexamples'] > 0:
            for ce in row['counterexamples'][:5]:
                r_val, t_ones = ce
                print(f"    КОНТРПРИМЕР: r={r_val} (bin=...{bin(r_val)[-min(k,32):]}) "
                      f"trailing_ones={t_ones} < {k/2:.1f}")
        
        results.append(row)
    
    total_time = time.time() - t0
    print(f"\nОбщее время: {total_time:.2f}s")
    
    # Итоговая таблица
    print("\n" + "=" * 70)
    print("ИТОГОВАЯ ТАБЛИЦА")
    print(f"{'k':>3} {'d_max':>5} {'residues':>9} {'survivors':>9} "
          f"{'counter':>7} {'spine':>5} {'verdict':>12}")
    print("-" * 70)
    
    total_counter = 0
    for row in results:
        spine_ok = "✓" if row['spine_control'] else "✗"
        verdict = "ЧИСТО" if row['num_counterexamples'] == 0 else "КОНТРПРИМЕР"
        total_counter += row['num_counterexamples']
        print(f"{row['k']:3d} {row['d_max']:5d} {row['total_odd_residues']:9d} "
              f"{row['num_survivors']:9d} {row['num_counterexamples']:7d} "
              f"{spine_ok:>5} {verdict:>12}")
    
    print("-" * 70)
    if total_counter == 0:
        print("ВЕРДИКТ: ✅ ГИПОТЕЗА ДЕРЖИТСЯ — 0 контрпримеров для k=4..20")
    else:
        print(f"ВЕРДИКТ: ❌ ГИПОТЕЗА ОПРОВЕРГНУТА — {total_counter} контрпримеров")
    
    # Сохраняем результаты
    outpath = r"C:\Users\Admin\Documents\Collatz\data\spine_collapse_results.json"
    import os
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nРезультаты сохранены: {outpath}")
