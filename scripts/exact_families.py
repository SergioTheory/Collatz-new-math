"""
exact_families.py — режим целевого поиска по известным семействам.

Запуск:
  CrystalHunter_Console.exe --mode families --bits 72 140
  CrystalHunter_Console.exe --mode families --bits 88 88
  CrystalHunter_Console.exe --mode families --bits 72 200 --families-wide
"""
from __future__ import annotations
import sys, time, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DELTAS_A = [0, -1, -2, -3, -4, -5, -6, -7, -8, -16, -32, +1, +2]
DELTAS_B = [0, -1, -2, -3, -4, -5, -6, -7, -8, -16, -29, -32, +1, +2]
DELTAS_WIDE = list(range(-128, 3))
CAP_STEPS = 5_000_000


def _family_b_base(bits: int) -> int:
    if bits % 2 == 0:
        return int("10" * (bits // 2), 2)
    else:
        return int("1" + "01" * (bits // 2), 2)


def _collatz_peak(n: int) -> int:
    pb = n.bit_length()
    cur = n
    for _ in range(CAP_STEPS):
        if cur <= 1:
            break
        cur = (cur * 3 + 1) if (cur & 1) else (cur >> 1)
        cb = cur.bit_length()
        if cb > pb:
            pb = cb
    return pb


def run_families(
    min_bits:  int   = 72,
    max_bits:  int   = 140,
    min_ratio: float = 1.40,
    workers:   int   = 0,
    wide:      bool  = False,
    save_dir:  Optional[Path] = None,
):
    deltas_a = DELTAS_WIDE if wide else DELTAS_A
    deltas_b = DELTAS_WIDE if wide else DELTAS_B

    if save_dir is None:
        exe_dir = (Path(sys.executable).parent if getattr(sys, "frozen", False)
                   else Path(__file__).parent)
        save_dir = exe_dir / "crystal_records"
    save_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  EXACT FAMILIES MODE")
    print(f"  Diapason: {min_bits}-{max_bits} bit")
    print(f"  Semeystva: A (1111...) + B (1010...)")
    print(f"  Delty: {'shirokiye -128..+2' if wide else 'standartnye'}")
    print(f"  Min ratio: {min_ratio}")
    print(f"{'='*60}\n")

    t0 = time.time()
    done = 0
    saved = 0
    results_by_bits: dict[int, dict] = {}

    for bits in range(min_bits, max_bits + 1):
        base_a = (1 << bits) - 1
        base_b = _family_b_base(bits)

        for fam_name, base, deltas in [
            ("A:1111", base_a, deltas_a),
            ("B:1010", base_b, deltas_b),
        ]:
            for delta in deltas:
                n = base + delta
                if n <= 0 or not (n & 1):
                    continue
                if n.bit_length() != bits:
                    continue

                pk    = _collatz_peak(n)
                ratio = pk / bits
                done += 1

                if ratio < min_ratio:
                    continue

                prev = results_by_bits.get(bits)
                if prev is None or ratio > prev["ratio"]:
                    results_by_bits[bits] = {
                        "n":         str(n),
                        "n_hex":     hex(n),
                        "bits":      bits,
                        "peak_bits": pk,
                        "ratio":     ratio,
                        "family":    fam_name,
                        "delta":     delta,
                    }
                    elapsed = time.time() - t0
                    marker = "  *** VYSHE 140! ***" if pk > 140 else ""
                    print(f"  [{elapsed:6.2f}s] {bits:>3} bit  "
                          f"{fam_name}  d={delta:+d}  "
                          f"peak={pk}  ratio={ratio:.5f}{marker}")

                    rec = {**results_by_bits[bits],
                           "found_at": datetime.now(timezone.utc).isoformat()}
                    fname = save_dir / f"families_{bits}bit_{ratio:.5f}.json"
                    with open(fname, "w") as f:
                        json.dump(rec, f, indent=2)
                    saved += 1

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  ITOG  ({elapsed:.2f}s  |  {done} chisel  |  sokhraneno: {saved})")
    print(f"{'='*60}")
    print(f"\n  {'bits':>5}  {'family':>8}  {'delta':>6}  {'peak':>5}  {'ratio':>8}")
    print(f"  {'-'*42}")
    for bits in sorted(results_by_bits):
        r = results_by_bits[bits]
        flag = "  *** >140 ***" if r["peak_bits"] > 140 else ""
        print(f"  {bits:>5}  {r['family']:>8}  {r['delta']:>+6}  "
              f"{r['peak_bits']:>5}  {r['ratio']:>8.5f}{flag}")

    summary = {str(b): r for b, r in sorted(results_by_bits.items())}
    sf = save_dir / "families_summary.json"
    with open(sf, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Summary -> {sf}\n")
