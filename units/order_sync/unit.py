from __future__ import annotations

import time
from dataclasses import asdict

from core.base_unit import BaseUnit
from units.order_sync.service import fetch_next_order


class OrderSyncUnit(BaseUnit):
    name = "order_sync"

    def setup(self) -> None:
        self._counter = 0
        self._interval = float(self.cfg.get("interval_seconds", 2.0))
        self._queue = self.cfg.get("out_queue")  # multiprocessing.Queue, injected
        self.log.info("ready (interval=%.1fs)", self._interval)

    def run(self) -> None:
        while not self.stop.is_set():
            self._counter += 1
            order = fetch_next_order(self._counter)
            self.log.info("synced order %s amount=%.2f", order.id, order.amount)
            if self._queue is not None:
                try:
                    self._queue.put(asdict(order), timeout=1.0)
                except Exception:
                    self.log.exception("failed to enqueue order %s", order.id)
            # Wake promptly on shutdown instead of sleeping the full interval.
            if self.stop.wait(self._interval):
                return

    def teardown(self) -> None:
        self.log.info("processed %d orders", self._counter)
