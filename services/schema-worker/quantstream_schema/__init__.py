"""QuantStream Labs schema worker.

Infers the event type and column mapping from a CSV's headers and sample rows, then
loads the file into canonical events, turning malformed rows into structured errors
rather than crashes.
"""

from __future__ import annotations

from .infer import infer_schema
from .loader import (
    LoadResult,
    RowError,
    load_csv_path,
    load_csv_text,
    load_events,
)
from .mapping import ColumnMapping, InferredSchema, TimestampUnit
from .parsing import parse_side, parse_timestamp

__all__ = [
    "infer_schema",
    "ColumnMapping",
    "InferredSchema",
    "TimestampUnit",
    "parse_timestamp",
    "parse_side",
    "load_events",
    "load_csv_text",
    "load_csv_path",
    "LoadResult",
    "RowError",
]
