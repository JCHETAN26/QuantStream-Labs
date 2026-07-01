"""Order-book state types.

Book confidence is not blindly trusted: a crossed or stale top-of-book downgrades it,
and it only returns to HEALTHY after a run of clean quotes.

    HEALTHY    -> DEGRADED     on a stale top-of-book
    HEALTHY    -> UNRELIABLE   on a crossed book (bid > ask)
    DEGRADED/UNRELIABLE -> RECOVERING  on the next clean, fresh quote
    RECOVERING -> HEALTHY      after `recovery_threshold` consecutive clean quotes
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BookConfidence(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNRELIABLE = "unreliable"
    RECOVERING = "recovering"


@dataclass(frozen=True)
class BookSnapshot:
    seq: int
    symbol: str
    timestamp_ns: int
    best_bid: int  # fixed-point
    best_ask: int  # fixed-point
    spread: int  # fixed-point (ask - bid)
    mid_price: int  # fixed-point
    quote_age_ns: int  # how long the current top-of-book has stood
    is_crossed: bool
    is_stale: bool
    confidence: BookConfidence


@dataclass(frozen=True)
class BookSummary:
    symbol: str
    quotes: int
    crossed_count: int
    stale_count: int
    final_confidence: BookConfidence
    min_spread: int | None
    max_spread: int | None
