"""Canonical typed market-data events.

These are the normalized events the whole pipeline agrees on. Raw file fields
must never leak past normalization: after this boundary everything speaks Trade /
Quote / OHLCV / L2Update, with prices and sizes already in fixed-point (see
fixed_point.py).

Design choices:

  * Events are frozen dataclasses: they are immutable facts, safe to hash, cache,
    and share across the raw and clean pipeline runs without defensive copying.
  * price / size fields are already fixed-point int64. Conversion from decimal
    strings happens once, at the normalization layer, via fixed_point.*_to_fixed.
    Keeping events integer-only is what makes the serialized stream deterministic.
  * `seq` is the source row index. It is the deterministic tie-breaker for events
    that share a timestamp, so ordering never depends on dict/hash iteration or
    the language doing the sort.

    Total order everywhere in the system: (timestamp_ns, seq).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .enums import BookAction, EventType, Side
from .fixed_point import INT64_MAX, INT64_MIN

_UINT64_MAX = 2**64 - 1
_INT32_MIN = -(2**31)
_INT32_MAX = 2**31 - 1
_MAX_STR_BYTES = 0xFFFF  # uint16 length prefix on the wire


def _check_int64(name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if not (INT64_MIN <= value <= INT64_MAX):
        raise ValueError(f"{name} out of int64 range: {value}")


def _check_uint64(name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if not (0 <= value <= _UINT64_MAX):
        raise ValueError(f"{name} out of uint64 range: {value}")


def _check_int32(name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if not (_INT32_MIN <= value <= _INT32_MAX):
        raise ValueError(f"{name} out of int32 range: {value}")


def _check_str(name: str, value: str, *, allow_empty: bool) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a str, got {type(value).__name__}")
    if not allow_empty and value == "":
        raise ValueError(f"{name} must not be empty")
    if len(value.encode("utf-8")) > _MAX_STR_BYTES:
        raise ValueError(f"{name} exceeds {_MAX_STR_BYTES} UTF-8 bytes")


def _validate_common(seq: int, timestamp_ns: int, symbol: str) -> None:
    _check_uint64("seq", seq)
    _check_int64("timestamp_ns", timestamp_ns)
    _check_str("symbol", symbol, allow_empty=False)


@dataclass(frozen=True, slots=True)
class Trade:
    seq: int
    timestamp_ns: int
    symbol: str
    price: int  # fixed-point, PRICE_SCALE
    size: int  # fixed-point, SIZE_SCALE
    side: Side
    trade_id: str
    venue: str
    event_type: ClassVar[EventType] = EventType.TRADE

    def __post_init__(self) -> None:
        _validate_common(self.seq, self.timestamp_ns, self.symbol)
        _check_int64("price", self.price)
        _check_int64("size", self.size)
        object.__setattr__(self, "side", Side(self.side))
        _check_str("trade_id", self.trade_id, allow_empty=True)
        _check_str("venue", self.venue, allow_empty=True)


@dataclass(frozen=True, slots=True)
class Quote:
    seq: int
    timestamp_ns: int
    symbol: str
    bid_price: int
    bid_size: int
    ask_price: int
    ask_size: int
    venue: str
    event_type: ClassVar[EventType] = EventType.QUOTE

    def __post_init__(self) -> None:
        _validate_common(self.seq, self.timestamp_ns, self.symbol)
        _check_int64("bid_price", self.bid_price)
        _check_int64("bid_size", self.bid_size)
        _check_int64("ask_price", self.ask_price)
        _check_int64("ask_size", self.ask_size)
        _check_str("venue", self.venue, allow_empty=True)


@dataclass(frozen=True, slots=True)
class OHLCV:
    seq: int
    timestamp_ns: int
    symbol: str
    open: int
    high: int
    low: int
    close: int
    volume: int
    venue: str
    event_type: ClassVar[EventType] = EventType.OHLCV

    def __post_init__(self) -> None:
        _validate_common(self.seq, self.timestamp_ns, self.symbol)
        for name in ("open", "high", "low", "close"):
            _check_int64(name, getattr(self, name))
        _check_int64("volume", self.volume)
        _check_str("venue", self.venue, allow_empty=True)


@dataclass(frozen=True, slots=True)
class L2Update:
    seq: int
    timestamp_ns: int
    symbol: str
    side: Side
    price: int
    size: int
    action: BookAction
    level: int
    sequence_number: int
    venue: str
    event_type: ClassVar[EventType] = EventType.L2_UPDATE

    def __post_init__(self) -> None:
        _validate_common(self.seq, self.timestamp_ns, self.symbol)
        object.__setattr__(self, "side", Side(self.side))
        _check_int64("price", self.price)
        _check_int64("size", self.size)
        object.__setattr__(self, "action", BookAction(self.action))
        _check_int32("level", self.level)
        _check_uint64("sequence_number", self.sequence_number)
        _check_str("venue", self.venue, allow_empty=True)


# Any canonical event. Kept as a tuple so serialization can dispatch on type.
Event = Trade | Quote | OHLCV | L2Update
