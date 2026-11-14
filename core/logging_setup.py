from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path

LOG_DIR = Path(os.environ.get("MY_SERVICE_LOG_DIR", "logs"))
LOG_LEVEL = os.environ.get("MY_SERVICE_LOG_LEVEL", "INFO").upper()

_FMT = "%(asctime)s %(levelname)-7s %(name)s [pid=%(process)d] %(message)s"


def _ensure_dir() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def _file_handler(filename: str) -> logging.Handler:
    path = _ensure_dir() / filename
    handler = logging.handlers.RotatingFileHandler(
        path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(_FMT))
    return handler


def _stream_handler() -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_FMT))
    return handler


def configure_supervisor_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(LOG_LEVEL)
    root.addHandler(_stream_handler())
    root.addHandler(_file_handler("supervisor.log"))


def configure_unit_logging(unit_name: str) -> None:
    """Called inside each worker process so its logs go to its own file."""
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    root.setLevel(LOG_LEVEL)
    root.addHandler(_stream_handler())
    root.addHandler(_file_handler(f"unit_{unit_name}.log"))
