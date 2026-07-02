"""Deterministic field parsers.

Timestamps become int64 nanoseconds; sides become the canonical Side enum. All
parsing is exact (no float): ISO timestamps are converted via timedelta components,
never via a float epoch, so the same input always yields the same nanoseconds.
"""

from __future__ import annotations

from datetime import datetime, timezone

from quantstream_contracts.enums import Side

from .mapping import TimestampUnit

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

_NUMERIC_FACTOR = {
    TimestampUnit.NS: 1,
    TimestampUnit.US: 1_000,
    TimestampUnit.MS: 1_000_000,
    TimestampUnit.S: 1_000_000_000,
}

_BUY = {"buy", "b", "bid", "1", "+1", "buyer"}
_SELL = {"sell", "s", "ask", "-1", "2", "seller"}


def parse_timestamp(value: str, unit: TimestampUnit) -> int:
    """Parse a timestamp string to int64 nanoseconds since the Unix epoch."""
    text = value.strip()
    if not text:
        raise ValueError("empty timestamp")

    if unit == TimestampUnit.ISO:
        # Python < 3.11 rejects the 'Z' suffix; market feeds stamp UTC as '...Z'.
        if text[-1:] in ("Z", "z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = dt - _EPOCH
        return (
            (delta.days * 86_400 + delta.seconds) * 1_000_000_000
            + delta.microseconds * 1_000
        )

    return int(text) * _NUMERIC_FACTOR[unit]


def parse_side(value: str) -> Side:
    """Parse a side string. Unknown/ambiguous values become Side.UNKNOWN."""
    text = value.strip().lower()
    if text in _BUY:
        return Side.BUY
    if text in _SELL:
        return Side.SELL
    return Side.UNKNOWN
