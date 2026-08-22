"""
confluence_catalog.py — Формальный каталог confluence-классов Коллатца

Собирает все известные структуры в единую таблицу:
  Zone 2 (x*), Barina, Mini-Zone 2 (27), Family A, Микро-плато, Ложная Zone 3.

Сохраняет как confluence_catalog.json и выводит читаемую сводку.

Использование:
  python confluence_catalog.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import collatz_peak, analyze_to_peak
from zone_parity_search import extract_shifts

LOG2_3 = math.log2(3)

X_STAR = 20152090995747160937051
BARINA_71 = 1765856170146672440559
N_27 = 27

# Микро-плато: нетривиальные b для Family A (S/d > 1.05 из family_a_spectrum.csv)
MICRO_PLATEAU_B = [83, 103, 104, 109, 113, 117, 173, 174, 176, 237, 261, 267, 301, 302]


def accel_trajectory(n: int, max_steps: int = 500) -> list[int]:
    """Ускоренная траектория (нечётные x_k)."""
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


def build_class_zone2() -> dict:
    """Класс 1: Zone 2 (основной, x*)"""
    info = analyze_to_peak(X_STAR, max_steps=500_000)
    shifts = extract_shifts(X_STAR, max_steps=500_000)
    d = info['total_o']
    S = info['total_e']

    return {
        "class_id": 1,
        "name": "Zone 2 (x*)",
        "status": "CONFIRMED",
        "canonical_center": str(X_STAR),
        "center_bits": X_STAR.bit_length(),
        "peak": info['peak'],
        "d_from_center": d,
        "S_from_center": S,
        "S_d_from_center": round(S / d, 6) if d else None,
        "gain_from_center": round(d * LOG2_3 - S, 4),
        "input_range": "71-87 bits",
        "num_known_inputs": 913,
        "adapter_max": 7,
        "tail_hash": shifts[:20],
        "residue_mod_2_20": X_STAR % (1 << 20),
        "residue_mod_3_10": X_STAR % (3 ** 10),
    }


def build_class_barina() -> dict:
    """Класс 2: Barina (изолированный)"""
    info = analyze_to_peak(BARINA_71, max_steps=500_000)
    shifts = extract_shifts(BARINA_71, max_steps=500_000)
    d = info['total_o']
    S = info['total_e']

    return {
        "class_id": 2,
        "name": "Barina (isolated)",
        "status": "ISOLATED",
        "n": str(BARINA_71),
        "bits": BARINA_71.bit_length(),
        "peak": info['peak'],
        "d": d,
        "S": S,
        "S_d": round(S / d, 6) if d else None,
        "gain": round(d * LOG2_3 - S, 4),
        "connection_to_xstar": "NONE — fully isolated, no common trajectory points",
        "shift_vector_first_20": shifts[:20],
        "num_known_inputs": 1,
        "adapter_max": None,
    }


def build_class_mini_zone2() -> dict:
    """Класс 3: Mini-Zone 2 (число 27)"""
    traj_27 = accel_trajectory(27, max_steps=100)
    x7 = traj_27[7] if len(traj_27) > 7 else traj_27[-1]

    info_x7 = analyze_to_peak(x7, max_steps=500_000)
    shifts_x7 = extract_shifts(x7, max_steps=500_000)
    d_x7 = info_x7['total_o']
    S_x7 = info_x7['total_e']

    info_27 = analyze_to_peak(27, max_steps=500_000)
    peak_27, _, _ = collatz_peak(27, max_steps=500_000)

    return {
        "class_id": 3,
        "name": "Mini-Zone 2 (n=27)",
        "status": "CONFIRMED",
        "canonical_center": str(x7),
        "center_bits": x7.bit_length(),
        "peak": peak_27,
        "d_total_27": info_27['total_o'],
        "S_total_27": info_27['total_e'],
        "d_from_center": d_x7,
        "S_from_center": S_x7,
        "S_d_from_center": round(S_x7 / d_x7, 6) if d_x7 else None,
        "input_range": "5-13 bits",
        "num_known_inputs": 27,
        "adapter_max": 5,
        "tail_hash": shifts_x7[:10],
    }


def build_class_family_a() -> dict:
    """Класс 4: Family A (базовый слой)"""
    # Пример: 2^100-1
    n_100 = (1 << 100) - 1
    info_100 = analyze_to_peak(n_100, max_steps=500_000)
    d_100 = info_100['total_o']
    S_100 = info_100['total_e']

    return {
        "class_id": 4,
        "name": "Family A (baseline)",
        "status": "BASELINE",
        "description": "Numbers 2^b - 1 (all-ones binary)",
        "peak_formula": "approx b * log2(3)",
        "S_d_typical": round(S_100 / d_100, 4) if d_100 else None,
        "ratio_range": "1.58-1.62",
        "example_b100": {
            "n": "2^100 - 1",
            "peak": info_100['peak'],
            "d": d_100,
            "S": S_100,
            "ratio": round(info_100['peak'] / 100, 4),
        },
        "notable_plateaus": [
            {"b_range": "173-176", "peak": 280, "note": "log2(3) approx 485/306"},
            {"b_range": "301-304", "peak": 483, "note": "convergent 485/306"},
        ],
        "num_known_inputs": "infinite (all 2^b - 1)",
        "canonical_center": None,
        "adapter_max": None,
    }


def build_class_micro_plateaus() -> dict:
    """Класс 5: Микро-плато Family A"""
    plateaus = []
    for b in MICRO_PLATEAU_B:
        n = (1 << b) - 1
        info = analyze_to_peak(n, max_steps=500_000)
        d = info['total_o']
        S = info['total_e']
        peak = info['peak']
        plateaus.append({
            "b": b,
            "peak": peak,
            "ratio": round(peak / b, 5),
            "d": d,
            "S": S,
            "S_d": round(S / d, 5) if d else None,
        })

    return {
        "class_id": 5,
        "name": "Micro-plateaus (Family A anomalies)",
        "status": "OBSERVED",
        "description": "Specific b where 2^b-1 has anomalous peak, related to rational "
                       "approximations of log2(3)",
        "note": "Only 2^b-1, do not form families with other inputs",
        "plateaus": plateaus,
        "canonical_center": None,
        "adapter_max": None,
        "num_known_inputs": "1 per plateau (only 2^b - 1)",
    }


def build_class_false_zone3() -> dict:
    """Класс 6: Ложная Zone 3"""
    return {
        "class_id": 6,
        "name": "False Zone 3 (Family A vicinity)",
        "status": "REFUTED",
        "description": "~150-bit numbers near 2^150-1, peaks 237-244",
        "peak_range": "237-244",
        "core": "112 unit shifts (all ones)",
        "formula": "peak ≈ bits + 65.5 + L*1.585 - tail_sum",
        "refutation": "All candidates are Family A variants with high ones-density bias. "
                      "Bit inversion test and independent generation confirm no independent structure.",
        "canonical_center": None,
        "adapter_max": None,
        "num_known_inputs": 0,
        "S_d_typical": "~1.07",
    }


def main():
    print(f"{'=' * 80}")
    print(f"  Confluence Catalog — Collatz Crystal Hunter")
    print(f"{'=' * 80}")
    print()

    catalog = []

    # ── Класс 1: Zone 2 ──────────────────────────────────────────────────────
    print("  Computing Class 1: Zone 2 (x*)...")
    c1 = build_class_zone2()
    catalog.append(c1)

    print(f"    center = {c1['canonical_center'][:20]}... ({c1['center_bits']} bits)")
    print(f"    peak = {c1['peak']}, d = {c1['d_from_center']}, "
          f"S = {c1['S_from_center']}, S/d = {c1['S_d_from_center']:.4f}")
    print(f"    gain = {c1['gain_from_center']}, inputs = {c1['num_known_inputs']}")
    print(f"    tail_hash = {c1['tail_hash']}")
    print(f"    x* mod 2^20 = {c1['residue_mod_2_20']}")
    print(f"    x* mod 3^10 = {c1['residue_mod_3_10']}")

    # ── Класс 2: Barina ──────────────────────────────────────────────────────
    print("\n  Computing Class 2: Barina...")
    c2 = build_class_barina()
    catalog.append(c2)

    print(f"    n = {c2['n'][:20]}... ({c2['bits']} bits)")
    print(f"    peak = {c2['peak']}, d = {c2['d']}, S = {c2['S']}, "
          f"S/d = {c2['S_d']:.4f}")
    print(f"    connection to x*: {c2['connection_to_xstar']}")
    print(f"    shifts[:20] = {c2['shift_vector_first_20']}")

    # ── Класс 3: Mini-Zone 2 ─────────────────────────────────────────────────
    print("\n  Computing Class 3: Mini-Zone 2 (n=27)...")
    c3 = build_class_mini_zone2()
    catalog.append(c3)

    print(f"    center = {c3['canonical_center']} ({c3['center_bits']} bits)")
    print(f"    peak = {c3['peak']}, inputs = {c3['num_known_inputs']}")
    print(f"    d_from_center = {c3['d_from_center']}, "
          f"S_from_center = {c3['S_from_center']}, "
          f"S/d = {c3['S_d_from_center']:.4f}")
    print(f"    tail_hash = {c3['tail_hash']}")

    # ── Класс 4: Family A ────────────────────────────────────────────────────
    print("\n  Computing Class 4: Family A...")
    c4 = build_class_family_a()
    catalog.append(c4)

    print(f"    S/d typical = {c4['S_d_typical']}")
    print(f"    example (b=100): peak={c4['example_b100']['peak']}, "
          f"ratio={c4['example_b100']['ratio']}")
    print(f"    plateaus: {c4['notable_plateaus']}")

    # ── Класс 5: Микро-плато ─────────────────────────────────────────────────
    print("\n  Computing Class 5: Micro-plateaus...")
    c5 = build_class_micro_plateaus()
    catalog.append(c5)

    print(f"    {'b':>4}  {'peak':>5}  {'ratio':>7}  {'d':>5}  {'S':>5}  {'S/d':>7}")
    print(f"    {'-' * 40}")
    for p in c5['plateaus']:
        print(f"    {p['b']:>4}  {p['peak']:>5}  {p['ratio']:>7.4f}  "
              f"{p['d']:>5}  {p['S']:>5}  {p['S_d']:>7.4f}")

    # ── Класс 6: Ложная Zone 3 ───────────────────────────────────────────────
    print("\n  Computing Class 6: False Zone 3...")
    c6 = build_class_false_zone3()
    catalog.append(c6)

    print(f"    status: {c6['status']}")
    print(f"    peak range: {c6['peak_range']}")
    print(f"    core: {c6['core']}")

    # ══════════════════════════════════════════════════════════════════════════
    # СРАВНИТЕЛЬНАЯ ТАБЛИЦА
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n{'=' * 80}")
    print(f"  СРАВНИТЕЛЬНАЯ ТАБЛИЦА")
    print(f"{'=' * 80}")

    # Вычислим S/d для таблицы
    sd_z2 = f"{c1['S_d_from_center']:.2f}" if c1['S_d_from_center'] else "—"
    sd_bar = f"{c2['S_d']:.3f}" if c2['S_d'] else "—"
    sd_mini = f"{c3['S_d_from_center']:.2f}" if c3['S_d_from_center'] else "—"
    sd_fa = f"{c4['S_d_typical']}"
    sd_fz3 = "~1.07"

    center_z2 = c1['canonical_center'][:10] + ".."
    center_bar = c2['n'][:10] + ".."
    center_mini = c3['canonical_center']

    header = (f"  {'Класс':<18} {'center':>12} {'c_bits':>6} {'peak':>7} "
              f"{'inputs':>7} {'S/d':>7} {'adapt':>5} {'status':>10}")
    sep = f"  {'-' * 78}"

    print(header)
    print(sep)

    rows = [
        ("Zone 2 (x*)",   center_z2,  str(c1['center_bits']),
         str(c1['peak']),  str(c1['num_known_inputs']),
         sd_z2, "<=7", "CONFIRMED"),

        ("Barina",         center_bar, str(c2['bits']),
         str(c2['peak']),  "1",
         sd_bar, "—",  "ISOLATED"),

        ("Mini-Z2 (27)",   center_mini, str(c3['center_bits']),
         str(c3['peak']),  str(c3['num_known_inputs']),
         sd_mini, "<=5", "CONFIRMED"),

        ("Family A",       "—",        "—",
         "b*1.585", "inf",
         sd_fa, "—",   "BASELINE"),

        ("Micro-plateaus", "—",        "—",
         "varies", str(len(c5['plateaus'])),
         "varies", "—", "OBSERVED"),

        ("False Zone 3",   "—",        "—",
         "237-244", "0",
         sd_fz3, "—",  "REFUTED"),
    ]

    for name, center, cbits, peak, inputs, sd, adapt, status in rows:
        print(f"  {name:<18} {center:>12} {cbits:>6} {peak:>7} "
              f"{inputs:>7} {sd:>7} {adapt:>5} {status:>10}")

    # ══════════════════════════════════════════════════════════════════════════
    # КЛЮЧЕВЫЕ ВЫВОДЫ
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n{'=' * 80}")
    print(f"  КЛЮЧЕВЫЕ ВЫВОДЫ")
    print(f"{'=' * 80}")

    print(f"""
  1. Zone 2 — единственный подтверждённый нетривиальный confluence-класс
     для больших чисел. 913 входов (71–87 бит) сливаются к x* за ≤7 шагов.

  2. Barina (71 бит, d=213) — полностью изолирован от Zone 2.
     Другой shift-вектор, другой S/d ({sd_bar} vs {sd_z2}), нет общих
     промежуточных точек с x*.

  3. Mini-Zone 2 (n=27) — масштабная копия Zone 2 для малых чисел.
     Center={center_mini} (7 бит), peak=14. Структурно аналогичен.

  4. Family A (2^b−1) — базовый слой с ratio ≈ log₂3 ≈ 1.585.
     Плато на b=173–176 (peak=280) и b=301–304 (peak=483) связаны
     с рациональными приближениями log₂3.

  5. Zone 3 — НЕ СУЩЕСТВУЕТ как самостоятельная структура.
     Все кандидаты оказались вариациями Family A.

  6. В диапазоне 88–170 бит нет confluence-классов выше Family A.
     «Мёртвая зона» подтверждена: после 87 бит Zone 2 угасает,
     а новых зон нет.
""")

    # ── Сохраняем JSON ────────────────────────────────────────────────────────
    output_path = os.path.join(os.path.dirname(__file__), 'confluence_catalog.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"  Сохранено: {output_path}")

    print(f"\n{'=' * 80}")
    print(f"  Готово.")
    print(f"{'=' * 80}")


if __name__ == '__main__':
    main()
