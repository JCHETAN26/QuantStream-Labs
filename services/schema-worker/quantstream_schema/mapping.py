"""Column-mapping and schema-inference result types.

A ColumnMapping says which source CSV column feeds each canonical field. An
InferredSchema is a best-guess ColumnMapping plus the event type, a confidence
score, and notes explaining what was and wasn't matched.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from quantstream_contracts.enums import EventType


class TimestampUnit(str, Enum):
    NS = "ns"
    US = "us"
    MS = "ms"
    S = "s"
    ISO = "iso"


@dataclass(frozen=True)
class ColumnMapping:
    timestamp: str
    symbol: str
    timestamp_unit: TimestampUnit = TimestampUnit.NS
    # Trade fields
    price: str | None = None
    size: str | None = None
    side: str | None = None
    trade_id: str | None = None
    venue: str | None = None
    # Quote fields
    bid_price: str | None = None
    bid_size: str | None = None
    ask_price: str | None = None
    ask_size: str | None = None


@dataclass(frozen=True)
class InferredSchema:
    event_type: EventType
    mapping: ColumnMapping
    confidence: float
    unmatched_columns: tuple[str, ...]
    notes: tuple[str, ...]
