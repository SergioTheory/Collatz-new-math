"""
logger.py — Централизованное логирование с ротацией по дням.
"""
from __future__ import annotations

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logger(log_dir: str = "./logs", level: str = "INFO") -> logging.Logger:
    """
    Создаёт и настраивает корневой логгер crystal_hunter.

    Args:
        log_dir:  папка для лог-файлов (создаётся если не существует)
        level:    уровень логирования (DEBUG / INFO / WARNING / ERROR)

    Returns:
        Настроенный Logger
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("crystal")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if logger.handlers:
        return logger  # уже настроен (во избежание дублирования)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ─── Консольный хендлер (только WARNING и выше, чтобы не мешать rich) ───
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # ─── Файловый хендлер с ротацией по дням ────────────────────────────────
    fh = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "crystal.log"),
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    fh.setLevel(getattr(logging, level.upper(), logging.INFO))
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


def get_logger(name: str = "crystal") -> logging.Logger:
    """Возвращает дочерний логгер с указанным именем."""
    return logging.getLogger(f"crystal.{name}")
