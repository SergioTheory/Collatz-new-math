"""
hr_depth_transitional.py — HR(dP) для переходных центров

Протокол:
1. Для каждого центра c с пиком P и глубины k:
   - Строим обратное дерево до depth=k
   - Берём узлы на глубине k, считаем распределение бит
   - Окно W = [q05, q95] фактического распределения бит
   - HR = доля узлов в окне W с peak == P
   - dP = P - q95 (запас до пика)
2. Строим HR vs dP для трёх групп: Class A, Class B, Transitional
3. Ключевая метрика: скорость спада dHR/d(dP)
"""

import sys
import os
import time
import random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crt_solver import collatz_peak

X_STAR = 20152090995747160937051

# ============================================================
# Центры по группам
# ============================================================
CENTERS = {
    'A': [
        (121, 14, "121"),
        (X_STAR, 140, "x*"),
    ],
    'B': [
        (35337455, 40, "35337455"),    # peak=40, d=41, S/d=1.27
        (8524379, 36, "8524379"),      # peak=36, d=53, S/d=1.38
        (1396693151, 50, "1396693151"),# peak=50, d=53, S/d=1.26
    ],
    'TR': [
        (26658983, 35, "26658983"),    # peak=35, d=61, S/d=1.459
        (67625867, 37, "67625867"),    # peak=37, d=69, S/d=1.464
        (37748015, 41, "37748015"),    # peak=41, d=81, S/d=1.420
        (2303929595, 48, "2303929595"),# peak=48, d=111, S/d=1.450
        (3830005073, 49, "3830005073"),# peak=49, d=73, S/d=1.384
    ],
}

DEPTHS = [1, 2, 3, 4, 5, 7, 9, 11, 13]


def reverse_step(x, max_a=15):
    """Обратный шаг: нечётные прообразы y = (x * 2^a - 1) / 3."""
    preds = []
    for a in range(1, max_a + 1):
        y = x * (1 << a) - 1
        if y % 3 == 0:
            y3 = y // 3
            if y3 > 0 and y3 % 2 == 1:
                preds.append(y3)
    return preds


def build_reverse_tree_by_depth(root, max_depth, max_bits=500, max_nodes_per_layer=50000):
    """Строим обратное дерево, возвращая узлы по глубинам."""
    layers = {0: [root]}
    all_seen = {root}
    for d in range(1, max_depth + 1):
        layer = []
        for parent in layers[d - 1]:
            for pred in reverse_step(parent, max_a=15):
                if pred.bit_length() <= max_bits and pred not in all_seen:
                    layer.append(pred)
                    all_seen.add(pred)
        if len(layer) > max_nodes_per_layer:
            print(f"      depth={d}: truncating from {len(layer)} to {max_nodes_per_layer}")
            layer = random.sample(layer, max_nodes_per_layer)
        layers[d] = layer
        if not layer:
            break
    return layers


def quantile(data, q):
    """Простой квантиль."""
    if not data:
        return 0
    s = sorted(data)
    idx = int(len(s) * q)
    idx = min(idx, len(s) - 1)
    return s[idx]


def run_experiment():
    print("=" * 75)
    print("HR(dP) EXPERIMENT: Class A vs Class B vs Transitional")
    print("=" * 75)
    print()

    global PEAK_CACHE
    PEAK_CACHE = {}

    # Результаты: group -> [(center_name, depth, HR, dP, window, n_in_window)]
    results = {}

    for group_name, centers in CENTERS.items():
        results[group_name] = []
        print(f"\n{'='*60}")
        print(f"GROUP: {group_name}")
        print(f"{'='*60}")

        for center, peak, label in centers:
            print(f"\n  Center: {label} (peak={peak}, {center.bit_length()} bits)")

            # x* имеет огромное обратное дерево, ограничим глубины
            if center == X_STAR:
                depths_to_use = [d for d in DEPTHS if d <= 9]
            else:
                depths_to_use = DEPTHS

            # Строим дерево до максимальной нужной глубины
            max_d = max(depths_to_use)
            t0 = time.time()
            layers = build_reverse_tree_by_depth(center, max_d, max_bits=500)
            t1 = time.time()
            total_nodes = sum(len(layers[d]) for d in layers)
            print(f"    Tree built: {total_nodes} nodes in {t1-t0:.1f}s")

            for k in depths_to_use:
                nodes_at_k = layers.get(k, [])
                if len(nodes_at_k) < 5:
                    print(f"    depth={k}: too few nodes ({len(nodes_at_k)}), skip")
                    continue

                bits_at_k = [n.bit_length() for n in nodes_at_k]
                q05 = quantile(bits_at_k, 0.05)
                q95 = quantile(bits_at_k, 0.95)
                window_top = min(q95, peak - 1)
                window = (q05, window_top)
                dP = peak - window_top

                # Фильтруем узлы в окне
                in_window = [n for n in nodes_at_k 
                             if q05 <= n.bit_length() <= window_top]

                if not in_window:
                    print(f"    depth={k}: W=[{q05},{window_top}], 0 nodes in window, skip (q05 > peak-1)")
                    continue
                
                if len(in_window) < 20:
                    print(f"    WARNING: small sample ({len(in_window)}), HR unreliable")

                # Считаем HR
                t2 = time.time()
                hits = 0
                for n in in_window:
                    if n not in PEAK_CACHE:
                        PEAK_CACHE[n] = collatz_peak(n)[0]
                    pk = PEAK_CACHE[n]
                    if pk == peak:
                        hits += 1
                t3 = time.time()

                hr = hits / len(in_window)
                results[group_name].append(
                    (label, k, hr, dP, window, len(in_window), hits))

                print(f"    depth={k}: W=[{q05},{q95}], dP={dP:+d}, "
                      f"HR={hr:.4f} ({hits}/{len(in_window)}), "
                      f"time={t3-t2:.1f}s")

    # ============================================================
    # Сводная таблица
    # ============================================================
    print(f"\n\n{'='*75}")
    print("SUMMARY TABLE: HR vs dP by group")
    print(f"{'='*75}")
    print(f"{'Group':<5} {'Center':<15} {'depth':>5} {'dP':>5} {'HR':>8} "
          f"{'hits/total':>12} {'Window':>12}")
    print("-" * 75)

    for group_name in ['A', 'B', 'TR']:
        for label, k, hr, dP, window, n_total, hits in results[group_name]:
            print(f"{group_name:<5} {label:<15} {k:>5} {dP:>5} {hr:>8.4f} "
                  f"{hits:>5}/{n_total:<5} [{window[0]:>3},{window[1]:>3}]")
        print()

    # ============================================================
    # Анализ наклонов
    # ============================================================
    print(f"\n{'='*75}")
    print("SLOPE ANALYSIS: dHR/d(dP) per center")
    print(f"{'='*75}")

    for group_name in ['A', 'B', 'TR']:
        print(f"\n  Group {group_name}:")
        # Группируем по центру
        by_center = {}
        for label, k, hr, dP, window, n_total, hits in results[group_name]:
            if label not in by_center:
                by_center[label] = []
            by_center[label].append((dP, hr))

        for label, points in by_center.items():
            points.sort(key=lambda x: -x[0])  # от большого dP к малому
            if len(points) >= 2:
                # Линейный наклон
                dPs = [p[0] for p in points]
                HRs = [p[1] for p in points]
                # Простая оценка среднего наклона
                slopes = []
                for i in range(len(points) - 1):
                    if dPs[i] != dPs[i+1]:
                        slope = (HRs[i+1] - HRs[i]) / (dPs[i+1] - dPs[i])
                        slopes.append(slope)
                if slopes:
                    avg_slope = sum(slopes) / len(slopes)
                    print(f"    {label}: dP range [{min(dPs)}, {max(dPs)}], "
                          f"HR range [{min(HRs):.4f}, {max(HRs):.4f}], "
                          f"avg slope = {avg_slope:.6f} HR/bit")
                else:
                    print(f"    {label}: only 1 point or constant dP")
            else:
                print(f"    {label}: only {len(points)} point(s)")

    # ============================================================
    # Интерпретация
    # ============================================================
    print(f"\n\n{'='*75}")
    print("INTERPRETATION MATRIX")
    print(f"{'='*75}")
    print("""
    If TR curve is flat like Class A (HR >= 0.95 for all dP):
      -> Transitional = proto-Class A
      -> Class A is tail of continuum, not discrete hierarchy
      -> Scaling x10 loses special status

    If TR curve drops like Class B:  
      -> Transitional = strong Class B
      -> Class A remains discrete extremum
      -> Scaling x10 hypothesis lives

    If TR curve has intermediate slope:
      -> Continuum with gradient boundary
      -> Refine section 9.4 accordingly
    """)


if __name__ == '__main__':
    run_experiment()
