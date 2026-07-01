"""Canonical byte-stable serialization and the deterministic stream checksum.

This is the wire/format contract the C++ replay engine must reproduce byte-for-byte.
Everything here is chosen for cross-language, cross-platform determinism:

  * little-endian, fixed-width integer encoding (no native-endianness surprises)
  * strings length-prefixed with a uint16 then raw UTF-8 bytes
  * a total event order of (timestamp_ns, seq) applied before hashing, so two
    events sharing a timestamp never reorder between runs or between languages
  * BLAKE2b-256 over the concatenated records as the replay checksum

Record layout (all integers little-endian):

    common header
      event_type    : uint8
      seq           : uint64
      timestamp_ns  : int64
      symbol        : uint16 length + UTF-8 bytes

    TRADE       price int64 | size int64 | side uint8 | trade_id str | venue str
    QUOTE       bid_price int64 | bid_size int64 | ask_price int64 | ask_size int64
                | venue str
    OHLCV       open int64 | high int64 | low int64 | close int64 | volume int64
                | venue str
    L2_UPDATE   side uint8 | price int64 | size int64 | action uint8 | level int32
                | sequence_number uint64 | venue str

`str` above means: uint16 byte-length, then UTF-8 bytes.
"""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Iterable

from .enums import EventType
from .events import OHLCV, Event, L2Update, Quote, Trade

_U8 = struct.Struct("<B")
_U16 = struct.Struct("<H")
_I32 = struct.Struct("<i")
_U64 = struct.Struct("<Q")
_I64 = struct.Struct("<q")

CHECKSUM_DIGEST_SIZE = 32


def _pack_str(value: str) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) > 0xFFFF:
        raise ValueError(f"string too long to serialize: {len(raw)} bytes")
    return _U16.pack(len(raw)) + raw


def _pack_header(event: Event) -> bytes:
    return (
        _U8.pack(event.event_type)
        + _U64.pack(event.seq)
        + _I64.pack(event.timestamp_ns)
        + _pack_str(event.symbol)
    )


def serialize_event(event: Event) -> bytes:
    """Serialize a single event to its canonical byte record."""
    et = event.event_type
    if et == EventType.TRADE:
        assert isinstance(event, Trade)
        body = (
            _I64.pack(event.price)
            + _I64.pack(event.size)
            + _U8.pack(event.side)
            + _pack_str(event.trade_id)
            + _pack_str(event.venue)
        )
    elif et == EventType.QUOTE:
        assert isinstance(event, Quote)
        body = (
            _I64.pack(event.bid_price)
            + _I64.pack(event.bid_size)
            + _I64.pack(event.ask_price)
            + _I64.pack(event.ask_size)
            + _pack_str(event.venue)
        )
    elif et == EventType.OHLCV:
        assert isinstance(event, OHLCV)
        body = (
            _I64.pack(event.open)
            + _I64.pack(event.high)
            + _I64.pack(event.low)
            + _I64.pack(event.close)
            + _I64.pack(event.volume)
            + _pack_str(event.venue)
        )
    elif et == EventType.L2_UPDATE:
        assert isinstance(event, L2Update)
        body = (
            _U8.pack(event.side)
            + _I64.pack(event.price)
            + _I64.pack(event.size)
            + _U8.pack(event.action)
            + _I32.pack(event.level)
            + _U64.pack(event.sequence_number)
            + _pack_str(event.venue)
        )
    else:  # pragma: no cover - guarded by EventType enum
        raise TypeError(f"cannot serialize unknown event type: {et!r}")

    return _pack_header(event) + body


def canonical_key(event: Event) -> tuple[int, int]:
    """The system-wide total order: (timestamp_ns, seq)."""
    return (event.timestamp_ns, event.seq)


def canonical_sort(events: Iterable[Event]) -> list[Event]:
    """Return events in canonical order. Stable and deterministic."""
    return sorted(events, key=canonical_key)


def serialize_stream(events: Iterable[Event], *, assume_sorted: bool = False) -> bytes:
    """Serialize an event stream to its canonical bytes.

    Sorts into canonical order first unless the caller guarantees the input is
    already sorted (`assume_sorted=True`), which the replay engine can assert.
    """
    ordered = list(events) if assume_sorted else canonical_sort(events)
    return b"".join(serialize_event(e) for e in ordered)


def stream_checksum(events: Iterable[Event], *, assume_sorted: bool = False) -> str:
    """BLAKE2b-256 hex digest over the canonical serialized stream.

    This is the deterministic replay checksum. Same events (in any input order)
    -> same checksum, on any platform, in any language that reproduces the byte
    layout above.
    """
    ordered = list(events) if assume_sorted else canonical_sort(events)
    digest = hashlib.blake2b(digest_size=CHECKSUM_DIGEST_SIZE)
    for event in ordered:
        digest.update(serialize_event(event))
    return digest.hexdigest()
