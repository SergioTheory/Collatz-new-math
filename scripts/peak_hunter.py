"""
peak_hunter.py — Peak Hunter Mode for Collatz Crystal Hunter.
Uses multiprocessing.Pool with batch returns (no persistent Queue).
Worker function is at module level so it is picklable on Windows/PyInstaller.
"""
from __future__ import annotations

import json
import math
import multiprocessing
import random
import sys
import time
from pathlib import Path

# ── Math ──────────────────────────────────────────────────────────────────────

def compute_threshold(target_peak: int) -> int:
    t = (2 ** (target_peak - 1) - 1) // 3
    return t + 1 if t % 2 == 0 else t

def proximity_score(max_odd: int, log2_thr: float) -> float:
    if max_odd <= 1:
        return 0.0
    return math.log2(float(max_odd)) / log2_thr

def collatz_max_odd_and_peak(n: int, cap: int = 500_000):
    max_odd = n if n & 1 else 0
    peak    = n.bit_length()
    cur     = n
    for _ in range(cap):
        if cur <= 1: break
        cur  = cur * 3 + 1 if cur & 1 else cur >> 1
        cb   = cur.bit_length()
        if cb > peak: peak = cb
        if cur & 1 and cur > max_odd: max_odd = cur
    return max_odd, peak

def collatz_peak_fast(n: int, cap: int = 500) -> int:
    pb  = n.bit_length()
    cur = n
    for _ in range(cap):
        if cur <= 1: break
        cur = cur * 3 + 1 if cur & 1 else cur >> 1
        cb  = cur.bit_length()
        if cb > pb: pb = cb
    return pb

# ── File paths ────────────────────────────────────────────────────────────────

def _extra_seeds_path() -> Path:
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) \
           else Path(__file__).parent
    return base / "extra_seeds.json"

def load_seeds(min_peak: int = 120) -> list[int]:
    seeds: list[int] = []
    try:
        from records_data import PATH_RECORDS_BINARY
        for b in PATH_RECORDS_BINARY:
            n = int(b, 2)
            if n.bit_length() >= 60 and collatz_peak_fast(n, 5000) >= min_peak:
                seeds.append(n)
    except Exception:
        pass
    p = _extra_seeds_path()
    if p.exists():
        try:
            for s in json.loads(p.read_text("utf-8")).get("seeds", []):
                try: seeds.append(int(s["binary"], 2))
                except: pass
        except: pass
    return seeds

def load_extra_seeds_binaries() -> list[str]:
    p = _extra_seeds_path()
    if not p.exists():
        return []
    try:
        out = []
        for s in json.loads(p.read_text("utf-8")).get("seeds", []):
            b = s.get("binary", "")
            if b and set(b) <= {"0", "1"}:
                out.append(b)
        return out
    except:
        return []

# ── Worker (MODULE LEVEL — required for multiprocessing pickling on Windows) ──

def _hunt_worker_batch(args: tuple) -> list[dict]:
    """
    Runs one batch of BATCH_SIZE numbers and returns list of good results.
    Module-level function = picklable = works with multiprocessing on Windows.
    """
    (worker_id, min_bits, max_bits, log2_thr, screen_thr,
     min_prox, seeds_ints, batch_size) = args

    rng   = random.Random(worker_id * 7919 + int(time.time() * 1000) % 10_000_000)
    pool  = [(0.5, s) for s in seeds_ints
             if min_bits <= s.bit_length() <= max_bits]
    results = []
    tested  = 0

    while tested < batch_size:
        r = rng.random()

        if r < 0.35 or not pool:
            nb = rng.randint(min_bits, max_bits)
            n  = rng.getrandbits(nb - 1) | (1 << (nb - 1))
            if rng.random() < 0.55:
                n |= rng.getrandbits(nb - 1)
            n |= 1

        elif r < 0.72:
            _, base = rng.choice(pool[:30] if len(pool) >= 30 else pool)
            nb_base = base.bit_length()
            nb = rng.randint(max(min_bits, nb_base-1), min(max_bits, nb_base+1))
            n  = base
            for _ in range(rng.randint(1, 5)):
                n ^= (1 << rng.randint(0, nb - 2))
            n |= (1 << (nb - 1)); n |= 1

        else:
            _, base = rng.choice(pool[:10] if len(pool) >= 10 else pool)
            nb_base = base.bit_length()
            nb = rng.randint(max(min_bits, nb_base-2), min(max_bits, nb_base+2))
            n  = base
            for _ in range(rng.randint(3, 9)):
                n ^= (1 << rng.randint(0, nb - 2))
            n |= (1 << (nb - 1)); n |= 1

        if not (min_bits <= n.bit_length() <= max_bits):
            continue
        tested += 1

        if collatz_peak_fast(n, 500) < screen_thr:
            continue

        max_odd, peak = collatz_max_odd_and_peak(n, 500_000)
        prox = proximity_score(max_odd, log2_thr)

        if prox >= min_prox:
            results.append({
                "binary":    bin(n)[2:],
                "bits":      n.bit_length(),
                "peak_bits": peak,
                "proximity": prox,
                "found_at":  time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            pool.append((prox, n))
            pool.sort(key=lambda x: -x[0])
            pool = pool[:100]

    return results

# ── Save ──────────────────────────────────────────────────────────────────────

def _save(candidates: list[dict], target_peak: int, top_n: int, path: Path) -> None:
    seen, deduped = set(), []
    for c in sorted(candidates, key=lambda x: -x["proximity"]):
        key = c["binary"][:40]
        if key not in seen:
            seen.add(key); deduped.append(c)
    deduped = deduped[:top_n]
    try:
        path.write_text(json.dumps({
            "target_peak": target_peak,
            "updated_at":  time.strftime("%Y-%m-%d %H:%M:%S"),
            "note":        "Auto-generated by --mode hunt.",
            "seeds":       [{"binary": c["binary"], "bits": c["bits"],
                             "peak_bits": c["peak_bits"],
                             "proximity": round(c["proximity"], 7),
                             "found_at":  c.get("found_at", "")}
                            for c in deduped],
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"  Warning: save failed: {e}")

# ── Main entry ────────────────────────────────────────────────────────────────

def run_hunt(
    min_bits:    int   = 72,
    max_bits:    int   = 80,
    target_peak: int   = 141,
    min_prox:    float = 0.990,
    top_n:       int   = 50,
    n_workers:   int   = 0,
) -> None:

    if n_workers <= 0:
        n_workers = max(1, multiprocessing.cpu_count() - 1)

    threshold  = compute_threshold(target_peak)
    log2_thr   = math.log2(float(threshold))
    # screen_thr: быстрый фильтр — отсекает числа без шансов
    # Для 100-120 бит входа пики до 500 шагов достигают ~120-133 бит
    # Поэтому screen_thr = max_bits + 15 (немного выше самого входа)
    # Не привязываем к target_peak — он может быть далёким идеалом
    screen_thr = max(min_bits + 10, min(max_bits + 20, target_peak - 5))
    save_path  = _extra_seeds_path()

    # Batch size: каждый воркер обрабатывает BATCH_SIZE чисел за один вызов
    # и возвращает результаты — никаких постоянных очередей
    BATCH = 5_000

    print(f"\n{'='*62}")
    print(f"  Collatz Crystal Hunter -- Peak Hunter Mode")
    print(f"{'='*62}")
    print(f"  Target peak:  {target_peak}")
    print(f"  Input range:  {min_bits}-{max_bits} bits")
    print(f"  Workers:      {n_workers}")
    print(f"  Threshold:    {threshold.bit_length()} bits (log2={log2_thr:.3f})")
    print(f"  Save when:    proximity >= {min_prox:.3f}")
    print(f"  Keep top:     {top_n}")
    print(f"  Output file:  {save_path}")
    print(f"{'='*62}")
    print(f"  proximity 0.990-0.999 = close to target")
    print(f"  proximity >= 1.000    = TARGET REACHED (peak={target_peak}!)")
    print(f"  Ctrl+C to stop and save")
    print()

    seeds = load_seeds(min_peak=max(100, target_peak - 30))
    print(f"  Seeds loaded: {len(seeds)}")

    all_candidates: list[dict] = []
    if save_path.exists():
        try:
            prev = json.loads(save_path.read_text("utf-8")).get("seeds", [])
            if prev:
                print(f"  Previous candidates: {len(prev)}")
                all_candidates = list(prev)
                for s in prev:
                    try: seeds.append(int(s["binary"], 2))
                    except: pass
        except: pass

    best_prox    = max((c.get("proximity", 0) for c in all_candidates), default=0.0)
    total_tested = 0
    found_target = 0
    start_time   = time.time()
    last_save    = time.time()
    last_status  = time.time()
    batch_num    = 0

    print(f"\n  Starting pool with {n_workers} workers, batch={BATCH}...\n")

    # Уникальный ID для каждого батча чтобы rng не повторялся
    def make_args(wid: int) -> tuple:
        return (wid + batch_num * n_workers,
                min_bits, max_bits, log2_thr, screen_thr,
                min_prox, seeds[:50], BATCH)

    try:
        with multiprocessing.Pool(processes=n_workers) as pool:
            # Запускаем первый раунд батчей
            # Запускаем n_workers*2 батчей — очередь всегда полная
            pending = [pool.apply_async(_hunt_worker_batch, (make_args(i),))
                       for i in range(n_workers * 2)]

            while True:
                # Собираем завершённые батчи
                next_pending = []
                for fut in pending:
                    if fut.ready():
                        try:
                            results = fut.get(timeout=1)
                        except Exception as e:
                            results = []
                        total_tested += BATCH

                        for r in results:
                            prox = r["proximity"]
                            all_candidates.append(r)

                            if prox > best_prox:
                                best_prox = prox
                                bar  = int(prox * 40)
                                fill = chr(9608)*bar + chr(9617)*(40-bar)
                                nb, pk = r["bits"], r["peak_bits"]
                                print(f"  NEW BEST  prox={prox:.6f}  bits={nb}"
                                      f"  peak={pk}  ratio={pk/nb:.4f}")
                                print(f"  [{fill}] -> 1.000000")
                                print(f"  n={r['binary'][:40]}...")
                                print()
                                # Добавляем в seeds для следующих батчей
                                try:
                                    seeds.append(int(r["binary"], 2))
                                    seeds = seeds[-100:]  # не раздувать
                                except: pass

                            if prox >= 1.0 or r["peak_bits"] >= target_peak:
                                found_target += 1
                                print(f"  {'!'*50}")
                                print(f"  TARGET REACHED: peak={r['peak_bits']}!")
                                print(f"  {'!'*50}")

                        # Дедупликация топа
                        all_candidates.sort(key=lambda x: -x["proximity"])
                        seen_keys, deduped = set(), []
                        for c in all_candidates:
                            key = c["binary"][:40]
                            if key not in seen_keys:
                                seen_keys.add(key); deduped.append(c)
                        all_candidates[:] = deduped[:top_n * 2]

                        # Сразу запускаем новый батч вместо завершённого
                        batch_num += 1
                        next_pending.append(
                            pool.apply_async(_hunt_worker_batch,
                                             (make_args(batch_num % n_workers),))
                        )
                    else:
                        next_pending.append(fut)

                pending = next_pending

                # Статус каждые 10 секунд
                now = time.time()
                if now - last_status >= 10.0:
                    elapsed = now - start_time
                    rate    = total_tested / max(elapsed, 1)
                    print(f"  [{elapsed:6.0f}s]  tested={total_tested/1e6:.1f}M"
                          f"  rate={rate/1000:.0f}K/s"
                          f"  best_prox={best_prox:.6f}"
                          f"  target_found={found_target}"
                          f"  candidates={min(len(all_candidates), top_n)}")
                    last_status = now

                # Сохранение каждые 60 секунд
                if now - last_save >= 60.0 and all_candidates:
                    _save(all_candidates, target_peak, top_n, save_path)
                    last_save = now

                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n  Stopping...")

    # Финал
    if all_candidates:
        _save(all_candidates, target_peak, top_n, save_path)

    elapsed = time.time() - start_time
    print(f"\n{'='*62}")
    print(f"  Hunt complete  ({elapsed:.0f}s)")
    print(f"{'='*62}")
    print(f"  Best proximity: {best_prox:.6f}  (target: 1.000000)")
    print(f"  Gap:            {1.0-best_prox:.6f}  ({(1.0-best_prox)*100:.4f}%)")
    print(f"  Targets found:  {found_target}")
    print(f"  Candidates:     {min(len(all_candidates), top_n)}")
    print(f"  Saved to:       {save_path}")
    print()
    print(f"  Top-5:")
    print(f"  {'bits':>5}  {'peak':>5}  {'ratio':>7}  {'proximity':>10}  first 28 bits")
    print(f"  {'-'*58}")
    for c in all_candidates[:5]:
        nb, pk, prox = c["bits"], c["peak_bits"], c["proximity"]
        print(f"  {nb:>5}  {pk:>5}  {pk/nb:>7.4f}  {prox:>10.6f}  {c['binary'][:28]}...")
    print()
    print(f"  Will auto-load on next normal-mode start.")
    print(f"{'='*62}")
