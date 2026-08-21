"""
reverse_tree_xstar.py — Обратное дерево предшественников x*

Строит дерево предшественников числа x* = 20152090995747160937051
на глубину 7 шагов ускоренной динамики Коллатца.
Фильтр: только предшественники с битностью ≤ 90 (ищем Zone 2 числа 71–87 бит).

Обратный шаг: если m — текущее нечётное число, предшественник n:
  n = (m · 2^a − 1) / 3, где a ≥ 1, n нечётное, n > 0, и m·2^a ≡ 1 (mod 3)

Использование:
  python reverse_tree_xstar.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import collatz_peak

X_STAR = 20152090995747160937051
MAX_BITS = 90   # фильтр: только узлы ≤ 90 бит
A_MAX = 15      # макс сдвиг (в Zone 2 данных первый сдвиг ≤ 8)
MAX_DEPTH = 7

# Zone 2 числа для сверки (нечётные версии — делим чётные на 2 до нечётного)
ZONE2_NUMBERS_RAW = {
    2358909599867980429759:      71,
    4717819199735960859518:      72,  # чётное
    9435638399471921719037:      73,
    18871276798943843438074:     74,  # чётное
    37742553597887686876149:     75,
    75485107195775373752296:     76,  # чётное
    150970214391550747504611:    77,
    301940428783101495009251:    78,
    603880857566202990018507:    79,
    1207761715132405980037043:   80,
    2415523430264811960074099:   81,
    4831046860529623920148297:   82,
    9662093721059247840295139:   83,
    19324187442118495680593175:  84,
    38648374884236991361186739:  85,
    77296749768473982722370787:  86,
    154593499536947965444748439: 87,
}

# Построим set нечётных версий для быстрой проверки
ZONE2_ODD_SET = set()        # {odd_n, ...}
ZONE2_ODD_TO_ORIG = {}       # odd_n -> (original_n, bits)
for n_val, bits in ZONE2_NUMBERS_RAW.items():
    odd_n = n_val
    while odd_n % 2 == 0:
        odd_n >>= 1
    ZONE2_ODD_SET.add(odd_n)
    ZONE2_ODD_TO_ORIG[odd_n] = (n_val, bits)

# Число Барины (71 бит, d=213)
BARINA_71 = 1765856170146672440559


def find_predecessors(m: int, a_max: int = A_MAX,
                      max_bits: int = MAX_BITS) -> list[tuple[int, int]]:
    """
    Находит все нечётные предшественники m с битностью ≤ max_bits.
    Возвращает список (n, a).
    """
    preds = []
    power2 = 1
    for a in range(1, a_max + 1):
        power2 <<= 1  # 2^a
        val = m * power2 - 1
        if val % 3 != 0:
            continue
        n = val // 3
        if n <= 0:
            continue
        if n % 2 == 0:
            continue
        if n.bit_length() > max_bits:
            continue  # ФИЛЬТР ПО БИТНОСТИ
        preds.append((n, a))
    return preds


def forward_trajectory(n: int, max_steps: int = 300) -> list[int]:
    """Прямая ускоренная траектория (нечётные шаги)."""
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


def main():
    print(f"{'=' * 78}")
    print(f"  Reverse Tree of x* = {X_STAR}")
    print(f"{'=' * 78}")
    print(f"  x* bits = {X_STAR.bit_length()}")
    print(f"  Max depth = {MAX_DEPTH}, a_max = {A_MAX}, max_bits = {MAX_BITS}")
    print()

    # ── Строим обратное дерево с фильтром по битности ─────────────────────────

    tree: dict[int, set[int]] = {0: {X_STAR}}
    # child -> (parent, a, depth)
    parents: dict[int, tuple[int, int, int]] = {}
    all_nodes: set[int] = {X_STAR}

    for depth in range(MAX_DEPTH):
        current_level = tree[depth]
        next_level: set[int] = set()

        for m in current_level:
            preds = find_predecessors(m, a_max=A_MAX, max_bits=MAX_BITS)
            for n, a in preds:
                if n not in all_nodes:
                    all_nodes.add(n)
                    next_level.add(n)
                    parents[n] = (m, a, depth + 1)

        tree[depth + 1] = next_level
        print(f"  Depth {depth} -> {depth + 1}: {len(current_level)} nodes "
              f"expanded to {len(next_level)} new predecessors (≤{MAX_BITS} bits)")

    total_nodes = sum(len(v) for v in tree.values())
    print(f"\n  Всего уникальных узлов (≤{MAX_BITS} bits): {total_nodes}")

    # ── Статистика по глубинам ────────────────────────────────────────────────
    print(f"\n  Статистика по глубинам:")
    print(f"  {'depth':>5}  {'nodes':>10}  {'min_bits':>8}  {'max_bits':>8}")
    print(f"  {'-' * 40}")
    for depth in range(MAX_DEPTH + 1):
        nodes = tree[depth]
        if not nodes:
            print(f"  {depth:>5}  {0:>10}")
            continue
        bits_list = [n.bit_length() for n in nodes]
        print(f"  {depth:>5}  {len(nodes):>10}  {min(bits_list):>8}  {max(bits_list):>8}")

    # ── Все узлы 71–87 бит: проверяем peak ────────────────────────────────────
    print(f"\n  Проверка всех узлов с 71 ≤ bits ≤ 87:")
    print(f"  {'-' * 70}")

    candidates_71_87 = []
    for depth in range(MAX_DEPTH + 1):
        for n in tree[depth]:
            bits = n.bit_length()
            if 71 <= bits <= 87:
                candidates_71_87.append((depth, n, bits))

    print(f"  Найдено {len(candidates_71_87)} узлов с 71–87 бит в дереве.")

    if candidates_71_87:
        print(f"\n  Вычисляем peak для каждого...")
        hits_140 = []
        hits_other = []

        for depth, n, bits in candidates_71_87:
            peak, steps, conv = collatz_peak(n, max_steps=500_000)
            ratio = peak / bits

            is_known = n in ZONE2_ODD_SET
            known_str = " ← KNOWN Z2" if is_known else ""

            if peak == 140:
                hits_140.append((depth, n, bits, peak, ratio, known_str))
            elif ratio > 1.58:
                hits_other.append((depth, n, bits, peak, ratio, known_str))

        # Выводим числа с peak=140
        print(f"\n  Числа с peak=140:")
        if hits_140:
            print(f"  {'depth':>5}  {'bits':>4}  {'peak':>4}  {'ratio':>7}  "
                  f"{'known?':<12}  n")
            print(f"  {'-' * 70}")
            hits_140.sort(key=lambda x: (x[2], x[0]))
            for depth, n, bits, peak, ratio, known_str in hits_140:
                n_str = str(n)
                n_short = n_str[:30] + ('...' if len(n_str) > 30 else '')
                print(f"  {depth:>5}  {bits:>4}  {peak:>4}  {ratio:>7.4f}  "
                      f"{known_str:<12}  {n_short}")

            # Сколько новых (не в нашем списке)?
            new_count = sum(1 for _, n, _, _, _, ks in hits_140 if not ks)
            known_count = len(hits_140) - new_count
            print(f"\n  Итого peak=140: {len(hits_140)} чисел "
                  f"({known_count} известных, {new_count} НОВЫХ)")

            # Для новых чисел — детали
            if new_count > 0:
                print(f"\n  НОВЫЕ числа с peak=140 (не в нашем списке Zone 2):")
                for depth, n, bits, peak, ratio, ks in hits_140:
                    if not ks:
                        print(f"    n = {n}")
                        print(f"    bits = {bits}, peak = {peak}, ratio = {ratio:.5f}")
                        print(f"    depth in tree = {depth}")
                        # Путь от x*
                        path = []
                        cur = n
                        while cur in parents:
                            parent, a, d = parents[cur]
                            path.append((d, cur, a, parent))
                            cur = parent
                        if path:
                            print(f"    Path from x*:")
                            for d, child, a, par in reversed(path):
                                print(f"      depth={d}: {par} --a={a}--> {child}")
                        print()
        else:
            print("    Нет.")

        # Выводим числа с ratio > 1.58 но peak ≠ 140
        if hits_other:
            print(f"\n  Другие числа с ratio > 1.58 (peak ≠ 140):")
            print(f"  {'depth':>5}  {'bits':>4}  {'peak':>4}  {'ratio':>7}  n")
            print(f"  {'-' * 55}")
            hits_other.sort(key=lambda x: -x[4])
            for depth, n, bits, peak, ratio, _ in hits_other[:20]:
                n_str = str(n)[:30]
                print(f"  {depth:>5}  {bits:>4}  {peak:>4}  {ratio:>7.4f}  {n_str}")
    else:
        print("  Нет узлов в этом диапазоне.")

    # ── Проверяем все Zone 2 числа ────────────────────────────────────────────
    print(f"\n  Проверка Zone 2 чисел в дереве:")
    print(f"  {'-' * 70}")

    found_z2 = []
    not_found_z2 = []

    for n_orig, bits_orig in sorted(ZONE2_NUMBERS_RAW.items(), key=lambda x: x[1]):
        # Нечётная версия
        odd_n = n_orig
        while odd_n % 2 == 0:
            odd_n >>= 1

        if odd_n in all_nodes:
            depth = -1
            for d in range(MAX_DEPTH + 1):
                if odd_n in tree[d]:
                    depth = d
                    break
            even_note = f" (odd ver of {bits_orig}b)" if n_orig != odd_n else ""
            found_z2.append((bits_orig, depth, even_note))
        else:
            not_found_z2.append(bits_orig)

    if found_z2:
        print(f"  НАЙДЕНЫ в дереве ({len(found_z2)} из {len(ZONE2_NUMBERS_RAW)}):")
        for bits, depth, note in found_z2:
            print(f"    {bits} бит: depth={depth}{note}")

    if not_found_z2:
        print(f"  НЕ найдены ({len(not_found_z2)}):")
        print(f"    битности: {not_found_z2}")

    # ── Прямая проверка: проходят ли Zone 2 числа через x* ───────────────────
    print(f"\n  Прямая проверка: проходят ли Zone 2 числа через x*?")
    print(f"  {'-' * 70}")

    for n_z2, bits_z2 in sorted(ZONE2_NUMBERS_RAW.items(), key=lambda x: x[1]):
        traj = forward_trajectory(n_z2, max_steps=300)
        found_xstar = False
        for k, x_k in enumerate(traj):
            if x_k == X_STAR:
                print(f"    {bits_z2} бит: x_{k} == x*  (шаг {k})")
                found_xstar = True
                break
        if not found_xstar:
            print(f"    {bits_z2} бит: НЕ проходит через x*")

    # ── Число Барины (d=213) ──────────────────────────────────────────────────
    print(f"\n  Число Барины (71 бит, d=213): n = {BARINA_71}")
    print(f"  {'-' * 70}")

    # Проверяем в дереве
    if BARINA_71 in all_nodes:
        for d in range(MAX_DEPTH + 1):
            if BARINA_71 in tree[d]:
                print(f"  Найдено в дереве на глубине {d}!")
                break
    else:
        print(f"  НЕ найдено в дереве (≤{MAX_BITS} бит, глубина ≤{MAX_DEPTH}).")

    # Прямая траектория
    traj_barina = forward_trajectory(BARINA_71, max_steps=500)
    found_xstar_barina = False
    for k, x_k in enumerate(traj_barina):
        if x_k == X_STAR:
            print(f"  x_{k} == x*  → Барина ПРОХОДИТ через x* на шаге {k}!")
            found_xstar_barina = True
            break

    if not found_xstar_barina:
        print(f"  Барина НЕ проходит через x* в {len(traj_barina)} шагах.")
        # Общие точки с деревом
        barina_set = set(traj_barina)
        common = barina_set & all_nodes
        if common:
            print(f"  Но есть {len(common)} общих точек с деревом x*:")
            for c in sorted(common, key=lambda x: x.bit_length()):
                k_barina = traj_barina.index(c)
                depth_tree = -1
                for d in range(MAX_DEPTH + 1):
                    if c in tree[d]:
                        depth_tree = d
                        break
                print(f"    bits={c.bit_length()}, barina_step={k_barina}, "
                      f"tree_depth={depth_tree}, x=...{str(c)[-15:]}")
        else:
            print(f"  Нет общих точек с деревом x*.")

    # ── Распределение битностей ───────────────────────────────────────────────
    print(f"\n  Распределение битностей (все глубины):")
    print(f"  {'-' * 50}")

    bits_by_depth = defaultdict(lambda: defaultdict(int))
    for depth in range(MAX_DEPTH + 1):
        for n in tree[depth]:
            bits_by_depth[depth][n.bit_length()] += 1

    # Суммарная гистограмма
    total_hist = defaultdict(int)
    for depth in range(MAX_DEPTH + 1):
        for b, cnt in bits_by_depth[depth].items():
            total_hist[b] += cnt

    if total_hist:
        for b in sorted(total_hist.keys()):
            cnt = total_hist[b]
            bar = '#' * min(cnt, 60)
            if cnt > 0:
                print(f"  {b:>4} bits: {cnt:>6}  {bar}")

    print(f"\n{'=' * 78}")
    print(f"  Готово.")
    print(f"{'=' * 78}")


if __name__ == '__main__':
    main()
