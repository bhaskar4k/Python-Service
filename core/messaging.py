from __future__ import annotations

import multiprocessing as mp
from queue import Empty, Full
from typing import Any, Protocol


class Bus(Protocol):
    def put(self, topic: str, message: Any, timeout: float | None = None) -> None: ...
    def get(self, topic: str, timeout: float | None = None) -> Any: ...


class QueueBus:
    """In-process bus backed by multiprocessing.Queue (one queue per topic).

    Created once in the supervisor, then its queues are passed into each
    unit's config so they share the same underlying objects across processes.
    """

    def __init__(self) -> None:
        self._queues: dict[str, mp.Queue] = {}

    def topic(self, name: str) -> mp.Queue:
        if name not in self._queues:
            self._queues[name] = mp.Queue(maxsize=10_000)
        return self._queues[name]

    def put(self, topic: str, message: Any, timeout: float | None = None) -> None:
        try:
            self.topic(topic).put(message, timeout=timeout)
        except Full as exc:
            raise RuntimeError(f"topic '{topic}' is full") from exc

    def get(self, topic: str, timeout: float | None = None) -> Any:
        try:
            return self.topic(topic).get(timeout=timeout)
        except Empty:
            return None
