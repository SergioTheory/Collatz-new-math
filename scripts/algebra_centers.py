"""
algebra_centers.py — Алгебраическая анатомия confluence-центров

Глубокий анализ:
  A. Факторизация
  B. Модулярная арифметика
  C. Двоичная структура
  D. Связь с 3^k / 2^m
  E. Траектория от центра до пика
  F. Рост центров: fit center vs peak
  G. Связь с конвергентами log₂3
  H. CRT-обратная задача
  I. Формулы-кандидаты

Использование:
  python algebra_centers.py
"""

from __future__ import annotations

import json
import math
import sys
import time
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from crt_solver import collatz_peak, analyze_to_peak

log23 = math.log2(3)

# ============================================================
# Данные
# ============================================================

CENTERS = {
    # peaks 14-30 (original)
    14:  719,
    16:  6803,
    18:  27611,
    19:  15977,
    21:  52487,
    22:  61823,
    23:  41471,
    24:  586115,
    25:  705307,
    26:  1085723,
    27:  4918427,
    30:  58595471,
    # peaks 31-40 (targeted_search_31_50)
    31:  48427561,
    32:  1242665,
    33:  3538943,
    34:  4205807,
    35:  26658983,
    36:  8524379,
    37:  67625867,
    38:  16348007,
    39:  19351295,
    40:  35337455,
    # peaks 41-45 (targeted_search_41_50)
    41:  37748015,
    42:  72481007,
    43:  467269499,
    44:  108893737,
    45:  236651489,
    # peaks 46-50 (exhaustive search, NEW!)
    46:  516844415,
    47:  442441855,
    48:  2303929595,
    49:  3830005073,
    50:  1396693151,
    # peak 140 (Zone 2)
    140: 20152090995747160937051,
}

ALT_CENTERS = {
    # Alternative centers for same peaks (including Class A candidates)
    14: (121, 7),       # Class A: 100% hit rate, d_peak=21, S/d=1.38
    18: (10151, 14),    # Census alternative
    27: (5808671, 23),  # Known predecessor
}


# ============================================================
# Факторизация
# ============================================================

def _trial_factors(n: int, limit: int = 100000):
    """Trial division до limit."""
    factors = {}
    for p in [2, 3]:
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
    d = 5
    w = 2
    while d * d <= n and d <= limit:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += w
        w = 6 - w
    return factors, n


def _is_probable_prime(n: int, k: int = 20):
    """Miller-Rabin."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    import random
    rng = random.Random(42)
    for _ in range(k):
        a = rng.randrange(2, n - 1) if n > 4 else 2
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _pollard_rho(n: int):
    """Pollard's rho для нахождения нетривиального делителя."""
    if n % 2 == 0:
        return 2
    import random
    rng = random.Random(n & 0xFFFF)
    for c in range(1, 100):
        x = rng.randrange(2, n)
        y = x
        d = 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d
    return n


def factorize(n: int):
    """Полная факторизация. Возвращает dict {prime: exp}."""
    if n <= 1:
        return {}

    # Пробуем sympy
    try:
        from sympy import factorint
        return dict(factorint(n))
    except ImportError:
        pass

    factors, remainder = _trial_factors(n, 1_000_000)
    if remainder == 1:
        return factors

    # Рекурсивно через Pollard's rho
    stack = [remainder]
    while stack:
        m = stack.pop()
        if m == 1:
            continue
        if _is_probable_prime(m):
            factors[m] = factors.get(m, 0) + 1
            continue
        d = _pollard_rho(m)
        if d == m:
            factors[m] = factors.get(m, 0) + 1
        else:
            stack.append(d)
            stack.append(m // d)

    return factors


def format_factors(fdict):
    """'2^3 × 5 × 719' format."""
    if not fdict:
        return "1"
    parts = []
    for p in sorted(fdict):
        e = fdict[p]
        parts.append(f"{p}^{e}" if e > 1 else str(p))
    return " × ".join(parts)


def v2(n: int):
    """2-adic valuation of n."""
    if n == 0:
        return -1
    c = 0
    while n % 2 == 0:
        c += 1
        n //= 2
    return c


# ============================================================
# Двоичная структура
# ============================================================

def binary_analysis(n: int):
    """Анализ двоичной записи числа."""
    b = bin(n)[2:]
    bits = len(b)
    ones = b.count('1')
    density = ones / bits if bits > 0 else 0

    # Максимальные серии
    max_run1 = max((len(s) for s in b.split('0') if s), default=0)
    max_run0 = max((len(s) for s in b.split('1') if s), default=0)

    # Первые и последние 8 бит
    first8 = b[:8] if len(b) >= 8 else b
    last8 = b[-8:] if len(b) >= 8 else b

    # Близость к 2^k
    k_up = bits
    dist_pow2 = (1 << k_up) - n

    # Близость к 2^k - 1
    dist_all1 = n - ((1 << bits) - 1)  # всегда <= 0 для MSB=1

    return {
        "binary": b if len(b) <= 80 else b[:40] + "..." + b[-40:],
        "bits": bits,
        "ones": ones,
        "density": density,
        "max_run1": max_run1,
        "max_run0": max_run0,
        "first8": first8,
        "last8": last8,
        "dist_pow2_above": dist_pow2,
        "dist_all_ones": abs(dist_all1),
    }


# ============================================================
# D. Связь с 3^k / 2^m
# ============================================================

def find_nearest_3k_2m(c: int, k_max: int = 300, m_max: int = 500):
    """
    Находит (k, m) минимизирующие |c * 2^m - 3^k|.
    Возвращает top-5 по относительной ошибке.
    """
    results = []
    c_bits = c.bit_length()

    for k in range(1, k_max + 1):
        pow3 = 3 ** k
        pow3_bits = pow3.bit_length()

        # m ≈ log2(3^k / c) = k * log2(3) - log2(c)
        m_approx = k * log23 - math.log2(c) if c > 0 else 0
        m_center = int(round(m_approx))

        for m in range(max(0, m_center - 2), min(m_max, m_center + 3)):
            c_shifted = c << m  # c * 2^m
            err = abs(c_shifted - pow3)
            rel_err = err / pow3 if pow3 > 0 else float('inf')
            results.append((k, m, err, rel_err))

    results.sort(key=lambda x: x[3])
    return results[:10]


# ============================================================
# E. Траектория от центра до пика (odd-to-odd)
# ============================================================

def trajectory_center_to_peak(c: int):
    """
    Ускоренная odd-to-odd динамика от c до пика.
    Возвращает d_after, S_after, shift_vector, peak_value.
    """
    cur = c
    peak_bits = cur.bit_length()
    peak_val = cur
    d = 0
    S = 0
    shifts = []

    # Сначала найдём пик через analyze_to_peak
    atp = analyze_to_peak(c, max_steps=2_000_000)
    d_total = atp['total_o']
    S_total = atp['total_e']

    # Теперь пройдём odd-to-odd и запишем shift-вектор
    cur = c
    peak_bits = c.bit_length()
    steps_past_peak = 0

    while cur > 1 and d < 10000:
        if cur % 2 == 0:
            while cur % 2 == 0:
                cur >>= 1
            continue

        nxt = cur * 3 + 1
        a = 0
        while nxt % 2 == 0:
            nxt >>= 1
            a += 1

        d += 1
        S += a
        shifts.append(a)

        if nxt.bit_length() > peak_bits:
            peak_bits = nxt.bit_length()
            peak_val = nxt
            steps_past_peak = 0
        else:
            steps_past_peak += 1

        cur = nxt

        if steps_past_peak > 10:
            break

    # Вычисляем peak_value точно через формулу: val = (3^d * c + c_d) / 2^S
    # c_d вычисляется рекуррентно: c_0 = 0, c_{k+1} = 3 * c_k + 2^{S_k}
    # Но проще: просто записываем peak_val из траектории
    # Для точности пересчитаем через формулу
    c_d = 0
    S_running = 0
    pow3 = 1
    for i, a in enumerate(shifts):
        c_d = 3 * c_d + (1 << S_running)
        S_running += a
        pow3 *= 3
        # Проверим: val = (pow3 * c + c_d) должно быть делимо на 2^S_running
        # и val / 2^S_running = текущее значение
        if S_running == S and i + 1 == d:
            break

    # peak через формулу
    numerator = pow3 * c + c_d
    if S_running > 0 and numerator % (1 << S_running) == 0:
        formula_val = numerator >> S_running
    else:
        formula_val = None  # Ошибка округления — не должно случиться

    return {
        "d_after": d,
        "S_after": S,
        "shifts": shifts[:50],  # первые 50
        "peak_bits": peak_bits,
        "peak_val_hex": hex(peak_val)[:40] if peak_val else None,
        "S_over_d": S / d if d > 0 else 0,
        "formula_val": formula_val,
        "formula_match": formula_val == peak_val if formula_val else False,
        "c_d": c_d,
    }


# ============================================================
# G. Конвергенты цепной дроби log₂3
# ============================================================

def convergents_log23(max_terms: int = 25):
    """Вычисляет конвергенты цепной дроби log₂3."""
    # log₂3 = [1; 1, 1, 2, 2, 3, 1, 5, 2, 23, 2, 2, 1, 1, 55, 1, 4, 3, 1, ...]
    cf = [1, 1, 1, 2, 2, 3, 1, 5, 2, 23, 2, 2, 1, 1, 55, 1, 4, 3, 1, 1, 15,
          1, 9, 2, 2]
    cf = cf[:max_terms]

    convs = []
    h_prev, h_curr = 0, 1
    k_prev, k_curr = 1, 0

    for a in cf:
        h_prev, h_curr = h_curr, a * h_curr + h_prev
        k_prev, k_curr = k_curr, a * k_curr + k_prev
        convs.append(Fraction(h_curr, k_curr))

    return convs


def nearest_convergent(x: float, convs: list[Fraction]):
    """Находит ближайший конвергент к x."""
    best = None
    best_err = float('inf')
    for c in convs:
        err = abs(float(c) - x)
        if err < best_err:
            best_err = err
            best = c
    return best, best_err


# ============================================================
# F. Fit: center vs peak
# ============================================================

def linear_regression(xs, ys):
    """Simple least squares y = a*x + b. Returns (a, b, R²)."""
    n = len(xs)
    if n < 2:
        return 0, 0, 0
    sx = sum(xs)
    sy = sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))

    denom = n * sxx - sx * sx
    if abs(denom) < 1e-30:
        return 0, 0, 0

    a = (n * sxy - sx * sy) / denom
    b = (sy - a * sx) / n

    ss_res = sum((y - (a * x + b)) ** 2 for x, y in zip(xs, ys))
    y_mean = sy / n
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot > 1e-30 else 0

    return a, b, r2


# ============================================================
# Main analysis
# ============================================================

def main():
    t_start = time.time()
    sep = "=" * 90
    all_data = {}

    peaks_sorted = sorted(CENTERS.keys())
    centers_list = [(p, CENTERS[p]) for p in peaks_sorted]

    print(f"\n{sep}")
    print("  Algebraic Anatomy of Confluence Centers")
    print(sep)

    # ==========================================================
    # A. ФАКТОРИЗАЦИЯ
    # ==========================================================
    print(f"\n  A. FACTORIZATION\n")
    print(f"  {'Center':>24}  {'Peak':>4}  {'Factorization':<40}  "
          f"{'Type':<12}  v2(3c+1)")
    print(f"  {'------':>24}  {'----':>4}  {'-------------':<40}  "
          f"{'----':<12}  --------")

    factor_data = {}
    for peak, c in centers_list:
        f = factorize(c)
        f_str = format_factors(f)
        f_3c1 = factorize(3 * c + 1)
        v2_3c1 = v2(3 * c + 1)

        n_primes = len(f)
        total_exp = sum(f.values())
        if n_primes == 1 and total_exp == 1:
            ctype = "prime"
        elif n_primes == 1:
            ctype = "prime_power"
        elif n_primes == 2 and total_exp == 2:
            ctype = "semiprime"
        else:
            ctype = f"{n_primes} factors"

        c_str = str(c)
        if len(c_str) > 22:
            c_str = c_str[:20] + ".."
        if len(f_str) > 38:
            f_str = f_str[:36] + ".."

        print(f"  {c_str:>24}  {peak:>4}  {f_str:<40}  "
              f"{ctype:<12}  {v2_3c1}")

        factor_data[peak] = {
            "center": str(c),
            "factors": {str(k): v for k, v in f.items()},
            "factors_str": format_factors(f),
            "type": ctype,
            "3c+1_factors": {str(k): v for k, v in f_3c1.items()},
            "v2_3c1": v2_3c1,
        }

        # Дополнительно: c mod 3, c-1, c+1
        f_cm1 = factorize(c - 1) if c > 1 else {}
        f_cp1 = factorize(c + 1)
        factor_data[peak]["c-1_factors"] = format_factors(f_cm1)
        factor_data[peak]["c+1_factors"] = format_factors(f_cp1)
        factor_data[peak]["c_mod3"] = c % 3

    all_data["factorization"] = factor_data

    # ==========================================================
    # B. МОДУЛЯРНАЯ АРИФМЕТИКА
    # ==========================================================
    print(f"\n  B. MODULAR PATTERNS\n")

    moduli = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 32, 64, 128, 256]

    # Header
    mod_header = "  " + f"{'Peak':>4} " + " ".join(f"{m:>4}" for m in moduli)
    print(mod_header)
    print("  " + "-" * (len(mod_header) - 2))

    mod_data = {}
    # Собираем остатки для поиска общих
    residues_by_mod = defaultdict(list)

    for peak, c in centers_list:
        row = f"  {peak:>4} "
        row_data = {}
        for m in moduli:
            r = c % m
            row += f"{r:>4} "
            row_data[str(m)] = r
            residues_by_mod[m].append(r)
        print(row)
        mod_data[peak] = row_data

    # Найти модули, где ВСЕ центры имеют одинаковый остаток
    print(f"\n  Constant residues (same for ALL centers):")
    for m in moduli:
        vals = residues_by_mod[m]
        if len(set(vals)) == 1:
            print(f"    mod {m}: ALL centers ≡ {vals[0]}")
        else:
            # Показать если >= 80% одинаковые
            from collections import Counter as C2
            mc = C2(vals).most_common(1)[0]
            if mc[1] >= len(vals) * 0.8:
                print(f"    mod {m}: {mc[1]}/{len(vals)} centers ≡ {mc[0]}")

    all_data["modular"] = mod_data

    # ==========================================================
    # C. ДВОИЧНАЯ СТРУКТУРА
    # ==========================================================
    print(f"\n  C. BINARY STRUCTURE\n")
    print(f"  {'Peak':>4}  {'Bits':>4}  {'Density':>7}  {'Run1':>4}  "
          f"{'Run0':>4}  {'First8':<10}  {'Last8':<10}  Binary")
    print(f"  {'----':>4}  {'----':>4}  {'-------':>7}  {'----':>4}  "
          f"{'----':>4}  {'------':<10}  {'-----':<10}  ------")

    bin_data = {}
    for peak, c in centers_list:
        ba = binary_analysis(c)
        b_disp = ba["binary"]
        if len(b_disp) > 30:
            b_disp = b_disp[:15] + "..." + b_disp[-15:]
        print(f"  {peak:>4}  {ba['bits']:>4}  {ba['density']:>7.3f}  "
              f"{ba['max_run1']:>4}  {ba['max_run0']:>4}  "
              f"{ba['first8']:<10}  {ba['last8']:<10}  {b_disp}")
        bin_data[peak] = ba

    all_data["binary"] = bin_data

    # ==========================================================
    # D. СВЯЗЬ С 3^k / 2^m
    # ==========================================================
    print(f"\n  D. NEAREST 3^k / 2^m  (c ≈ 3^k · 2^{-m})\n")
    print(f"  {'Peak':>4}  {'Center':>22}  {'k':>4}  {'m':>4}  "
          f"{'RelError':>12}  {'m/k':>8}  {'log₂3':>8}  {'|err|':>12}")
    print(f"  {'----':>4}  {'------':>22}  {'--':>4}  {'--':>4}  "
          f"{'--------':>12}  {'---':>8}  {'-----':>8}  {'-----':>12}")

    d_data = {}
    for peak, c in centers_list:
        k_max = 300 if c.bit_length() < 70 else 500
        m_max = 500 if c.bit_length() < 70 else 800
        results = find_nearest_3k_2m(c, k_max=k_max, m_max=m_max)

        best = results[0]
        k, m, err, rel_err = best
        mk_ratio = m / k if k > 0 else 0

        c_str = str(c)
        if len(c_str) > 20:
            c_str = c_str[:18] + ".."
        err_str = str(err)
        if len(err_str) > 10:
            err_str = f"{err:.3e}"

        print(f"  {peak:>4}  {c_str:>22}  {k:>4}  {m:>4}  "
              f"{rel_err:>12.6e}  {mk_ratio:>8.5f}  {log23:>8.5f}  "
              f"{err_str:>12}")

        d_data[peak] = {
            "best_k": k, "best_m": m,
            "abs_error": str(err),
            "rel_error": rel_err,
            "m_over_k": mk_ratio,
            "top5": [{"k": r[0], "m": r[1], "rel_err": r[3]} for r in results[:5]],
        }

    all_data["nearest_3k_2m"] = d_data

    # ==========================================================
    # E. ТРАЕКТОРИЯ ОТ ЦЕНТРА ДО ПИКА
    # ==========================================================
    print(f"\n  E. TRAJECTORY FROM CENTER TO PEAK\n")
    print(f"  {'Peak':>4}  {'Center':>22}  {'d_aft':>5}  {'S_aft':>5}  "
          f"{'S/d':>7}  {'PeakBits':>8}  {'Fmatch':>6}  PeakVal(hex)")
    print(f"  {'----':>4}  {'------':>22}  {'-----':>5}  {'-----':>5}  "
          f"{'---':>7}  {'--------':>8}  {'------':>6}  -----------")

    traj_data = {}
    for peak, c in centers_list:
        tr = trajectory_center_to_peak(c)

        c_str = str(c)
        if len(c_str) > 20:
            c_str = c_str[:18] + ".."
        pv_hex = tr["peak_val_hex"] or "?"
        if len(pv_hex) > 20:
            pv_hex = pv_hex[:20] + ".."
        fm = "YES" if tr["formula_match"] else "no"

        print(f"  {peak:>4}  {c_str:>22}  {tr['d_after']:>5}  "
              f"{tr['S_after']:>5}  {tr['S_over_d']:>7.4f}  "
              f"{tr['peak_bits']:>8}  {fm:>6}  {pv_hex}")

        traj_data[peak] = {
            "d_after": tr["d_after"],
            "S_after": tr["S_after"],
            "S_over_d": tr["S_over_d"],
            "peak_bits": tr["peak_bits"],
            "formula_match": tr["formula_match"],
            "shifts_first20": tr["shifts"][:20],
            "c_d": str(tr["c_d"]),
        }

    all_data["trajectory"] = traj_data

    # ==========================================================
    # F. РОСТ ЦЕНТРОВ: FIT
    # ==========================================================
    print(f"\n  F. GROWTH FIT\n")

    # Exclude peak=140 for fits (outlier)
    peaks_small = [p for p in peaks_sorted if p < 140]
    centers_small = [CENTERS[p] for p in peaks_small]

    # 1. log(center) vs peak → center ≈ A * B^peak
    log_centers = [math.log(c) for c in centers_small]
    a_exp, b_exp, r2_exp = linear_regression(peaks_small, log_centers)
    A_exp = math.exp(b_exp)
    B_exp = math.exp(a_exp)

    print(f"  Exponential fit (peaks 14-30): center ≈ A · B^peak")
    print(f"    A = {A_exp:.6f}")
    print(f"    B = {B_exp:.6f}")
    print(f"    R² = {r2_exp:.6f}")
    print(f"    log₂(B) = {math.log2(B_exp):.6f}")

    # Предсказание для peak=140
    pred_140 = A_exp * B_exp ** 140
    actual_140 = CENTERS[140]
    print(f"\n    Prediction peak=140: {pred_140:.3e}")
    print(f"    Actual peak=140:     {actual_140:.3e}")
    print(f"    Ratio actual/pred:   {actual_140 / pred_140:.3e}")

    # 2. center_bits vs peak → linear
    bits_small = [CENTERS[p].bit_length() for p in peaks_small]
    a_lin, b_lin, r2_lin = linear_regression(peaks_small, bits_small)

    print(f"\n  Linear fit: center_bits ≈ α · peak + β")
    print(f"    α = {a_lin:.6f}")
    print(f"    β = {b_lin:.6f}")
    print(f"    R² = {r2_lin:.6f}")

    # Включая peak=140
    all_bits = [CENTERS[p].bit_length() for p in peaks_sorted]
    a_lin2, b_lin2, r2_lin2 = linear_regression(peaks_sorted, all_bits)
    print(f"\n  Linear fit (ALL peaks including 140): center_bits ≈ α · peak + β")
    print(f"    α = {a_lin2:.6f}")
    print(f"    β = {b_lin2:.6f}")
    print(f"    R² = {r2_lin2:.6f}")
    pred_bits_140 = a_lin2 * 140 + b_lin2
    print(f"    Predicted bits for peak=140: {pred_bits_140:.1f}, actual: 75")

    # 3. Отношения последовательных центров
    print(f"\n  Sequential ratios:")
    print(f"  {'p1':>4} → {'p2':>4}  {'c2/c1':>10}  {'Δp':>3}  "
          f"{'(c2/c1)^(1/Δp)':>14}")
    for i in range(len(peaks_small) - 1):
        p1, p2 = peaks_small[i], peaks_small[i + 1]
        c1, c2 = CENTERS[p1], CENTERS[p2]
        ratio = c2 / c1
        dp = p2 - p1
        ratio_per_unit = ratio ** (1.0 / dp) if dp > 0 else 0
        print(f"  {p1:>4} → {p2:>4}  {ratio:>10.3f}  {dp:>3}  "
              f"{ratio_per_unit:>14.6f}")

    all_data["growth_fit"] = {
        "exponential": {"A": A_exp, "B": B_exp, "R2": r2_exp,
                        "log2_B": math.log2(B_exp)},
        "linear_bits": {"alpha": a_lin, "beta": b_lin, "R2": r2_lin},
        "linear_bits_all": {"alpha": a_lin2, "beta": b_lin2, "R2": r2_lin2},
    }

    # ==========================================================
    # G. КОНВЕРГЕНТЫ log₂3
    # ==========================================================
    print(f"\n  G. CONTINUED FRACTION CONNECTION (log₂3)\n")

    convs = convergents_log23(25)
    print(f"  Convergents of log₂3:")
    for i, c in enumerate(convs[:15]):
        print(f"    [{i}] {c.numerator}/{c.denominator} = "
              f"{float(c):.10f}  (err={float(c) - log23:+.2e})")

    print(f"\n  {'Peak':>4}  {'d_aft':>5}  {'S_aft':>5}  {'S/d':>8}  "
          f"{'Near.conv':>12}  {'Conv.err':>10}  {'d=denom?':>9}")
    print(f"  {'----':>4}  {'-----':>5}  {'-----':>5}  {'---':>8}  "
          f"{'--------':>12}  {'--------':>10}  {'--------':>9}")

    conv_data = {}
    for peak, c in centers_list:
        tr = traj_data[peak]
        d = tr["d_after"]
        S = tr["S_after"]
        sd = tr["S_over_d"]

        nearest, nerr = nearest_convergent(sd, convs)
        is_denom = any(c_.denominator == d for c_ in convs)

        print(f"  {peak:>4}  {d:>5}  {S:>5}  {sd:>8.5f}  "
              f"{nearest.numerator}/{nearest.denominator:>9}  "
              f"{nerr:>10.2e}  {'YES' if is_denom else 'no':>9}")

        conv_data[peak] = {
            "S_over_d": sd,
            "nearest_convergent": f"{nearest.numerator}/{nearest.denominator}",
            "convergent_error": nerr,
            "d_is_convergent_denom": is_denom,
        }

    all_data["convergents"] = conv_data

    # ==========================================================
    # H. CRT-ОБРАТНАЯ ЗАДАЧА
    # ==========================================================
    print(f"\n  H. CRT INVERSE — minimal S for center residue class\n")
    print(f"  {'Peak':>4}  {'Center':>22}  {'min_S':>5}  "
          f"{'c mod 2^S':>22}  {'2^S':>12}")
    print(f"  {'----':>4}  {'------':>22}  {'-----':>5}  "
          f"{'--------':>22}  {'---':>12}")

    crt_data = {}
    for peak, c in centers_list:
        # Находим минимальный S такой что траектория c определяется
        # первыми S битами: c mod 2^S фиксирует shift-вектор до пика
        # Практически: пробуем S = 1,2,...  и проверяем совпадение
        # shift-вектора для c и c + 2^S
        shifts_c = traj_data[peak]["shifts_first20"]
        min_S = None

        for S in range(1, min(c.bit_length() + 20, 200)):
            mod = 1 << S
            c2 = c + mod
            if c2.bit_length() > 200:
                break

            # Вычисляем первые шаги shift-вектора для c2
            cur = c2
            shifts2 = []
            ok = True
            for s_expected in shifts_c:
                if cur <= 1 or cur % 2 == 0:
                    ok = False
                    break
                nxt = cur * 3 + 1
                a = 0
                while nxt % 2 == 0:
                    nxt >>= 1
                    a += 1
                shifts2.append(a)
                cur = nxt

            if not ok or shifts2 != shifts_c:
                continue
            else:
                min_S = S
                break

        c_str = str(c)
        if len(c_str) > 20:
            c_str = c_str[:18] + ".."
        r_str = str(c % (1 << min_S)) if min_S else "?"
        if len(r_str) > 20:
            r_str = r_str[:18] + ".."
        mod_str = str(1 << min_S) if min_S else "?"
        if len(mod_str) > 10:
            mod_str = f"2^{min_S}"

        print(f"  {peak:>4}  {c_str:>22}  {min_S or '?':>5}  "
              f"{r_str:>22}  {mod_str:>12}")

        crt_data[peak] = {
            "min_S": min_S,
            "residue": str(c % (1 << min_S)) if min_S else None,
        }

    all_data["crt_inverse"] = crt_data

    # ==========================================================
    # I. ФОРМУЛЫ-КАНДИДАТЫ
    # ==========================================================
    print(f"\n  I. FORMULA CANDIDATES\n")

    # Гипотеза 1: center ≈ A * 2^(α*peak)
    print(f"  Hypothesis 1: center ≈ A · 2^(α·peak)")
    log2_centers = [math.log2(CENTERS[p]) for p in peaks_small]
    a_h1, b_h1, r2_h1 = linear_regression(peaks_small, log2_centers)
    print(f"    α = {a_h1:.6f}")
    print(f"    A = 2^{b_h1:.4f} = {2**b_h1:.6f}")
    print(f"    R² = {r2_h1:.6f}")
    pred_30_h1 = 2 ** (a_h1 * 30 + b_h1)
    pred_140_h1 = 2 ** (a_h1 * 140 + b_h1)
    print(f"    Pred peak=30: {pred_30_h1:.0f} (actual: {CENTERS[30]})")
    print(f"    Pred peak=140: {pred_140_h1:.3e} (actual: {CENTERS[140]:.3e})")

    # Гипотеза 2: center ≈ (3^k - 2^m) / N
    # Используем best (k,m) из раздела D
    print(f"\n  Hypothesis 2: center ≈ (3^k - 2^m) / N  or  (2^m - 3^k) / N")
    for peak in peaks_small:
        c = CENTERS[peak]
        dk = d_data[peak]
        k, m = dk["best_k"], dk["best_m"]
        diff = 3 ** k - (c << m)
        if diff == 0:
            print(f"    peak={peak}: EXACT  c = 3^{k} / 2^{m}")
        else:
            # c * 2^m = 3^k - diff  →  c = (3^k - diff) / 2^m
            sign = "+" if diff > 0 else "-"
            print(f"    peak={peak}: c·2^{m} = 3^{k} {sign} {abs(diff)}, "
                  f"|diff|/{3**k:.2e} = {abs(diff)/3**k:.2e}")

    # Гипотеза 3: center_bits ≈ α * peak  (simple linear)
    print(f"\n  Hypothesis 3: center_bits = α · peak + β")
    print(f"    From small: α={a_lin:.4f}, β={b_lin:.2f}, R²={r2_lin:.4f}")
    print(f"    From all:   α={a_lin2:.4f}, β={b_lin2:.2f}, R²={r2_lin2:.4f}")
    print(f"    Note: α≈{a_lin2:.3f} means center grows as ~2^({a_lin2:.2f}·peak)")

    # Гипотеза 4: S_after/d_after ≈ конвергент
    print(f"\n  Hypothesis 4: S/d from center is near log₂3 convergent")
    sd_values = [traj_data[p]["S_over_d"] for p in peaks_small]
    mean_sd = sum(sd_values) / len(sd_values)
    print(f"    Mean S/d = {mean_sd:.6f} (log₂3 = {log23:.6f})")
    nearest_mean, err_mean = nearest_convergent(mean_sd, convs)
    print(f"    Nearest convergent: {nearest_mean.numerator}/"
          f"{nearest_mean.denominator} (err={err_mean:.2e})")

    # Финальная проверка
    print(f"\n  PREDICTIONS VS ACTUAL:")
    for peak, c in centers_list:
        pred = 2 ** (a_h1 * peak + b_h1)
        ratio = c / pred
        print(f"    peak={peak:>3}: predicted={pred:>15.0f}  "
              f"actual={c:>24}  ratio={ratio:>8.2f}")

    all_data["formulas"] = {
        "h1_exp": {"alpha": a_h1, "log2_A": b_h1, "R2": r2_h1},
        "h3_linear_bits": {"alpha": a_lin2, "beta": b_lin2, "R2": r2_lin2},
        "mean_S_over_d": mean_sd,
    }

    # ==========================================================
    # СОХРАНЕНИЕ
    # ==========================================================
    elapsed = time.time() - t_start

    out_path = "algebra_centers.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{sep}")
    print(f"  JSON сохранён: {out_path}")
    print(f"  Время: {elapsed:.1f}s")
    print(f"{sep}\n")


if __name__ == "__main__":
    main()
