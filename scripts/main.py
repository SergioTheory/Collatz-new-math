#!/usr/bin/env python3
"""
main.py — Collatz Crystal Hunter v5.3a (distributed-learning edition)

Architecture:
  • Each worker process has its OWN HybridCrystalGenerator (unique seed)
  • Worker loop:
      1. generate_batch  →  fast sim (200 steps)  →  feedback_fast (updates prefix/Markov locally)
      2. if passes filter  →  full sim  →  add to results
      3. drain personal feedback queue  →  generator.feedback() for each saved record
  • Main process: collect results, save, push feedback into per-worker queues

Result: 100% CPU (all cores generate+fast-sim continuously),
        only ~2-3% numbers reach full sim,
        each worker's Markov chain learns from its own and main-pushed good results.
"""
from __future__ import annotations
import argparse, multiprocessing, os, pickle, sys, time, threading
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone, timedelta
from pathlib import Path
import queue as _queue
import json

sys.path.insert(0, str(Path(__file__).parent))
import yaml
from stats_collector import StatsCollector


# ── Windows VT (ANSI escape) support ─────────────────────────────────────────
def _enable_vt_mode() -> bool:
    """Enable ANSI escape code processing on Windows 10+. Returns True if OK."""
    if sys.platform != 'win32':
        return True
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        h = kernel32.GetStdHandle(-11)           # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(h, ctypes.byref(mode))
        kernel32.SetConsoleMode(h, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return True
    except Exception:
        return False

# ── Startup log ──────────────────────────────────────────────────────────────
def _open_log():
    try:
        exe_dir = (Path(sys.executable).parent if getattr(sys, "frozen", False)
                   else Path(__file__).parent)
        fh = open(exe_dir / "crystal_log.txt", "a", encoding="utf-8")
        return fh, str(exe_dir / "crystal_log.txt")
    except Exception:
        return None, None

_LOG_FH, LOG_PATH = _open_log()

def log(msg: str):
    ts   = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    if _LOG_FH:
        try:
            _LOG_FH.write(line + "\n"); _LOG_FH.flush()
        except Exception:
            pass

def log_only(msg: str):
    """Write to log file ONLY — no console output. Used for high-frequency events."""
    ts   = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    if _LOG_FH:
        try:
            _LOG_FH.write(line + "\n"); _LOG_FH.flush()
        except Exception:
            pass

def log_exception(where: str, exc: Exception = None):
    import traceback
    log(f"ERROR in {where}: {exc or ''}")
    if _LOG_FH:
        try:
            _LOG_FH.write(traceback.format_exc() + "\n"); _LOG_FH.flush()
        except Exception:
            pass


# ============================================================
# WORKER STATE — per-process globals (each spawned process has
#                its own copy; no sharing between processes)
# ============================================================
_w_gen:   object = None   # HybridCrystalGenerator for this process
_w_id:    int    = -1     # index of this worker (0 … max_workers-1)
_w_queue: object = None   # multiprocessing.Queue for feedback from main


def _worker_init(worker_id: int, feedback_queue, cfg: dict) -> None:
    """Called once per worker process at startup by ProcessPoolExecutor initializer."""
    global _w_gen, _w_id, _w_queue
    import sys, os
    sys.path.insert(0, str(Path(__file__).parent))
    from generators.hybrid import HybridCrystalGenerator

    _w_id    = worker_id
    _w_queue = feedback_queue

    # Unique seed: time × pid × worker_id prevents correlated generators
    seed = (int(time.time() * 1000) ^ os.getpid() ^ (worker_id * 0xDEAD)) & 0xFFFFFFFF
    _w_gen   = HybridCrystalGenerator(cfg, seed=seed)
    _w_gen.min_bits = cfg["search"]["min_bits"]
    _w_gen.max_bits = cfg["search"]["max_bits"]


# ============================================================
# WORKER TASK
# ============================================================

def _worker_task(task_args: tuple):
    """
    Executed in worker process (state already in _w_gen / _w_queue / _w_id).

    Steps per batch:
      for each number n:
        1. fast sim (200 steps)   → always
        2. generator.feedback_fast([(n, fast_k)])  → updates prefix/Markov locally
        3. if passes filter: full sim → collect result
      drain personal feedback queue → generator.feedback() for each good record

    Returns (results, worker_id, n_generated)
    """
    global _w_gen, _w_id, _w_queue

    (batch_size, fast_steps, fast_ratio_thr, fast_k_thr,
     cap_steps, min_bits, max_bits) = task_args

    # Update bit range from settings
    _w_gen.min_bits = min_bits
    _w_gen.max_bits = max_bits

    # ── 1. Generate ─────────────────────────────────────────────────────────
    candidates = _w_gen.generate_batch(batch_size)

    # ── 2. Fast-sim + feedback_fast + optional full sim ──────────────────────
    full_results  = []
    fast_fb_batch = []   # ALL stage-1 survivors → generator.feedback_fast()
    n_stage3      = 0    # stage-2 FILTER survivors → what we call "fast_pass"

    for n in candidates:
        if n <= 1:
            continue
        ob = n.bit_length()
        if ob == 0:
            continue

        # Stage 1: pre-filter (50 steps, ratio≥1.03 — eliminates ~70%)
        pb = ob; cur = n; s = 0
        while cur > 1 and s < 50:
            cur = cur * 3 + 1 if cur & 1 else cur >> 1
            s += 1
            cb = cur.bit_length()
            if cb > pb: pb = cb
        if pb / ob < 1.03 and cur > 1:
            continue

        # Stage 2: fast simulation (up to fast_steps)
        while cur > 1 and s < fast_steps:
            cur = cur * 3 + 1 if cur & 1 else cur >> 1
            s += 1
            cb = cur.bit_length()
            if cb > pb: pb = cb

        ratio_fast = pb / ob
        k_fast     = s / ob if ob else 0.0

        # ALL stage-1 survivors go to generator feedback (smart restarts)
        fast_fb_batch.append((n, k_fast))

        # Stage-2 FILTER: only promising candidates reach full sim
        # fast_ratio_thr / fast_k_thr come from task args → updated each submit
        if not (cur <= 1 or ratio_fast >= fast_ratio_thr or k_fast >= fast_k_thr):
            continue
        n_stage3 += 1   # ← this is what "fast_pass" actually tracks

        # Stage 3: full simulation (capped at cap_steps)
        while cur > 1 and s < cap_steps:
            cur = cur * 3 + 1 if cur & 1 else cur >> 1
            s += 1
            cb = cur.bit_length()
            if cb > pb: pb = cb

        ratio = pb / ob
        k     = s / ob if ob else 0.0
        full_results.append({
            "n":         n,
            "n_bits":    ob,
            "peak_bits": pb,
            "ratio":     ratio,
            "steps":     s,
            "converged": cur <= 1,
            "k":         k,
            "worker_id": _w_id,
        })

    # ── 3. Update local generator with fast-sim statistics ───────────────────
    #   feedback_fast updates per-prefix rolling average → smart restarts
    if fast_fb_batch:
        try:
            _w_gen.feedback_fast(fast_fb_batch)
        except Exception:
            pass

    # ── 4. Drain personal feedback queue from main process ───────────────────
    #   Each saved record → generator.feedback() → updates prefix weights + Markov
    if _w_queue is not None:
        try:
            while True:
                msg = _w_queue.get_nowait()   # (n, k, bits_str, ratio)
                n_fb, k_fb, bs_fb, ratio_fb = msg
                _w_gen.feedback(n_fb, k_fb, bs_fb, ratio=ratio_fb)
        except Exception:
            pass   # queue.Empty or any other — silently continue

    return full_results, _w_id, len(candidates), n_stage3, []


# ============================================================
# Simple storage
# ============================================================

class SimpleStorage:
    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._seen: set[str] = set()
        self.alltime_best_ratio: float = 0.0
        self.alltime_best_steps: int   = 0
        self.best_per_bits: dict[int, float] = {}
        self._load_existing()

    def _load_existing(self) -> None:
        """Загружает уже найденные числа для дедупликации + исторический best."""
        for f in self.out_dir.glob("*.json"):
            try:
                with open(f, encoding="utf-8") as fp:
                    data = json.load(fp)
                if "n" in data:
                    self._seen.add(str(data["n"]))
                r = float(data.get("ratio", 0) or 0)
                s = int(data.get("steps", 0) or 0)
                b = int(data.get("bits", 0) or 0)
                if r > self.alltime_best_ratio:
                    self.alltime_best_ratio = r
                if s > self.alltime_best_steps:
                    self.alltime_best_steps = s
                if b > 0 and r > 0:
                    if r > self.best_per_bits.get(b, 0.0):
                        self.best_per_bits[b] = r
            except Exception:
                pass

    def is_new(self, n: int) -> bool:
        return str(n) not in self._seen

    def add(self, r: dict):
        ns = str(r["n"])
        if ns in self._seen:
            return
        self._seen.add(ns)
        fname = (f"rec_{int(time.time())}_{r['n_bits']}b"
                 f"_r{r['ratio']:.5f}_s{r['steps']}.json")
        with open(self.out_dir / fname, "w", encoding="utf-8") as f:
            json.dump({
                "n":         ns,
                "n_hex":     hex(r["n"]),
                "bits":      r["n_bits"],
                "peak_bits": r["peak_bits"],
                "ratio":     round(r["ratio"], 8),
                "steps":     r["steps"],
                "k":         round(r["k"], 4),
                "found_at":  datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)


# ============================================================
# CrystalHunter
# ============================================================

class CrystalHunter:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        par  = cfg.get("parallel",  {})
        srch = cfg.get("search",    {})
        sim  = cfg.get("simulator", {})
        stor = cfg.get("storage",   {})

        _cw = par.get("max_workers", 0)
        self.max_workers: int = (_cw if _cw > 0
                                 else max(1, (os.cpu_count() or 4) - 1))
        self.batch_size:  int = par.get("batch_size", 2048)

        self.min_bits: int = srch.get("min_bits", 80)
        self.max_bits: int = srch.get("max_bits", 120)

        self._fast_steps: int   = sim.get("fast_sim_steps", 200)
        self._fast_ratio: float = sim.get("full_sim_threshold_ratio", 1.065)
        self._fast_k:     float = sim.get("full_sim_threshold_k", 1.75)
        self._cap_steps:  int   = min(sim.get("max_steps", 500_000), 50_000)

        # Улучшение 2: адаптивные пороги быстрого фильтра
        self._adapt_on:       bool  = sim.get("adaptive_thresholds", False)
        self._adapt_min:      float = sim.get("target_fast_pass_min", 2.0)
        self._adapt_max:      float = sim.get("target_fast_pass_max", 5.0)
        self._adapt_interval: int   = sim.get("threshold_adapt_interval", 10_000)
        self._adapt_step:     float = sim.get("threshold_adapt_step", 0.005)
        # Max clamps so thresholds never go infinite
        self._adapt_ratio_max: float = sim.get("adaptive_ratio_max", 3.0)
        self._adapt_k_max:     float = sim.get("adaptive_k_max", 10.0)
        # Interval counters (sliding window — reset each interval)
        self._iw_generated:   int   = 0
        self._iw_fast_pass:   int   = 0
        self._adapt_min:      float = sim.get("target_fast_pass_min", 2.0)   # %
        self._adapt_max:      float = sim.get("target_fast_pass_max", 5.0)   # %
        self._adapt_interval: int   = sim.get("threshold_adapt_interval", 10_000)
        self._adapt_step:     float = sim.get("threshold_adapt_step", 0.001)
        self._adapt_last_gen: int   = 0   # total_generated at last adapt check

        self._save_ratio: float = srch.get("target_ratio", 1.10)
        self._save_steps: int   = srch.get("target_steps", 800)

        out_dir = Path(stor.get("output_dir", "./crystal_records"))
        self.storage    = SimpleStorage(out_dir)
        self.snap_file  = Path(stor.get("snapshot_file", "./crystal_snapshot.pkl"))
        self.snap_every = stor.get("snapshot_interval", 200_000)
        # Pause-file: create "pause.flag" next to EXE to pause; delete to resume
        _exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) \
                   else Path.cwd()
        self._pause_file    = _exe_dir / "pause.flag"
        self._paused        = False
        self._pause_time: float = 0.0

        # Statistics collector (optional CSV writer)
        self._stats_col = StatsCollector(cfg)

        # ── Адаптивные параметры (из секции generator) ────────────────────────
        gen_cfg = cfg.get("generator", {})

        # Планировщик порядков Маркова
        self._markov_orders: list[int]   = gen_cfg.get("markov_orders", [])
        self._markov_switch_interval:int = gen_cfg.get("markov_order_switch_interval", 300)
        self._markov_order_idx:      int = 0
        self._last_order_switch:   float = time.time()
        _base_order = gen_cfg.get("markov_order", 5)
        self._current_markov_order: int  = (
            self._markov_orders[0] if self._markov_orders else _base_order
        )

        # Детектор стагнации
        self._stagnation_enabled: bool  = gen_cfg.get("stagnation_detection_enabled", False)
        self._stagnation_ratio_thr: int = gen_cfg.get("stagnation_ratio_threshold", 200)
        self._stagnation_timeout: float = gen_cfg.get("stagnation_timeout", 600.0)
        self._forced_anomaly_rate: float= gen_cfg.get("forced_anomaly_rate", 1.0)
        self._forced_mode_duration:float= gen_cfg.get("forced_mode_duration", 60.0)
        self._last_best_update_time:float = time.time()
        self._stagnation_active:   bool  = False
        self._stagnation_end_time: float = 0.0
        self._anomaly_override:    Optional[float] = None   # None = use config value

        # Приоритетное обучение
        self._elite_weight:       float = gen_cfg.get("elite_weight",        10.0)
        self._local_max_weight:   float = gen_cfg.get("local_max_weight",     3.0)
        self._novelty_hamming_thr:float = gen_cfg.get("novelty_hamming_threshold", 0.15)
        self._novelty_bonus:      float = gen_cfg.get("novelty_bonus",        5.0)
        self._top_saved:          list  = []   # бинарные строки топ-10 сохранённых
        self._top_saved_max:      int   = 10

        # ── Plateau Hunter ────────────────────────────────────────────────────
        ph = cfg.get("plateau_hunter", {})
        self._ph_enabled:      bool  = ph.get("enabled",             False)
        self._ph_min_height:   float = ph.get("min_plateau_height",  1.4)
        self._ph_min_duration: int   = ph.get("min_plateau_duration", 50)
        self._ph_weight:       float = ph.get("plateau_weight",      10.0)
        self._ph_save:         bool  = ph.get("save_records",        False)
        self._ph_max_per_batch:int   = ph.get("max_per_batch",       3)
        self._ph_dynamic_factor:float= ph.get("dynamic_factor",      0.95)
        self._last_plateau_print: float = 0.0   # rate-limit: макс 1 строка/сек
        # Глобальный rate-limit: не более N плато-feedback в секунду на всю программу
        self._ph_rate_limit:    int   = ph.get("feedback_rate_limit", 20)
        self._ph_feedback_count:int   = 0        # счётчик за текущую секунду
        self._ph_rate_window:   float = 0.0      # начало текущей секунды
        # Дедупликация: не отправлять одинаковый peak_bits повторно за N секунд
        self._ph_dedup_window:  float = ph.get("dedup_window_sec",   30.0)
        self._ph_seen: dict     = {}             # peak_bits → last_send_time
        # Минимальный ratio плато относительно текущего best (не учиться на хуже best*X)
        self._ph_min_rel:       float = ph.get("min_relative_to_best", 0.85)

        self._stats = {
            "total_generated":  0, "total_checked": 0,
            "session_generated": 0,  # resets each run — for accurate speed display
            "session_fast_pass": 0,   # session-only fast_pass counter
            "total_found":      0, "total_saved":   0,
            "total_fast_pass":  0,
            "total_plateau":    0,   # плато-кандидаты для обучения Маркова
            "start_time":   time.time(),
            "best_ratio":   0.0, "best_steps": 0, "best_bits": 0,
            "recent_k":     [],
            "active_workers": 0,
        }

        # Seed best_ratio / save thresholds from already-saved JSON records
        # so BEST= and save_thr are correct even without --resume
        at_r = self.storage.alltime_best_ratio
        at_s = self.storage.alltime_best_steps
        if at_r > 0:
            self._stats["best_ratio"] = at_r
            tiers   = srch.get("save_tiers", [])
            min_abs = srch.get("min_absolute", srch.get("target_ratio", 1.10))
            if tiers:
                factor = tiers[-1].get("factor", 0.97)
                for tier in tiers:
                    if at_r <= tier["max_best"]:
                        factor = tier["factor"]
                        break
                new_thr = round(max(min_abs, at_r * factor), 4)
            else:
                new_thr = round(at_r - 0.005, 4)
            if new_thr > self._save_ratio:
                self._save_ratio = new_thr
        if at_s > 0:
            self._stats["best_steps"] = at_s
            new_st = at_s - 5
            if new_st > self._save_steps:
                self._save_steps = new_st
        self._running = True

        # Per-bit best ratio dashboard
        self._best_per_bits: dict[int, float] = {}
        self._dashboard_ready: bool = False
        self._dashboard_vt_ok:  bool = False
        self._dash_height:      int  = 0

        # Preload per-bit bests from existing saved records
        for b, r in self.storage.best_per_bits.items():
            self._best_per_bits[b] = r

        import signal
        signal.signal(signal.SIGINT,  self._sig)
        signal.signal(signal.SIGTERM, self._sig)

        log(f"Init OK. workers={self.max_workers} batch={self.batch_size}"
            f" bits={self.min_bits}-{self.max_bits}"
            f" cap_steps={self._cap_steps}")
        if at_r > 0:
            log(f"Alltime best (from saved records): ratio={at_r:.5f}"
                f"  steps={at_s}  save_thr set to {self._save_ratio:.4f}")
        if self._stats_col.enabled:
            _max = self._stats_col.max_records
            _max_str = f"  max_records={_max:,}" if _max else "  max_records=unlimited"
            log(f"Statistics: ON  dir={self._stats_col.output_dir}"
                f"  flush={self._stats_col.flush_interval:,}"
                f"  include_n={self._stats_col.include_n}"
                f"{_max_str}")
        else:
            log("Statistics: OFF (set statistics.enabled: true in config.yaml)")
        if self._adapt_on:
            log(f"Adaptive thresholds: ON  target={self._adapt_min:.1f}%-{self._adapt_max:.1f}%"
                f"  interval={self._adapt_interval:,}  base_step={self._adapt_step}"
                f"  initial ratio_thr={self._fast_ratio:.4f}  k_thr={self._fast_k:.4f}")
        else:
            log(f"Adaptive thresholds: OFF (set adaptive_thresholds: true in config.yaml to enable)")

    def _sig(self, *_):
        log("Signal — stopping...")
        self._running = False

    # ── Result handler ────────────────────────────────────────────────────────

    def _handle_results(self,
                        full_results:    list,
                        worker_id:       int,
                        worker_queues:   list,
                        plateau_cands:   list | None = None):
        for r in full_results:
            # Record every stage-3 result for statistical analysis
            if not self._stats_col.is_full:
                was_full_before = False
                self._stats_col.record(r)
                if self._stats_col.is_full:
                    log(f"Statistics: limit reached "
                        f"({self._stats_col.max_records:,} records) — "
                        f"collection stopped, search continues")

            n     = r["n"];   ratio = r["ratio"]
            steps = r["steps"]; k  = r["k"]; nb = r["n_bits"]

            self._stats["total_checked"] += 1
            self._stats["recent_k"].append(k)
            if len(self._stats["recent_k"]) > 500:
                self._stats["recent_k"].pop(0)

            if not (ratio >= self._save_ratio or steps >= self._save_steps):
                continue

            self._stats["total_found"] += 1

            if not self.storage.is_new(n):
                continue

            self.storage.add(r)
            self._stats["total_saved"] += 1

            # Обновляем дашборд лучших ratio по битности
            self._update_best_per_bits(nb, ratio)

            # Бинарная строка для обучения и вычисления новизны
            bs = bin(n)[2:]

            is_new_best = False

            # Auto-raise ratio threshold only on genuine new record
            if ratio > self._stats["best_ratio"]:
                self._stats["best_ratio"] = ratio
                self._stats["best_bits"]  = nb
                is_new_best = True
                self._last_best_update_time = time.time()   # сброс детектора стагнации
                if self._stagnation_active:                 # выходим из форсированного режима
                    self._stagnation_active = False
                    self._anomaly_override  = None
                    log("Stagnation mode OFF — new best found")
                # Tiered save-threshold policy
                tiers = self.cfg.get("search", {}).get("save_tiers", [])
                min_abs = self.cfg.get("search", {}).get("min_absolute", self.cfg.get("search", {}).get("target_ratio", 1.10))
                if tiers:
                    factor = tiers[-1].get("factor", 0.97)   # fallback: last tier
                    for tier in tiers:
                        if ratio <= tier["max_best"]:
                            factor = tier["factor"]
                            break
                    new_thr = round(max(min_abs, ratio * factor), 4)
                else:
                    new_thr = round(ratio - 0.005, 4)        # legacy behaviour
                if new_thr > self._save_ratio:
                    old = self._save_ratio
                    self._save_ratio = new_thr
                    log(f"Auto-raise ratio_thr: {old:.4f} → {self._save_ratio:.4f}"
                        f" (best {ratio:.5f}  factor={factor if tiers else 'legacy'})")

            if steps > self._stats["best_steps"]:
                self._stats["best_steps"] = steps
                is_new_best = True
                new_st = steps - 5
                if new_st > self._save_steps:
                    old = self._save_steps
                    self._save_steps = new_st
                    log(f"Auto-raise steps_thr: {old} → {self._save_steps}"
                        f" (best {steps})")

            if is_new_best:
                log(f"NEW BEST: ratio={self._stats['best_ratio']:.5f}"
                    f"  steps={self._stats['best_steps']}  bits={nb}"
                    f"  [fast thr={self._fast_ratio:.3f}/{self._fast_k:.2f}]")

            # Обновляем top_saved (топ по ratio, не более _top_saved_max строк)
            self._top_saved.append(bs)
            if len(self._top_saved) > self._top_saved_max:
                self._top_saved.pop(0)

            # Вычисляем вес для обучения Маркова (с учётом новизны и типа)
            mw = self._compute_markov_weight(ratio, k, bs)

            # Push feedback to the worker that found this number
            # Also broadcast to a few other workers so all learn from good finds
            feedback_msg = (n, k, bs, ratio, mw)
            recipients = set()
            recipients.add(worker_id)
            # Broadcast to 2 additional random workers
            import random as _rnd
            others = [i for i in range(len(worker_queues)) if i != worker_id]
            for wid in _rnd.sample(others, min(2, len(others))):
                recipients.add(wid)

            for wid in recipients:
                try:
                    worker_queues[wid].put_nowait(feedback_msg)
                except Exception:
                    pass  # queue full or process died — skip

        # ── Plateau Hunter ────────────────────────────────────────────────────
        # Принцип: учить Марков ТОЛЬКО на числах с пиком ВЫШЕ текущего best.
        # Плато ниже best = шум → Марков забывает паттерны для 1.9+.
        # Rate-limit: максимум 1 плато за вызов _handle_results (≈36/сек max).
        if self._ph_enabled and plateau_cands:
            best_now = self._stats["best_ratio"]
            # Порог: только плато лучше best * 0.98 (почти рекордный уровень).
            # При best=1.61 и factor=0.95 → dynamic_min=1.530.
            dynamic_min = max(self._ph_min_height, best_now * self._ph_dynamic_factor)

            # Сортируем по ratio убыванию, берём только лучшее из батча
            top_pc = sorted(plateau_cands, key=lambda x: x["peak_bits"], reverse=True)
            for pc in top_pc[:1]:   # строго 1 на вызов
                nb_pc  = pc["n_bits"]
                pb_pc  = pc["peak_bits"]
                rat_pc = pb_pc / nb_pc if nb_pc else 0.0
                if rat_pc < dynamic_min:
                    break   # лучшее не прошло → остальные тем более

                self._stats["total_plateau"] += 1
                n_pc  = pc["n"]
                st_pc = pc["peak_step"]
                bs_pc = bin(n_pc)[2:]

                # Feedback только воркеру-первооткрывателю (не всем 18!)
                fb_msg = (n_pc, st_pc / nb_pc if nb_pc else 0.0,
                          bs_pc, rat_pc, self._ph_weight)
                try:
                    worker_queues[worker_id].put_nowait(fb_msg)
                except Exception:
                    pass

                if self._ph_save and self.storage.is_new(n_pc):
                    self.storage.add({
                        "n": n_pc, "n_bits": nb_pc, "peak_bits": pb_pc,
                        "ratio": rat_pc, "steps": st_pc,
                        "k": st_pc / nb_pc if nb_pc else 0.0,
                        "converged": False, "source": "plateau",
                    })

                now_p = time.time()
                if now_p - self._last_plateau_print >= 5.0:
                    log(f"Plateau: bits={nb_pc}  peak={pb_pc}  ratio={rat_pc:.5f}"
                        f"  thr={dynamic_min:.4f}  total={self._stats['total_plateau']}")
                    self._last_plateau_print = now_p

    # ── Status display ────────────────────────────────────────────────────────

    def _adapt_thresholds(self):
        """
        Калибрует пороги fast-фильтра на основе СКОЛЬЗЯЩЕГО ОКНА (не накопленной
        статистики). Счётчики сбрасываются после каждого интервала, поэтому
        fast_pass отражает ТЕКУЩУЮ пропускную способность, а не историю.

        Проблема накопленной статистики:
          После 1M чисел с fast_pass=16% накоплено 160K прошедших.
          Поднимаем пороги → следующие 100K дают 0% → общий fast_pass = 160/1100 = 14.5%
          Требуются МИЛЛИОНЫ чисел чтобы "вымыть" старую статистику.
          → Пороги улетают в бесконечность раньше.

        Решение: сбрасывать _iw_generated/_iw_fast_pass после каждого интервала.
        """
        if not self._adapt_on:
            return
        if self._iw_generated < self._adapt_interval:
            return

        fp = self._iw_fast_pass / self._iw_generated * 100

        # Сброс счётчиков скользящего окна
        self._iw_generated = 0
        self._iw_fast_pass = 0

        if fp > self._adapt_max:
            # Слишком много кандидатов → повышаем пороги
            deviation = fp / max(0.01, self._adapt_max)
            step = round(self._adapt_step * min(deviation, 10.0), 5)
            old_r, old_k = self._fast_ratio, self._fast_k
            self._fast_ratio = min(self._adapt_ratio_max,
                                   round(self._fast_ratio + step, 4))
            self._fast_k     = min(self._adapt_k_max,
                                   round(self._fast_k     + step, 4))
            # Log ONLY when values actually changed (suppresses cap-hit spam)
            pass  # thresholds updated silently

        elif fp < self._adapt_min:
            # Слишком мало кандидатов → снижаем пороги
            deviation = max(1.0, self._adapt_min / max(0.01, fp))
            step = round(self._adapt_step * min(deviation, 10.0), 5)
            old_r, old_k = self._fast_ratio, self._fast_k
            self._fast_ratio = max(1.01, round(self._fast_ratio - step, 4))
            self._fast_k     = max(0.50, round(self._fast_k     - step, 4))
            pass  # thresholds updated silently
        # else: in range — silent

    # ── Per-bit dashboard (ANSI fixed header) ────────────────────────────────

    def _setup_dashboard(self) -> None:
        """
        Печатает фиксированный блок вверху консоли и устанавливает
        зону прокрутки ниже него. Вызывается один раз после шапки.
        """
        self._dashboard_vt_ok = _enable_vt_mode()
        if not self._dashboard_vt_ok:
            return   # fallback: обычный режим без дашборда

        bits_count   = self.max_bits - self.min_bits + 1
        data_rows    = (bits_count + 3) // 4          # 4 бита в строке
        self._dash_height = data_rows + 3             # шапка + строки + разделитель + пустая

        try:
            term_rows = os.get_terminal_size().lines
        except Exception:
            term_rows = 50

        # Печатаем пустые строки под дашборд (потом будем перезаписывать)
        sys.stdout.write('\n' * self._dash_height)
        # Устанавливаем зону прокрутки: от строки (dash_height+1) до конца
        sys.stdout.write(f'\033[{self._dash_height + 1};{term_rows}r')
        # Ставим курсор в начало зоны прокрутки
        sys.stdout.write(f'\033[{self._dash_height + 1};1H')
        sys.stdout.flush()
        self._dashboard_ready = True

    def _render_dashboard(self) -> None:
        """Перерисовывает дашборд без мерцания через ANSI save/restore cursor."""
        if not self._dashboard_ready:
            return

        COLS = 4
        bits_list = list(range(self.min_bits, self.max_bits + 1))
        rows = [bits_list[i:i + COLS] for i in range(0, len(bits_list), COLS)]
        W    = 70   # ширина рамки

        def cell(b: int) -> str:
            r = self._best_per_bits.get(b, 0.0)
            if r == 0.0:
                return f'{b:>2}: -------   '
            tag = ' **' if r >= 1.75 else '   '
            return f'{b:>2}:{r:.5f}{tag}'

        lines: list[str] = []
        lines.append(' +-- Per-bit best ratio'
                     f' [{self.min_bits}..{self.max_bits}] '
                     + '-' * (W - 24 - len(str(self.min_bits)) - len(str(self.max_bits))) + '+')
        for row in rows:
            cells = '  '.join(cell(b) for b in row)
            # pad to fixed width
            inner = f' | {cells}'
            lines.append(inner.ljust(W - 1) + '|')
        lines.append(' +' + '-' * (W - 2) + '+')
        lines.append('')   # пустая строка-буфер

        # Строим одну строку вывода: сохранить → перейти вверх → вписать → восстановить
        out = ['\033[s']    # save cursor
        for i, line in enumerate(lines):
            out.append(f'\033[{i + 1};1H\033[2K{line}')
        out.append('\033[u')  # restore cursor
        sys.stdout.write(''.join(out))
        sys.stdout.flush()

    def _update_best_per_bits(self, bits: int, ratio: float) -> None:
        if ratio > self._best_per_bits.get(bits, 0.0):
            self._best_per_bits[bits] = ratio

    # ── Status line ───────────────────────────────────────────────────────────

    def _print_status(self):
        self._render_dashboard()   # обновляем дашборд перед статус-строкой
        st      = self._stats
        elapsed = time.time() - st["start_time"]
        speed   = st["session_generated"] / elapsed if elapsed > 0 else 0
        avg_k   = (sum(st["recent_k"]) / len(st["recent_k"])
                   if st["recent_k"] else 0.0)
        fast_pct = (st["session_fast_pass"] / max(1, st["session_generated"]) * 100)

        def fn(n):
            if n >= 1e9: return f"{n/1e9:.1f}G"
            if n >= 1e6: return f"{n/1e6:.1f}M"
            if n >= 1e3: return f"{n/1e3:.1f}K"
            return str(int(n))
        def ft(s):
            s = int(s); h, r = divmod(s, 3600); m, sec = divmod(r, 60)
            return f"{h}h{m:02d}m" if h else f"{m}m{sec:02d}s" if m else f"{sec}s"

        print(
            f"\r[{ft(elapsed)}]"
            f"  gen={fn(speed)}/s"
            f"  total={fn(st['total_generated'])}"
            f"  workers={st['active_workers']}/{self.max_workers}"
            f"  fp={fast_pct:.1f}%"
            f"  found={st['total_found']}  saved={st['total_saved']}"
            f"  plt={st['total_plateau']}"
            f"  avgk={avg_k:.2f}"
            f"  save_thr={self._save_ratio:.4f}"
            f"  fast({self._fast_ratio:.3f}/{self._fast_k:.2f})"
            f"  BEST={st['best_ratio']:.5f}",
            end="", flush=True
        )

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def _check_order_switch(self) -> None:
        """
        Планировщик переключения порядков Маркова.
        Переключает порядок циклически каждые markov_order_switch_interval секунд.
        Новый порядок передаётся воркерам через task_args при следующем submit.
        """
        if len(self._markov_orders) < 2:
            return
        now = time.time()
        if now - self._last_order_switch < self._markov_switch_interval:
            return
        self._markov_order_idx = (self._markov_order_idx + 1) % len(self._markov_orders)
        new_order = self._markov_orders[self._markov_order_idx]
        if new_order != self._current_markov_order:
            self._current_markov_order = new_order
            log(f"Markov hierarchy: climber order->{new_order} "
                f"(idx={self._markov_order_idx}, interval={self._markov_switch_interval}s)")
        self._last_order_switch = now

    def _check_stagnation(self) -> None:
        """
        Детектор стагнации: если best_ratio не улучшался дольше stagnation_timeout
        и found/saved > stagnation_ratio_threshold — активирует форсированный режим
        (anomaly_rate=1.0 на forced_mode_duration секунд).
        """
        if not self._stagnation_enabled:
            return
        now = time.time()

        # Деактивация: время форсированного режима вышло
        if self._stagnation_active and now >= self._stagnation_end_time:
            self._stagnation_active = True
            self._anomaly_override  = None
            self._stagnation_active = False
            log("Stagnation mode OFF — resuming normal anomaly_rate")
            return

        if self._stagnation_active:
            return  # ещё идёт форсированный режим

        # Проверяем условия активации
        st    = self._stats
        saved = st["total_saved"]
        found = st["total_found"]
        ratio = found / max(1, saved)
        time_since_best = now - self._last_best_update_time

        if (time_since_best > self._stagnation_timeout and
                ratio > self._stagnation_ratio_thr):
            self._stagnation_active    = True
            self._stagnation_end_time  = now + self._forced_mode_duration
            self._anomaly_override     = self._forced_anomaly_rate
            # Сбрасываем планировщик на самый низкий порядок (максимальная разведка)
            if self._markov_orders:
                self._current_markov_order = min(self._markov_orders)
                self._markov_order_idx     = self._markov_orders.index(self._current_markov_order)
            log(f"STAGNATION DETECTED: no improvement for {time_since_best:.0f}s, "
                f"found/saved={ratio:.0f}. "
                f"Forced mode ON: anomaly=100%, markov_order={self._current_markov_order}, "
                f"duration={self._forced_mode_duration}s")

    def _compute_markov_weight(self, ratio: float, k: float, bs: str) -> float:
        """
        Вычисляет вес для обучения Маркова с учётом типа кандидата и новизны.
        Вызывается из _handle_results для каждого сохранённого числа.
        """
        best = self._stats["best_ratio"]

        # Элитный: сильно лучше текущего рекорда
        if best > 0 and ratio > best * 1.05:
            mw = self._elite_weight
            ctype = "elite"
        # Новый локальный максимум
        elif ratio >= best and best > 0:
            mw = self._local_max_weight
            ctype = "local_max"
        # HQ кандидат
        elif ratio >= self._save_ratio * 1.05 or k >= 8.0:
            mw = 1.0
            ctype = "hq"
        else:
            mw = 0.5
            ctype = "normal"

        # Бонус за новизну (расстояние Хэмминга от топ-10)
        if self._top_saved and self._novelty_hamming_thr > 0:
            min_len = min(len(bs), 200)
            dists = []
            for s in self._top_saved:
                n = min(len(bs), len(s), min_len)
                if n == 0: continue
                d = sum(a != b for a, b in zip(bs[:n], s[:n])) / n
                dists.append(d)
            if dists:
                avg_dist = sum(dists) / len(dists)
                if avg_dist > self._novelty_hamming_thr:
                    mw *= self._novelty_bonus
                    log(f"Novelty bonus x{self._novelty_bonus} ({ctype}): "
                        f"hamming={avg_dist:.3f}  mw→{mw:.2f}  ratio={ratio:.5f}")

        return mw

    def _check_pause(self) -> None:
        """
        Pause when pause.flag exists, resume when it is deleted.
        While paused: saves snapshot, prints [PAUSED], sleeps 1s.
        Works on Windows (no UNIX signals needed).
        """
        if not self._pause_file.exists():
            if self._paused:
                self._paused = False
                self._stats["start_time"] += time.time() - self._pause_time
                log("RESUMED  (pause.flag removed)")
            return

        if not self._paused:
            self._paused = True
            self._pause_time = time.time()
            self.save_snapshot()
            log(f"PAUSED   (delete pause.flag to resume)  "
                f"snapshot saved → {self.snap_file}")

        # Print blinking status while paused
        elapsed = time.time() - self._stats["start_time"]
        def ft(s):
            s = int(s); h, r = divmod(s, 3600); m, sec = divmod(r, 60)
            return f"{h}h{m:02d}m" if h else f"{m}m{sec:02d}s" if m else f"{sec}s"
        print(
            f"\r[{ft(elapsed)}]  *** PAUSED ***  "
            f"best={self._stats['best_ratio']:.5f}  "
            f"saved={self._stats['total_saved']}  "
            f"Delete pause.flag to resume     ",
            end="", flush=True)
        time.sleep(0.8)

    def save_snapshot(self):
        try:
            self.snap_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.snap_file, "wb") as f:
                pickle.dump({
                    "stats":       self._stats,
                    "save_ratio":  self._save_ratio,
                    "save_steps":  self._save_steps,
                    "fast_ratio":  self._fast_ratio,   # adaptive thresholds
                    "fast_k":      self._fast_k,
                    "ts":          datetime.now(timezone.utc).isoformat(),
                }, f)
        except Exception as e:
            log(f"Snapshot save error: {e}")

    def load_snapshot(self) -> bool:
        if not self.snap_file.exists():
            return False
        try:
            with open(self.snap_file, "rb") as f:
                s = pickle.load(f)
            for k in ("total_generated","total_checked","total_found","total_saved",
                      "best_ratio","best_steps","best_bits"):
                if k in s.get("stats", {}):
                    self._stats[k] = s["stats"][k]
            self._save_ratio  = s.get("save_ratio",  self._save_ratio)
            self._save_steps  = s.get("save_steps",  self._save_steps)
            # Restore adaptive thresholds (avoids oscillation on resume)
            self._fast_ratio  = s.get("fast_ratio",  self._fast_ratio)
            self._fast_k      = s.get("fast_k",      self._fast_k)
            self._stats["start_time"]    = time.time()
            self._stats["session_generated"] = 0  # reset session counter
            self._stats["session_fast_pass"]  = 0
            log(f"Snapshot loaded: best_ratio={self._stats['best_ratio']:.5f}"
                f"  fast_thr={self._fast_ratio:.3f}/{self._fast_k:.2f}")
            return True
        except Exception as e:
            log(f"Snapshot load error: {e}")
            return False

    # ── Main run loop ─────────────────────────────────────────────────────────

    def run(self):
        N = self.max_workers

        # Create N personal feedback queues via Manager (picklable proxy objects)
        # multiprocessing.Queue CANNOT be passed via submit() — must use Manager().Queue()
        mp_manager   = multiprocessing.Manager()
        worker_queues = [mp_manager.Queue(maxsize=200) for _ in range(N)]

        # task_args template (no queue — queue stored in worker via initializer)
        def make_task():
            return (self.batch_size, self._fast_steps, self._fast_ratio,
                    self._fast_k, self._cap_steps, self.min_bits, self.max_bits)

        # futures dict: future → worker_id (for routing feedback)
        futures: dict = {}
        snap_counter  = 0
        max_inflight  = N * 2   # 2 tasks queued per worker process

        print()
        print("=" * 70)
        print(f"  Collatz Crystal Hunter v5.3a  —  Distributed-Learning Edition")
        print(f"  Workers:  {N} processes (each with own HybridGenerator)")
        print(f"  Bits:     {self.min_bits}–{self.max_bits}")
        print(f"  Filters:  fast({self._fast_steps}steps) → full({self._cap_steps}steps)")
        print(f"  Save:     ratio≥{self._save_ratio:.4f}  steps≥{self._save_steps}")
        if LOG_PATH: print(f"  Log:      {LOG_PATH}")
        print("=" * 70)
        print()
        log(f"Starting: max_inflight={max_inflight}  "
             f"pause: create '{self._pause_file.name}' in same folder as EXE")

        # Инициализируем дашборд (ANSI фиксированная шапка с per-bit статистикой)
        self._setup_dashboard()

        last_print  = 0.0
        worker_rr   = 0   # round-robin counter for assigning worker_ids to futures

        # Each worker process gets: (worker_id, its_queue, cfg)
        # We create N initializer-arg tuples and use a custom pool setup below
        # ProcessPoolExecutor only supports ONE initargs tuple for all workers,
        # so we use a different approach: pass queue via task args at first call,
        # and store it in worker global on first invocation.
        #
        # Implementation: pass (worker_id, feedback_queue) in every task args.
        # Worker checks if _w_queue is None on first call and initialises.
        # Subsequent calls with same worker_id reuse stored state.

        def make_task_with_id(wid: int):
            time_since_best = time.time() - self._last_best_update_time
            anomaly = self._anomaly_override   # None = worker uses its own config value
            return (wid, worker_queues[wid],
                    self.batch_size, self._fast_steps, self._fast_ratio,
                    self._fast_k, self._cap_steps, self.min_bits, self.max_bits,
                    self._current_markov_order,
                    time_since_best,
                    self._stats["best_ratio"],
                    anomaly,
                    self._ph_enabled, self._ph_min_height,
                    self._ph_min_duration, self._ph_max_per_batch)

        try:
          with ProcessPoolExecutor(max_workers=N) as executor:
            # Submit initial wave round-robin
            for i in range(max_inflight):
                wid = i % N
                futures[executor.submit(_worker_task_with_init, make_task_with_id(wid))] = wid

            while self._running:
                if futures:
                    done_set, _ = wait(list(futures.keys()),
                                       timeout=0.05,
                                       return_when=FIRST_COMPLETED)
                else:
                    done_set = set()
                    time.sleep(0.01)

                for fut in done_set:
                    wid = futures.pop(fut, 0)
                    try:
                        fr, ret_wid, n_gen, n_fast, plateau_cands = fut.result(timeout=10)
                        self._stats["total_generated"]  += n_gen
                        self._stats["session_generated"] += n_gen
                        self._stats["total_fast_pass"]   += n_fast
                        self._stats["session_fast_pass"] += n_fast
                        self._iw_generated               += n_gen
                        self._iw_fast_pass               += n_fast
                        snap_counter                   += n_gen
                        self._handle_results(fr, ret_wid, worker_queues, plateau_cands)
                        self._adapt_thresholds()
                    except Exception as e:
                        log_exception("worker result", e)

                    # Immediately re-submit same worker_id to keep the process busy
                    if self._running:
                        futures[executor.submit(
                            _worker_task_with_init, make_task_with_id(wid)
                        )] = wid

                self._stats["active_workers"] = len(futures)

                self._check_pause()  # pause if pause.flag exists
                self._check_order_switch()   # цикличное переключение порядка Маркова
                self._check_stagnation()     # детектор стагнации + форсированный режим

                now = time.time()
                if now - last_print >= 1.0:
                    self._print_status()
                    last_print = now

                if snap_counter >= self.snap_every:
                    self.save_snapshot()
                    snap_counter = 0

            print()
            log("Draining remaining tasks...")
            for fut in list(futures):
                try:
                    fr, wid, n_gen, n_fast, plateau_cands = fut.result(timeout=60)
                    self._stats["total_generated"]  += n_gen
                    self._stats["session_generated"] += n_gen
                    self._stats["total_fast_pass"]   += n_fast
                    self._stats["session_fast_pass"] += n_fast
                    self._handle_results(fr, wid, worker_queues, plateau_cands)
                except Exception:
                    pass

        except (KeyboardInterrupt, SystemExit):
            log("Interrupted — saving snapshot...")
        finally:
            self.save_snapshot()
            self._stats_col.flush()
        e = time.time() - self._stats["start_time"]
        self._stats_col.close()
        log(f"Done!  time={timedelta(seconds=int(e))}"
            f"  gen={self._stats['total_generated']:,}"
            f"  saved={self._stats['total_saved']}"
            f"  best={self._stats['best_ratio']:.5f}")


# ============================================================
# Worker entry-point that handles its own initialisation
# (since ProcessPoolExecutor can't pass different initargs per worker)
# ============================================================

# Per-process state: keyed by worker_id
_wp_state: dict = {}   # { worker_id: {"gen": ..., "queue": ...} }

def _worker_task_with_init(task_args: tuple):
    """
    Single entry-point for all worker tasks.
    Handles first-call initialisation of generator and queue storage.
    """
    global _wp_state
    import sys, os
    sys.path.insert(0, str(Path(__file__).parent))

    (worker_id, feedback_queue,
     batch_size, fast_steps, fast_ratio_thr, fast_k_thr,
     cap_steps, min_bits, max_bits,
     markov_order, time_since_best, global_best_ratio,
     anomaly_override,
     ph_enabled, ph_min_height, ph_min_duration, ph_max_per_batch) = task_args

    # ── Initialise on first call for this worker_id in this process ──────────
    if worker_id not in _wp_state:
        from generators.hybrid import HybridCrystalGenerator
        import yaml as _yaml
        cfg_path = Path(__file__).parent / "config.yaml"
        if not cfg_path.exists() and getattr(sys, "frozen", False):
            cfg_path = Path(sys.executable).parent / "config.yaml"
        with open(cfg_path, encoding="utf-8") as f:
            cfg = _yaml.safe_load(f)
        seed = (int(time.time() * 1000) ^ os.getpid() ^ (worker_id * 0xDEADBEEF)) & 0xFFFFFFFF
        gen  = HybridCrystalGenerator(cfg, seed=seed)
        gen._cfg_anomaly_rate = gen._anomaly_rate_base   # сохраняем оригинальное значение
        _wp_state[worker_id] = {"gen": gen, "queue": feedback_queue}

    state = _wp_state[worker_id]
    gen   = state["gen"]
    q     = state["queue"]

    # Update dynamic settings
    gen.min_bits = min_bits
    gen.max_bits = max_bits

    # Переключаем порядок Маркова если изменился
    if gen.markov.order != markov_order:
        gen.set_markov_order(markov_order)

    # Обновляем контекст для адаптивной температуры
    gen.set_context(
        time_since_last_best=time_since_best,
        global_best_ratio=global_best_ratio,
        local_best_ratio=gen._local_best_ratio,
    )

    # Форсированный anomaly_rate при стагнации (переопределяет config)
    if anomaly_override is not None:
        gen._anomaly_rate_base = anomaly_override
    else:
        # Восстанавливаем из cfg если был переопределён
        gen._anomaly_rate_base = gen._cfg_anomaly_rate if hasattr(gen, "_cfg_anomaly_rate") \
                                 else gen._anomaly_rate_base

    # ── Generate ─────────────────────────────────────────────────────────────
    candidates = gen.generate_batch(batch_size)

    # ── Fast sim + feedback_fast + optional full sim ──────────────────────────
    full_results       = []
    plateau_candidates = []   # плато-кандидаты для обучения Маркова
    fast_fb_batch      = []   # ALL stage-1 survivors → generator.feedback_fast()
    n_stage3           = 0    # stage-2 FILTER survivors → reported as fast_pass

    for n in candidates:
        if n <= 1: continue
        ob = n.bit_length()
        if ob == 0: continue

        # Stage 1: pre-filter 50 steps
        pb = ob; cur = n; s = 0
        while cur > 1 and s < 50:
            cur = cur * 3 + 1 if cur & 1 else cur >> 1
            s += 1
            cb = cur.bit_length()
            if cb > pb: pb = cb
        if pb / ob < 1.03 and cur > 1:
            continue

        # Stage 2: fast sim up to fast_steps
        while cur > 1 and s < fast_steps:
            cur = cur * 3 + 1 if cur & 1 else cur >> 1
            s += 1
            cb = cur.bit_length()
            if cb > pb: pb = cb
        ratio_fast = pb / ob
        k_fast     = s / ob if ob else 0.0

        # ALL stage-1 survivors → generator feedback (smart restarts)
        fast_fb_batch.append((n, k_fast))

        # Stage-2 FILTER: fast_ratio_thr/fast_k_thr from task args (updated per submit)
        if not (cur <= 1 or ratio_fast >= fast_ratio_thr or k_fast >= fast_k_thr):
            continue
        n_stage3 += 1   # ← real fast_pass metric, affected by adaptive thresholds

        # Stage 3: full sim (capped) + plateau detection
        # Plateau = локальный максимум траектории выше адаптивного порога.
        #
        # АДАПТИВНЫЙ ПОРОГ: фиксированный ph_min_height хорошо работает для 72 бит,
        # но для 100-150 бит почти любая траектория даёт ratio>1.2 → шум.
        # Масштабируем: effective_height = ph_min_height + (ob-72)*0.0015
        #   72  бит → ph_min_height (без изменений)
        #   100 бит → +0.042
        #   150 бит → +0.117
        # АДАПТИВНЫЙ ИНТЕРВАЛ: для длинных траекторий пики встречаются чаще,
        # масштабируем интервал дедупликации: 72 бит → base, 150 бит → base*2
        effective_height   = ph_min_height + max(0, ob - 72) * 0.0015
        ph_threshold_b     = int(ob * effective_height) + 1
        effective_duration = int(ph_min_duration * (1.0 + max(0, ob - 72) / 78.0))
        ph_prev_cb         = pb
        plateau_list       = []
        ph_last_peak_s     = -effective_duration

        while cur > 1 and s < cap_steps:
            cur = cur * 3 + 1 if cur & 1 else cur >> 1
            s += 1
            cb = cur.bit_length()
            if cb > pb: pb = cb

            # Plateau tracking (only when ph_enabled)
            if ph_enabled:
                if ph_prev_cb > cb and ph_prev_cb >= ph_threshold_b:
                    if (s - 1) - ph_last_peak_s >= effective_duration:
                        plateau_list.append((ph_prev_cb, s - 1))
                        ph_last_peak_s = s - 1
                ph_prev_cb = cb

        # Проверяем последний шаг как возможный пик
        if ph_enabled and ph_prev_cb >= ph_threshold_b:
            if s - ph_last_peak_s >= effective_duration:
                plateau_list.append((ph_prev_cb, s))

        ratio = pb / ob
        k     = s / ob if ob else 0.0
        full_results.append({
            "n": n, "n_bits": ob, "peak_bits": pb,
            "ratio": ratio, "steps": s,
            "converged": cur <= 1, "k": k,
            "worker_id": worker_id,
        })

        # Collect plateau candidates — только ЛУЧШИЙ пик за всё число,
        # и только если он реально высокий (ratio >= ph_min_height + буфер).
        # Фильтруем в воркере чтобы не передавать мусор в main process.
        if ph_enabled and plateau_list:
            best_peak_b, best_peak_s = max(plateau_list, key=lambda x: x[0])
            best_ratio_pc = best_peak_b / ob if ob else 0.0
            # Передаём только если пик ≥ ph_min_height — остальное выбросит main
            if best_ratio_pc >= ph_min_height:
                plateau_candidates.append({
                    "n":         n,
                    "n_bits":    ob,
                    "peak_bits": best_peak_b,
                    "peak_step": best_peak_s,
                })

    # ── Update local generator stats (fast_k rolling averages) ───────────────
    if fast_fb_batch:
        try:
            gen.feedback_fast(fast_fb_batch)
        except Exception:
            pass

    # ── Drain personal feedback queue (main → this worker) ───────────────────
    try:
        while True:
            msg = q.get_nowait()
            if len(msg) == 5:
                n_fb, k_fb, bs_fb, ratio_fb, mw_fb = msg
            else:
                n_fb, k_fb, bs_fb, ratio_fb = msg; mw_fb = None
            # Обновляем local_best_ratio воркера
            if ratio_fb > gen._local_best_ratio:
                gen._local_best_ratio = ratio_fb
            gen.feedback(n_fb, k_fb, bs_fb, ratio=ratio_fb, markov_weight=mw_fb)
    except Exception:
        pass  # queue.Empty or similar

    return full_results, worker_id, len(candidates), n_stage3, plateau_candidates


# ============================================================
# Config + CLI
# ============================================================

def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    log("=== Collatz Crystal Hunter v5.3a ===")
    log(f"Python {sys.version}")
    log(f"CWD: {os.getcwd()}  EXE: {sys.executable}")
    if LOG_PATH:
        print(f"Log: {LOG_PATH}")

    p = argparse.ArgumentParser(description="Collatz Crystal Hunter v5.3a")
    p.add_argument("--config",       default="config.yaml")
    p.add_argument("--resume",       action="store_true")
    p.add_argument("--target-ratio", type=float)
    p.add_argument("--target-steps", type=int)
    p.add_argument("--bits",         nargs=2, type=int, metavar=("MIN","MAX"))
    p.add_argument("--workers",      type=int)
    p.add_argument("--batch",        type=int)
    # ── Режим охоты ──────────────────────────────────────────────────────────
    p.add_argument("--mode",          default="search",
                   choices=["search", "hunt", "families"],
                   help="search=обычный поиск, hunt=охота за пиком, families=точный поиск по семействам A/B")
    p.add_argument("--hunt-target",   type=int,   default=141,
                   help="Целевой пик для режима hunt (default: 141)")
    p.add_argument("--hunt-bits",     nargs=2, type=int, metavar=("MIN","MAX"),
                   default=None,
                   help="Диапазон битности входных чисел для hunt (default: берётся из --bits или config)")
    p.add_argument("--hunt-min-prox", type=float, default=0.990,
                   help="Минимальный proximity для сохранения кандидата (default: 0.990)")
    p.add_argument("--hunt-top",      type=int,   default=50,
                   help="Сколько лучших кандидатов хранить в extra_seeds.json (default: 50)")
    # ── Режим families ────────────────────────────────────────────────────────
    p.add_argument("--families-wide",  action="store_true", default=False,
                   help="Расширенный поиск дельт (-128..+2) вместо стандартного")
    p.add_argument("--families-ratio", type=float, default=1.40,
                   help="Минимальный ratio для сохранения (default: 1.40)")
    args = p.parse_args()

    # ── Режим hunt: запускаем и выходим ──────────────────────────────────────
    if args.mode == "hunt":
        from peak_hunter import run_hunt
        hunt_bits = args.hunt_bits or args.bits or [72, 80]
        n_workers = args.workers or 0
        run_hunt(
            min_bits    = hunt_bits[0],
            max_bits    = hunt_bits[1],
            target_peak = args.hunt_target,
            min_prox    = args.hunt_min_prox,
            top_n       = args.hunt_top,
            n_workers   = n_workers,
        )
        return

    # ── Режим families: запускаем и выходим ──────────────────────────────────
    if args.mode == "families":
        from exact_families import run_families
        fam_bits = args.hunt_bits or args.bits or [72, 140]
        run_families(
            min_bits  = fam_bits[0],
            max_bits  = fam_bits[1],
            min_ratio = args.families_ratio,
            workers   = args.workers or 0,
            wide      = args.families_wide,
        )
        return

    # Locate config
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        cfg_path = Path(__file__).parent / args.config
    if not cfg_path.exists() and getattr(sys, "frozen", False):
        cfg_path = Path(sys.executable).parent / args.config
    if not cfg_path.exists():
        log(f"ERROR: config not found: {args.config}")
        input("Press Enter..."); sys.exit(1)

    try:
        cfg = load_config(str(cfg_path))
    except Exception as e:
        log_exception("load_config", e); input("Press Enter..."); sys.exit(1)

    if args.target_ratio: cfg.setdefault("search",   {})["target_ratio"] = args.target_ratio
    if args.target_steps: cfg.setdefault("search",   {})["target_steps"] = args.target_steps
    if args.bits:
        cfg.setdefault("search",{})["min_bits"] = args.bits[0]
        cfg.setdefault("search",{})["max_bits"] = args.bits[1]
    if args.workers: cfg.setdefault("parallel",{})["max_workers"] = args.workers
    if args.batch:   cfg.setdefault("parallel",{})["batch_size"]  = args.batch

    par = cfg.setdefault("parallel", {})
    if not par.get("batch_size"): par["batch_size"] = 2048

    try:
        from logger import setup_logger
        lc = cfg.get("logging", {})
        setup_logger(lc.get("log_dir","./logs"), lc.get("level","INFO"))
    except Exception:
        pass

    srch = cfg.get("search", {})
    log(f"Config: bits={srch.get('min_bits',80)}-{srch.get('max_bits',120)}"
        f"  workers={par.get('max_workers',0) or 'auto'}"
        f"  batch={par.get('batch_size')}")

    try:
        hunter = CrystalHunter(cfg)
    except Exception as e:
        log_exception("CrystalHunter init", e); input("Press Enter..."); sys.exit(1)

    if args.resume:
        if not hunter.load_snapshot():
            log("No snapshot, starting fresh")
    try:
        hunter.run()
    except Exception as e:
        log_exception("hunter.run()", e); input("Press Enter...")


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()
