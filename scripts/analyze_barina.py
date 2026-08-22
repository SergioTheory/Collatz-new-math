"""
analyze_barina.py — Анализ числа Барины (71 бит, d=213) и сравнение с Zone 2

Число Барины не проходит через x* = 20152090995747160937051.
Ищем: есть ли другая точка слияния с основной Zone 2 траекторией?

Использование:
  python analyze_barina.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import collatz_peak, analyze_to_peak

LOG2_3 = math.log2(3)

BARINA_71 = 1765856170146672440559
ZONE2_71 = 2358909599867980429759  # 71 бит, d=259, peak=140
X_STAR = 20152090995747160937051


def accel_trajectory(n: int, max_steps: int = 500) -> list[int]:
    """Ускоренная траектория (нечётные x_k)."""
    cur = n
    while cur > 1 and cur % 2 == 0:
        cur >>= 1
    traj = [cur]
    for _ in range(max_steps):
        if cur <= 1:
            break
        val = 3 * cur + 1
        while val % 2 == 0:
            val >>= 1
        cur = val
        traj.append(cur)
    return traj


def extract_shifts_local(n: int, max_steps: int = 500) -> list[int]:
    cur = n
    while cur > 1 and cur % 2 == 0:
        cur >>= 1
    shifts = []
    for _ in range(max_steps):
        if cur <= 1:
            break
        val = 3 * cur + 1
        count = 0
        while val % 2 == 0:
            val >>= 1
            count += 1
        shifts.append(count)
        cur = val
    return shifts


def cumulative_gain(shifts: list[int]) -> list[float]:
    result = []
    cs = 0
    for k, s in enumerate(shifts):
        cs += s
        result.append((k + 1) * LOG2_3 - cs)
    return result


def find_predecessors(m: int, a_max: int = 15, max_bits: int = 90) -> list[tuple[int, int]]:
    preds = []
    power2 = 1
    for a in range(1, a_max + 1):
        power2 <<= 1
        val = m * power2 - 1
        if val % 3 != 0:
            continue
        n = val // 3
        if n <= 0 or n % 2 == 0:
            continue
        if n.bit_length() > max_bits:
            continue
        preds.append((n, a))
    return preds


def main():
    print(f"{'=' * 78}")
    print(f"  Analyze Barina (71 bit, d=213)")
    print(f"{'=' * 78}")

    # ── ЧАСТЬ 1: Полная ускоренная траектория ─────────────────────────────────
    print(f"\n  ЧАСТЬ 1: Ускоренная траектория числа Барины")
    print(f"  {'-' * 70}")

    traj_bar = accel_trajectory(BARINA_71, max_steps=500)
    traj_z2 = accel_trajectory(ZONE2_71, max_steps=500)

    print(f"  Barina: n = {BARINA_71}")
    print(f"  bits = {BARINA_71.bit_length()}, len(traj) = {len(traj_bar)}")
    print(f"  Zone2-71: n = {ZONE2_71}")
    print(f"  bits = {ZONE2_71.bit_length()}, len(traj) = {len(traj_z2)}")

    # ── ЧАСТЬ 2: Shift-вектор Барины ─────────────────────────────────────────
    print(f"\n  ЧАСТЬ 2: Shift-вектор Барины")
    print(f"  {'-' * 70}")

    shifts_bar = extract_shifts_local(BARINA_71, max_steps=500)
    d_bar = len(shifts_bar)
    S_bar = sum(shifts_bar)
    gain_bar = cumulative_gain(shifts_bar)

    print(f"  d = {d_bar}, S = {S_bar}, S/d = {S_bar/d_bar:.4f}")
    print(f"  gain = d·log₂3 − S = {d_bar*LOG2_3 - S_bar:.2f}")

    dist_bar = defaultdict(int)
    for s in shifts_bar:
        dist_bar[s] += 1
    print(f"  Распределение:")
    for v in sorted(dist_bar.keys()):
        print(f"    {v}: {dist_bar[v]} ({100*dist_bar[v]/d_bar:.1f}%)")

    print(f"\n  Первые 30 элементов: {shifts_bar[:30]}")
    print(f"  Последние 30 элементов: {shifts_bar[-30:]}")

    max_g = max(gain_bar)
    max_g_k = gain_bar.index(max_g) + 1
    dips = sum(1 for k in range(1, len(gain_bar)) if gain_bar[k] < gain_bar[k-1])
    print(f"\n  Max G(k) = {max_g:.3f} на шаге k={max_g_k}")
    print(f"  Провалов в G(k): {dips}")

    # ── ЧАСТЬ 3: Общие точки с Zone 2 (71 бит) ──────────────────────────────
    print(f"\n  ЧАСТЬ 3: Общие точки Barina ↔ Zone2-71")
    print(f"  {'-' * 70}")

    # Точное совпадение
    z2_set = {x: k for k, x in enumerate(traj_z2)}
    exact_matches = []
    for k_bar, x in enumerate(traj_bar):
        if x in z2_set:
            exact_matches.append((k_bar, z2_set[x], x))

    if exact_matches:
        print(f"  Найдено {len(exact_matches)} точных совпадений!")
        print(f"  {'k_barina':>10}  {'k_zone2':>8}  {'x_bits':>7}  x_value")
        print(f"  {'-' * 60}")
        for k_b, k_z, x in exact_matches[:10]:
            x_str = str(x)[:25] + ('...' if len(str(x)) > 25 else '')
            print(f"  {k_b:>10}  {k_z:>8}  {x.bit_length():>7}  {x_str}")
        if exact_matches:
            k_b, k_z, x = exact_matches[0]
            print(f"\n  Первая точка слияния:")
            print(f"    Barina шаг {k_b}, Zone2 шаг {k_z}")
            print(f"    x = {x}")
            print(f"    x bits = {x.bit_length()}")
            print(f"    Это x*? {'ДА' if x == X_STAR else 'НЕТ'}")
            # После слияния всё совпадает?
            remaining = min(len(traj_bar) - k_b, len(traj_z2) - k_z)
            all_match = all(traj_bar[k_b + i] == traj_z2[k_z + i]
                           for i in range(remaining))
            print(f"    Полное слияние: {'ДА' if all_match else 'НЕТ'} "
                  f"(проверено {remaining} шагов)")
    else:
        print(f"  Нет точных совпадений!")

        # Проверяем по модулю
        MOD = 1 << 30
        z2_mod = {x % MOD: (k, x) for k, x in enumerate(traj_z2)}
        mod_matches = []
        for k_bar, x in enumerate(traj_bar):
            xmod = x % MOD
            if xmod in z2_mod:
                k_z, x_z = z2_mod[xmod]
                mod_matches.append((k_bar, k_z, x, x_z))

        if mod_matches:
            print(f"  Совпадений mod 2^30: {len(mod_matches)}")
            for k_b, k_z, xb, xz in mod_matches[:5]:
                exact = "EXACT" if xb == xz else "mod only"
                print(f"    k_bar={k_b}, k_z2={k_z}, [{exact}]")
        else:
            print(f"  Нет совпадений даже mod 2^30.")

    # ── ЧАСТЬ 4: Обратное дерево от x_{d=213} Барины ─────────────────────────
    print(f"\n  ЧАСТЬ 4: Обратное дерево от пиковой точки Барины")
    print(f"  {'-' * 70}")

    # Находим шаг пика в траектории Барины
    info_bar = analyze_to_peak(BARINA_71, max_steps=500_000)
    d_to_peak = info_bar['total_o']
    print(f"  d до пика = {d_to_peak}")

    # x на шаге d_to_peak
    if d_to_peak < len(traj_bar):
        x_peak_bar = traj_bar[d_to_peak]
    else:
        x_peak_bar = traj_bar[-1]

    print(f"  x_peak = {x_peak_bar} ({x_peak_bar.bit_length()} bits)")
    print(f"  x_peak == x*? {'ДА' if x_peak_bar == X_STAR else 'НЕТ'}")

    # Обратное дерево от x_peak
    tree_nodes: set[int] = {x_peak_bar}
    tree_levels = {0: {x_peak_bar}}

    for depth in range(5):
        current = tree_levels[depth]
        nxt: set[int] = set()
        for m in current:
            for n, a in find_predecessors(m, a_max=15, max_bits=90):
                if n not in tree_nodes:
                    tree_nodes.add(n)
                    nxt.add(n)
        tree_levels[depth + 1] = nxt
        print(f"  Depth {depth}->{depth+1}: {len(current)} -> {len(nxt)} nodes")

    print(f"  Всего узлов: {len(tree_nodes)}")

    # Есть ли x* в дереве?
    if X_STAR in tree_nodes:
        for d in range(6):
            if X_STAR in tree_levels.get(d, set()):
                print(f"  x* найден в дереве на глубине {d}!")
                break
    else:
        print(f"  x* НЕ найден в дереве от пика Барины.")

    # Сколько узлов с peak=140?
    peak_140_in_bar_tree = 0
    for n in tree_nodes:
        if n.bit_length() < 5 or n.bit_length() > 90:
            continue
        pk, _, _ = collatz_peak(n, max_steps=500_000)
        if pk == 140:
            peak_140_in_bar_tree += 1

    print(f"  Узлов с peak=140 в дереве от пика Барины: {peak_140_in_bar_tree}")

    # ── ЧАСТЬ 5: Сравнение shift-векторов ─────────────────────────────────────
    print(f"\n  ЧАСТЬ 5: Сравнение Barina vs Zone2-71")
    print(f"  {'-' * 70}")

    shifts_z2 = extract_shifts_local(ZONE2_71, max_steps=500)
    d_z2 = len(shifts_z2)
    S_z2 = sum(shifts_z2)

    dist_z2 = defaultdict(int)
    for s in shifts_z2:
        dist_z2[s] += 1

    gain_z2 = cumulative_gain(shifts_z2)
    max_g_z2 = max(gain_z2)
    dips_z2 = sum(1 for k in range(1, len(gain_z2)) if gain_z2[k] < gain_z2[k-1])

    print(f"  {'Параметр':<25} {'Barina':>12} {'Zone2-71':>12}")
    print(f"  {'-' * 50}")
    print(f"  {'bits':<25} {BARINA_71.bit_length():>12} {ZONE2_71.bit_length():>12}")
    print(f"  {'peak':<25} {info_bar['peak']:>12} {140:>12}")
    print(f"  {'d':<25} {d_bar:>12} {d_z2:>12}")
    print(f"  {'S':<25} {S_bar:>12} {S_z2:>12}")
    print(f"  {'S/d':<25} {S_bar/d_bar:>12.4f} {S_z2/d_z2:>12.4f}")
    print(f"  {'gain':<25} {d_bar*LOG2_3-S_bar:>12.2f} {d_z2*LOG2_3-S_z2:>12.2f}")
    print(f"  {'max G(k)':<25} {max_g:>12.3f} {max_g_z2:>12.3f}")
    print(f"  {'провалов':<25} {dips:>12} {dips_z2:>12}")

    print(f"\n  Распределение сдвигов:")
    all_vals = sorted(set(list(dist_bar.keys()) + list(dist_z2.keys())))
    print(f"  {'shift':<8} {'Barina':>12} {'Zone2-71':>12}")
    print(f"  {'-' * 35}")
    for v in all_vals:
        p_b = f"{100*dist_bar.get(v,0)/d_bar:.1f}%" if v in dist_bar else "—"
        p_z = f"{100*dist_z2.get(v,0)/d_z2:.1f}%" if v in dist_z2 else "—"
        print(f"  {v:<8} {p_b:>12} {p_z:>12}")

    # Общий суффикс shift-векторов?
    print(f"\n  Общий суффикс shift-векторов:")
    common_suffix = 0
    for i in range(1, min(d_bar, d_z2) + 1):
        if shifts_bar[-i] == shifts_z2[-i]:
            common_suffix += 1
        else:
            break
    print(f"  Общий суффикс: {common_suffix} элементов из min({d_bar}, {d_z2})")
    if common_suffix > 0:
        print(f"  Последние {min(common_suffix, 20)} общих: "
              f"{shifts_bar[-common_suffix:][:20]}")

    # ── ВЫВОД ─────────────────────────────────────────────────────────────────
    print(f"\n{'=' * 78}")
    print(f"  ВЫВОД")
    print(f"{'=' * 78}")

    if exact_matches:
        k_b, k_z, x = exact_matches[0]
        print(f"\n  Barina и Zone2-71 СЛИВАЮТСЯ на шаге {k_b}/{k_z}!")
        print(f"  Точка слияния: {x} ({x.bit_length()} bits)")
        if x == X_STAR:
            print(f"  Это x* — обе траектории проходят через тот же центр.")
        else:
            print(f"  Это НЕ x* — другая точка слияния.")
            print(f"  Barina имеет собственный путь к пику 140, который")
            print(f"  присоединяется к общей траектории позже.")
    else:
        print(f"\n  Barina и Zone2-71 НЕ сливаются (нет общих точек).")
        print(f"  Barina — полностью независимый путь к peak=140.")

    print(f"\n{'=' * 78}")
    print(f"  Готово.")
    print(f"{'=' * 78}")


if __name__ == '__main__':
    main()
