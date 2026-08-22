"""
verify_candidates.py — Верификация кандидатов в confluence-центры

Строит обратное дерево depth=5 для каждого кандидата и проверяет,
сколько предшественников дают тот же peak.

Использование:
  python verify_candidates.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import collatz_peak

CANDIDATES = [
    {"peak": 12, "center": 49,      "center_bits": 6},
    {"peak": 16, "center": 6803,    "center_bits": 13},
    {"peak": 18, "center": 27611,   "center_bits": 15},
    {"peak": 22, "center": 61823,   "center_bits": 16},
    {"peak": 27, "center": 5808671, "center_bits": 23},
]


def find_predecessors(m: int, a_max: int = 12, max_bits: int = 200) -> list[tuple[int, int]]:
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


def build_reverse_tree(root: int, depth: int, a_max: int,
                       max_bits: int) -> dict[int, set[int]]:
    tree = {0: {root}}
    all_nodes = {root}
    for d in range(depth):
        nxt = set()
        for m in tree[d]:
            for n, a in find_predecessors(m, a_max=a_max, max_bits=max_bits):
                if n not in all_nodes:
                    all_nodes.add(n)
                    nxt.add(n)
        tree[d + 1] = nxt
    return tree


def main():
    print(f"{'=' * 78}")
    print(f"  Verify Confluence Candidates (depth=5)")
    print(f"{'=' * 78}")
    print()

    results = []

    for cand in CANDIDATES:
        peak = cand["peak"]
        center = cand["center"]
        cbits = cand["center_bits"]
        max_bits_tree = cbits + peak  # фильтр

        print(f"  Processing peak={peak}, center={center} ({cbits} bits), "
              f"max_bits={max_bits_tree}...")

        tree = build_reverse_tree(center, depth=5, a_max=12,
                                  max_bits=max_bits_tree)

        total_nodes = sum(len(v) for v in tree.values())

        # Диапазон битности для проверки
        bit_lo = max(3, cbits - 5)
        bit_hi = peak - 1

        # Собираем узлы в диапазоне
        in_range = []
        for d in range(6):
            for n in tree[d]:
                b = n.bit_length()
                if bit_lo <= b <= bit_hi:
                    in_range.append(n)

        # Проверяем peak
        correct_peak = 0
        correct_nodes = []
        for n in in_range:
            pk, _, _ = collatz_peak(n, max_steps=500_000)
            if pk == peak:
                correct_peak += 1
                correct_nodes.append(n)

        hit_rate = (100 * correct_peak / len(in_range)) if in_range else 0

        if correct_peak >= 5 and hit_rate > 80:
            status = "CONFIRMED"
        elif correct_peak >= 2:
            status = "CANDIDATE"
        elif correct_peak == 1:
            status = "WEAK"
        else:
            status = "REFUTED"

        results.append({
            "peak": peak,
            "center": center,
            "tree_size": total_nodes,
            "in_range": len(in_range),
            "correct_peak": correct_peak,
            "hit_rate": hit_rate,
            "status": status,
        })

        print(f"    tree={total_nodes}, in_range={len(in_range)}, "
              f"correct_peak={correct_peak}, hit_rate={hit_rate:.1f}%, "
              f"status={status}")

        if correct_nodes and len(correct_nodes) <= 20:
            for n in sorted(correct_nodes, key=lambda x: x.bit_length()):
                print(f"      {n.bit_length()}b: n={n}")

    # Итоговая таблица
    print(f"\n{'=' * 78}")
    print(f"  ИТОГОВАЯ ТАБЛИЦА")
    print(f"{'=' * 78}")
    print(f"  {'peak':>5}  {'center':>12}  {'tree':>6}  {'range':>6}  "
          f"{'correct':>7}  {'hit%':>6}  {'status':<10}")
    print(f"  {'-' * 62}")

    for r in results:
        c_str = str(r["center"])
        if len(c_str) > 10:
            c_str = c_str[:10] + ".."
        print(f"  {r['peak']:>5}  {c_str:>12}  {r['tree_size']:>6}  "
              f"{r['in_range']:>6}  {r['correct_peak']:>7}  "
              f"{r['hit_rate']:>5.1f}%  {r['status']:<10}")

    print(f"\n{'=' * 78}")
    print(f"  Готово.")
    print(f"{'=' * 78}")


if __name__ == '__main__':
    main()
