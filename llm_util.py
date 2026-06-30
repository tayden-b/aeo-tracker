"""Tiny retry helper — free API tiers rate-limit (HTTP 429), so back off and retry."""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def call_with_retries(fn: Callable[[], T], *, tries: int = 6, base: float = 2.0) -> T:
    last: Exception | None = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - we re-raise after exhausting tries
            last = e
            msg = str(e).lower()
            wait = base * (2**i)
            if any(k in msg for k in (
                "429", "rate", "quota", "resource_exhausted", "exhausted",
                "503", "unavailable", "high demand", "overload",
            )):
                wait = max(wait, 12)  # rate limits / transient server overloads need a real pause
            time.sleep(min(wait, 60))
    assert last is not None
    raise last
