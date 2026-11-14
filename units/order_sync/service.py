from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class Order:
    id: int
    amount: float


def fetch_next_order(counter: int) -> Order:
    """Stand-in for whatever real source orders come from."""
    return Order(id=counter, amount=round(random.uniform(10, 500), 2))
