"""
zone_parity_search.py — Поиск новых зон через перебор parity-строк
Collatz Crystal Hunter — новый подход

Ключевая идея: вместо перебора чисел перебираем ТРАЕКТОРИИ (shift-векторы),
а числа конструируем через CRT. Для каждой траектории можем подобрать
число любой нужной битности.

Использование:
  python zone_parity_search.py --mode search --target-peak 233 --bits 117 146
  python zone_parity_search.py --mode scan --d-range 30 80
  python zone_parity_search.py --mode markov --train zone2_shifts.csv
"""

from __future__ import annotations

import argparse
import csv
import ast
import json
import math
import multiprocessing
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

# ── Импорт из crt_solver ─────────────────────────────────────────────────────

# Добавляем текущую директорию в path
sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import number_from_parity, collatz_peak, analyze_to_peak

LOG2_3 = math.log2(3)


# ============================================================
# БАЗОВЫЕ ФУНКЦИИ
# ============================================================

def shifts_to_parity(shifts: list[int]) -> str:
    """Shift-вектор → parity-строка (1 = odd, 0 = even)"""
    return ''.join('1' + '0' * s for s in shifts)


def random_shift_vector(d: int, S: int) -> list[int]:
    """Случайный вектор из d элементов с суммой S, каждый >= 1"""
    vec = [1] * d
    for _ in range(S - d):
        vec[random.randint(0, d - 1)] += 1
    return vec


def structured_shift_vector(d: int, S: int, style: str = 'zone2') -> list[int]:
    """
    Генерация shift-вектора с определённой структурой.
    style='zone2': имитация Zone 2 (75% единиц, 21% двоек, 4% троек)
    style='dense': больше единиц (90%+), быстрый набор gain
    style='mixed': случайное распределение с весами
    """
    extra = S - d  # сколько "лишних" делений распределить

    if style == 'zone2':
        # Zone 2 паттерн: двойки примерно каждые 3-4 шага
        vec = [1] * d
        # Расставляем двойки с интервалом ~3-4
        positions = list(range(d))
        random.shuffle(positions)
        placed = 0
        for p in positions:
            if placed >= extra:
                break
            # С вероятностью пропорциональной Zone 2 распределению
            r = random.random()
            if r < 0.75:  # оставить единицу
                continue
            elif r < 0.96:  # поставить двойку
                vec[p] += 1
                placed += 1
            else:  # тройка
                add = min(2, extra - placed)
                vec[p] += add
                placed += add

        # Если не распределили всё — добиваем случайно
        while placed < extra:
            p = random.randint(0, d - 1)
            vec[p] += 1
            placed += 1
        return vec

    elif style == 'dense':
        # Концентрируем лишние деления в начале (как Zone 2 адаптер)
        vec = [1] * d
        for i in range(extra):
            pos = random.randint(0, min(d // 4, d - 1))
            vec[pos] += 1
        return vec

    else:  # mixed
        return random_shift_vector(d, S)


def construct_for_bitlength(parity_str: str, target_bits: int):
    """
    Конструирует число заданной битности, реализующее parity-строку.
    Все решения: n0 + k * 2^S.  Ищем k такое, что n попадает в [2^(b-1), 2^b).
    """
    n0 = number_from_parity(parity_str)
    if n0 is None or n0 <= 0:
        return None

    S = parity_str.count('0')
    mod = 1 << S

    lo = 1 << (target_bits - 1)
    hi = 1 << target_bits

    if n0 >= lo and n0 < hi:
        return n0

    if n0 < lo:
        k_min = (lo - n0 + mod - 1) // mod
        candidate = n0 + k_min * mod
        if candidate < hi:
            return candidate
    else:
        # n0 > hi — число слишком большое, нет решения меньше
        return None

    return None


def peak_within_steps(n: int, max_steps: int) -> tuple[int, int]:
    """
    Пик ТОЛЬКО в пределах первых max_steps элементарных шагов Коллатца.
    Возвращает (peak_bits, odd_steps_done).
    Не считает полную траекторию — останавливается ровно на max_steps.
    """
    cur = n
    pb = n.bit_length()
    odd_done = 0
    step = 0
    while step < max_steps and cur > 1:
        if cur & 1:
            cur = cur * 3 + 1
            odd_done += 1
        else:
            cur >>= 1
        step += 1
        cb = cur.bit_length()
        if cb > pb:
            pb = cb
    return pb, odd_done


def extract_shifts(n: int, max_steps: int = 2_000_000) -> list[int]:
    """Извлекает shift-вектор из числа (количество делений на 2 после каждого 3n+1)"""
    cur = n
    shifts = []
    steps = 0
    while cur > 1 and steps < max_steps:
        if cur & 1:
            cur = cur * 3 + 1
            count = 0
            while cur > 1 and cur % 2 == 0:
                cur >>= 1
                count += 1
                steps += 1
            shifts.append(count)
            steps += 1
        else:
            cur >>= 1
            steps += 1
    return shifts


# ============================================================
# РЕЖИМ 1: ЦЕЛЕВОЙ ПОИСК ЗОНЫ
# ============================================================

def _search_worker(args):
    """Воркер для параллельного поиска (module-level для pickling)"""
    (worker_id, target_peak, bits_lo, bits_hi,
     d_lo, d_hi, trials, min_ratio, styles) = args

    rng = random.Random(worker_id * 7919 + int(time.time() * 1000) % 10_000_000)
    results = []
    best_ratio = 0.0
    target_bits_mid = (bits_lo + bits_hi) / 2

    for trial in range(trials):
        d = rng.randint(d_lo, d_hi)

        # Вычисляем нужное S для целевого gain
        gain_target = target_peak - target_bits_mid
        # Добавляем случайное отклонение ±10%
        gain_actual = gain_target * (0.9 + 0.2 * rng.random())
        S = int(d * LOG2_3 - gain_actual)

        if S < d or S > d * 3:
            continue

        # Генерируем shift-вектор
        style = rng.choice(styles)
        try:
            shifts = structured_shift_vector(d, S, style)
        except:
            shifts = random_shift_vector(d, S)

        parity = shifts_to_parity(shifts)

        # Пробуем разные битности
        for tb in range(bits_lo, bits_hi + 1, 2):  # шаг 2 для скорости
            n = construct_for_bitlength(parity, tb)
            if n is None:
                continue

            actual_bits = n.bit_length()
            if actual_bits < bits_lo or actual_bits > bits_hi:
                continue

            # Пик ТОЛЬКО в пределах аккорда (d + S + буфер для граничных пиков)
            chord_steps = d + S + 5
            peak, odd_done = peak_within_steps(n, chord_steps)
            ratio = peak / actual_bits

            if ratio <= min_ratio:
                continue

            # Верификация: реальное d_actual должно быть близко к d_designed
            info = analyze_to_peak(n, max_steps=chord_steps + 50)
            d_actual = info['total_o']
            if d_actual > d + 3:
                # Пик достигается за пределами аккорда — ложный результат
                continue

            results.append({
                'n': str(n),
                'bits': actual_bits,
                'peak': peak,
                'peak_verified': info['peak'],
                'ratio': round(ratio, 6),
                'd': d,
                'd_actual': d_actual,
                'S': S,
                'S_actual': info['total_e'],
                'style': style,
                'trial': trial,
            })

            if ratio > best_ratio:
                best_ratio = ratio
            break

    return results, trials


def run_targeted_search(
    target_peak: int = 233,
    bits_lo: int = 117,
    bits_hi: int = 146,
    d_lo: int = 80,
    d_hi: int = 500,
    min_ratio: float = 1.60,
    total_trials: int = 1_000_000,
    n_workers: int = 0,
    output: str = 'zone_search_results.json',
):
    if n_workers <= 0:
        n_workers = max(1, (os.cpu_count() or 4) - 1)

    trials_per_worker = total_trials // n_workers
    styles = ['zone2', 'dense', 'mixed']

    print(f"\n{'=' * 68}")
    print(f"  Zone Parity Search — Targeted Mode")
    print(f"{'=' * 68}")
    print(f"  Target peak:    {target_peak}")
    print(f"  Input bits:     {bits_lo}–{bits_hi}")
    print(f"  d range:        {d_lo}–{d_hi}")
    print(f"  Min ratio:      {min_ratio}")
    print(f"  Total trials:   {total_trials:,}")
    print(f"  Workers:        {n_workers}")
    print(f"  Styles:         {styles}")
    print(f"{'=' * 68}\n")

    args_list = [
        (wid, target_peak, bits_lo, bits_hi,
         d_lo, d_hi, trials_per_worker, min_ratio, styles)
        for wid in range(n_workers)
    ]

    all_results = []
    t0 = time.time()

    try:
        with multiprocessing.Pool(n_workers) as pool:
            for batch_results, batch_trials in pool.imap_unordered(
                _search_worker, args_list
            ):
                all_results.extend(batch_results)
                if batch_results:
                    for r in batch_results:
                        print(f"  FOUND: bits={r['bits']}, peak={r['peak']}, "
                              f"ratio={r['ratio']:.4f}, d={r['d']}, "
                              f"S={r['S']}, style={r['style']}")
    except KeyboardInterrupt:
        print("\n  Остановлено пользователем.")

    elapsed = time.time() - t0

    # Сортируем и дедуплицируем
    all_results.sort(key=lambda x: -x['ratio'])
    seen = set()
    unique = []
    for r in all_results:
        key = r['n'][:40]
        if key not in seen:
            seen.add(key)
            unique.append(r)
    all_results = unique[:100]

    print(f"\n{'=' * 68}")
    print(f"  Завершено за {elapsed:.1f}с")
    print(f"  Найдено: {len(all_results)}")
    print(f"{'=' * 68}")

    if all_results:
        print(f"\n  Top-10:")
        print(f"  {'bits':>5}  {'peak':>5}  {'ratio':>7}  {'d':>5}  {'S':>5}  style")
        print(f"  {'-' * 50}")
        for r in all_results[:10]:
            print(f"  {r['bits']:>5}  {r['peak']:>5}  {r['ratio']:>7.4f}  "
                  f"{r['d']:>5}  {r['S']:>5}  {r['style']}")

    # Сохраняем
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n  Сохранено: {output}")

    return all_results


# ============================================================
# РЕЖИМ 2: СКАНИРОВАНИЕ КОРОТКИХ АККОРДОВ
# ============================================================

def _scan_worker(args):
    """Сканирование всех d,S в заданном диапазоне с верификацией"""
    (worker_id, d_lo, d_hi, trials_per_ds, min_ratio) = args

    rng = random.Random(worker_id * 6271 + int(time.time() * 1000) % 10_000_000)
    results = []
    total = 0

    # Целевые битности для construct_for_bitlength
    target_bits_range = list(range(50, 201, 5))

    for d in range(d_lo, d_hi + 1):
        for S in range(d, int(d * 2.0) + 1):
            chord_steps = d + S + 5

            for _ in range(trials_per_ds):
                total += 1
                shifts = random_shift_vector(d, S)
                parity = shifts_to_parity(shifts)

                # Перебираем разные битности
                for tb in target_bits_range:
                    n = construct_for_bitlength(parity, tb)
                    if n is None:
                        continue

                    bits = n.bit_length()
                    if bits < 20:
                        continue

                    # Пик ТОЛЬКО в пределах аккорда
                    peak, odd_done = peak_within_steps(n, chord_steps)
                    ratio = peak / bits

                    if ratio <= min_ratio:
                        continue

                    # Верификация: d_actual должно быть близко к d_designed
                    info = analyze_to_peak(n, max_steps=chord_steps + 50)
                    d_actual = info['total_o']
                    if d_actual > d + 3:
                        # Пик за пределами аккорда — ложный результат
                        continue

                    results.append({
                        'n': str(n),
                        'bits': bits,
                        'peak': peak,
                        'peak_verified': info['peak'],
                        'ratio': round(ratio, 6),
                        'd': d,
                        'd_actual': d_actual,
                        'S': S,
                        'S_actual': info['total_e'],
                        'S_d': round(S / d, 4),
                        'constructed_for': tb,
                    })

    return results, total


def run_scan(
    d_lo: int = 30,
    d_hi: int = 80,
    trials_per_ds: int = 500,
    min_ratio: float = 1.62,
    n_workers: int = 0,
    output: str = 'scan_results.json',
):
    if n_workers <= 0:
        n_workers = max(1, (os.cpu_count() or 4) - 1)

    # Разбиваем диапазон d по воркерам
    d_range = d_hi - d_lo + 1
    chunk = max(1, d_range // n_workers)

    print(f"\n{'=' * 68}")
    print(f"  Zone Parity Search — Scan Mode")
    print(f"{'=' * 68}")
    print(f"  d range:        {d_lo}–{d_hi}")
    print(f"  Trials per (d,S): {trials_per_ds}")
    print(f"  Min ratio:      {min_ratio}")
    print(f"  Workers:        {n_workers}")
    print(f"{'=' * 68}\n")

    args_list = []
    for wid in range(n_workers):
        lo = d_lo + wid * chunk
        hi = min(d_lo + (wid + 1) * chunk - 1, d_hi)
        if lo <= hi:
            args_list.append((wid, lo, hi, trials_per_ds, min_ratio))

    all_results = []
    total_checked = 0
    t0 = time.time()

    try:
        with multiprocessing.Pool(n_workers) as pool:
            for batch_results, batch_total in pool.imap_unordered(
                _scan_worker, args_list
            ):
                all_results.extend(batch_results)
                total_checked += batch_total
                if batch_results:
                    for r in batch_results:
                        print(f"  ANOMALY: bits={r['bits']}, peak={r['peak']}, "
                              f"ratio={r['ratio']:.4f}, d={r['d']}, "
                              f"S={r['S']}, S/d={r['S_d']}")
    except KeyboardInterrupt:
        print("\n  Остановлено.")

    elapsed = time.time() - t0

    all_results.sort(key=lambda x: -x['ratio'])
    all_results = all_results[:200]

    print(f"\n{'=' * 68}")
    print(f"  Завершено за {elapsed:.1f}с, проверено {total_checked:,}")
    print(f"  Аномалий (ratio > {min_ratio}): {len(all_results)}")
    print(f"{'=' * 68}")

    if all_results:
        print(f"\n  Top-10:")
        print(f"  {'bits':>5}  {'peak':>5}  {'ratio':>7}  {'d':>4}  {'S':>5}  {'S/d':>6}")
        print(f"  {'-' * 45}")
        for r in all_results[:10]:
            print(f"  {r['bits']:>5}  {r['peak']:>5}  {r['ratio']:>7.4f}  "
                  f"{r['d']:>4}  {r['S']:>5}  {r['S_d']:>6.3f}")

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n  Сохранено: {output}")

    return all_results


# ============================================================
# РЕЖИМ 3: МАРКОВ НА SHIFT-ВЕКТОРАХ
# ============================================================

class ShiftMarkov:
    def __init__(self, order: int = 3):
        self.order = order
        self.transitions = defaultdict(lambda: defaultdict(int))

    def train(self, vectors: list[list[int]]):
        for vec in vectors:
            for i in range(len(vec) - self.order):
                context = tuple(vec[i:i + self.order])
                next_val = vec[i + self.order]
                self.transitions[context][next_val] += 1

    def generate(self, length: int, seed: list[int] | None = None) -> list[int]:
        if seed is None:
            seed = [1] * self.order
        result = list(seed)
        for _ in range(length - self.order):
            context = tuple(result[-self.order:])
            options = self.transitions.get(context)
            if not options:
                result.append(1)
                continue
            total = sum(options.values())
            r = random.randint(1, total)
            cum = 0
            for val, count in options.items():
                cum += count
                if cum >= r:
                    result.append(val)
                    break
        return result

    def stats(self):
        print(f"  Марков order={self.order}")
        print(f"  Контекстов: {len(self.transitions)}")
        total_trans = sum(
            sum(v.values()) for v in self.transitions.values()
        )
        print(f"  Переходов: {total_trans}")


def run_markov(
    train_csv: str = 'zone2_shifts.csv',
    order: int = 3,
    d_target: int = 258,
    trials: int = 100_000,
    min_ratio: float = 1.60,
    output: str = 'markov_results.json',
):
    print(f"\n{'=' * 68}")
    print(f"  Zone Parity Search — Markov Mode")
    print(f"{'=' * 68}")
    print(f"  Training data:  {train_csv}")
    print(f"  Order:          {order}")
    print(f"  Target d:       {d_target}")
    print(f"  Trials:         {trials:,}")
    print(f"  Min ratio:      {min_ratio}")
    print(f"{'=' * 68}\n")

    # Загружаем обучающие данные
    vectors = []
    with open(train_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                vec = ast.literal_eval(row['blocks'])
                vectors.append(vec)
            except:
                pass

    if not vectors:
        print("  Ошибка: нет обучающих данных!")
        return []

    print(f"  Загружено векторов: {len(vectors)}")
    print(f"  Длины: {[len(v) for v in vectors]}")

    # Обучаем Марков
    markov = ShiftMarkov(order=order)
    markov.train(vectors)
    markov.stats()

    # Целевые битности для construct_for_bitlength
    target_bits_range = list(range(70, 151, 3))  # 70, 73, 76, ..., 148

    # Генерируем и проверяем
    results = []
    best_ratio = 0.0
    t0 = time.time()

    for trial in range(trials):
        # Варьируем длину вокруг целевой
        d = d_target + random.randint(-30, 30)

        # Генерируем shift-вектор через Марков
        shifts = markov.generate(d)
        S = sum(shifts)

        parity = shifts_to_parity(shifts)
        chord_steps = d + S + 5

        # Перебираем целевые битности (вместо использования n0 напрямую)
        for tb in target_bits_range:
            n = construct_for_bitlength(parity, tb)
            if n is None:
                continue

            actual_bits = n.bit_length()
            if actual_bits < 50:
                continue

            # Пик ТОЛЬКО в пределах аккорда
            peak, odd_done = peak_within_steps(n, chord_steps)
            ratio = peak / actual_bits

            if ratio <= min_ratio:
                continue

            # Верификация: d_actual должно быть близко к d
            info = analyze_to_peak(n, max_steps=chord_steps + 50)
            d_actual = info['total_o']
            if d_actual > d + 3:
                continue

            results.append({
                'n': str(n),
                'bits': actual_bits,
                'peak': peak,
                'peak_verified': info['peak'],
                'ratio': round(ratio, 6),
                'd': d,
                'd_actual': d_actual,
                'S': S,
                'S_actual': info['total_e'],
                'S_d': round(S / d, 4),
                'constructed_for': tb,
            })

            if ratio > best_ratio:
                best_ratio = ratio
                print(f"  [{trial:>7d}] NEW BEST: bits={actual_bits}, "
                      f"peak={peak}, ratio={ratio:.4f}, d={d}, "
                      f"d_actual={d_actual}, target_bits={tb}")

        if (trial + 1) % 10000 == 0:
            elapsed = time.time() - t0
            rate = (trial + 1) / elapsed
            print(f"  [{trial + 1:>7d}] {rate:.0f}/с, "
                  f"best_ratio={best_ratio:.4f}, found={len(results)}")

    elapsed = time.time() - t0
    results.sort(key=lambda x: -x['ratio'])
    results = results[:200]

    print(f"\n{'=' * 68}")
    print(f"  Завершено за {elapsed:.1f}с")
    print(f"  Найдено (ratio > {min_ratio}): {len(results)}")
    print(f"  Лучший ratio: {best_ratio:.4f}")
    print(f"{'=' * 68}")

    if results:
        print(f"\n  Top-10:")
        for r in results[:10]:
            print(f"  bits={r['bits']}, peak={r['peak']}, ratio={r['ratio']:.4f}, "
                  f"d={r['d']}, S/d={r['S_d']}")

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Сохранено: {output}")

    return results


# ============================================================
# CLI
# ============================================================

def main():
    multiprocessing.freeze_support()

    p = argparse.ArgumentParser(
        description="Zone Parity Search — поиск новых зон через перебор траекторий"
    )
    p.add_argument('--mode', default='search',
                   choices=['search', 'scan', 'markov'],
                   help='search=целевой поиск, scan=сканирование коротких, '
                        'markov=генерация через Марков')

    # Общие
    p.add_argument('--workers', type=int, default=0)
    p.add_argument('--output', default=None)

    # Search mode
    p.add_argument('--target-peak', type=int, default=233)
    p.add_argument('--bits', nargs=2, type=int, default=[117, 146],
                   metavar=('LO', 'HI'))
    p.add_argument('--d-range', nargs=2, type=int, default=[80, 500],
                   metavar=('LO', 'HI'))
    p.add_argument('--trials', type=int, default=1_000_000)
    p.add_argument('--min-ratio', type=float, default=1.60)

    # Scan mode
    p.add_argument('--scan-d', nargs=2, type=int, default=[30, 80],
                   metavar=('LO', 'HI'))
    p.add_argument('--trials-per-ds', type=int, default=500)

    # Markov mode
    p.add_argument('--train', default='zone2_shifts.csv')
    p.add_argument('--order', type=int, default=3)
    p.add_argument('--markov-d', type=int, default=258)
    p.add_argument('--markov-trials', type=int, default=100_000)

    args = p.parse_args()

    if args.mode == 'search':
        output = args.output or 'zone_search_results.json'
        run_targeted_search(
            target_peak=args.target_peak,
            bits_lo=args.bits[0],
            bits_hi=args.bits[1],
            d_lo=args.d_range[0],
            d_hi=args.d_range[1],
            min_ratio=args.min_ratio,
            total_trials=args.trials,
            n_workers=args.workers,
            output=output,
        )

    elif args.mode == 'scan':
        output = args.output or 'scan_results.json'
        run_scan(
            d_lo=args.scan_d[0],
            d_hi=args.scan_d[1],
            trials_per_ds=args.trials_per_ds,
            min_ratio=args.min_ratio,
            n_workers=args.workers,
            output=output,
        )

    elif args.mode == 'markov':
        output = args.output or 'markov_results.json'
        run_markov(
            train_csv=args.train,
            order=args.order,
            d_target=args.markov_d,
            trials=args.markov_trials,
            min_ratio=args.min_ratio,
            output=output,
        )


if __name__ == '__main__':
    main()
