from __future__ import annotations

import time
from collections import defaultdict

from core.base_unit import BaseUnit


class ReportGenUnit(BaseUnit):
    """Consumes order messages from a queue and prints a rolling summary.

    Shows how units communicate without calling each other directly.
    """

    name = "report_gen"

    def setup(self) -> None:
        self._queue = self.cfg.get("in_queue")
        self._summary_interval = float(self.cfg.get("summary_interval_seconds", 10.0))
        self._totals: dict[str, float] = defaultdict(float)
        self._counts: dict[str, int] = defaultdict(int)
        self._last_summary = time.monotonic()
        self.log.info(
            "ready (summary every %.1fs, queue=%s)",
            self._summary_interval,
            "yes" if self._queue else "no",
        )

    def run(self) -> None:
        while not self.stop.is_set():
            if self._queue is not None:
                try:
                    msg = self._queue.get(timeout=0.5)
                except Exception:
                    msg = None
                if msg:
                    self._totals["amount"] += float(msg.get("amount", 0))
                    self._counts["orders"] += 1
            else:
                self.stop.wait(0.5)

            now = time.monotonic()
            if now - self._last_summary >= self._summary_interval:
                self._emit_summary()
                self._last_summary = now

    def _emit_summary(self) -> None:
        self.log.info(
            "summary: orders=%d total=%.2f",
            self._counts["orders"],
            self._totals["amount"],
        )

    def teardown(self) -> None:
        self._emit_summary()
