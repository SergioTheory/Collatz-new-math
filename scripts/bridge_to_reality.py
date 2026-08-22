"""
bridge_to_reality.py — Bridge from symbolic automaton to real Collatz numbers

Maps every symbolic shift-word to concrete integer representatives,
verifies each against the real Collatz trajectory, and aggregates
results by symbolic word and by actual confluence center.

Architecture:
  A. Symbolic layer   — builds path states via transition()
  B. Representative   — turns (r, S) into concrete integers in target bit windows
  C. Verification     — runs Collatz peak analysis, checks center hits before peak
  D. Aggregation      — groups by symbolic word and by center

Usage:
  python bridge_to_reality.py [OPTIONS]
  python bridge_to_reality.py --max-depth 8 --a-max 3 --windows 5,10 71,87
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from crt_solver import collatz_peak, analyze_to_peak
from collatz_automaton import transition, count_representatives

LOG2_3 = math.log2(3)

KNOWN_CENTERS = {
    121:                       "c121",
    6803:                      "c6803",
    27611:                     "c27611",
    61823:                     "c61823",
    5808671:                   "c5808671",
    20152090995747160937051:   "xstar",
}

KNOWN_CENTER_NAMES = {v: k for k, v in KNOWN_CENTERS.items()}


# ═══════════════════════════════════════════════════════════════════════════
# A. SYMBOLIC LAYER
# ═══════════════════════════════════════════════════════════════════════════

def build_symbolic_layer(max_depth, a_max, delta_cutoff, max_states_per_layer):
    """
    Builds the symbolic automaton layer by layer.
    Unlike collatz_automaton.py, we KEEP the shift-word (as a tuple)
    because bridge mode needs it. To stay memory-safe we cap each layer.

    Yields (depth, layer) where layer = list of (k, S, c, r, delta, word).
    Only yields the final requested depth, or all depths if needed.
    Returns a dict: depth -> list of states (with word).
    """
    # State: (k, S, c, r, delta, word)
    current = [(0, 0, 0, 0, 0.0, ())]
    layers = {0: current}

    for depth in range(max_depth):
        nxt = []
        for (k, S, c, r, delta, word) in current:
            for a in range(1, a_max + 1):
                child = transition(k, S, c, r, delta, a)
                if child is None:
                    continue
                k2, S2, c2, r2, delta2 = child
                if delta2 < delta_cutoff:
                    continue
                nxt.append((k2, S2, c2, r2, delta2, word + (a,)))

        if len(nxt) > max_states_per_layer:
            nxt.sort(key=lambda s: -s[4])
            nxt = nxt[:max_states_per_layer]

        layers[depth + 1] = nxt
        current = nxt

        if not nxt:
            break

    return layers


# ═══════════════════════════════════════════════════════════════════════════
# B. REPRESENTATIVE LAYER
# ═══════════════════════════════════════════════════════════════════════════

def enumerate_representatives(r, S, b_min, b_max, max_count=20):
    """
    Enumerate concrete odd integers n ≡ r (mod 2^S) in [2^{b_min-1}, 2^{b_max}).
    Returns list of integers, up to max_count.
    """
    mod = 1 << S
    lo = 1 << (b_min - 1)
    hi = (1 << b_max) - 1

    if r > hi:
        return []
    if r == 0:
        r_eff = mod  # smallest positive in class
    else:
        r_eff = r

    if r_eff >= lo:
        m_start = 0
    else:
        m_start = (lo - r_eff + mod - 1) // mod

    results = []
    for m in range(m_start, m_start + max_count + 1):
        n = r_eff + m * mod
        if n > hi:
            break
        if n < lo:
            continue
        results.append(n)
        if len(results) >= max_count:
            break

    return results


# ═══════════════════════════════════════════════════════════════════════════
# C. VERIFICATION LAYER
# ═══════════════════════════════════════════════════════════════════════════

def accel_trajectory_to_peak(n, max_odd_steps=1000):
    """
    Accelerated Collatz trajectory (odd steps only) up to peak.
    Returns (peak_bits, odd_values_before_peak).
    odd_values_before_peak: list of odd x_k encountered BEFORE peak is reached.
    """
    cur = n
    while cur > 1 and cur % 2 == 0:
        cur >>= 1

    peak_val = cur
    peak_bits = cur.bit_length()
    trajectory = [cur]

    for _ in range(max_odd_steps):
        if cur <= 1:
            break
        val = 3 * cur + 1
        while val % 2 == 0:
            val >>= 1
        cur = val
        trajectory.append(cur)
        if cur.bit_length() > peak_bits:
            peak_bits = cur.bit_length()
            peak_val = cur

    # Split into before-peak and after-peak
    # Find index of peak_val (first occurrence of max bit_length)
    peak_idx = 0
    for i, x in enumerate(trajectory):
        if x.bit_length() == peak_bits:
            peak_idx = i
            break

    before_peak = trajectory[:peak_idx]  # strictly before
    return peak_bits, before_peak, trajectory


def verify_representative(n, known_centers_set):
    """
    Verify one concrete representative.
    Returns dict with verification results.
    """
    bits = n.bit_length()
    peak, steps, conv = collatz_peak(n, max_steps=500_000)
    ratio = peak / bits if bits > 0 else 0

    # Accelerated trajectory for center detection
    peak_bits_accel, before_peak, full_traj = accel_trajectory_to_peak(
        n, max_odd_steps=1000
    )

    before_peak_set = set(before_peak)
    full_set = set(full_traj)

    pre_peak_hits = {}
    post_peak_hits = {}

    for center in known_centers_set:
        if center in before_peak_set:
            # Find step
            for k, x in enumerate(before_peak):
                if x == center:
                    pre_peak_hits[center] = k
                    break
        elif center in full_set:
            for k, x in enumerate(full_traj):
                if x == center:
                    post_peak_hits[center] = k
                    break

    return {
        "n": n,
        "bits": bits,
        "peak": peak,
        "ratio": round(ratio, 6),
        "steps": steps,
        "pre_peak_centers": pre_peak_hits,
        "post_peak_centers": post_peak_hits,
        "any_pre_peak": len(pre_peak_hits) > 0,
        "any_center": len(pre_peak_hits) + len(post_peak_hits) > 0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# D. AGGREGATION LAYER
# ═══════════════════════════════════════════════════════════════════════════

class WordAggregator:
    """Aggregates results per symbolic word."""

    __slots__ = (
        "word", "k", "S", "gain", "S_over_d",
        "total_repr", "repr_with_center", "repr_with_pre_peak",
        "centers_hit", "sample_n", "sample_peaks",
    )

    def __init__(self, word, k, S):
        self.word = word
        self.k = k
        self.S = S
        self.gain = round(k * LOG2_3 - S, 6)
        self.S_over_d = round(S / k, 6) if k > 0 else 0
        self.total_repr = 0
        self.repr_with_center = 0
        self.repr_with_pre_peak = 0
        self.centers_hit = set()
        self.sample_n = []
        self.sample_peaks = []

    def add(self, vr):
        self.total_repr += 1
        if vr["any_center"]:
            self.repr_with_center += 1
        if vr["any_pre_peak"]:
            self.repr_with_pre_peak += 1
        for c in vr["pre_peak_centers"]:
            self.centers_hit.add(c)
        for c in vr["post_peak_centers"]:
            self.centers_hit.add(c)
        if len(self.sample_n) < 5:
            self.sample_n.append(vr["n"])
            self.sample_peaks.append(vr["peak"])

    def to_dict(self):
        return {
            "word": list(self.word),
            "k": self.k,
            "S": self.S,
            "gain": self.gain,
            "S_over_d": self.S_over_d,
            "total_repr": self.total_repr,
            "repr_with_center": self.repr_with_center,
            "repr_with_pre_peak": self.repr_with_pre_peak,
            "centers_hit": sorted(self.centers_hit),
            "sample_n": [str(x) for x in self.sample_n],
            "sample_peaks": self.sample_peaks,
        }


class CenterAggregator:
    """Aggregates results per known center."""

    def __init__(self, center_value, center_name):
        self.center = center_value
        self.name = center_name
        self.words = set()          # distinct symbolic words
        self.total_repr = 0
        self.pre_peak_repr = 0
        self.sum_k = 0
        self.sum_gain = 0.0
        self.sum_sd = 0.0
        self.sample_words = []
        self.sample_n = []

    def add(self, word_agg, vr, is_pre_peak):
        word_tuple = word_agg.word
        self.words.add(word_tuple)
        self.total_repr += 1
        if is_pre_peak:
            self.pre_peak_repr += 1
        self.sum_k += word_agg.k
        self.sum_gain += word_agg.gain
        self.sum_sd += word_agg.S_over_d
        if len(self.sample_words) < 10 and word_tuple not in set(
            tuple(w) for w in self.sample_words
        ):
            self.sample_words.append(list(word_tuple))
        if len(self.sample_n) < 10:
            self.sample_n.append(str(vr["n"]))

    def to_dict(self):
        n = self.total_repr if self.total_repr > 0 else 1
        return {
            "center": str(self.center),
            "name": self.name,
            "distinct_words": len(self.words),
            "total_repr": self.total_repr,
            "pre_peak_repr": self.pre_peak_repr,
            "avg_k": round(self.sum_k / n, 2),
            "avg_gain": round(self.sum_gain / n, 4),
            "avg_S_over_d": round(self.sum_sd / n, 4),
            "sample_words": self.sample_words[:5],
            "sample_n": self.sample_n[:5],
        }


# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def parse_windows(windows_str):
    """Parse '5,10 71,87 88,90' into [(5,10), (71,87), (88,90)]."""
    result = []
    for w in windows_str.split():
        parts = w.split(',')
        if len(parts) == 2:
            result.append((int(parts[0]), int(parts[1])))
    return result


def run_bridge(max_depth, a_max, delta_cutoff, max_states,
               windows, max_repr_per_state, output_json, output_csv):

    known_set = set(KNOWN_CENTERS.keys())

    print(f"{'=' * 78}")
    print(f"  Bridge to Reality — symbolic automaton → real Collatz numbers")
    print(f"{'=' * 78}")
    print(f"  max_depth={max_depth}, a_max={a_max}, delta_cutoff={delta_cutoff}")
    print(f"  max_states/layer={max_states}, max_repr/state={max_repr_per_state}")
    print(f"  windows={windows}")
    print(f"  known centers: {list(KNOWN_CENTERS.values())}")
    print()

    # ── A. Build symbolic layers ─────────────────────────────────────────
    t0 = time.time()
    print("  Building symbolic automaton...")
    layers = build_symbolic_layer(max_depth, a_max, delta_cutoff, max_states)
    t_sym = time.time() - t0

    total_states = sum(len(v) for v in layers.values())
    print(f"  Done in {t_sym:.1f}s. Total states: {total_states:,}")

    # Layer summary
    print(f"\n  {'k':>3}  {'states':>10}  {'gain>0':>7}")
    print(f"  {'-' * 25}")
    for k in sorted(layers.keys()):
        layer = layers[k]
        gp = sum(1 for s in layer if s[4] > 0)
        print(f"  {k:>3}  {len(layer):>10,}  {gp:>7,}")

    # ── B+C+D. Process each depth: representatives + verification ────────
    print(f"\n  Processing representatives and verification...")

    word_aggs = {}  # word_tuple -> WordAggregator
    center_aggs = {c: CenterAggregator(c, name)
                   for c, name in KNOWN_CENTERS.items()}

    # Per-window counters
    window_counts = {w: 0 for w in windows}
    window_verified = {w: 0 for w in windows}

    # Depth statistics for report
    depth_stats = defaultdict(lambda: {
        "states": 0, "repr_total": 0, "repr_any_center": 0,
        "repr_pre_peak": 0,
    })

    total_verified = 0
    total_pre_peak = 0
    t_start = time.time()

    for depth in sorted(layers.keys()):
        if depth == 0:
            continue

        layer = layers[depth]
        ds = depth_stats[depth]
        ds["states"] = len(layer)

        for (k, S, c, r, delta, word) in layer:
            # Create or get word aggregator
            if word not in word_aggs:
                word_aggs[word] = WordAggregator(word, k, S)
            wa = word_aggs[word]

            # Enumerate representatives for each window
            for (b_min, b_max) in windows:
                reps = enumerate_representatives(
                    r, S, b_min, b_max, max_count=max_repr_per_state
                )
                window_counts[(b_min, b_max)] += len(reps)

                for n in reps:
                    if n <= 1 or n % 2 == 0:
                        continue

                    vr = verify_representative(n, known_set)
                    wa.add(vr)
                    total_verified += 1

                    ds["repr_total"] += 1
                    window_verified[(b_min, b_max)] += 1

                    if vr["any_center"]:
                        ds["repr_any_center"] += 1

                    if vr["any_pre_peak"]:
                        ds["repr_pre_peak"] += 1
                        total_pre_peak += 1

                    # Feed center aggregators
                    for center_val, step in vr["pre_peak_centers"].items():
                        if center_val in center_aggs:
                            center_aggs[center_val].add(wa, vr, True)

                    for center_val, step in vr["post_peak_centers"].items():
                        if center_val in center_aggs:
                            center_aggs[center_val].add(wa, vr, False)

        elapsed = time.time() - t_start
        if elapsed > 0:
            rate = total_verified / elapsed
        else:
            rate = 0
        print(f"    depth {depth:>2}: {len(layer):>8,} states, "
              f"verified {ds['repr_total']:>6,} reps, "
              f"pre-peak hits {ds['repr_pre_peak']:>4,}  "
              f"({rate:.0f} verif/s)")

    t_total = time.time() - t0

    # Free layers
    del layers

    # ══════════════════════════════════════════════════════════════════════
    # REPORTS
    # ══════════════════════════════════════════════════════════════════════

    print(f"\n{'=' * 78}")
    print(f"  RESULTS ({t_total:.1f}s total)")
    print(f"{'=' * 78}")

    # 1. Symbolic depth statistics
    print(f"\n  1. SYMBOLIC DEPTH STATISTICS")
    print(f"  {'k':>3}  {'states':>8}  {'repr':>8}  {'any_ctr':>8}  "
          f"{'pre_peak':>8}  {'pre%':>6}")
    print(f"  {'-' * 50}")
    for k in sorted(depth_stats.keys()):
        ds = depth_stats[k]
        pct = (100 * ds["repr_pre_peak"] / ds["repr_total"]
               if ds["repr_total"] > 0 else 0)
        print(f"  {k:>3}  {ds['states']:>8,}  {ds['repr_total']:>8,}  "
              f"{ds['repr_any_center']:>8,}  {ds['repr_pre_peak']:>8,}  "
              f"{pct:>5.1f}%")

    # 2. Representative counts by bit window
    print(f"\n  2. REPRESENTATIVES BY BIT WINDOW")
    print(f"  {'window':>12}  {'enumerated':>10}  {'verified':>10}")
    print(f"  {'-' * 35}")
    for w in windows:
        print(f"  [{w[0]:>3},{w[1]:>3}]  {window_counts[w]:>10,}  "
              f"{window_verified[w]:>10,}")

    # 3. Center multiplicity table
    print(f"\n  3. CENTER MULTIPLICITY TABLE")
    print(f"  {'center':>25}  {'name':>10}  {'words':>6}  {'repr':>6}  "
          f"{'pre_pk':>6}  {'avg_k':>5}  {'avg_gain':>8}  {'avg_S/d':>7}")
    print(f"  {'-' * 85}")
    for c_val in sorted(KNOWN_CENTERS.keys()):
        ca = center_aggs[c_val]
        d = ca.to_dict()
        c_short = str(c_val)
        if len(c_short) > 22:
            c_short = c_short[:10] + ".." + c_short[-10:]
        print(f"  {c_short:>25}  {d['name']:>10}  {d['distinct_words']:>6}  "
              f"{d['total_repr']:>6}  {d['pre_peak_repr']:>6}  "
              f"{d['avg_k']:>5}  {d['avg_gain']:>8}  {d['avg_S_over_d']:>7}")

    # 4. Top symbolic words per center
    print(f"\n  4. TOP SYMBOLIC WORDS PER CENTER")
    for c_val in sorted(KNOWN_CENTERS.keys()):
        ca = center_aggs[c_val]
        if not ca.sample_words:
            continue
        print(f"\n  {ca.name} (center={c_val}):")
        for sw in ca.sample_words[:5]:
            print(f"    word={sw}")

    # 5. Pre-peak hit rate summary
    print(f"\n  5. PRE-PEAK HIT RATE SUMMARY")
    print(f"  Total representatives verified: {total_verified:,}")
    print(f"  Pre-peak center hits: {total_pre_peak:,}")
    if total_verified > 0:
        print(f"  Overall pre-peak rate: "
              f"{100 * total_pre_peak / total_verified:.2f}%")

    # Words with pre-peak hits
    words_with_prepeak = [w for w, wa in word_aggs.items()
                          if wa.repr_with_pre_peak > 0]
    print(f"  Distinct words with pre-peak hits: {len(words_with_prepeak)}")

    if words_with_prepeak:
        print(f"\n  Top words by pre-peak hit count:")
        top = sorted(words_with_prepeak,
                     key=lambda w: -word_aggs[w].repr_with_pre_peak)[:15]
        print(f"  {'word':>35}  {'k':>3}  {'S':>4}  {'gain':>7}  "
              f"{'S/d':>6}  {'repr':>5}  {'pre_pk':>6}  centers")
        print(f"  {'-' * 90}")
        for w in top:
            wa = word_aggs[w]
            w_str = str(list(w))
            if len(w_str) > 32:
                w_str = w_str[:30] + ".."
            c_str = ",".join(KNOWN_CENTERS.get(c, str(c))
                            for c in sorted(wa.centers_hit))
            print(f"  {w_str:>35}  {wa.k:>3}  {wa.S:>4}  {wa.gain:>7.2f}  "
                  f"{wa.S_over_d:>6.3f}  {wa.total_repr:>5}  "
                  f"{wa.repr_with_pre_peak:>6}  {c_str}")

    # 6. Known example verification
    print(f"\n  6. KNOWN EXAMPLE VERIFICATION")

    # n=27 → should map to center 121
    print(f"\n  n=27 check:")
    vr27 = verify_representative(27, known_set)
    print(f"    peak={vr27['peak']}, ratio={vr27['ratio']}")
    if 121 in vr27["pre_peak_centers"]:
        print(f"    center 121 hit BEFORE peak at step "
              f"{vr27['pre_peak_centers'][121]}  ← CONFIRMED")
    elif 121 in vr27["post_peak_centers"]:
        print(f"    center 121 hit AFTER peak (step "
              f"{vr27['post_peak_centers'][121]})")
    else:
        print(f"    center 121 NOT hit")

    # Zone 2 representative → should hit xstar
    z2_71 = 2358909599867980429759
    print(f"\n  Zone2-71b check (n={z2_71}):")
    vr_z2 = verify_representative(z2_71, known_set)
    xstar = 20152090995747160937051
    print(f"    peak={vr_z2['peak']}, ratio={vr_z2['ratio']}")
    if xstar in vr_z2["pre_peak_centers"]:
        print(f"    x* hit BEFORE peak at step "
              f"{vr_z2['pre_peak_centers'][xstar]}  ← CONFIRMED")
    elif xstar in vr_z2["post_peak_centers"]:
        print(f"    x* hit AFTER peak (step {vr_z2['post_peak_centers'][xstar]})")
    else:
        print(f"    x* NOT hit in accelerated trajectory")

    # Barina → should NOT hit xstar before peak
    barina = 1765856170146672440559
    print(f"\n  Barina check (n={barina}):")
    vr_bar = verify_representative(barina, known_set)
    print(f"    peak={vr_bar['peak']}, ratio={vr_bar['ratio']}")
    if xstar in vr_bar["pre_peak_centers"]:
        print(f"    x* hit BEFORE peak — UNEXPECTED")
    elif xstar in vr_bar["post_peak_centers"]:
        print(f"    x* hit AFTER peak (not pre-peak) — expected isolation")
    else:
        print(f"    x* NOT hit at all  ← CONFIRMED ISOLATED")

    # Family A: 2^80 - 1
    fa_80 = (1 << 80) - 1
    print(f"\n  Family A check (2^80-1):")
    vr_fa = verify_representative(fa_80, known_set)
    print(f"    peak={vr_fa['peak']}, ratio={vr_fa['ratio']}")
    any_pre = vr_fa["pre_peak_centers"]
    if any_pre:
        print(f"    Pre-peak centers: {any_pre}  — NOT baseline")
    else:
        print(f"    No pre-peak center hits  ← CONFIRMED BASELINE")

    # ── Save JSON ────────────────────────────────────────────────────────
    if output_json:
        out = {
            "meta": {
                "max_depth": max_depth,
                "a_max": a_max,
                "delta_cutoff": delta_cutoff,
                "max_states_per_layer": max_states,
                "max_repr_per_state": max_repr_per_state,
                "windows": [[w[0], w[1]] for w in windows],
                "total_verified": total_verified,
                "total_pre_peak": total_pre_peak,
                "time_seconds": round(t_total, 1),
            },
            "depth_stats": {
                str(k): v for k, v in depth_stats.items()
            },
            "centers": {
                name: center_aggs[val].to_dict()
                for val, name in KNOWN_CENTERS.items()
            },
            "top_words": [
                word_aggs[w].to_dict()
                for w in sorted(
                    word_aggs.keys(),
                    key=lambda w: -word_aggs[w].repr_with_pre_peak
                )[:100]
            ],
        }
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"\n  JSON saved: {output_json}")

    # ── Save CSV ─────────────────────────────────────────────────────────
    if output_csv:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "word", "k", "S", "gain", "S_over_d",
                "total_repr", "repr_with_center", "repr_with_pre_peak",
                "centers_hit", "sample_n",
            ])
            for w in sorted(word_aggs.keys(),
                            key=lambda w: -word_aggs[w].repr_with_pre_peak):
                wa = word_aggs[w]
                if wa.total_repr == 0:
                    continue
                writer.writerow([
                    str(list(wa.word)),
                    wa.k, wa.S, wa.gain, wa.S_over_d,
                    wa.total_repr, wa.repr_with_center,
                    wa.repr_with_pre_peak,
                    ";".join(str(c) for c in sorted(wa.centers_hit)),
                    ";".join(str(x) for x in wa.sample_n),
                ])
        print(f"  CSV saved: {output_csv}")

    print(f"\n{'=' * 78}")
    print(f"  Done.")
    print(f"{'=' * 78}")


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(
        description="Bridge to Reality — symbolic automaton → real Collatz"
    )
    p.add_argument('--max-depth', type=int, default=8)
    p.add_argument('--a-max', type=int, default=4)
    p.add_argument('--delta-cutoff', type=float, default=-10.0)
    p.add_argument('--max-states', type=int, default=50_000)
    p.add_argument('--max-repr', type=int, default=5,
                   help="Max representatives per state per window")
    p.add_argument('--windows', type=str, default="5,10 71,87 88,90",
                   help="Bit windows, e.g. '5,10 71,87'")
    p.add_argument('--output-json', type=str,
                   default='bridge_results.json')
    p.add_argument('--output-csv', type=str,
                   default='bridge_results.csv')

    args = p.parse_args()
    windows = parse_windows(args.windows)

    run_bridge(
        max_depth=args.max_depth,
        a_max=args.a_max,
        delta_cutoff=args.delta_cutoff,
        max_states=args.max_states,
        windows=windows,
        max_repr_per_state=args.max_repr,
        output_json=args.output_json,
        output_csv=args.output_csv,
    )


if __name__ == '__main__':
    main()
