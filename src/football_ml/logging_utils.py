from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path

from football_ml.paths import INGESTION_LOGS_DIR, ensure_dir


def configure_logger(name: str) -> tuple[logging.Logger, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_dir = ensure_dir(INGESTION_LOGS_DIR)
    log_path = log_dir / f"{name}-{timestamp}.log"

    logger = logging.getLogger(f"football_ml.{name}.{timestamp}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger, log_path

