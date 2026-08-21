"""
basin_test.py — Проходят ли случайные числа через confluence-центры ДО пика?

Для случайной выборки нечётных чисел (bits 10–90) проверяет, встречается ли
в траектории на фазе роста (до пика) одно из известных confluence-центров.

Использование:
  python basin_test.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import collatz_peak

# Confluence-центры (от малого к большому)
CENTERS = {
    121:                        "c121",
    6803:                       "c6803",
    27611:                      "c27611",
    61823:                      "c61823",
    5808671:                    "c5808671",
    20152090995747160937051:    "xstar",
}

CENTERS_SET = set(CENTERS.keys())

SAMPLES_PER_BITS = 1000


def trajectory_to_peak(n: int, max_steps: int = 1000) -> tuple[list[int], int]:
    """
    Ускоренная траектория ДО ПИКА (фаза роста).
    Возвращает (список нечётных x_k до пика включительно, peak_bits).

    Пик = максимальная битность. После пика траектория не интересна.
    """
    cur = n
    while cur > 1 and cur % 2 == 0:
        cur >>= 1

    traj = [cur]
    peak_val = cur
    peak_bits = cur.bit_length()
    peak_idx = 0

    for k in range(1, max_steps + 1):
        if cur <= 1:
            break
        val = 3 * cur + 1
        while val % 2 == 0:
            val >>= 1
        cur = val
        traj.append(cur)

        cb = cur.bit_length()
        if cb > peak_bits:
            peak_bits = cb
            peak_val = cur
            peak_idx = k

    # Обрезаем траекторию до пика (включительно)
    traj_to_peak = traj[:peak_idx + 1]
    return traj_to_peak, peak_bits


def check_centers(traj: list[int]) -> str | None:
    """Проверяет, есть ли в траектории один из центров. Возвращает имя или None."""
    traj_set = set(traj)
    hits = traj_set & CENTERS_SET
    if not hits:
        return None
    # Возвращаем наибольший центр (самый значимый)
    best = max(hits)
    return CENTERS[best]


def generate_odd_b_bit(b: int, rng: random.Random) -> int:
    """Генерирует случайное нечётное число ровно b бит."""
    if b <= 1:
        return 1
    # Старший бит = 1, младший бит = 1 (нечётное)
    n = (1 << (b - 1)) | 1
    # Заполняем средние биты случайно
    for i in range(1, b - 1):
        if rng.random() > 0.5:
            n |= (1 << i)
    return n


def main():
    print(f"{'=' * 90}")
    print(f"  Basin Test — проходят ли случайные числа через confluence-центры до пика?")
    print(f"{'=' * 90}")
    print(f"  Центры: {', '.join(f'{v}={k}' for k, v in sorted(CENTERS.items()))}")
    print(f"  Samples per bitlength: {SAMPLES_PER_BITS}")
    print()

    rng = random.Random()  # каждый запуск — новая выборка

    # Результаты: bits -> {center_name: count}
    results_all = defaultdict(lambda: defaultdict(int))
    results_high = defaultdict(lambda: defaultdict(int))  # ratio > 1.5
    results_very_high = defaultdict(lambda: defaultdict(int))  # ratio > 1.6

    center_names = sorted(CENTERS.values())
    bit_values = list(range(10, 91, 5))

    for b in bit_values:
        for _ in range(SAMPLES_PER_BITS):
            n = generate_odd_b_bit(b, rng)
            traj, peak_bits = trajectory_to_peak(n, max_steps=1000)
            ratio = peak_bits / b

            hit = check_centers(traj)
            hit_name = hit if hit else "none"

            results_all[b][hit_name] += 1
            results_all[b]["_total"] += 1

            if ratio > 1.5:
                results_high[b][hit_name] += 1
                results_high[b]["_total"] += 1

            if ratio > 1.6:
                results_very_high[b][hit_name] += 1
                results_very_high[b]["_total"] += 1

        # Прогресс
        total_so_far = results_all[b]["_total"]
        any_hit = total_so_far - results_all[b].get("none", 0)
        print(f"  bits={b:>3}: {total_so_far} samples, "
              f"hit_any={any_hit}, "
              f"high_ratio(>1.5)={results_high[b].get('_total', 0)}, "
              f"very_high(>1.6)={results_very_high[b].get('_total', 0)}")

    # ══════════════════════════════════════════════════════════════════════════
    # ТАБЛИЦА 1: Все числа
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n{'=' * 90}")
    print(f"  ТАБЛИЦА 1: Все числа")
    print(f"{'=' * 90}")

    header = (f"  {'bits':>4}  {'total':>5}  {'c121':>5}  {'c6803':>5}  "
              f"{'c27611':>6}  {'c61823':>6}  {'c5808671':>8}  {'xstar':>6}  "
              f"{'any':>5}  {'none':>5}")
    print(header)
    print(f"  {'-' * 85}")

    grand_total = 0
    grand_any = 0

    for b in bit_values:
        r = results_all[b]
        total = r.get("_total", 0)
        none_cnt = r.get("none", 0)
        any_cnt = total - none_cnt

        grand_total += total
        grand_any += any_cnt

        print(f"  {b:>4}  {total:>5}  "
              f"{r.get('c121', 0):>5}  "
              f"{r.get('c6803', 0):>5}  "
              f"{r.get('c27611', 0):>6}  "
              f"{r.get('c61823', 0):>6}  "
              f"{r.get('c5808671', 0):>8}  "
              f"{r.get('xstar', 0):>6}  "
              f"{any_cnt:>5}  "
              f"{none_cnt:>5}")

    pct_any = 100 * grand_any / grand_total if grand_total else 0
    print(f"  {'-' * 85}")
    print(f"  {'ALL':>4}  {grand_total:>5}  {'':>5}  {'':>5}  {'':>6}  "
          f"{'':>6}  {'':>8}  {'':>6}  {grand_any:>5}  "
          f"{grand_total - grand_any:>5}  ({pct_any:.1f}%)")

    # ══════════════════════════════════════════════════════════════════════════
    # ТАБЛИЦА 2: Числа с ratio > 1.5
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n{'=' * 90}")
    print(f"  ТАБЛИЦА 2: Числа с ratio > 1.5")
    print(f"{'=' * 90}")
    print(header)
    print(f"  {'-' * 85}")

    grand_total_h = 0
    grand_any_h = 0

    for b in bit_values:
        r = results_high[b]
        total = r.get("_total", 0)
        if total == 0:
            continue
        none_cnt = r.get("none", 0)
        any_cnt = total - none_cnt

        grand_total_h += total
        grand_any_h += any_cnt

        print(f"  {b:>4}  {total:>5}  "
              f"{r.get('c121', 0):>5}  "
              f"{r.get('c6803', 0):>5}  "
              f"{r.get('c27611', 0):>6}  "
              f"{r.get('c61823', 0):>6}  "
              f"{r.get('c5808671', 0):>8}  "
              f"{r.get('xstar', 0):>6}  "
              f"{any_cnt:>5}  "
              f"{none_cnt:>5}")

    if grand_total_h > 0:
        pct_h = 100 * grand_any_h / grand_total_h
        print(f"  {'-' * 85}")
        print(f"  {'ALL':>4}  {grand_total_h:>5}  {'':>5}  {'':>5}  {'':>6}  "
              f"{'':>6}  {'':>8}  {'':>6}  {grand_any_h:>5}  "
              f"{grand_total_h - grand_any_h:>5}  ({pct_h:.1f}%)")

    # ══════════════════════════════════════════════════════════════════════════
    # ТАБЛИЦА 3: Числа с ratio > 1.6
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n{'=' * 90}")
    print(f"  ТАБЛИЦА 3: Числа с ratio > 1.6 (КЛЮЧЕВАЯ)")
    print(f"{'=' * 90}")
    print(header)
    print(f"  {'-' * 85}")

    grand_total_vh = 0
    grand_any_vh = 0

    for b in bit_values:
        r = results_very_high[b]
        total = r.get("_total", 0)
        if total == 0:
            continue
        none_cnt = r.get("none", 0)
        any_cnt = total - none_cnt

        grand_total_vh += total
        grand_any_vh += any_cnt

        print(f"  {b:>4}  {total:>5}  "
              f"{r.get('c121', 0):>5}  "
              f"{r.get('c6803', 0):>5}  "
              f"{r.get('c27611', 0):>6}  "
              f"{r.get('c61823', 0):>6}  "
              f"{r.get('c5808671', 0):>8}  "
              f"{r.get('xstar', 0):>6}  "
              f"{any_cnt:>5}  "
              f"{none_cnt:>5}")

    if grand_total_vh > 0:
        pct_vh = 100 * grand_any_vh / grand_total_vh
        print(f"  {'-' * 85}")
        print(f"  {'ALL':>4}  {grand_total_vh:>5}  {'':>5}  {'':>5}  {'':>6}  "
              f"{'':>6}  {'':>8}  {'':>6}  {grand_any_vh:>5}  "
              f"{grand_total_vh - grand_any_vh:>5}  ({pct_vh:.1f}%)")
    else:
        print(f"  Нет чисел с ratio > 1.6 в выборке.")

    # ══════════════════════════════════════════════════════════════════════════
    # ИТОГ
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n{'=' * 90}")
    print(f"  ИТОГ")
    print(f"{'=' * 90}")
    print(f"  Всего чисел: {grand_total}")
    print(f"  Проходят через центр (любой): {grand_any} ({pct_any:.2f}%)")
    if grand_total_h > 0:
        print(f"  Среди ratio > 1.5: {grand_any_h}/{grand_total_h} ({pct_h:.2f}%)")
    if grand_total_vh > 0:
        print(f"  Среди ratio > 1.6: {grand_any_vh}/{grand_total_vh} ({pct_vh:.2f}%)")
    else:
        print(f"  Среди ratio > 1.6: нет данных")

    print(f"\n  Интерпретация:")
    if grand_total_vh > 0 and pct_vh > 50:
        print(f"  → Большинство аномальных чисел проходят через центры!")
        print(f"  → Confluence-центры — магистрали высоких пиков.")
    elif grand_total_vh > 0 and pct_vh > 10:
        print(f"  → Заметная доля аномальных чисел проходит через центры.")
        print(f"  → Центры — один из путей к высоким пикам, но не единственный.")
    else:
        print(f"  → Центры редко встречаются в случайных траекториях.")
        print(f"  → Они специфичны для определённых входов (Zone 2, рекордсмены).")

    print(f"\n{'=' * 90}")
    print(f"  Готово.")
    print(f"{'=' * 90}")


if __name__ == '__main__':
    main()
