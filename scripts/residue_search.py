"""
residue_search.py — Beam search по shift-словам Коллатца

Строим shift-слово (a_0, a_1, ...) посимвольно, отсекая тупиковые ветви.
Ускоренная динамика: x_{k+1} = (3·x_k + 1) / 2^{a_k}
После k шагов: x_k = (3^k · x_0 + c_k) / 2^{S_k}

Использование:
  python residue_search.py --bits 88 170 --beam-width 5000
  python residue_search.py --bits 71 87 --d-range 200 270 --min-ratio 1.62
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from crt_solver import collatz_peak

LOG2_3 = math.log2(3)

# Границы бинов по S/d для niching
NICHE_BINS = [
    (0.00, 1.05),  # bin 0: единичные пути, Family A
    (1.05, 1.15),  # bin 1: слабые аккорды
    (1.15, 1.25),  # bin 2: промежуточные
    (1.25, 1.40),  # bin 3: Zone 2-like (S/d≈1.33)
    (1.40, 99.0),  # bin 4: очень тяжёлые
]


def niche_bin(s_over_d: float) -> int:
    """Определяет номер бина по S/d."""
    for i, (lo, hi) in enumerate(NICHE_BINS):
        if lo <= s_over_d < hi:
            return i
    return len(NICHE_BINS) - 1


def beam_prune_niched(frontier: list, beam_width: int) -> tuple[list, list[int]]:
    """
    Beam pruning с niching: делим frontier на бины по S/d,
    каждому бину — квота beam_width // n_bins.
    Внутри бина сортируем по delta (абсолютный gain).
    Возвращает (pruned_frontier, bin_sizes).
    """
    n_bins = len(NICHE_BINS)
    quota = beam_width // n_bins

    # Раскидываем по бинам
    bins: list[list] = [[] for _ in range(n_bins)]
    for st in frontier:
        s_over_d = st.S / max(1, st.k)
        b = niche_bin(s_over_d)
        bins[b].append(st)

    # Сортируем каждый бин по delta (убывание) и берём квоту
    result = []
    bin_sizes = []
    overflow = 0  # неиспользованные слоты от пустых бинов

    # Первый проход: заполняем квоты, считаем overflow
    taken = [[] for _ in range(n_bins)]
    for i in range(n_bins):
        bins[i].sort(key=lambda s: -s.delta)
        take = min(len(bins[i]), quota)
        taken[i] = bins[i][:take]
        overflow += quota - take

    # Второй проход: распределяем overflow пропорционально
    if overflow > 0:
        for i in range(n_bins):
            remaining = bins[i][len(taken[i]):]
            if remaining:
                extra = min(len(remaining), overflow)
                taken[i].extend(remaining[:extra])
                overflow -= extra
            if overflow <= 0:
                break

    for i in range(n_bins):
        result.extend(taken[i])
        bin_sizes.append(len(taken[i]))

    return result, bin_sizes


@dataclass(slots=True)
class State:
    k: int          # число нечётных шагов
    S: int          # сумма сдвигов S_k
    c: int          # коэффициент c_k (big integer)
    r: int          # остаточный класс r_k (big integer)
    delta: float    # k * log2(3) - S (кумулятивный gain)
    score: float    # delta / max(1, k) — для beam pruning


def run_beam_search(
    b_min: int = 88,
    b_max: int = 170,
    d_min: int = 80,
    d_max: int = 300,
    beam_width: int = 5000,
    a_max: int = 5,
    min_ratio: float = 1.62,
    time_limit: float = 600.0,
    max_hits: int = 200,
    niching: bool = True,
    output: str = 'residue_results.json',
):
    print(f"\n{'=' * 68}")
    print(f"  Residue Beam Search")
    print(f"{'=' * 68}")
    print(f"  Target bits:    {b_min}–{b_max}")
    print(f"  d range:        {d_min}–{d_max}")
    print(f"  Beam width:     {beam_width}")
    print(f"  a_max:          {a_max}")
    print(f"  Min ratio:      {min_ratio}")
    print(f"  Niching:        {niching}")
    print(f"  Time limit:     {time_limit}s")
    print(f"{'=' * 68}\n")

    # Границы целевой битности
    low = 1 << (b_min - 1)   # 2^(b_min-1)
    high = (1 << b_max) - 1  # 2^b_max - 1

    # Начальное состояние
    frontier = [State(k=0, S=0, c=0, r=0, delta=0.0, score=0.0)]

    results = []
    t0 = time.time()
    best_delta_ever = 0.0
    best_score_ever = 0.0
    total_verified = 0

    for step in range(d_max):
        if not frontier:
            print(f"  [k={step}] Frontier пуст — останавливаемся.")
            break

        elapsed = time.time() - t0
        if elapsed > time_limit:
            print(f"  Превышен лимит времени ({time_limit}s).")
            break

        if len(results) >= max_hits:
            print(f"  Достигнут лимит хитов ({max_hits}).")
            break

        k_new = step + 1  # после этого шага будет k_new нечётных шагов

        # ---------- Верификация кандидатов (k >= d_min) ----------
        if step >= d_min:
            for st in frontier:
                if st.delta < 0:
                    continue  # gain отрицательный — пик не выше входа

                mod = 1 << st.S
                if mod == 0:
                    continue

                m_start = max(0, (low - st.r + mod - 1) // mod) if st.r < low else 0
                for m in range(m_start, m_start + 10):
                    x0 = st.r + m * mod
                    if x0 > high:
                        break
                    if x0 < low:
                        continue
                    if x0 <= 1 or x0 % 2 == 0:
                        continue

                    total_verified += 1
                    peak, steps_done, conv = collatz_peak(x0, max_steps=500_000)
                    bits = x0.bit_length()
                    ratio = peak / bits

                    if ratio > min_ratio:
                        results.append({
                            'x0': str(x0),
                            'bits': bits,
                            'peak': peak,
                            'ratio': round(ratio, 6),
                            'd': st.k,
                            'S': st.S,
                            'delta': round(st.delta, 4),
                            'score': round(st.score, 6),
                        })
                        print(f"  *** HIT: bits={bits}, peak={peak}, "
                              f"ratio={ratio:.4f}, d={st.k}, S={st.S}, "
                              f"delta={st.delta:.2f}")

        # ---------- Расширение frontier ----------
        new_frontier = []
        seen = set()

        for st in frontier:
            pow_2_S = 1 << st.S  # 2^{S_k}

            for a in range(1, a_max + 1):
                S_new = st.S + a
                c_new = 3 * st.c + pow_2_S
                delta_new = k_new * LOG2_3 - S_new

                # --- Энергетический фильтр ---
                if delta_new < -10:
                    continue
                if S_new > 3 * k_new:
                    continue

                # --- Вычисляем r_new ---
                mod_new = 1 << S_new
                try:
                    inv3k = pow(3, -k_new, mod_new)
                except ValueError:
                    continue
                r_new = (-c_new * inv3k) % mod_new

                # --- Битовый фильтр (interval intersection) ---
                if r_new > high:
                    continue
                m_min = max(0, (low - r_new + mod_new - 1) // mod_new)
                m_max_val = (high - r_new) // mod_new
                if m_min > m_max_val:
                    continue

                # --- Дедупликация ---
                trunc_bits = min(S_new, 64)
                dedup_key = (S_new, r_new & ((1 << trunc_bits) - 1))
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                score_new = delta_new / max(1, k_new)

                new_frontier.append(State(
                    k=k_new,
                    S=S_new,
                    c=c_new,
                    r=r_new,
                    delta=delta_new,
                    score=score_new,
                ))

        # ---------- Beam pruning ----------
        bin_sizes = None
        if niching:
            new_frontier, bin_sizes = beam_prune_niched(new_frontier, beam_width)
        else:
            if len(new_frontier) > beam_width:
                new_frontier.sort(key=lambda s: -s.score)
                new_frontier = new_frontier[:beam_width]

        frontier = new_frontier

        # ---------- Прогресс ----------
        if frontier:
            cur_best_delta = max(s.delta for s in frontier)
            cur_best_score = max(s.score for s in frontier)
            if cur_best_delta > best_delta_ever:
                best_delta_ever = cur_best_delta
            if cur_best_score > best_score_ever:
                best_score_ever = cur_best_score

        if k_new % 5 == 0 or k_new <= 10:
            elapsed = time.time() - t0
            bins_str = f"  bins={bin_sizes}" if bin_sizes else ""
            print(f"  [k={k_new:>3d}]  frontier={len(frontier):>6d}  "
                  f"best_delta={best_delta_ever:>7.2f}  "
                  f"best_score={best_score_ever:>.4f}  "
                  f"hits={len(results)}  verified={total_verified}  "
                  f"t={elapsed:.1f}s{bins_str}")

    # ---------- Итоги ----------
    elapsed = time.time() - t0
    results.sort(key=lambda x: -x['ratio'])
    results = results[:max_hits]

    print(f"\n{'=' * 68}")
    print(f"  Завершено за {elapsed:.1f}с")
    print(f"  Всего верифицировано: {total_verified}")
    print(f"  Найдено (ratio > {min_ratio}): {len(results)}")
    if results:
        print(f"  Лучший ratio: {results[0]['ratio']}")
    print(f"{'=' * 68}")

    if results:
        print(f"\n  Top-10:")
        print(f"  {'bits':>5}  {'peak':>5}  {'ratio':>7}  {'d':>4}  "
              f"{'S':>5}  {'delta':>7}  {'score':>7}")
        print(f"  {'-' * 52}")
        for r in results[:10]:
            print(f"  {r['bits']:>5}  {r['peak']:>5}  {r['ratio']:>7.4f}  "
                  f"{r['d']:>4}  {r['S']:>5}  {r['delta']:>7.2f}  "
                  f"{r['score']:>7.4f}")

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Сохранено: {output}")

    return results


def main():
    p = argparse.ArgumentParser(
        description="Residue Beam Search — направленный поиск аномалий Коллатца"
    )
    p.add_argument('--bits', nargs=2, type=int, default=[88, 170],
                   metavar=('LO', 'HI'))
    p.add_argument('--d-range', nargs=2, type=int, default=[80, 300],
                   metavar=('LO', 'HI'))
    p.add_argument('--beam-width', type=int, default=5000)
    p.add_argument('--a-max', type=int, default=5)
    p.add_argument('--min-ratio', type=float, default=1.62)
    p.add_argument('--time-limit', type=float, default=600.0)
    p.add_argument('--niching', type=str, default='true',
                   help='Niching по S/d бинам (true/false, default true)')
    p.add_argument('--output', default='residue_results.json')

    args = p.parse_args()

    niching = args.niching.lower() in ('true', '1', 'yes')

    run_beam_search(
        b_min=args.bits[0],
        b_max=args.bits[1],
        d_min=args.d_range[0],
        d_max=args.d_range[1],
        beam_width=args.beam_width,
        a_max=args.a_max,
        min_ratio=args.min_ratio,
        time_limit=args.time_limit,
        niching=niching,
        output=args.output,
    )


if __name__ == '__main__':
    main()
