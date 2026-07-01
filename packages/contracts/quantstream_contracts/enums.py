"""Canonical enumerations, encoded as small fixed integers on the wire.

Integer values are part of the serialization contract: the C++ replay engine must
use the identical numbers. Never renumber an existing member; only append.
"""

from __future__ import annotations

from enum import IntEnum


class EventType(IntEnum):
    TRADE = 1
    QUOTE = 2
    OHLCV = 3
    L2_UPDATE = 4


class Side(IntEnum):
    UNKNOWN = 0
    BUY = 1
    SELL = 2


class BookAction(IntEnum):
    UNKNOWN = 0
    ADD = 1
    UPDATE = 2
    DELETE = 3
