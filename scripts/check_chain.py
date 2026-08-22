"""
check_chain.py — Проверка цепочки confluence-центров

Проверяет, проходит ли траектория каждого центра через все меньшие центры.
Если да — они образуют вложенную цепочку:
  x* → 5808671 → 61823 → 27611 → 6803 → 121 → 1

Использование:
  python check_chain.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# (peak, center_value)
CENTERS = [
    (14,  121),
    (16,  6803),
    (18,  27611),
    (22,  61823),
    (27,  5808671),
    (140, 20152090995747160937051),
]


def accel_trajectory_indexed(n: int, max_steps: int = 500_000) -> dict[int, int]:
    """
    Ускоренная траектория. Возвращает {x_value: step_k} для быстрого поиска.
    """
    cur = n
    while cur > 1 and cur % 2 == 0:
        cur >>= 1
    index = {cur: 0}
    for k in range(1, max_steps + 1):
        if cur <= 1:
            break
        val = 3 * cur + 1
        while val % 2 == 0:
            val >>= 1
        cur = val
        if cur not in index:
            index[cur] = k
    return index


def main():
    print(f"{'=' * 78}")
    print(f"  Check Chain — цепочка confluence-центров")
    print(f"{'=' * 78}")
    print()

    # Сортируем от большего peak к меньшему
    centers_desc = sorted(CENTERS, key=lambda x: -x[0])

    # Предвычисляем траектории (от большего к меньшему — большие включают малые)
    trajectories = {}  # center_value -> {x_value: step}

    for peak, center in centers_desc:
        print(f"  Computing trajectory of c({peak}) = {center} "
              f"({center.bit_length()} bits)...")
        traj = accel_trajectory_indexed(center, max_steps=500_000)
        trajectories[center] = traj
        print(f"    {len(traj)} unique values")

    # Проверяем все пары (i → j), где peak_i > peak_j
    print(f"\n{'=' * 78}")
    print(f"  Проверка переходов c_i → c_j (peak_i > peak_j)")
    print(f"{'=' * 78}")

    connections = {}  # (peak_i, peak_j) -> step or None

    for i, (peak_i, center_i) in enumerate(centers_desc):
        traj_i = trajectories[center_i]
        for j in range(i + 1, len(centers_desc)):
            peak_j, center_j = centers_desc[j]

            if center_j in traj_i:
                step = traj_i[center_j]
                connections[(peak_i, peak_j)] = step
                print(f"  c({peak_i}) → c({peak_j}): YES  (step={step})")
            else:
                connections[(peak_i, peak_j)] = None
                print(f"  c({peak_i}) → c({peak_j}): NO")

    # Проверяем последовательную цепочку
    print(f"\n{'=' * 78}")
    print(f"  Последовательная цепочка")
    print(f"{'=' * 78}")

    centers_asc = sorted(CENTERS, key=lambda x: x[0])
    chain_ok = True
    chain_steps = []

    for i in range(len(centers_asc) - 1):
        peak_lo, center_lo = centers_asc[i]
        peak_hi, center_hi = centers_asc[i + 1]

        step = connections.get((peak_hi, peak_lo))
        if step is not None:
            chain_steps.append((peak_hi, peak_lo, step))
            print(f"  c({peak_hi}) → c({peak_lo}): step={step}  ✓")
        else:
            chain_ok = False
            chain_steps.append((peak_hi, peak_lo, None))
            print(f"  c({peak_hi}) → c({peak_lo}): MISSING  ✗")

    # Итог
    print(f"\n{'=' * 78}")
    if chain_ok:
        print(f"  ЦЕПОЧКА ПОДТВЕРЖДЕНА!")
        print()
        chain_str = " → ".join(
            f"c({p})={c}" for p, c in reversed(centers_asc)
        )
        print(f"  {chain_str} → 1")
        print()
        print(f"  Шаги между уровнями:")
        for peak_hi, peak_lo, step in chain_steps:
            print(f"    c({peak_hi}) → c({peak_lo}): {step} нечётных шагов")

        total_steps = sum(s for _, _, s in chain_steps if s is not None)
        print(f"\n  Суммарно от x* до c(14)=121: {total_steps} нечётных шагов")
    else:
        print(f"  ЦЕПОЧКА НЕ ПОЛНАЯ")
        print()
        # Показываем самую длинную подцепочку
        longest = []
        current = []
        for peak_hi, peak_lo, step in chain_steps:
            if step is not None:
                current.append((peak_hi, peak_lo, step))
            else:
                if len(current) > len(longest):
                    longest = current
                current = []
        if len(current) > len(longest):
            longest = current

        if longest:
            print(f"  Самая длинная подцепочка ({len(longest)} звеньев):")
            for peak_hi, peak_lo, step in longest:
                print(f"    c({peak_hi}) → c({peak_lo}): step={step}")

    print(f"\n{'=' * 78}")
    print(f"  Готово.")
    print(f"{'=' * 78}")


if __name__ == '__main__':
    main()
