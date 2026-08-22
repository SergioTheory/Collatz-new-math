#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zone_search.py v2 FINAL
=======================

Поиск "zone-like" семейств для Collatz через обратную генерацию parity-pattern.

Основная идея:
- задаём число odd-шагов d и even-шагов S
- строим parity pattern (схему шагов) длины d+S
- восстанавливаем стартовое n по обратному ходу (CRT-подобная обратная конструкция)
- фильтруем по bit-length и реальной Collatz-проверке ДО ПИКА

Поддерживаемые режимы:
  1) random_parity     - случайное распределение even-шагов между odd-шагами
  2) balanced12        - равномерное распределение (разница <= 1..2)
  3) scaled_from_seed  - масштабирование шаблона even-блоков от seed pattern
  4) sweep_ds          - перебор сетки d/S вокруг целевой зоны

Выход:
- hits.jsonl         : кандидаты, прошедшие фильтр
- near_miss.jsonl    : near-miss по близости к target peak / ratio
- summary.json       : сводка по запуску

Пример:
  python zone_search.py --mode random_parity --bits-min 120 --bits-max 140 --d 259 --s-min 390 --s-max 430 --target-peak 190 --workers 18 --samples 50000 --out-dir out1

Windows CMD:
  python zone_search.py --mode balanced12 --bits-min 120 --bits-max 145 --d 259 --s-min 390 --s-max 430 --target-peak 190 --workers 18 --samples 200000 --out-dir out_bal

Примечание:
- Для очень больших запусков используйте JSONL (построчно), так безопаснее.
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import os
import random
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

LOG23 = math.log2(3)


# ============================================================
# Utility
# ============================================================

def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def safe_int(x: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return default


# ============================================================
# Collatz forward analysis: ДО ПИКА
# ============================================================

def analyze_to_peak(n: int, include_partial_shift: bool = False) -> Dict[str, Any]:
    """
    Анализ ДО ПИКА:
      - bits
      - peak
      - ratio = peak / bits
      - d = odd steps before (or at) peak
      - S = even steps before (or at) peak
      - gain = d*log2(3) - S
      - peak_step

    include_partial_shift=False:
      берём odd/even строго до первого достижения peak
      (классическая интерпретация "до пика")

    include_partial_shift=True:
      если пик достигнут внутри even-хвоста после odd,
      включаем этот odd-шаг тоже.
      В текущей реализации это влияет только в специальных случаях,
      но флаг оставлен для совместимости и исследований.
    """
    if n <= 0:
        raise ValueError("n must be positive")

    start_bits = n.bit_length()
    cur = n

    peak_bits = start_bits
    peak_step = 0

    odd = 0
    even = 0
    step = 0

    odd_at_peak = 0
    even_at_peak = 0

    # Для include_partial_shift
    last_odd_count = 0
    last_even_count = 0

    max_steps = 10_000_000

    while cur != 1 and step < max_steps:
        if cur & 1:
            cur = 3 * cur + 1
            odd += 1
            last_odd_count = odd
            last_even_count = even
        else:
            cur >>= 1
            even += 1

        step += 1
        b = cur.bit_length()

        if b > peak_bits:
            peak_bits = b
            peak_step = step
            odd_at_peak = odd
            even_at_peak = even

    d = odd_at_peak
    S = even_at_peak

    if include_partial_shift:
        # Консервативная логика:
        # если пик случился на even-цепочке сразу после odd, и odd_at_peak может
        # не включать "последний незавершённый odd-блок", можно использовать last_odd_count.
        # В реальной классической Collatz-трассе здесь почти всегда совпадает.
        d = max(d, odd_at_peak)
        S = max(S, even_at_peak)

    ratio = peak_bits / start_bits
    gain = d * LOG23 - S
    S_d = (S / d) if d else float("inf")

    return {
        "bits": start_bits,
        "peak": peak_bits,
        "ratio": ratio,
        "d": d,
        "S": S,
        "S_d": S_d,
        "gain": gain,
        "peak_step": peak_step,
    }


# ============================================================
# Reverse construction helpers
# ============================================================

def inverse_odd_step(x: int) -> Optional[int]:
    """
    Обратный odd-шаг:
      n -> 3n + 1
    Значит обратно:
      n = (x - 1) / 3
    И n должен быть нечётным.
    """
    y = x - 1
    if y % 3 != 0:
        return None
    n = y // 3
    if n <= 0:
        return None
    if (n & 1) == 0:
        return None
    return n


def reverse_from_pattern(blocks: List[int], final_value: int = 1) -> Optional[int]:
    """
    blocks = [e1, e2, ..., ed]
    Интерпретация:
      для каждого odd-шагa:
        odd: n -> 3n+1
        затем ei even-шагов: >>= ei

    Вперёд:
      odd -> even^ei -> odd -> even^e(i+1) -> ...

    Обратно:
      начиная с final_value:
      x <- x << ei
      x <- inverse_odd_step(x)
    """
    x = final_value
    for ei in reversed(blocks):
        x <<= ei
        x = inverse_odd_step(x)
        if x is None:
            return None
    return x


def number_from_parity(blocks: List[int], final_value: int = 1, max_tail_twos: int = 0) -> Optional[int]:
    """
    Базовый reverse_from_pattern.
    max_tail_twos можно использовать, если хотите попробовать
    финальный хвост дополнительных even-сдвигов перед 1.

    Обычно для Collatz естественный конец = 1.
    """
    if max_tail_twos <= 0:
        return reverse_from_pattern(blocks, final_value=final_value)

    # Попробуем несколько вариантов конечного 2^k
    for k in range(max_tail_twos + 1):
        x = reverse_from_pattern(blocks, final_value=(1 << k))
        if x is not None:
            return x
    return None


def number_from_blocks_crt(blocks: List[int]) -> Optional[int]:
    """
    CRT-конструктор по parity-префиксу, полученному из blocks:
      parity = '1' + '0'*s для каждого блока s.
    Возвращает минимальное положительное n или None.
    """
    if not blocks:
        return None

    # Преобразуем в булев parity (True=odd, False=even)
    norm: List[bool] = []
    for s in blocks:
        if s < 0:
            return None
        norm.append(True)
        norm.extend([False] * int(s))

    if not norm:
        return None

    pow3 = 1
    numerator = 0
    k_even = 0

    for is_odd in reversed(norm):
        if is_odd:
            numerator += pow3
            pow3 *= 3
        else:
            numerator *= 2
            k_even += 1

    if k_even == 0:
        return 1

    mod = 1 << k_even
    try:
        inv = pow(pow3 % mod, -1, mod)
    except ValueError:
        return None

    x0 = ((-numerator % mod) * inv) % mod
    return x0 if x0 != 0 else mod


# ============================================================
# Pattern generation
# ============================================================

def balanced_blocks(d: int, S: int, jitter: int = 0, rng: Optional[random.Random] = None) -> List[int]:
    """
    Равномерное распределение S even-шагов по d блокам.
    Разница между блоками обычно <= 1.
    Если jitter > 0, делаем лёгкие локальные перестановки.
    """
    base = S // d
    rem = S % d
    blocks = [base + 1] * rem + [base] * (d - rem)

    if rng is not None:
        rng.shuffle(blocks)

    if jitter > 0 and d >= 2 and rng is not None:
        for _ in range(jitter):
            i = rng.randrange(d)
            j = rng.randrange(d)
            if i == j:
                continue
            # переносим 1 шаг, если не нарушаем неотрицательность
            if blocks[i] > 0:
                blocks[i] -= 1
                blocks[j] += 1

    return blocks


def random_blocks(d: int, S: int, rng: random.Random) -> List[int]:
    """
    Случайное распределение S одинаковых even-шагов по d корзинам.
    """
    blocks = [0] * d
    for _ in range(S):
        blocks[rng.randrange(d)] += 1
    return blocks


def scaled_blocks_from_seed(seed_blocks: List[int], new_S: int, rng: Optional[random.Random] = None) -> List[int]:
    """
    Масштабирование шаблона even-блоков seed -> сумма new_S.
    Сохраняем относительную форму.

    Если длина seed = d, то новый d должен совпадать с len(seed).
    """
    d = len(seed_blocks)
    old_S = sum(seed_blocks)
    if old_S <= 0:
        return balanced_blocks(d, new_S, rng=rng)

    raw = [x * new_S / old_S for x in seed_blocks]
    ints = [int(math.floor(v)) for v in raw]
    rem = new_S - sum(ints)

    frac = [(raw[i] - ints[i], i) for i in range(d)]
    frac.sort(reverse=True)

    for _, i in frac[:rem]:
        ints[i] += 1

    # лёгкая рандомизация одинаковых зон
    if rng is not None:
        rng.shuffle(ints)

    return ints


def scale_blocks_general(
    seed_blocks: List[int],
    target_d: int,
    target_S: int,
    rng: random.Random,
    jitter: int = 0
) -> List[int]:
    """
    Обобщённое масштабирование seed-блоков:
    - меняем и длину (d), и сумму (S);
    - сохраняем форму распределения excess = (s_i - 1) через кумулятив и интерполяцию.

    Гарантирует:
      len(result) == target_d
      sum(result) == target_S
      result[i] >= 1
    """
    if target_d <= 0:
        raise ValueError("target_d must be positive")
    if target_S < target_d:
        raise ValueError("target_S must be >= target_d for blocks >= 1")
    if not seed_blocks:
        raise ValueError("seed_blocks must be non-empty")

    d0 = len(seed_blocks)
    S0 = sum(seed_blocks)

    # Ключевая проверка: если целевые параметры совпадают с seed,
    # возвращаем seed точно (без интерполяции и без jitter),
    # чтобы гарантировать воспроизводимость базового случая.
    if target_d == d0 and target_S == S0:
        return [int(x) for x in seed_blocks]

    excess0 = [max(0, int(s) - 1) for s in seed_blocks]
    E0 = sum(excess0)
    E1 = target_S - target_d

    # Если в seed нет excess, просто случайно раскладываем excess по новой длине.
    if E0 == 0:
        excess1 = [0] * target_d
        for _ in range(E1):
            excess1[rng.randrange(target_d)] += 1
    else:
        # Кумулятив исходного excess
        cum0 = [0]
        for e in excess0:
            cum0.append(cum0[-1] + e)

        # Интерполированный и нормированный кумулятив для target_d
        cum1 = [0.0] * (target_d + 1)
        for i in range(target_d + 1):
            pos = i * d0 / target_d
            idx = int(math.floor(pos))
            frac = pos - idx
            if idx >= d0:
                val = float(cum0[d0])
            else:
                val = (1.0 - frac) * cum0[idx] + frac * cum0[idx + 1]
            cum1[i] = val * E1 / E0

        # Целочисленный монотонный кумулятив
        cum_int = [int(round(v)) for v in cum1]
        cum_int[0] = 0
        for i in range(1, target_d + 1):
            if cum_int[i] < cum_int[i - 1]:
                cum_int[i] = cum_int[i - 1]
        if cum_int[-1] != E1:
            shift = E1 - cum_int[-1]
            for i in range(target_d + 1):
                cum_int[i] += shift
            cum_int[0] = 0
            cum_int[-1] = E1
            for i in range(1, target_d + 1):
                if cum_int[i] < cum_int[i - 1]:
                    cum_int[i] = cum_int[i - 1]
            for i in range(target_d - 1, -1, -1):
                if cum_int[i] > cum_int[i + 1]:
                    cum_int[i] = cum_int[i + 1]

        excess1 = [max(0, cum_int[i + 1] - cum_int[i]) for i in range(target_d)]
        diff = E1 - sum(excess1)
        if diff != 0:
            idxs = list(range(target_d))
            rng.shuffle(idxs)
            if diff > 0:
                for i in range(diff):
                    excess1[idxs[i % target_d]] += 1
            else:
                need = -diff
                k = 0
                while need > 0 and k < target_d * 20:
                    j = idxs[k % target_d]
                    if excess1[j] > 0:
                        excess1[j] -= 1
                        need -= 1
                    k += 1
                if need > 0:
                    for j in range(target_d):
                        while need > 0 and excess1[j] > 0:
                            excess1[j] -= 1
                            need -= 1

    blocks = [e + 1 for e in excess1]

    # Локальный jitter: перенос "1" между соседними блоками.
    if jitter > 0 and target_d >= 2:
        for _ in range(jitter):
            i = rng.randrange(target_d)
            if rng.random() < 0.5:
                j = i - 1 if i > 0 else 1
            else:
                j = i + 1 if i < target_d - 1 else target_d - 2
            if blocks[i] > 1:
                blocks[i] -= 1
                blocks[j] += 1

    # Финальная страховка на точную сумму и минимум 1.
    cur_sum = sum(blocks)
    if cur_sum != target_S:
        delta = target_S - cur_sum
        idxs = list(range(target_d))
        rng.shuffle(idxs)
        if delta > 0:
            for i in range(delta):
                blocks[idxs[i % target_d]] += 1
        else:
            need = -delta
            k = 0
            while need > 0 and k < target_d * 20:
                j = idxs[k % target_d]
                if blocks[j] > 1:
                    blocks[j] -= 1
                    need -= 1
                k += 1
            if need > 0:
                raise RuntimeError("Could not normalize blocks to target sum with min block >= 1")

    return blocks


def load_seed_blocks(path: Path) -> List[int]:
    """
    Форматы:
    1) JSON array: [1,2,1,3,...]
    2) JSON object: {"blocks":[...]}
    3) plain text: 1 2 1 3 ...
    """
    text = path.read_text(encoding="utf-8").strip()

    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            return [int(x) for x in obj]
        if isinstance(obj, dict) and "blocks" in obj:
            return [int(x) for x in obj["blocks"]]
    except Exception:
        pass

    parts = text.replace(",", " ").split()
    return [int(x) for x in parts]


# ============================================================
# Candidate scoring
# ============================================================

def score_candidate(
    n: int,
    target_peak: Optional[int],
    target_ratio: Optional[float],
    include_partial_shift: bool
) -> Dict[str, Any]:
    """
    Возвращает реальный forward-анализ + score.
    """
    a = analyze_to_peak(n, include_partial_shift=include_partial_shift)

    peak = a["peak"]
    ratio = a["ratio"]

    peak_err = None
    ratio_err = None

    score = 0.0
    if target_peak is not None:
        peak_err = abs(peak - target_peak)
        score += peak_err * 10.0

    if target_ratio is not None:
        ratio_err = abs(ratio - target_ratio)
        score += ratio_err * 1000.0

    return {
        "n": n,
        **a,
        "peak_err": peak_err,
        "ratio_err": ratio_err,
        "score": score,
    }


# ============================================================
# Worker config
# ============================================================

@dataclass
class SearchConfig:
    mode: str
    bits_min: int
    bits_max: int

    d: Optional[int]
    s_min: Optional[int]
    s_max: Optional[int]

    target_peak: Optional[int]
    target_ratio: Optional[float]
    constructor: str

    samples: int
    per_ds_samples: int

    workers: int
    seed: int

    include_partial_shift: bool

    near_miss_topk: int
    hit_peak_tol: int
    hit_ratio_tol: float

    out_dir: str

    # mode-specific
    balanced_jitter: int
    max_tail_twos: int

    # sweep_ds
    d_min: Optional[int]
    d_max: Optional[int]
    d_step: int
    s_step: int

    # scaled_from_seed
    seed_blocks_file: Optional[str]

    # v3 analytics
    percentiles: List[float]
    bit_hist_bin: int
    log_constructed: str
    max_constructed_log: int
    ds_prefilter_samples: int
    ds_prefilter_min_hits: int
    target_input_bits_min: Optional[int]
    target_input_bits_max: Optional[int]

    # scaled_ds debug/controls
    scaled_include_seed_baseline: bool
    debug_show_blocks: int
    debug_max_prints: int


# ============================================================
# Worker logic
# ============================================================

def worker_run(args: Tuple[int, SearchConfig]) -> Dict[str, Any]:
    worker_id, cfg = args
    rng = random.Random(cfg.seed + worker_id * 1_000_003)

    local_hits: List[Dict[str, Any]] = []
    local_near: List[Dict[str, Any]] = []
    local_constructed_rows: List[Dict[str, Any]] = []

    tested = 0
    constructed = 0
    constructed_bits_counter: Dict[int, int] = {}
    ds_stats: Dict[str, Dict[str, Any]] = {}
    debug_printed = 0

    target_window_enabled = (
        cfg.target_input_bits_min is not None and
        cfg.target_input_bits_max is not None
    )

    def ds_key(dv: Optional[int], sv: Optional[int]) -> Optional[str]:
        if dv is None or sv is None:
            return None
        return f"{dv}:{sv}"

    def ds_touch(dv: Optional[int], sv: Optional[int]) -> Optional[Dict[str, Any]]:
        k = ds_key(dv, sv)
        if k is None:
            return None
        if k not in ds_stats:
            ds_stats[k] = {
                "pattern_d": int(dv),
                "pattern_S": int(sv),
                "tested": 0,
                "constructed": 0,
                "bits_in_target_window": 0,
                "bits_sum": 0,
                "bits_count": 0,
                "bits_min": None,
                "bits_max": None,
                "hits": 0,
                "prefilter_tested": 0,
                "prefilter_in_window": 0,
            }
        return ds_stats[k]

    def debug_blocks(tag: str, blocks: List[int], dv: Optional[int], sv: Optional[int]) -> None:
        nonlocal debug_printed
        if cfg.debug_show_blocks <= 0:
            return
        if debug_printed >= max(0, cfg.debug_max_prints):
            return
        prefix = blocks[:cfg.debug_show_blocks]
        print(
            f"[debug][w{worker_id}] {tag} d={dv} S={sv} "
            f"len={len(blocks)} sum={sum(blocks)} first={prefix}"
        )
        debug_printed += 1

    def maybe_record(candidate: Dict[str, Any], dv: Optional[int], sv: Optional[int]):
        nonlocal local_hits, local_near

        is_hit = True

        if cfg.target_peak is not None:
            if candidate["peak_err"] is None or candidate["peak_err"] > cfg.hit_peak_tol:
                is_hit = False

        if cfg.target_ratio is not None:
            if candidate["ratio_err"] is None or candidate["ratio_err"] > cfg.hit_ratio_tol:
                is_hit = False

        if is_hit:
            local_hits.append(candidate)
            st = ds_touch(dv, sv)
            if st is not None:
                st["hits"] += 1
        else:
            local_near.append(candidate)
            local_near.sort(key=lambda x: x["score"])
            if len(local_near) > cfg.near_miss_topk:
                local_near = local_near[:cfg.near_miss_topk]

    def try_one(blocks: List[int], dv: Optional[int], sv: Optional[int], prefilter_phase: bool = False):
        nonlocal tested, constructed
        tested += 1
        st = ds_touch(dv, sv)
        if st is not None:
            st["tested"] += 1

        n = None
        if cfg.constructor in ("reverse", "auto"):
            n = number_from_parity(blocks, final_value=1, max_tail_twos=cfg.max_tail_twos)
        if n is None and cfg.constructor in ("crt", "auto"):
            n = number_from_blocks_crt(blocks)
        if n is None:
            return

        constructed += 1

        bits = n.bit_length()
        constructed_bits_counter[bits] = constructed_bits_counter.get(bits, 0) + 1

        if st is not None:
            st["constructed"] += 1
            st["bits_sum"] += bits
            st["bits_count"] += 1
            if st["bits_min"] is None or bits < st["bits_min"]:
                st["bits_min"] = bits
            if st["bits_max"] is None or bits > st["bits_max"]:
                st["bits_max"] = bits

        in_target_window = False
        if target_window_enabled:
            if cfg.target_input_bits_min <= bits <= cfg.target_input_bits_max:
                in_target_window = True
            if st is not None:
                if prefilter_phase:
                    st["prefilter_tested"] += 1
                    if in_target_window:
                        st["prefilter_in_window"] += 1
                if in_target_window:
                    st["bits_in_target_window"] += 1

        if cfg.log_constructed != "none" and len(local_constructed_rows) < cfg.max_constructed_log:
            row: Dict[str, Any] = {
                "n": n,
                "bits": bits,
                "pattern_d": dv,
                "pattern_S": sv,
            }
            if cfg.log_constructed == "full":
                full = score_candidate(
                    n=n,
                    target_peak=cfg.target_peak,
                    target_ratio=cfg.target_ratio,
                    include_partial_shift=cfg.include_partial_shift
                )
                row.update(full)
            local_constructed_rows.append(row)

        if prefilter_phase:
            return

        if bits < cfg.bits_min or bits > cfg.bits_max:
            return

        cand = score_candidate(
            n=n,
            target_peak=cfg.target_peak,
            target_ratio=cfg.target_ratio,
            include_partial_shift=cfg.include_partial_shift
        )
        cand["blocks"] = blocks
        cand["pattern_d"] = dv
        cand["pattern_S"] = sv
        maybe_record(cand, dv, sv)

    # --------------------------------------------------------
    # Mode: random_parity / balanced12
    # --------------------------------------------------------
    if cfg.mode in ("random_parity", "balanced12"):
        if cfg.d is None or cfg.s_min is None or cfg.s_max is None:
            raise ValueError("For random_parity/balanced12 need --d --s-min --s-max")

        for _ in range(cfg.samples):
            S = rng.randint(cfg.s_min, cfg.s_max)

            if cfg.mode == "random_parity":
                blocks = random_blocks(cfg.d, S, rng)
            else:
                blocks = balanced_blocks(cfg.d, S, jitter=cfg.balanced_jitter, rng=rng)

            try_one(blocks, cfg.d, S)

    # --------------------------------------------------------
    # Mode: scaled_from_seed
    # --------------------------------------------------------
    elif cfg.mode == "scaled_from_seed":
        if cfg.seed_blocks_file is None:
            raise ValueError("scaled_from_seed requires --seed-blocks-file")
        if cfg.s_min is None or cfg.s_max is None:
            raise ValueError("scaled_from_seed requires --s-min --s-max")

        seed_blocks = load_seed_blocks(Path(cfg.seed_blocks_file))
        d = len(seed_blocks)

        for _ in range(cfg.samples):
            S = rng.randint(cfg.s_min, cfg.s_max)
            blocks = scaled_blocks_from_seed(seed_blocks, S, rng=rng)
            if len(blocks) != d:
                continue
            try_one(blocks, d, S)

    # --------------------------------------------------------
    # Mode: scaled_ds (seed-guided scaling by both d and S)
    # --------------------------------------------------------
    elif cfg.mode == "scaled_ds":
        if cfg.seed_blocks_file is None:
            raise ValueError("scaled_ds requires --seed-blocks-file")
        if cfg.d_min is None or cfg.d_max is None or cfg.s_min is None or cfg.s_max is None:
            raise ValueError("scaled_ds requires --d-min --d-max --s-min --s-max")

        seed_blocks = load_seed_blocks(Path(cfg.seed_blocks_file))
        seed_d = len(seed_blocks)
        seed_S = sum(seed_blocks)

        all_pairs_raw = [
            (d, S)
            for d in range(cfg.d_min, cfg.d_max + 1, max(1, cfg.d_step))
            for S in range(cfg.s_min, cfg.s_max + 1, max(1, cfg.s_step))
        ]
        all_pairs = [(d, S) for (d, S) in all_pairs_raw if S >= d]
        skipped_invalid_pairs = len(all_pairs_raw) - len(all_pairs)
        if skipped_invalid_pairs > 0 and worker_id == 0:
            print(f"[warn] scaled_ds: skipped {skipped_invalid_pairs} invalid (d,S) pairs with S < d")
        worker_pairs = all_pairs[worker_id::max(1, cfg.workers)]

        for d, S in worker_pairs:
            keep_pair = True

            if cfg.scaled_include_seed_baseline and d == seed_d and S == seed_S:
                exact_seed = [int(x) for x in seed_blocks]
                debug_blocks("scaled_ds_seed_baseline", exact_seed, d, S)
                try_one(exact_seed, d, S, prefilter_phase=False)

            if cfg.ds_prefilter_samples > 0 and target_window_enabled:
                for _ in range(cfg.ds_prefilter_samples):
                    blocks = scale_blocks_general(
                        seed_blocks=seed_blocks,
                        target_d=d,
                        target_S=S,
                        rng=rng,
                        jitter=cfg.balanced_jitter
                    )
                    debug_blocks("scaled_ds_prefilter", blocks, d, S)
                    try_one(blocks, d, S, prefilter_phase=True)

                k = ds_key(d, S)
                warm_hits = ds_stats[k]["prefilter_in_window"] if (k is not None and k in ds_stats) else 0
                keep_pair = warm_hits >= cfg.ds_prefilter_min_hits

            if not keep_pair:
                continue

            trials = cfg.per_ds_samples if cfg.per_ds_samples > 0 else cfg.samples
            for _ in range(trials):
                blocks = scale_blocks_general(
                    seed_blocks=seed_blocks,
                    target_d=d,
                    target_S=S,
                    rng=rng,
                    jitter=cfg.balanced_jitter
                )
                debug_blocks("scaled_ds_main", blocks, d, S)
                try_one(blocks, d, S, prefilter_phase=False)

    # --------------------------------------------------------
    # Mode: sweep_ds
    # --------------------------------------------------------
    elif cfg.mode in ("sweep_ds", "map_ds"):
        if cfg.d_min is None or cfg.d_max is None or cfg.s_min is None or cfg.s_max is None:
            raise ValueError("sweep_ds requires --d-min --d-max --s-min --s-max")

        all_pairs_raw = [
            (d, S)
            for d in range(cfg.d_min, cfg.d_max + 1, max(1, cfg.d_step))
            for S in range(cfg.s_min, cfg.s_max + 1, max(1, cfg.s_step))
        ]
        all_pairs = [(d, S) for (d, S) in all_pairs_raw if S >= d]
        skipped_invalid_pairs = len(all_pairs_raw) - len(all_pairs)
        if skipped_invalid_pairs > 0 and worker_id == 0:
            print(f"[warn] {cfg.mode}: skipped {skipped_invalid_pairs} invalid (d,S) pairs with S < d")
        worker_pairs = all_pairs[worker_id::max(1, cfg.workers)]

        for d, S in worker_pairs:
            keep_pair = True

            if cfg.ds_prefilter_samples > 0 and target_window_enabled:
                for _ in range(cfg.ds_prefilter_samples):
                    if rng.random() < 0.5:
                        blocks = balanced_blocks(d, S, jitter=cfg.balanced_jitter, rng=rng)
                    else:
                        blocks = random_blocks(d, S, rng)
                    try_one(blocks, d, S, prefilter_phase=True)

                k = ds_key(d, S)
                warm_hits = ds_stats[k]["prefilter_in_window"] if (k is not None and k in ds_stats) else 0
                keep_pair = warm_hits >= cfg.ds_prefilter_min_hits

            if not keep_pair:
                continue

            for _ in range(cfg.per_ds_samples):
                # Смешиваем balanced и random, чтобы не застрять в одном типе
                if rng.random() < 0.5:
                    blocks = balanced_blocks(d, S, jitter=cfg.balanced_jitter, rng=rng)
                else:
                    blocks = random_blocks(d, S, rng)
                try_one(blocks, d, S, prefilter_phase=False)

    else:
        raise ValueError(f"Unknown mode: {cfg.mode}")

    return {
        "worker_id": worker_id,
        "tested": tested,
        "constructed": constructed,
        "hits": local_hits,
        "near": local_near,
        "constructed_bits_counter": constructed_bits_counter,
        "ds_stats": ds_stats,
        "constructed_rows": local_constructed_rows,
    }


# ============================================================
# Output helpers
# ============================================================

def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def dedupe_candidates(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Убираем дубликаты по n.
    """
    seen = set()
    out = []
    for r in rows:
        n = r.get("n")
        if n in seen:
            continue
        seen.add(n)
        out.append(r)
    return out


def _quantile_from_counter(counter: Dict[int, int], q: float) -> Optional[float]:
    """
    q in [0, 1]
    """
    if not counter:
        return None
    if q <= 0:
        return float(min(counter))
    if q >= 1:
        return float(max(counter))

    total = sum(counter.values())
    target = q * (total - 1)
    rank_low = int(math.floor(target))
    rank_high = int(math.ceil(target))

    cur = 0
    low_val = None
    high_val = None

    for b in sorted(counter):
        nxt = cur + counter[b]
        if low_val is None and rank_low < nxt:
            low_val = b
        if rank_high < nxt:
            high_val = b
            break
        cur = nxt

    if low_val is None:
        low_val = max(counter)
    if high_val is None:
        high_val = low_val

    if rank_low == rank_high:
        return float(low_val)

    w = target - rank_low
    return float(low_val * (1.0 - w) + high_val * w)


def summarize_bit_counter(counter: Dict[int, int], percentiles: List[float], hist_bin: int) -> Dict[str, Any]:
    if not counter:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "percentiles": {},
            "histogram_bits": {},
            "histogram_bins": {},
        }

    total = sum(counter.values())
    weighted_sum = sum(bit * cnt for bit, cnt in counter.items())
    median = _quantile_from_counter(counter, 0.5)

    pct = {}
    for p in percentiles:
        if 0 <= p <= 100:
            pct[str(p)] = _quantile_from_counter(counter, p / 100.0)

    hist_bits = {str(k): counter[k] for k in sorted(counter)}

    bin_size = max(1, int(hist_bin))
    bins: Dict[str, int] = {}
    for b, cnt in counter.items():
        lo = (b // bin_size) * bin_size
        hi = lo + bin_size - 1
        key = f"{lo}-{hi}"
        bins[key] = bins.get(key, 0) + cnt
    bins = dict(sorted(bins.items(), key=lambda x: int(x[0].split("-")[0])))

    return {
        "count": total,
        "min": min(counter),
        "max": max(counter),
        "mean": weighted_sum / total,
        "median": median,
        "percentiles": pct,
        "histogram_bits": hist_bits,
        "histogram_bins": bins,
    }


def merge_ds_stats(dst: Dict[str, Dict[str, Any]], src: Dict[str, Dict[str, Any]]) -> None:
    for key, v in src.items():
        if key not in dst:
            dst[key] = {
                "pattern_d": v["pattern_d"],
                "pattern_S": v["pattern_S"],
                "tested": 0,
                "constructed": 0,
                "bits_in_target_window": 0,
                "bits_sum": 0,
                "bits_count": 0,
                "bits_min": None,
                "bits_max": None,
                "hits": 0,
                "prefilter_tested": 0,
                "prefilter_in_window": 0,
            }
        d = dst[key]
        d["tested"] += v.get("tested", 0)
        d["constructed"] += v.get("constructed", 0)
        d["bits_in_target_window"] += v.get("bits_in_target_window", 0)
        d["bits_sum"] += v.get("bits_sum", 0)
        d["bits_count"] += v.get("bits_count", 0)
        d["hits"] += v.get("hits", 0)
        d["prefilter_tested"] += v.get("prefilter_tested", 0)
        d["prefilter_in_window"] += v.get("prefilter_in_window", 0)

        smin = v.get("bits_min")
        smax = v.get("bits_max")
        if smin is not None:
            d["bits_min"] = smin if d["bits_min"] is None else min(d["bits_min"], smin)
        if smax is not None:
            d["bits_max"] = smax if d["bits_max"] is None else max(d["bits_max"], smax)


def finalize_ds_stats(ds_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for key, v in ds_stats.items():
        bits_count = v.get("bits_count", 0)
        row = {
            "pattern_d": v["pattern_d"],
            "pattern_S": v["pattern_S"],
            "tested": v.get("tested", 0),
            "constructed": v.get("constructed", 0),
            "bits_in_target_window": v.get("bits_in_target_window", 0),
            "bits_min": v.get("bits_min"),
            "bits_max": v.get("bits_max"),
            "bits_mean": (v["bits_sum"] / bits_count) if bits_count else None,
            "hits": v.get("hits", 0),
            "prefilter_tested": v.get("prefilter_tested", 0),
            "prefilter_in_window": v.get("prefilter_in_window", 0),
            "prefilter_ratio": (
                v["prefilter_in_window"] / v["prefilter_tested"]
                if v.get("prefilter_tested", 0) else None
            ),
        }
        rows.append(row)

    rows.sort(key=lambda x: (x["pattern_d"], x["pattern_S"]))
    return rows


# ============================================================
# Main
# ============================================================

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="zone_search.py v3 ANALYTICS")

    ap.add_argument("--mode", required=True,
                    choices=["random_parity", "balanced12", "scaled_from_seed", "scaled_ds", "sweep_ds", "map_ds"],
                    help="Search mode")

    ap.add_argument("--bits-min", type=int, required=True, help="Minimum bit length of reconstructed n")
    ap.add_argument("--bits-max", type=int, required=True, help="Maximum bit length of reconstructed n")

    # fixed d / S range
    ap.add_argument("--d", type=int, default=None, help="Fixed odd-step count for random_parity / balanced12")
    ap.add_argument("--s-min", type=int, default=None, help="Minimum even-step count S")
    ap.add_argument("--s-max", type=int, default=None, help="Maximum even-step count S")

    # target
    ap.add_argument("--target-peak", type=int, default=None, help="Target peak bits")
    ap.add_argument("--target-ratio", type=float, default=None, help="Target peak/start ratio")
    ap.add_argument("--constructor", choices=["auto", "reverse", "crt"], default="auto",
                    help="Number construction method from blocks")

    # sampling
    ap.add_argument("--samples", type=int, default=10000, help="Samples per worker (or total-like workload per worker)")
    ap.add_argument("--per-ds-samples", type=int, default=10, help="For sweep_ds: samples per (d,S) pair per worker")

    # workers
    ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1), help="Number of worker processes")
    ap.add_argument("--seed", type=int, default=123456789, help="Global random seed for reproducibility")

    # options
    ap.add_argument("--include-partial-shift", action="store_true",
                    help="Include partial odd-shift interpretation in analysis")
    ap.add_argument("--balanced-jitter", type=int, default=2,
                    help="Extra local perturbations for balanced12")
    ap.add_argument("--max-tail-twos", type=int, default=0,
                    help="Try final value 2^k, k in [0..max_tail_twos] in reverse construction")

    # hit / near-miss thresholds
    ap.add_argument("--near-miss-topk", type=int, default=200, help="Keep top-K near misses overall")
    ap.add_argument("--hit-peak-tol", type=int, default=0, help="Allowed absolute error in peak for a hit")
    ap.add_argument("--hit-ratio-tol", type=float, default=0.01, help="Allowed abs error in ratio for a hit")

    # sweep_ds
    ap.add_argument("--d-min", type=int, default=None, help="Minimum d for sweep_ds")
    ap.add_argument("--d-max", type=int, default=None, help="Maximum d for sweep_ds")
    ap.add_argument("--d-step", type=int, default=1, help="Step for d in sweep_ds")
    ap.add_argument("--s-step", type=int, default=1, help="Step for S in sweep_ds/scaled_ds")

    # scaled_from_seed
    ap.add_argument("--seed-blocks-file", type=str, default=None,
                    help="Path to seed blocks file for scaled_from_seed")

    # v3 analytics
    ap.add_argument("--percentiles", type=str, default="1,5,10,25,50,75,90,95,99",
                    help="Comma-separated percentile list for bit distribution")
    ap.add_argument("--bit-hist-bin", type=int, default=1,
                    help="Histogram bin size for bit distribution")
    ap.add_argument("--log-constructed", choices=["none", "bits", "full"], default="none",
                    help="Optional logging of all constructed numbers")
    ap.add_argument("--max-constructed-log", type=int, default=500000,
                    help="Safety cap for constructed log rows per worker")
    ap.add_argument("--ds-prefilter-samples", type=int, default=0,
                    help="For sweep_ds/map_ds: warmup samples per (d,S) before main phase")
    ap.add_argument("--ds-prefilter-min-hits", type=int, default=1,
                    help="Minimum warmup in-window count to keep (d,S) pair")
    ap.add_argument("--target-input-bits-min", type=int, default=None,
                    help="Target window min for analytics/prefilter")
    ap.add_argument("--target-input-bits-max", type=int, default=None,
                    help="Target window max for analytics/prefilter")

    # scaled_ds controls / debug
    ap.add_argument("--scaled-include-seed-baseline", action=argparse.BooleanOptionalAction, default=True,
                    help="In scaled_ds, add one exact-seed attempt when (d,S)==(seed_d,seed_S)")
    ap.add_argument("--debug-show-blocks", type=int, default=0,
                    help="Print first N blocks for debug in worker logs (0 disables)")
    ap.add_argument("--debug-max-prints", type=int, default=3,
                    help="Max debug block prints per worker")

    # output
    ap.add_argument("--out-dir", type=str, required=True, help="Output directory")

    return ap


def main():
    ap = build_arg_parser()
    args = ap.parse_args()

    percentiles = []
    for tok in args.percentiles.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            percentiles.append(float(tok))
        except Exception:
            pass
    if not percentiles:
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]

    cfg = SearchConfig(
        mode=args.mode,
        bits_min=args.bits_min,
        bits_max=args.bits_max,

        d=args.d,
        s_min=args.s_min,
        s_max=args.s_max,

        target_peak=args.target_peak,
        target_ratio=args.target_ratio,
        constructor=args.constructor,

        samples=args.samples,
        per_ds_samples=args.per_ds_samples,

        workers=args.workers,
        seed=args.seed,

        include_partial_shift=args.include_partial_shift,

        near_miss_topk=args.near_miss_topk,
        hit_peak_tol=args.hit_peak_tol,
        hit_ratio_tol=args.hit_ratio_tol,

        out_dir=args.out_dir,

        balanced_jitter=args.balanced_jitter,
        max_tail_twos=args.max_tail_twos,

        d_min=args.d_min,
        d_max=args.d_max,
        d_step=args.d_step,
        s_step=args.s_step,

        seed_blocks_file=args.seed_blocks_file,

        percentiles=percentiles,
        bit_hist_bin=args.bit_hist_bin,
        log_constructed=args.log_constructed,
        max_constructed_log=args.max_constructed_log,
        ds_prefilter_samples=args.ds_prefilter_samples,
        ds_prefilter_min_hits=args.ds_prefilter_min_hits,
        target_input_bits_min=args.target_input_bits_min,
        target_input_bits_max=args.target_input_bits_max,
        scaled_include_seed_baseline=args.scaled_include_seed_baseline,
        debug_show_blocks=args.debug_show_blocks,
        debug_max_prints=args.debug_max_prints,
    )

    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{now_ts()}] zone_search.py v3 ANALYTICS")
    print(f"Mode: {cfg.mode}")
    print(f"Workers: {cfg.workers}")
    print(f"Seed: {cfg.seed}")
    print(f"Output: {out_dir.resolve()}")
    print()

    t0 = time.time()

    worker_args = [(i, cfg) for i in range(cfg.workers)]

    if cfg.workers <= 1:
        results = [worker_run(worker_args[0])]
    else:
        with mp.Pool(processes=cfg.workers) as pool:
            results = pool.map(worker_run, worker_args)

    # merge
    total_tested = 0
    total_constructed = 0
    all_hits: List[Dict[str, Any]] = []
    all_near: List[Dict[str, Any]] = []
    all_constructed_rows: List[Dict[str, Any]] = []
    merged_bits_counter: Dict[int, int] = {}
    merged_ds_stats: Dict[str, Dict[str, Any]] = {}

    for r in results:
        total_tested += r["tested"]
        total_constructed += r["constructed"]
        all_hits.extend(r["hits"])
        all_near.extend(r["near"])
        all_constructed_rows.extend(r.get("constructed_rows", []))
        merge_ds_stats(merged_ds_stats, r.get("ds_stats", {}))

        for k, v in r.get("constructed_bits_counter", {}).items():
            ik = int(k)
            merged_bits_counter[ik] = merged_bits_counter.get(ik, 0) + int(v)

    all_hits = dedupe_candidates(all_hits)
    all_near = dedupe_candidates(all_near)
    all_near.sort(key=lambda x: x["score"])
    all_near = all_near[:cfg.near_miss_topk]

    # sort hits
    all_hits.sort(key=lambda x: (x["bits"], x["peak"], x["score"], x["n"]))
    all_constructed_rows.sort(key=lambda x: (x.get("bits", 0), x.get("n", 0)))

    # write
    hits_path = out_dir / "hits.jsonl"
    near_path = out_dir / "near_miss.jsonl"
    constructed_path = out_dir / "constructed.jsonl"
    ds_map_path = out_dir / "ds_map.json"
    summary_path = out_dir / "summary.json"

    write_jsonl(hits_path, all_hits)
    write_jsonl(near_path, all_near)
    if cfg.log_constructed != "none":
        write_jsonl(constructed_path, all_constructed_rows)

    ds_rows = finalize_ds_stats(merged_ds_stats)
    ds_map_path.write_text(json.dumps(ds_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    bit_distribution = summarize_bit_counter(
        merged_bits_counter,
        percentiles=cfg.percentiles,
        hist_bin=cfg.bit_hist_bin
    )

    dt = time.time() - t0

    summary = {
        "timestamp": now_ts(),
        "version": "v3 ANALYTICS",
        "config": asdict(cfg),
        "total_tested_patterns": total_tested,
        "total_constructed_numbers": total_constructed,
        "hits_count": len(all_hits),
        "near_miss_count": len(all_near),
        "constructed_log_count": len(all_constructed_rows),
        "elapsed_sec": dt,
        "bit_distribution_constructed": bit_distribution,
        "ds_map_size": len(ds_rows),
        "hits_file": str(hits_path),
        "near_miss_file": str(near_path),
        "constructed_file": str(constructed_path) if cfg.log_constructed != "none" else None,
        "ds_map_file": str(ds_map_path),
    }

    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    # console summary
    print("=== DONE ===")
    print(f"Tested patterns:      {total_tested}")
    print(f"Constructed numbers:  {total_constructed}")
    print(f"Hits:                 {len(all_hits)}")
    print(f"Near misses kept:     {len(all_near)}")
    if bit_distribution["count"] > 0:
        print(f'Constructed bits:     min={bit_distribution["min"]} max={bit_distribution["max"]} mean={bit_distribution["mean"]:.3f} median={bit_distribution["median"]:.3f}')
    else:
        print("Constructed bits:     no data")
    print(f"Elapsed:              {dt:.2f} sec")
    print()
    print(f"Hits file:            {hits_path}")
    print(f"Near file:            {near_path}")
    if cfg.log_constructed != "none":
        print(f"Constructed file:     {constructed_path}")
    print(f"DS map file:          {ds_map_path}")
    print(f"Summary:              {summary_path}")

    if all_hits:
        print("\nTop hits:")
        print("Bits  Peak  Ratio      d    S   S/d     Score")
        print("-" * 52)
        for r in all_hits[:20]:
            print(
                f'{r["bits"]:4d}  '
                f'{r["peak"]:4d}  '
                f'{r["ratio"]:<8.6f}  '
                f'{r["d"]:3d}  '
                f'{r["S"]:4d}  '
                f'{r["S_d"]:<7.4f}  '
                f'{r["score"]:<7.3f}'
            )

    elif all_near:
        print("\nTop near misses:")
        print("Bits  Peak  Ratio      d    S   S/d     Score")
        print("-" * 52)
        for r in all_near[:20]:
            print(
                f'{r["bits"]:4d}  '
                f'{r["peak"]:4d}  '
                f'{r["ratio"]:<8.6f}  '
                f'{r["d"]:3d}  '
                f'{r["S"]:4d}  '
                f'{r["S_d"]:<7.4f}  '
                f'{r["score"]:<7.3f}'
            )


if __name__ == "__main__":
    # Windows multiprocessing safety
    mp.freeze_support()
    main()
