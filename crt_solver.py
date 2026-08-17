"""
crt_solver.py — Zone Core Synthesizer
Collatz Crystal Hunter — расширение (FIXED)

Что мы знаем:
  - Zone 2 инвариант: ~259 нечётных шагов до пика=140 для всех Zone 2 чисел
  - Zone 2 E/O≈1.427 (до пика), Family A E/O≈1.752 (объясняет gain)
  - CRT из случайного паттерна = случайное число (ratio ~1.006)
  - Zone 3 нельзя получить масштабированием Zone 2 траектории

CLI:
  python crt_solver.py --mode info
  python crt_solver.py --mode family --k 117
  python crt_solver.py --mode verify --n 4717819199735960859518
  python crt_solver.py --mode search --bits 71 200 --budget 10000000 --workers 17
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing
import os
import random
import time

log23 = math.log2(3)

# Подтверждено: это ваш 72-битный Zone 2 core
Z2_CORE = "111111111100000011100100110011100001010100011011100111100111001101111110"

_G_MIN_RATIO = 1.60
_G_MIN_BITS = 71
_G_MAX_BITS = 200


# ============================================================
# БАЗОВЫЕ COLLatz-ФУНКЦИИ
# ============================================================

def collatz_peak(n: int, max_steps: int = 2_000_000):
    """
    Возвращает:
      peak_bits, steps_done, converged
    peak_bits = максимальная битность по полной траектории до 1 (или до max_steps)
    """
    ob = n.bit_length()
    cur = n
    pb = ob
    s = 0

    while cur > 1 and s < max_steps:
        cur = cur * 3 + 1 if (cur & 1) else (cur >> 1)
        s += 1
        cb = cur.bit_length()
        if cb > pb:
            pb = cb

    return pb, s, (cur <= 1)


def number_from_parity(pattern: str):
    """
    CRT-конструктор числа из parity pattern.
    Принимает символы:
      O / 1 = odd-step
      E / 0 = even-step

    Возвращает минимальное положительное x, реализующее данный префикс шагов,
    либо None, если pattern пустой / невалидный.
    """
    norm = [c in ('O', '1') for c in pattern.upper() if c in 'OE01']
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
# АНАЛИЗ ТРАЕКТОРИИ
# ============================================================

def analyze_full_trajectory(n: int, max_steps: int = 2_000_000):
    """
    Полный анализ до 1 (или до max_steps).
    Считает:
      - total_o = число обычных odd-steps (3n+1)
      - total_e = число обычных even-steps (n>>1)
      - peak = max bit_length
      - peak_step = шаг первого достижения нового максимума
    """
    cur = n
    ob = n.bit_length()
    pb = ob
    peak_step = 0

    run = 0
    run_type = None
    e_groups = []
    o_groups = []

    for i in range(max_steps):
        if cur <= 1:
            break

        if cur & 1:
            if run_type == 'E' and run > 0:
                e_groups.append(run)
                run = 0
            run_type = 'O'
            cur = cur * 3 + 1
            run += 1
        else:
            if run_type == 'O' and run > 0:
                o_groups.append(run)
                run = 0
            run_type = 'E'
            cur >>= 1
            run += 1

        if cur.bit_length() > pb:
            pb = cur.bit_length()
            peak_step = i + 1

    if run > 0:
        if run_type == 'E':
            e_groups.append(run)
        else:
            o_groups.append(run)

    total_o = sum(o_groups)
    total_e = sum(e_groups)
    gain = total_o * log23 - total_e if total_o > 0 else 0.0

    return {
        'peak': pb,
        'peak_step': peak_step,
        'total_o': total_o,
        'total_e': total_e,
        'e_mean': (sum(e_groups) / len(e_groups)) if e_groups else 0.0,
        'e_o_ratio': (total_e / total_o) if total_o else 0.0,
        'gain': gain,
    }


def analyze_to_peak(n: int, max_steps: int = 2_000_000):
    """
    Анализ ТОЛЬКО ДО ПИКА.
    Важно для Zone 2 / Zone 3:
      d = total_o (число odd-steps до пика)
      S = total_e (число even-steps до пика)

    Возвращает:
      peak, peak_step, total_o, total_e, e_mean, e_o_ratio, gain
    """
    cur = n
    ob = n.bit_length()
    pb = ob
    peak_step = 0

    # Сначала находим шаг достижения пика
    states = [cur]  # states[i] = значение после i шагов, states[0]=start
    steps = 0

    while cur > 1 and steps < max_steps:
        cur = cur * 3 + 1 if (cur & 1) else (cur >> 1)
        steps += 1
        states.append(cur)

        if cur.bit_length() > pb:
            pb = cur.bit_length()
            peak_step = steps

    # Если peak_step == 0, значит выше стартовой битности не поднималось
    # Тогда анализ "до пика" = 0 шагов
    if peak_step == 0:
        return {
            'peak': pb,
            'peak_step': 0,
            'total_o': 0,
            'total_e': 0,
            'e_mean': 0.0,
            'e_o_ratio': 0.0,
            'gain': 0.0,
        }

    # Анализируем только первые peak_step шагов
    cur = states[0]
    total_o = 0
    total_e = 0

    e_groups = []
    run_e = 0

    for _ in range(peak_step):
        if cur & 1:
            total_o += 1
            if run_e > 0:
                e_groups.append(run_e)
                run_e = 0
            cur = cur * 3 + 1
        else:
            total_e += 1
            run_e += 1
            cur >>= 1

    if run_e > 0:
        e_groups.append(run_e)

    gain = total_o * log23 - total_e if total_o > 0 else 0.0

    return {
        'peak': pb,
        'peak_step': peak_step,
        'total_o': total_o,
        'total_e': total_e,
        'e_mean': (sum(e_groups) / len(e_groups)) if e_groups else 0.0,
        'e_o_ratio': (total_e / total_o) if total_o else 0.0,
        'gain': gain,
    }


# ============================================================
# FAMILY A
# ============================================================

def family_a_core(k: int):
    """
    Ваш текущий эвристический генератор Family A.
    Оставлен без изменения, чтобы не ломать совместимость.
    """
    x = 1
    for bit in range(1, k):
        cur = x
        fail = False
        for _ in range(k):
            if cur % 2 == 0:
                fail = True
                break
            cur = (cur * 3 + 1) // 2
        if fail:
            x |= (1 << bit)
    return x


# ============================================================
# SEARCH WORKERS
# ============================================================

def _init_worker(mr, mn, mx):
    global _G_MIN_RATIO, _G_MIN_BITS, _G_MAX_BITS
    _G_MIN_RATIO = mr
    _G_MIN_BITS = mn
    _G_MAX_BITS = mx


def _search_worker(args):
    """
    Возвращает:
      (results, checked)
    """
    wid, budget, seed = args
    rng = random.Random(seed ^ (wid * 0xDEADBEEF))

    mr = _G_MIN_RATIO
    mn = _G_MIN_BITS
    mx = _G_MAX_BITS

    core_len = len(Z2_CORE)
    results = []
    checked = 0

    for i in range(budget):
        nb = rng.randint(mn, mx)
        method = i % 3
        checked += 1

        if method == 0 and nb > core_len:
            # Приклеиваем случайный хвост к Zone 2 core
            tail = ''.join(rng.choice('01') for _ in range(nb - core_len))
            n = int(Z2_CORE + tail, 2) | 1

        elif method == 1:
            # Более плотное по единицам случайное число
            bits = ['1']  # MSB
            for _ in range(nb - 2):
                bits.append('1' if rng.random() < 0.65 else '0')
            bits.append('1')  # LSB
            n = int(''.join(bits), 2)

        else:
            # Обычное случайное нечётное число заданной битности
            n = rng.getrandbits(nb - 1) | (1 << (nb - 1)) | 1

        if n.bit_length() < 50:
            continue

        peak, steps, conv = collatz_peak(n, 300_000)
        ratio = peak / n.bit_length()

        if ratio >= mr:
            results.append({
                'n': str(n),
                'binary': bin(n)[2:],
                'bits': n.bit_length(),
                'peak_bits': peak,
                'ratio': round(ratio, 8),
                'steps': steps,
                'converged': conv,
                'method': method,
            })

    return results, checked


# ============================================================
# SEARCH
# ============================================================

def run_search(
    min_bits=71,
    max_bits=200,
    min_ratio=1.60,
    n_workers=0,
    budget=5_000_000,
    output='crt_results.json',
    verbose=True,
):
    nw = n_workers if n_workers > 0 else max(1, (os.cpu_count() or 4) - 1)

    if verbose:
        print(f"\n{'=' * 68}")
        print(f"  Zone Search  bits={min_bits}-{max_bits}  ratio>={min_ratio}  budget={budget:,}  workers={nw}")
        print(f"  Z2_CORE bits={len(Z2_CORE)}")
        print(f"{'=' * 68}\n")

    from concurrent.futures import ProcessPoolExecutor, wait as fw, FIRST_COMPLETED

    CHUNK = 50_000
    bpw = max(1, budget // nw)
    base_seed = int(time.time() * 1000) & 0xFFFFFFFF

    chunks = []
    for wid in range(nw):
        rem = bpw
        cs = base_seed ^ (wid * 0x9E3779B9)
        while rem > 0:
            c = min(CHUNK, rem)
            chunks.append((wid, c, cs))
            rem -= c
            cs ^= 0x12345678

    all_results = []
    t0 = time.time()
    t_print = t0 - 4.5

    total_done = 0
    best = 0.0
    n_done = 0
    n_total = len(chunks)

    try:
        with ProcessPoolExecutor(
            max_workers=nw,
            initializer=_init_worker,
            initargs=(min_ratio, min_bits, max_bits),
        ) as exe:
            inflight = {}
            it = iter(enumerate(chunks))

            def refill():
                while len(inflight) < nw * 4:
                    try:
                        i, ch = next(it)
                        inflight[exe.submit(_search_worker, ch)] = i
                    except StopIteration:
                        break

            refill()

            while inflight:
                done_set, _ = fw(
                    list(inflight.keys()),
                    timeout=1.0,
                    return_when=FIRST_COMPLETED
                )

                for fut in done_set:
                    del inflight[fut]
                    n_done += 1

                    try:
                        batch, nc = fut.result(timeout=60)
                    except Exception as e:
                        print(f"  [!] worker error: {e}")
                        continue

                    all_results.extend(batch)
                    total_done += nc

                    for r in batch:
                        if r['ratio'] > best:
                            best = r['ratio']
                            if verbose:
                                print(
                                    f"  [BEST]  bits={r['bits']:4d}  peak={r['peak_bits']:4d}  ratio={r['ratio']:.5f}",
                                    flush=True
                                )

                refill()

                now = time.time()
                if verbose and (now - t_print) >= 5.0:
                    el = now - t0
                    sp = total_done / el if el > 0 else 0
                    pct = (n_done * 100 // n_total) if n_total else 100
                    print(
                        f"  [{el:5.0f}с]  {sp / 1000:.1f}K/с  {n_done}/{n_total} ({pct}%)  found={len(all_results)}  BEST={best:.5f}",
                        flush=True
                    )
                    t_print = now

    except Exception as e:
        print(f"  [!] search failed: {e}")

    el = time.time() - t0
    sp = total_done / el if el > 0 else 0

    # Убираем дубликаты по n, сортируем по ratio
    seen = set()
    uniq = []
    for r in sorted(all_results, key=lambda x: -x['ratio']):
        if r['n'] not in seen:
            seen.add(r['n'])
            uniq.append(r)
    all_results = uniq

    if verbose:
        print(f"\n  Итого: {el:.1f}с  {sp / 1000:.1f}K/с  {total_done / 1e6:.1f}M  найдено={len(all_results)}")
        for r in all_results[:5]:
            print(f"  {r['bits']}бит  ratio={r['ratio']:.5f}  peak={r['peak_bits']}  method={r['method']}")

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)

    if verbose:
        print(f"  Сохранено: {output}")

    return all_results


# ============================================================
# EXPORT
# ============================================================

def export_to_records(results, path='crt_records_patch.py'):
    lines = [
        f"# crt_solver.py  {time.strftime('%Y-%m-%d')}\n",
        "# Добавьте в PATH_RECORDS_BINARY\n\n",
    ]

    for r in results:
        lines.append(
            f'    "{r["binary"]}",  # {r["bits"]}бит ratio={r["ratio"]:.5f} peak={r["peak_bits"]}\n'
        )

    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"Патч: {path}")


# ============================================================
# CLI
# ============================================================

def main():
    multiprocessing.freeze_support()

    p = argparse.ArgumentParser(description="CRT Zone Synthesizer (FIXED)")
    p.add_argument('--mode', default='search', choices=['info', 'family', 'verify', 'search'])
    p.add_argument('--bits', nargs=2, type=int, default=[71, 200], metavar=('MIN', 'MAX'))
    p.add_argument('--budget', type=int, default=5_000_000)
    p.add_argument('--workers', type=int, default=0)
    p.add_argument('--min-ratio', type=float, default=1.60)
    p.add_argument('--output', default='crt_results.json')
    p.add_argument('--patch', default='crt_records_patch.py')
    p.add_argument('--n', type=str)
    p.add_argument('--k', type=int, default=117)

    args = p.parse_args()

    if args.mode == 'info':
        print("\n=== Анализ Zone 2 (FIXED: анализ ДО ПИКА) ===\n")
        print(f"Z2_CORE bits = {len(Z2_CORE)}")
        print(f"Z2_CORE int bit_length = {int(Z2_CORE, 2).bit_length()}")
        print()

        z2s = {
            72: int("111111111100000011100100110011100001010100011011100111100111001101111110", 2),
            79: int("1111111111000000111001001100111000010101000110111001111001110011011111111001011", 2),
        }

        for bits, n in z2s.items():
            a_peak = analyze_to_peak(n)
            a_full = analyze_full_trajectory(n)

            print(
                f"  {bits}бит:"
                f"  peak={a_peak['peak']}"
                f"  peak_step={a_peak['peak_step']}"
                f"  E/O_to_peak={a_peak['e_o_ratio']:.4f}"
                f"  k_odd_to_peak={a_peak['total_o']}"
                f"  gain_to_peak={a_peak['gain']:.1f}бит"
            )
            print(
                f"         FULL:"
                f"  E/O_full={a_full['e_o_ratio']:.4f}"
                f"  k_odd_full={a_full['total_o']}"
                f"  gain_full={a_full['gain']:.1f}бит"
            )

        print("\nИнтерпретация:")
        print("  - Для Zone 2 / Zone 3 теории используйте метрики ДО ПИКА")
        print("  - d = total_o_to_peak")
        print("  - S = total_e_to_peak")
        print("  - E/O_to_peak = S / d")
        print("  - gain_to_peak ≈ d*log2(3) - S")

    elif args.mode == 'family':
        k = args.k
        x = family_a_core(k)
        exp = (1 << k) - 1

        print(f"family_a_core({k}) = {x}")
        print(f"2^{k}-1 = {exp}")
        print(f"match = {x == exp}")

        if x == exp:
            peak, _, _ = collatz_peak(x)
            print(f"peak = {peak}")
            print(f"ratio = {peak / x.bit_length():.5f}")

    elif args.mode == 'verify':
        if not args.n:
            print("Ошибка: для --mode verify нужно указать --n")
            return

        n_str = args.n.strip()
        n = int(n_str, 16) if n_str.startswith('0x') else int(n_str)

        bits = n.bit_length()
        peak, steps, conv = collatz_peak(n)
        ratio = peak / bits

        a_peak = analyze_to_peak(n)
        a_full = analyze_full_trajectory(n)

        print(f"bits={bits}  peak={peak}  ratio={ratio:.6f}  steps={steps:,}  converged={conv}")
        print(
            f"[TO PEAK] peak_step={a_peak['peak_step']}  "
            f"E/O={a_peak['e_o_ratio']:.4f}  gain={a_peak['gain']:.1f}бит  k_odd={a_peak['total_o']}  S={a_peak['total_e']}"
        )
        print(
            f"[FULL]    peak_step={a_full['peak_step']}  "
            f"E/O={a_full['e_o_ratio']:.4f}  gain={a_full['gain']:.1f}бит  k_odd={a_full['total_o']}  E={a_full['total_e']}"
        )

        if peak == 140 and ratio > 1.60:
            print("→ Zone 2 candidate / known Zone 2-like")
        elif ratio > 1.62:
            print(f"→ АНОМАЛИЯ ratio={ratio:.5f}!")
        else:
            print("→ Family A / ordinary high-growth candidate")

    elif args.mode == 'search':
        results = run_search(
            min_bits=args.bits[0],
            max_bits=args.bits[1],
            min_ratio=args.min_ratio,
            n_workers=args.workers,
            budget=args.budget,
            output=args.output,
            verbose=True,
        )

        if results:
            export_to_records(results, args.patch)


if __name__ == '__main__':
    main()
