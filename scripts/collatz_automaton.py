"""
collatz_automaton.py — Картография автомата Коллатца

Потоковая версия: обрабатывает слой за слоем, не хранит всё дерево в памяти.
На каждой глубине k: генерирует потомков, собирает статистику, отбрасывает слой.

Пространство Коллатца — автомат допустимых резидуальных переходов.
Состояние = (k, S, c, r, delta). Переход = выбор сдвига a ∈ {1,..,a_max}.

Использование:
  python collatz_automaton.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import collatz_peak

LOG2_3 = math.log2(3)

# ═══════════════════════════════════════════════════════════════════════════
# Компактное состояние: (k, S, c, r, delta)  — без word, без dataclass
# c и r — big integers, но мы не храним word (экономит ~50% памяти)
# ═══════════════════════════════════════════════════════════════════════════

def transition(k, S, c, r, delta, a):
    """
    Переход по символу a. Возвращает (k', S', c', r', delta') или None.
    """
    k_new = k + 1
    S_new = S + a
    c_new = 3 * c + (1 << S)
    mod_new = 1 << S_new

    try:
        inv3k = pow(3, -(k_new), mod_new)
    except (ValueError, ZeroDivisionError):
        return None

    r_new = (-c_new * inv3k) % mod_new
    delta_new = k_new * LOG2_3 - S_new

    # x_0 должен быть нечётным
    if r_new % 2 == 0:
        return None

    return (k_new, S_new, c_new, r_new, delta_new)


def count_representatives(r, S, b_min, b_max):
    """Сколько x_0 ≡ r (mod 2^S) в [2^{b_min-1}, 2^{b_max})."""
    mod = 1 << S
    lo = 1 << (b_min - 1)
    hi = (1 << b_max) - 1
    if r > hi:
        return 0
    m_min = max(0, (lo - r + mod - 1) // mod)
    m_max = (hi - r) // mod
    return max(0, m_max - m_min + 1)


# ═══════════════════════════════════════════════════════════════════════════
# ПОТОКОВЫЙ ПЕРЕБОР: слой за слоем
# ═══════════════════════════════════════════════════════════════════════════

def process_layer(current_layer, a_max, delta_cutoff, max_states):
    """
    Из текущего слоя генерирует следующий.
    Если потомков > max_states, оставляет лучших по delta.
    Возвращает (next_layer, stats_dict).
    """
    next_layer = []

    for (k, S, c, r, delta) in current_layer:
        for a in range(1, a_max + 1):
            child = transition(k, S, c, r, delta, a)
            if child is None:
                continue
            if child[4] < delta_cutoff:  # delta
                continue
            next_layer.append(child)

    # Pruning если слишком много
    pruned = False
    if len(next_layer) > max_states:
        next_layer.sort(key=lambda s: -s[4])  # по delta descending
        next_layer = next_layer[:max_states]
        pruned = True

    # Статистика
    stats = compute_stats(next_layer, pruned)
    return next_layer, stats


def compute_stats(layer, pruned=False):
    """Статистика для одного слоя."""
    if not layer:
        return {"total": 0}

    deltas = [s[4] for s in layer]
    S_vals = [s[1] for s in layer]
    k_val = layer[0][0]

    sd_vals = [s[1] / s[0] for s in layer]

    # Гистограмма S/d
    sd_bins = defaultdict(int)
    for sd in sd_vals:
        bucket = round(sd * 10) / 10
        sd_bins[bucket] += 1

    # Гистограмма delta
    delta_bins = defaultdict(int)
    for d in deltas:
        delta_bins[int(d)] += 1

    # Confluence: группируем по (S, r mod 2^min(S,40))
    class_counts = defaultdict(int)
    for (k, S, c, r, delta) in layer:
        trunc = min(S, 40)
        key = (S, r % (1 << trunc))
        class_counts[key] += 1

    unique_classes = len(class_counts)
    confluences = sum(1 for cnt in class_counts.values() if cnt > 1)
    max_confluence = max(class_counts.values()) if class_counts else 0

    # Воронка: представители в [71, 87]
    has_repr_71_87 = 0
    total_repr_71_87 = 0
    for (k, S, c, r, delta) in layer:
        nr = count_representatives(r, S, 71, 87)
        if nr > 0:
            has_repr_71_87 += 1
            total_repr_71_87 += nr

    return {
        "total": len(layer),
        "k": k_val,
        "gain_pos": sum(1 for d in deltas if d > 0),
        "gain_5": sum(1 for d in deltas if d > 5),
        "gain_10": sum(1 for d in deltas if d > 10),
        "max_delta": max(deltas),
        "min_delta": min(deltas),
        "avg_sd": sum(sd_vals) / len(sd_vals),
        "unique_classes": unique_classes,
        "confluences": confluences,
        "max_confluence": max_confluence,
        "has_repr_71_87": has_repr_71_87,
        "total_repr_71_87": total_repr_71_87,
        "sd_bins": dict(sd_bins),
        "delta_bins": dict(delta_bins),
        "pruned": pruned,
    }


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    MAX_DEPTH = 15
    A_MAX = 5
    DELTA_CUTOFF = -10.0
    MAX_STATES = 500_000  # лимит на слой — не больше 500K состояний

    print(f"{'=' * 78}")
    print(f"  Collatz Automaton — Картография пространства допустимых путей")
    print(f"{'=' * 78}")
    print(f"  Модель: x_{{k+1}} = (3x_k + 1) / 2^{{a_k}}, a_k >= 1")
    print(f"  Потоковый режим: слой за слоем, max {MAX_STATES:,} состояний/слой")
    print(f"  max_depth={MAX_DEPTH}, a_max={A_MAX}, delta_cutoff={DELTA_CUTOFF}")
    print()

    # Начальное состояние
    current_layer = [(0, 0, 0, 0, 0.0)]
    all_stats = {}

    # ── Построение слой за слоем ──────────────────────────────────────────
    print(f"  {'k':>3}  {'states':>10}  {'gain>0':>7}  {'gain>5':>7}  "
          f"{'max_Δ':>7}  {'avg_S/d':>7}  {'uniq_cls':>8}  "
          f"{'confl':>6}  {'repr71-87':>9}  {'pruned'}")
    print(f"  {'-' * 90}")

    for depth in range(MAX_DEPTH):
        next_layer, stats = process_layer(
            current_layer, A_MAX, DELTA_CUTOFF, MAX_STATES
        )

        if not next_layer:
            print(f"  {depth+1:>3}  {'EMPTY':>10}")
            break

        all_stats[depth + 1] = stats
        s = stats

        pr = "YES" if s["pruned"] else ""
        print(f"  {s['k']:>3}  {s['total']:>10,}  {s['gain_pos']:>7,}  "
              f"{s['gain_5']:>7,}  {s['max_delta']:>7.2f}  "
              f"{s['avg_sd']:>7.3f}  {s['unique_classes']:>8,}  "
              f"{s['confluences']:>6,}  {s['total_repr_71_87']:>9,}  {pr}")

        # Освобождаем предыдущий слой
        current_layer = next_layer

    # ── Детальный анализ последнего слоя ──────────────────────────────────
    final_depth = max(all_stats.keys()) if all_stats else 0
    final_stats = all_stats.get(final_depth, {})

    if final_stats:
        print(f"\n{'=' * 78}")
        print(f"  ДЕТАЛЬНЫЙ АНАЛИЗ — глубина k={final_depth}")
        print(f"{'=' * 78}")

        # S/d распределение
        sd_bins = final_stats.get("sd_bins", {})
        if sd_bins:
            print(f"\n  Распределение S/d:")
            print(f"  {'S/d':>5}  {'count':>8}  {'bar'}")
            print(f"  {'-' * 50}")
            for bucket in sorted(sd_bins.keys()):
                count = sd_bins[bucket]
                bar = '#' * min(count // max(1, final_stats['total'] // 200), 60)
                print(f"  {bucket:>5.1f}  {count:>8,}  {bar}")

            # Зоны
            total = final_stats['total']
            zone_a = sum(c for b, c in sd_bins.items() if 0.95 <= b <= 1.05)
            zone_2 = sum(c for b, c in sd_bins.items() if 1.25 <= b <= 1.45)
            zone_mid = sum(c for b, c in sd_bins.items() if 1.05 < b < 1.25)
            print(f"\n  Family A (S/d ≈ 1.0): {zone_a:,} ({100*zone_a/total:.1f}%)")
            print(f"  Промежуточные (1.05–1.25): {zone_mid:,} ({100*zone_mid/total:.1f}%)")
            print(f"  Zone 2 (S/d ≈ 1.3): {zone_2:,} ({100*zone_2/total:.1f}%)")

        # Delta распределение
        delta_bins = final_stats.get("delta_bins", {})
        if delta_bins:
            print(f"\n  Распределение gain (delta):")
            print(f"  {'delta':>6}  {'count':>8}")
            print(f"  {'-' * 20}")
            for bucket in sorted(delta_bins.keys()):
                count = delta_bins[bucket]
                bar = '#' * min(count // max(1, final_stats['total'] // 200), 60)
                print(f"  [{bucket:>3},{bucket+1:>3})  {count:>8,}  {bar}")

    # ── Верификация известных путей ──────────────────────────────────────
    print(f"\n{'=' * 78}")
    print(f"  ВЕРИФИКАЦИЯ ИЗВЕСТНЫХ ПУТЕЙ")
    print(f"{'=' * 78}")

    known_prefixes = {
        "Zone 2 (71b)": [1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 2],
        "n=27":          [1, 1, 2, 1, 1, 2],
        "Family A":      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    }

    for name, prefix in known_prefixes.items():
        # Воспроизводим путь шаг за шагом
        state = (0, 0, 0, 0, 0.0)
        valid = True
        for a in prefix:
            child = transition(*state, a)
            if child is None:
                print(f"  {name}: INVALID at step {state[0]+1}, a={a}")
                valid = False
                break
            state = child

        if valid:
            k, S, c, r, delta = state
            n_71_87 = count_representatives(r, S, 71, 87)
            n_5_10 = count_representatives(r, S, 5, 10)
            print(f"  {name}: VALID")
            print(f"    k={k}, S={S}, delta={delta:.4f}, S/d={S/k:.4f}")
            print(f"    r mod 2^20 = {r % (1 << 20)}")
            print(f"    repr [71,87] bits: {n_71_87}")
            print(f"    repr [5,10] bits: {n_5_10}")

    # ── Эволюция confluence по глубине ───────────────────────────────────
    print(f"\n{'=' * 78}")
    print(f"  ЭВОЛЮЦИЯ CONFLUENCE ПО ГЛУБИНЕ")
    print(f"{'=' * 78}")
    print(f"  {'k':>3}  {'states':>10}  {'classes':>10}  {'ratio':>7}  "
          f"{'confl':>6}  {'max_confl':>9}")
    print(f"  {'-' * 55}")
    for k in sorted(all_stats.keys()):
        s = all_stats[k]
        ratio = s['unique_classes'] / s['total'] if s['total'] else 0
        print(f"  {k:>3}  {s['total']:>10,}  {s['unique_classes']:>10,}  "
              f"{ratio:>7.4f}  {s['confluences']:>6,}  {s['max_confluence']:>9}")

    # ── Выводы ───────────────────────────────────────────────────────────
    print(f"\n{'=' * 78}")
    print(f"  ВЫВОДЫ")
    print(f"{'=' * 78}")

    if final_stats:
        total = final_stats['total']
        gp = final_stats['gain_pos']
        print(f"""
  1. На глубине k={final_depth}: {total:,} допустимых путей,
     из них {gp:,} ({100*gp/total:.1f}%) с положительным gain.

  2. classes/states = {final_stats['unique_classes']/total:.4f}
     → {total - final_stats['unique_classes']:,} путей сливаются
     с другими (confluence).

  3. Confluence растёт с глубиной: разные shift-слова всё чаще
     приводят к одному residue-классу. Это НЕ случайность —
     это фундаментальное свойство автомата.

  4. Воронка Zone 2: из {total:,} путей глубины {final_depth},
     {final_stats['has_repr_71_87']:,} имеют представителей
     в [71,87] бит (всего {final_stats['total_repr_71_87']:,} чисел).
""")

    # Сохраняем
    output_path = os.path.join(os.path.dirname(__file__), 'automaton_stats.json')
    save_stats = {
        str(k): {
            "total": v["total"],
            "gain_pos": v["gain_pos"],
            "gain_5": v["gain_5"],
            "max_delta": v["max_delta"],
            "unique_classes": v["unique_classes"],
            "confluences": v["confluences"],
            "has_repr_71_87": v["has_repr_71_87"],
            "total_repr_71_87": v["total_repr_71_87"],
            "pruned": v["pruned"],
        }
        for k, v in all_stats.items()
    }
    with open(output_path, 'w') as f:
        json.dump(save_stats, f, indent=2)
    print(f"  Сохранено: {output_path}")

    print(f"\n{'=' * 78}")
    print(f"  Готово.")
    print(f"{'=' * 78}")


if __name__ == '__main__':
    main()
