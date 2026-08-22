"""
stats_collector.py  —  Collatz Crystal Hunter v5.3a
====================================================
Collects per-number statistics for all stage-3 (full-sim) results.
Writes to daily rotating CSV files; buffered for performance.

Config section (config.yaml):
  statistics:
    enabled: false
    output_dir: "./stats"
    flush_interval: 10000   # records between disk flushes
    include_n: false        # include the actual number (can be huge)
"""
from __future__ import annotations

import csv
import io
import os
from datetime import datetime, date
from pathlib import Path
from typing import Optional


class StatsCollector:
    """
    Thread-safe CSV writer for full-sim results.

    Call .record(r) for every dict returned from stage-3.
    Call .flush() periodically and .close() on shutdown.
    """

    FIELDS_BASE  = ["timestamp", "bits", "ratio", "steps", "k", "converged"]
    FIELDS_WITH_N = FIELDS_BASE + ["n"]

    def __init__(self, cfg: dict):
        stat = cfg.get("statistics", {})
        self.enabled        = stat.get("enabled", False)
        self.output_dir     = Path(stat.get("output_dir", "./stats"))
        self.flush_interval = int(stat.get("flush_interval", 10_000))
        self.include_n      = bool(stat.get("include_n", False))
        _max = stat.get("max_records", 0)
        self.max_records    = int(_max) if _max else 0   # 0 = unlimited

        self._buf:      list[dict] = []
        self._fh:       Optional[io.TextIOWrapper] = None
        self._writer:   Optional[csv.DictWriter]   = None
        self._cur_date: Optional[date]             = None
        self._count:    int                        = 0   # records since last flush
        self._total:    int                        = 0

        if self.enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def record(self, r: dict) -> None:
        """Add one stage-3 result. Returns immediately (buffered)."""
        if not self.enabled:
            return
        if self.max_records and self._total >= self.max_records:
            return   # limit reached — silently ignore
        self._ensure_file()
        row = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            "bits":      r["n_bits"],
            "ratio":     round(r["ratio"], 6),
            "steps":     r["steps"],
            "k":         round(r["k"], 4),
            "converged": int(r.get("converged", True)),
        }
        if self.include_n:
            row["n"] = r["n"]
        self._writer.writerow(row)
        self._count += 1
        self._total += 1
        if self.max_records and self._total >= self.max_records:
            self._flush_file()   # flush immediately on hitting the limit
        elif self._count >= self.flush_interval:
            self._flush_file()
            self._count = 0

    def flush(self) -> None:
        """Force flush to disk (call on shutdown or periodically)."""
        if self.enabled and self._fh:
            self._flush_file()
            self._count = 0

    def close(self) -> None:
        """Flush and close the current file."""
        self.flush()
        if self._fh:
            try:
                self._fh.close()
            except Exception:
                pass
            self._fh = None
            self._writer = None

    @property
    def total(self) -> int:
        return self._total

    @property
    def is_full(self) -> bool:
        """True when max_records limit has been reached."""
        return bool(self.max_records) and self._total >= self.max_records

    # ── Internal ──────────────────────────────────────────────────────────────

    def _today_path(self) -> Path:
        d = date.today()
        return self.output_dir / f"stats_{d.strftime('%Y%m%d')}.csv"

    def _ensure_file(self) -> None:
        today = date.today()
        if self._cur_date == today and self._fh is not None:
            return  # already open for today

        # Day rolled over or first open — close old, open new
        self.close()
        self._cur_date = today
        path = self._today_path()
        need_header = not path.exists() or path.stat().st_size == 0
        self._fh = open(path, "a", encoding="utf-8", newline="")
        fields = self.FIELDS_WITH_N if self.include_n else self.FIELDS_BASE
        self._writer = csv.DictWriter(
            self._fh, fieldnames=fields,
            extrasaction="ignore", lineterminator="\n"
        )
        if need_header:
            self._writer.writeheader()
            self._fh.flush()

    def _flush_file(self) -> None:
        if self._fh:
            try:
                self._fh.flush()
                os.fsync(self._fh.fileno())
            except Exception:
                pass
