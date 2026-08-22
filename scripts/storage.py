"""
storage.py — Хранение найденных рекордов.

Форматы: Parquet (основной) + JSON + CSV.
Дедупликация по числу n (через seen_n set).
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from simulator import SimResult
from logger import get_logger

log = get_logger("storage")


class ResultStorage:
    """Хранит и сохраняет найденные рекорды."""

    def __init__(self, cfg: dict) -> None:
        st_cfg = cfg.get("storage", {})
        self.output_dir:   Path = Path(st_cfg.get("output_dir", "./crystal_records"))
        self.save_parquet: bool = st_cfg.get("save_parquet", True)
        self.save_json:    bool = st_cfg.get("save_json", True)
        self.save_csv:     bool = st_cfg.get("save_csv", True)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Дедупликация
        self._seen_n: set[str] = set()
        self._load_existing()

        # Буфер для batch-записи в parquet
        self._buffer: list[dict] = []
        self._buffer_size = 100

        # Статистика
        self._total_saved = 0

        log.info(f"Storage: dir={self.output_dir}, seen={len(self._seen_n)}")

    def _load_existing(self) -> None:
        """Загружает уже найденные числа для дедупликации + определяет исторический best."""
        best_ratio = 0.0
        best_steps = 0
        for f in self.output_dir.glob("*.json"):
            try:
                with open(f, encoding="utf-8") as fp:
                    data = json.load(fp)
                    if "n" in data:
                        self._seen_n.add(str(data["n"]))
                    r = float(data.get("ratio", 0) or 0)
                    s = int(data.get("steps", 0) or 0)
                    if r > best_ratio:
                        best_ratio = r
                    if s > best_steps:
                        best_steps = s
            except Exception:
                pass
        self.alltime_best_ratio = best_ratio
        self.alltime_best_steps = best_steps
        log.info(f"Loaded {len(self._seen_n)} existing records for dedup"
                 f"  alltime best ratio={best_ratio:.5f}  steps={best_steps}")

    def is_new(self, n: int) -> bool:
        """Проверяет, не было ли это число найдено ранее."""
        return str(n) not in self._seen_n

    def add(
        self,
        result:    SimResult,
        source:    str = "hybrid",
        cluster:   Optional[list[int]] = None,
    ) -> Optional[Path]:
        """
        Сохраняет результат, если он новый.

        Args:
            result:  SimResult от симулятора
            source:  источник ("hybrid", "reverse_tree", "cluster", "anomaly")
            cluster: список соседних чисел из кластера

        Returns:
            Путь к JSON-файлу или None если дубликат
        """
        n_str = str(result.n)
        if n_str in self._seen_n:
            return None
        self._seen_n.add(n_str)

        record = {
            "n":           n_str,
            "n_hex":       hex(result.n),
            "binary":      bin(result.n)[2:],
            "bits":        result.n_bits,
            "peak_bits":   result.peak_bits,
            "ratio":       round(result.ratio, 8),
            "steps":       result.steps,
            "k":           round(result.k, 4),
            "converged":   result.converged,
            "source":      source,
            "cluster_size": len(cluster) if cluster else 0,
            "found_at":    datetime.utcnow().isoformat() + "Z",
            "timestamp":   int(time.time()),
        }

        fpath = None

        # JSON
        if self.save_json:
            fname = (
                f"record_{record['timestamp']}_{result.n_bits}bit"
                f"_ratio{result.ratio:.5f}_steps{result.steps}.json"
            )
            fpath = self.output_dir / fname
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)

        # Буфер для parquet/csv
        self._buffer.append(record)
        if len(self._buffer) >= self._buffer_size:
            self._flush_buffer()

        self._total_saved += 1
        log.info(
            f"Saved: bits={result.n_bits}, ratio={result.ratio:.5f}, "
            f"steps={result.steps}, source={source}"
        )
        return fpath

    def _flush_buffer(self) -> None:
        """Сбрасывает буфер на диск."""
        if not self._buffer:
            return

        df = pd.DataFrame(self._buffer)

        if self.save_parquet:
            pq_path = self.output_dir / "records.parquet"
            if pq_path.exists():
                existing = pq.read_table(str(pq_path)).to_pandas()
                df = pd.concat([existing, df], ignore_index=True)
            table = pa.Table.from_pandas(df)
            pq.write_table(table, str(pq_path), compression="snappy")

        if self.save_csv:
            csv_path = self.output_dir / "records.csv"
            header = not csv_path.exists()
            df.to_csv(csv_path, mode="a", header=header, index=False)

        log.debug(f"Flushed {len(self._buffer)} records to disk")
        self._buffer.clear()

    def flush(self) -> None:
        """Принудительный сброс буфера."""
        self._flush_buffer()

    @property
    def total_saved(self) -> int:
        return self._total_saved

    def top_by_ratio(self, n: int = 10) -> list[dict]:
        """Возвращает топ-N записей по ratio."""
        pq_path = self.output_dir / "records.parquet"
        if not pq_path.exists():
            return []
        try:
            df = pq.read_table(str(pq_path)).to_pandas()
            return df.nlargest(n, "ratio").to_dict("records")
        except Exception:
            return []
