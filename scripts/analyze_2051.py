"""
analyze_2051.py — Анализ числа 2051 как спускового транзитного хаба

Проверяем гипотезу: 2051 не является восходящим центром слияния (Class A/B),
а является спусковым транзитным хабом — малым числом, через которое проходят
многие траектории при спуске от пика к 1.

Задачи:
1. Траектория 2051 -> пик -> 1 (прямая)
2. Обратное дерево от 2051 (depth=7): какие пики у прообразов?
3. Прямой тест: проходят ли числа с разными пиками через 2051 при СПУСКЕ?
4. Сравнение с другими транзитными хабами (23, 29, 35, 37)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crt_solver import collatz_peak, analyze_to_peak

log23 = 1.584962500721156  # log2(3)


def collatz_trajectory(n, max_steps=500_000):
    """Полная траектория до 1 (нечётные точки)."""
    odd_points = []
    cur = n
    while cur > 1 and len(odd_points) < max_steps:
        if cur & 1:
            odd_points.append(cur)
            cur = cur * 3 + 1
        else:
            cur >>= 1
    if cur == 1:
        odd_points.append(1)
    return odd_points


def accelerated_trajectory(n, max_steps=10000):
    """Ускоренная траектория (только нечётные значения + сдвиги)."""
    cur = n
    points = [cur]
    shifts = []
    for _ in range(max_steps):
        if cur <= 1:
            break
        cur = cur * 3 + 1
        a = 0
        while cur % 2 == 0:
            cur //= 2
            a += 1
        shifts.append(a)
        points.append(cur)
    return points, shifts


def reverse_step(x, max_a=15):
    """Обратный шаг: все нечётные прообразы x."""
    preds = []
    for a in range(1, max_a + 1):
        y = x * (1 << a) - 1
        if y % 3 == 0:
            y3 = y // 3
            if y3 > 0 and y3 % 2 == 1:
                preds.append((y3, a))
    return preds


def build_reverse_tree(root, depth=7, max_bits=200):
    """Строим обратное дерево до заданной глубины."""
    tree = {0: [root]}
    all_nodes = {root}
    for d in range(1, depth + 1):
        tree[d] = []
        for parent in tree[d - 1]:
            for pred, a in reverse_step(parent):
                if pred.bit_length() <= max_bits and pred not in all_nodes:
                    tree[d].append(pred)
                    all_nodes.add(pred)
        if not tree[d]:
            break
    return tree, all_nodes


def check_passes_through(n, target, max_steps=500_000):
    """Проходит ли траектория n через target (на любом участке)?"""
    cur = n
    steps = 0
    while cur > 1 and steps < max_steps:
        if cur == target:
            return True, steps, 'before_peak'
        cur = cur * 3 + 1 if (cur & 1) else (cur >> 1)
        steps += 1
    return False, -1, 'none'


def check_passes_through_descent(n, target, max_steps=500_000):
    """Проходит ли n через target, разделяя на фазу подъёма и спуска."""
    cur = n
    steps = 0
    peak_bits = n.bit_length()
    peak_step = 0
    passed_peak = False

    while cur > 1 and steps < max_steps:
        if cur == target:
            phase = 'descent' if passed_peak else 'ascent'
            return True, steps, phase
        cur = cur * 3 + 1 if (cur & 1) else (cur >> 1)
        steps += 1
        cb = cur.bit_length()
        if cb > peak_bits:
            peak_bits = cb
            peak_step = steps
        # Считаем что прошли пик после того как упали на 10+ бит от максимума
        if not passed_peak and peak_bits - cur.bit_length() > 10:
            passed_peak = True

    return False, -1, 'none'


print("=" * 70)
print("АНАЛИЗ ЧИСЛА 2051 КАК ТРАНЗИТНОГО ХАБА")
print("=" * 70)

# 1. Базовая информация
n = 2051
print(f"\n{'='*40}")
print(f"1. БАЗОВАЯ ИНФОРМАЦИЯ О 2051")
print(f"{'='*40}")
print(f"  Число: {n}")
print(f"  Двоичное: {bin(n)}")
print(f"  Бит: {n.bit_length()}")
print(f"  n mod 3: {n % 3}")
print(f"  3n+1: {3*n+1}")
print(f"  v2(3n+1): {(3*n+1 & -(3*n+1)).bit_length()-1}")

# Прямая траектория
peak_bits, total_steps, converged = collatz_peak(n)
atp = analyze_to_peak(n)
print(f"  Пик: {peak_bits} бит")
print(f"  Шагов до 1: {total_steps}")
print(f"  Converged: {converged}")
print(f"  d (odd steps до пика): {atp['total_o']}")
print(f"  S (even steps до пика): {atp['total_e']}")
if atp['total_o'] > 0:
    print(f"  S/d: {atp['total_e']/atp['total_o']:.4f}")
    print(f"  Gain: {atp['gain']:.2f}")

# Ускоренная траектория
pts, shifts = accelerated_trajectory(n, 50)
print(f"\n  Ускоренная траектория (первые 20 нечётных точек):")
for i, p in enumerate(pts[:20]):
    bits = p.bit_length()
    print(f"    step {i}: {p} ({bits} бит)" + (f" shift={shifts[i]}" if i < len(shifts) else ""))

# 2. Обратное дерево от 2051
print(f"\n{'='*40}")
print(f"2. ОБРАТНОЕ ДЕРЕВО ОТ 2051 (depth=7)")
print(f"{'='*40}")

tree, all_nodes = build_reverse_tree(2051, depth=7, max_bits=200)
total_nodes = sum(len(tree[d]) for d in tree)
print(f"  Всего узлов: {total_nodes}")

for d in sorted(tree.keys()):
    nodes_at_d = tree[d]
    if nodes_at_d:
        bits_list = [x.bit_length() for x in nodes_at_d]
        print(f"  Depth {d}: {len(nodes_at_d)} узлов, bits: {min(bits_list)}–{max(bits_list)}")

# Пики прообразов
print(f"\n  Пики прообразов (глубина 1-7):")
peak_counts = {}
for d in range(1, 8):
    for node in tree.get(d, []):
        pk = collatz_peak(node)[0]
        peak_counts[pk] = peak_counts.get(pk, 0) + 1

for pk in sorted(peak_counts.keys()):
    print(f"    peak={pk}: {peak_counts[pk]} узлов")

# HR по пикам
print(f"\n  Hit Rate по пикам (все прообразы):")
total_preds = sum(peak_counts.values())
for pk in sorted(peak_counts.keys(), key=lambda x: -peak_counts[x])[:15]:
    hr = peak_counts[pk] / total_preds * 100
    print(f"    peak={pk}: {peak_counts[pk]}/{total_preds} = {hr:.1f}%")

# 3. Тест: числа с РАЗНЫМИ пиками проходят через 2051 при СПУСКЕ?
print(f"\n{'='*40}")
print(f"3. СПУСКОВОЙ ТЕСТ: числа с разными пиками -> 2051?")
print(f"{'='*40}")

import random
random.seed(42)

test_targets = [2051, 23, 29, 35, 37]
# Берём случайные числа разных размеров
test_numbers = []
for bits in [20, 30, 40, 50, 60, 70, 80]:
    for _ in range(200):
        x = random.randrange(1 << (bits - 1), 1 << bits) | 1  # нечётное
        test_numbers.append(x)

print(f"  Тестируем {len(test_numbers)} случайных нечётных чисел (20-80 бит)")

for target in test_targets:
    ascent_count = 0
    descent_count = 0
    total_pass = 0
    for x in test_numbers:
        found, step, phase = check_passes_through_descent(x, target)
        if found:
            total_pass += 1
            if phase == 'ascent':
                ascent_count += 1
            else:
                descent_count += 1

    pct = total_pass / len(test_numbers) * 100
    print(f"\n  Цель {target} (= {bin(target)}):")
    print(f"    Проходят: {total_pass}/{len(test_numbers)} ({pct:.2f}%)")
    print(f"    На подъёме: {ascent_count}")
    print(f"    На спуске: {descent_count}")
    if total_pass > 0:
        print(f"    Доля спусковых: {descent_count/total_pass*100:.1f}%")

# 4. Сравнение с известными центрами
print(f"\n{'='*40}")
print(f"4. СРАВНЕНИЕ: ЦЕНТРЫ vs ТРАНЗИТНЫЕ ХАБЫ")
print(f"{'='*40}")

centers_and_hubs = [
    (121, "Class A center (peak 14)"),
    (719, "Class B center (peak 14)"),
    (2051, "Transit hub candidate"),
    (23, "Small transit hub"),
    (29, "Small transit hub"),
    (35, "Small transit hub"),
    (37, "Small transit hub"),
]

for c, label in centers_and_hubs:
    pk = collatz_peak(c)[0]
    atp = analyze_to_peak(c)
    d = atp['total_o']
    s = atp['total_e']
    sd = s / d if d > 0 else 0
    print(f"\n  {c} [{label}]:")
    print(f"    bits={c.bit_length()}, peak={pk}, d={d}, S={s}, S/d={sd:.3f}")

# 5. Вывод
print(f"\n{'='*70}")
print(f"ВЫВОД")
print(f"{'='*70}")
print("""
Если 2051 имеет пик ≤ 14 бит, а подавляющее большинство проходящих через 
него чисел попадают на 2051 на СПУСКЕ (а не на подъёме), то 2051 является
спусковым транзитным хабом, а не восходящим центром слияния.
""")
