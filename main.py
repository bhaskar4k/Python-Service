from __future__ import annotations

import logging
import multiprocessing as mp
import signal
import sys
import threading
from pathlib import Path
from typing import Any

import uvicorn
import yaml

from api.control import build_app
from core.logging_setup import configure_supervisor_logging
from core.messaging import QueueBus
from core.registry import resolve
from core.supervisor import Supervisor

CONFIG_PATH = Path(__file__).with_name("config") / "settings.yaml"
log = logging.getLogger("main")


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_units(
    config: dict[str, Any], bus: QueueBus
) -> dict[str, tuple[type, dict[str, Any]]]:
    """Resolve enabled units from config and wire their queues.

    Each unit's cfg gets ``in_queue``/``out_queue`` references when it
    declares ``consumes``/``produces`` topics, so units can talk through
    the shared bus without knowing about each other.
    """
    units: dict[str, tuple[type, dict[str, Any]]] = {}
    for name, entry in (config.get("units") or {}).items():
        if not entry.get("enabled", True):
            continue
        cls = resolve(name)
        cfg = dict(entry.get("cfg") or {})
        produces = entry.get("produces") or []
        consumes = entry.get("consumes") or []
        if produces:
            cfg["out_queue"] = bus.topic(produces[0])
        if consumes:
            cfg["in_queue"] = bus.topic(consumes[0])
        units[name] = (cls, cfg)
    return units


def main() -> int:
    configure_supervisor_logging()
    config = load_config()
    bus = QueueBus()
    units = build_units(config, bus)
    if not units:
        log.error("no units enabled in %s; exiting", CONFIG_PATH)
        return 1

    supervisor = Supervisor(units)
    supervisor.start()

    api_cfg = config.get("api") or {}
    app = build_app(supervisor)
    server_config = uvicorn.Config(
        app,
        host=api_cfg.get("host", "127.0.0.1"),
        port=int(api_cfg.get("port", 8000)),
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(server_config)

    def _shutdown(signum: int, _frame) -> None:  # noqa: ANN001
        log.info("received signal %s", signum)
        server.should_exit = True

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        server.run()  # blocks until should_exit
    finally:
        supervisor.shutdown()
    return 0


if __name__ == "__main__":
    # ``spawn`` is required on Windows and keeps Linux/macOS behavior identical.
    mp.set_start_method("spawn", force=True)
    sys.exit(main())

