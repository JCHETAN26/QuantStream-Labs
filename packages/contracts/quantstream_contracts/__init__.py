"""QuantStream Labs canonical event contracts.

The single source of truth for the normalized market-data events, their
fixed-point representation, and the deterministic byte-stable serialization that
backs the replay checksum. Every other service depends on this package; the C++
replay engine reproduces its serialization byte-for-byte.
"""

from __future__ import annotations

from .enums import BookAction, EventType, Side
from .events import OHLCV, Event, L2Update, Quote, Trade
from .fixed_point import (
    INT64_MAX,
    INT64_MIN,
    PRICE_SCALE,
    SIZE_SCALE,
    from_fixed,
    price_from_fixed,
    price_to_fixed,
    size_from_fixed,
    size_to_fixed,
    to_fixed,
)
from .serialization import (
    CHECKSUM_DIGEST_SIZE,
    canonical_key,
    canonical_sort,
    serialize_event,
    serialize_stream,
    stream_checksum,
)

__all__ = [
    "BookAction",
    "EventType",
    "Side",
    "Event",
    "Trade",
    "Quote",
    "OHLCV",
    "L2Update",
    "PRICE_SCALE",
    "SIZE_SCALE",
    "INT64_MIN",
    "INT64_MAX",
    "to_fixed",
    "from_fixed",
    "price_to_fixed",
    "size_to_fixed",
    "price_from_fixed",
    "size_from_fixed",
    "CHECKSUM_DIGEST_SIZE",
    "canonical_key",
    "canonical_sort",
    "serialize_event",
    "serialize_stream",
    "stream_checksum",
]
