"""A bundled quote stream that exercises every confidence state.

Healthy quotes, then a crossed book (UNRELIABLE), a clean recovery back to HEALTHY, a
stale top-of-book (DEGRADED), and another recovery. Deterministic.
"""

from __future__ import annotations

from decimal import Decimal

from quantstream_contracts.events import Quote
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed

SAMPLE_SYMBOL = "BOOK"
_SIZE = size_to_fixed("5")


def _q(seq: int, ts_s: int, bid: str, ask: str) -> Quote:
    return Quote(
        seq=seq,
        timestamp_ns=ts_s * 1_000_000_000,
        symbol=SAMPLE_SYMBOL,
        bid_price=price_to_fixed(Decimal(bid)),
        bid_size=_SIZE,
        ask_price=price_to_fixed(Decimal(ask)),
        ask_size=_SIZE,
        venue="DEMO",
    )


def sample_quotes() -> list[Quote]:
    return [
        _q(0, 0, "100.00", "100.02"),   # healthy
        _q(1, 1, "100.01", "100.03"),   # healthy
        _q(2, 2, "100.05", "100.01"),   # crossed -> UNRELIABLE
        _q(3, 3, "100.02", "100.04"),   # recovering (1)
        _q(4, 4, "100.03", "100.05"),   # recovering (2)
        _q(5, 5, "100.04", "100.06"),   # recovering (3) -> HEALTHY
        _q(6, 6, "100.10", "100.12"),   # healthy, fresh top-of-book
        _q(7, 7, "100.10", "100.12"),   # same book, age 1s (not stale)
        _q(8, 13, "100.10", "100.12"),  # same book, age 7s -> stale -> DEGRADED
        _q(9, 14, "100.20", "100.22"),  # recovering (1)
        _q(10, 15, "100.21", "100.23"), # recovering (2)
        _q(11, 16, "100.22", "100.24"), # recovering (3) -> HEALTHY
    ]
