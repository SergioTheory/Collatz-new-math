"""
count_zone2_in_tree.py — Сколько чисел с peak=140 в обратном дереве x*?

Строит обратное дерево x* (depth=7, bits≤90, a_max=15), затем для каждого
узла 71–87 бит вычисляет collatz_peak и проверяет peak==140.

Использование:
  python count_zone2_in_tree.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import collatz_peak

X_STAR = 20152090995747160937051
MAX_BITS = 90
A_MAX = 15
MAX_DEPTH = 7


def find_predecessors(m: int) -> list[tuple[int, int]]:
    """Нечётные предшественники m с bits ≤ MAX_BITS."""
    preds = []
    power2 = 1
    for a in range(1, A_MAX + 1):
        power2 <<= 1
        val = m * power2 - 1
        if val % 3 != 0:
            continue
        n = val // 3
        if n <= 0 or n % 2 == 0:
            continue
        if n.bit_length() > MAX_BITS:
            continue
        preds.append((n, a))
    return preds


def main():
    print(f"{'=' * 70}")
    print(f"  Count Zone 2 in Reverse Tree of x*")
    print(f"{'=' * 70}")
    print(f"  x* = {X_STAR}")
    print(f"  depth={MAX_DEPTH}, bits≤{MAX_BITS}, a_max={A_MAX}")
    print()

    # Строим дерево
    tree: dict[int, set[int]] = {0: {X_STAR}}
    all_nodes: set[int] = {X_STAR}

    for depth in range(MAX_DEPTH):
        current = tree[depth]
        nxt: set[int] = set()
        for m in current:
            for n, a in find_predecessors(m):
                if n not in all_nodes:
                    all_nodes.add(n)
                    nxt.add(n)
        tree[depth + 1] = nxt
        print(f"  Depth {depth}->{depth+1}: {len(current)} -> {len(nxt)} nodes")

    total = sum(len(v) for v in tree.values())
    print(f"\n  Всего узлов: {total}")

    # Собираем узлы 71–87 бит
    nodes_by_bits: dict[int, list[int]] = defaultdict(list)
    for depth in range(MAX_DEPTH + 1):
        for n in tree[depth]:
            bits = n.bit_length()
            if 71 <= bits <= 87:
                nodes_by_bits[bits].append(n)

    total_71_87 = sum(len(v) for v in nodes_by_bits.values())
    print(f"  Узлов с 71–87 бит: {total_71_87}")
    print(f"\n  Вычисляем peak для каждого...")

    # Проверяем peak для каждого
    peak_140_by_bits: dict[int, list[int]] = defaultdict(list)

    print(f"\n  {'bits':>4}  {'total':>6}  {'peak=140':>8}  {'fraction':>9}")
    print(f"  {'-' * 35}")

    for bits in range(71, 88):
        nodes = nodes_by_bits.get(bits, [])
        count_140 = 0
        for n in nodes:
            peak, _, _ = collatz_peak(n, max_steps=500_000)
            if peak == 140:
                count_140 += 1
                peak_140_by_bits[bits].append(n)

        frac = f"{100*count_140/len(nodes):.1f}%" if nodes else "—"
        print(f"  {bits:>4}  {len(nodes):>6}  {count_140:>8}  {frac:>9}")

    total_140 = sum(len(v) for v in peak_140_by_bits.values())
    if total_71_87 > 0:
        print(f"  {'-' * 35}")
        print(f"  {'ИТОГО':>4}  {total_71_87:>6}  {total_140:>8}  "
              f"{100*total_140/total_71_87:.1f}%")

    print(f"\n  Всего чисел Zone 2 (peak=140) в дереве x*: {total_140}")

    # Выводим все числа peak=140
    if 0 < total_140 <= 50:
        print(f"\n  Полный список:")
        for bits in range(71, 88):
            for n in peak_140_by_bits.get(bits, []):
                ratio = 140 / bits
                print(f"    {bits}b: n={n}, ratio={ratio:.4f}")

    print(f"\n{'=' * 70}")
    print(f"  Готово.")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
