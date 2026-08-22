#!/usr/bin/env python3
"""
analyze_zone2_CORRECT.py

ПРАВИЛЬНЫЙ анализ Zone 2 чисел из records_data.py.

КЛЮЧЕВОЙ МОМЕНТ: Коллатц имеет ДВЕ фазы:
  Фаза 1: ПОДЪЁМ от старта до пика (d_to_peak шагов)
  Фаза 2: СПУСК от пика до 1 (ещё ~300+ шагов)

Zone 2 инварианты (d=258, S/d=1.33) относятся ТОЛЬКО к фазе подъёма.
Полная траектория (d_total≈600, S/d≈1.72) — это подъём + спуск.

Предыдущие версии v1-v4 считали ПОЛНУЮ траекторию, поэтому получали d≈600.
"""

import sys
import os

# Добавляем путь к records_data.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from records_data import PATH_RECORDS_BINARY
    print("✓ records_data.py загружен")
except ImportError:
    print("❌ records_data.py не найден!")
    sys.exit(1)


XSTAR = 20152090995747160937051  # Точка слияния Zone 2 (75 бит)


def analyze_to_peak(n):
    """
    Ускоренная odd-to-odd динамика: x_{k+1} = (3*x_k + 1) / 2^{a_k}
    
    Считаем ТОЛЬКО нечётные шаги.
    Пик определяется как МАКСИМАЛЬНАЯ битность среди ВСЕХ промежуточных
    значений (включая чётные 3x+1 до деления).
    Останавливаемся когда текущее значение упало ниже 1/4 от пика
    (значит пик точно пройден).
    """
    if n <= 1 or n % 2 == 0:
        return None
    
    cur = n
    input_bits = n.bit_length()
    
    # Отслеживание пика (по ВСЕМ значениям, включая чётные)
    peak_bits = input_bits
    peak_value = n
    
    # Shift-вектор (только нечётные шаги)
    shifts = []
    
    # Отслеживание нечётных значений (для проверки x*)
    odd_values = [n]
    
    max_iter = 10000
    for _ in range(max_iter):
        if cur <= 1:
            break
        
        # Шаг 1: 3x + 1 (cur нечётное → результат чётный)
        val = 3 * cur + 1
        
        # !! Измеряем пик ДО деления !!
        val_bits = val.bit_length()
        if val_bits > peak_bits:
            peak_bits = val_bits
            peak_value = val
        
        # Шаг 2: делим на 2^a
        a = (val & -val).bit_length() - 1  # v2(val)
        cur = val >> a
        
        shifts.append(a)
        odd_values.append(cur)
        
        # Условие остановки: упали значительно ниже пика
        if cur.bit_length() < peak_bits - 10 and len(shifts) > 5:
            break
    
    # Теперь найдём, на каком шаге был достигнут пик
    # Пик — это максимум среди 3*odd_values[k]+1 для k=0..len-2
    peak_step = 0
    max_pre_div = 0
    for k in range(len(odd_values) - 1):
        pre_div = 3 * odd_values[k] + 1
        if pre_div.bit_length() > max_pre_div:
            max_pre_div = pre_div.bit_length()
            peak_step = k + 1  # шаг k+1 (после k-го нечётного значения)
    
    # Метрики ДО пика
    shifts_to_peak = shifts[:peak_step]
    d_to_peak = len(shifts_to_peak)
    S_to_peak = sum(shifts_to_peak)
    
    # Метрики ПОЛНОЙ траектории (для сравнения)
    d_total = len(shifts)
    S_total = sum(shifts)
    
    # Shift-профиль до пика
    if d_to_peak > 0:
        pct_1 = shifts_to_peak.count(1) / d_to_peak
        pct_2 = shifts_to_peak.count(2) / d_to_peak
        s_d_peak = S_to_peak / d_to_peak
    else:
        pct_1 = pct_2 = s_d_peak = 0
    
    # Проверка прохода через x*
    xstar_step = None
    for k, v in enumerate(odd_values[:peak_step + 1]):
        if v == XSTAR:
            xstar_step = k
            break
    
    return {
        'input_bits': input_bits,
        'peak_bits': peak_bits,  # Должно быть 140 для Zone 2
        'd_to_peak': d_to_peak,  # Должно быть ~258 для Zone 2
        'S_to_peak': S_to_peak,
        'S_d_peak': round(s_d_peak, 4),  # Должно быть ~1.33 для Zone 2
        'd_total': d_total,
        'S_total': S_total,
        'S_d_total': round(S_total / d_total, 4) if d_total > 0 else 0,
        'pct_1': round(pct_1 * 100, 1),
        'pct_2': round(pct_2 * 100, 1),
        'xstar_step': xstar_step,  # None = не проходит, число = шаг
    }


def main():
    print("=" * 90)
    print("  ПРАВИЛЬНЫЙ АНАЛИЗ ZONE 2 — метрики ДО ПИКА vs ПОЛНАЯ ТРАЕКТОРИЯ")
    print("=" * 90)
    
    results = []
    
    for binary in PATH_RECORDS_BINARY:
        binary = binary.strip().replace(' ', '')
        if not binary or not all(c in '01' for c in binary):
            continue
        
        bits = len(binary)
        if bits < 71 or bits > 87:
            continue
        
        n = int(binary, 2)
        if n % 2 == 0:
            continue
        
        r = analyze_to_peak(n)
        if r:
            results.append(r)
    
    if not results:
        print("❌ Нет чисел 71-87 бит в records_data.py")
        return
    
    # Таблица
    print(f"\n  {'Бит':>4} | {'peak':>4} | {'d_peak':>6} | {'S_peak':>6} | {'S/d_pk':>7} | "
          f"{'d_tot':>6} | {'S/d_tot':>7} | {'%1':>5} | {'%2':>5} | {'x*?':>6}")
    print("  " + "-" * 85)
    
    for r in sorted(results, key=lambda x: x['input_bits']):
        xstar_str = f"шаг {r['xstar_step']}" if r['xstar_step'] is not None else "нет"
        print(f"  {r['input_bits']:>4} | {r['peak_bits']:>4} | {r['d_to_peak']:>6} | "
              f"{r['S_to_peak']:>6} | {r['S_d_peak']:>7.4f} | {r['d_total']:>6} | "
              f"{r['S_d_total']:>7.4f} | {r['pct_1']:>5.1f} | {r['pct_2']:>5.1f} | {xstar_str:>6}")
    
    # Итог
    print("\n" + "=" * 90)
    print("  СРАВНЕНИЕ: d_to_peak vs d_total")
    print("=" * 90)
    
    zone2 = [r for r in results if r['peak_bits'] == 140 and r['d_to_peak'] > 200]
    family_a = [r for r in results if r['d_to_peak'] < 100]
    barina = [r for r in results if r['peak_bits'] == 140 and r['d_to_peak'] < 220 and r['d_to_peak'] > 100]
    
    if zone2:
        avg_d_peak = sum(r['d_to_peak'] for r in zone2) / len(zone2)
        avg_d_total = sum(r['d_total'] for r in zone2) / len(zone2)
        avg_sd_peak = sum(r['S_d_peak'] for r in zone2) / len(zone2)
        avg_sd_total = sum(r['S_d_total'] for r in zone2) / len(zone2)
        xstar_count = sum(1 for r in zone2 if r['xstar_step'] is not None)
        
        print(f"\n  Zone 2 кандидаты ({len(zone2)} чисел, peak=140, d>200):")
        print(f"    d_to_peak = {avg_d_peak:.1f}  (ожидается ~258)")
        print(f"    d_total   = {avg_d_total:.1f}  (это ПОЛНАЯ траектория до 1)")
        print(f"    S/d_peak  = {avg_sd_peak:.4f}  (ожидается ~1.33)")
        print(f"    S/d_total = {avg_sd_total:.4f}  (это НЕ инвариант Zone 2)")
        print(f"    Проход x* = {xstar_count}/{len(zone2)}")
    
    if barina:
        print(f"\n  Число Барины ({len(barina)} чисел, peak=140, d=200-220):")
        for r in barina:
            print(f"    {r['input_bits']} бит: d_peak={r['d_to_peak']}, S/d={r['S_d_peak']}, x*={'да' if r['xstar_step'] else 'нет'}")
    
    if family_a:
        print(f"\n  Family A ({len(family_a)} чисел, d<100):")
        for r in family_a:
            print(f"    {r['input_bits']} бит: d_peak={r['d_to_peak']}, S/d={r['S_d_peak']}, peak={r['peak_bits']}")
    
    print(f"""
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║  ОБЪЯСНЕНИЕ РАСХОЖДЕНИЯ:                                               ║
  ║                                                                        ║
  ║  d_to_peak ≈ 258  — число нечётных шагов от старта ДО ПИКА            ║
  ║  d_total   ≈ 600  — число нечётных шагов от старта ДО 1               ║
  ║                                                                        ║
  ║  Zone 2 инварианты (d=258, S/d=1.33) относятся к d_to_peak.           ║
  ║  Предыдущие скрипты v1-v4 считали d_total, поэтому получали d≈600.    ║
  ║  Это НЕ ошибка в данных, а ошибка в ИЗМЕРЕНИИ.                        ║
  ╚══════════════════════════════════════════════════════════════════════════╝
""")


if __name__ == '__main__':
    main()
