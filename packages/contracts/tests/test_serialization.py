"""Serialization layout, canonical ordering, and checksum determinism.

These tests verify the byte layout *independently* (by rebuilding the expected
bytes with struct), not just by snapshotting the serializer against itself. The
snapshot/regression + cross-language contract lives in test_golden.py.
"""

from __future__ import annotations

import random
import struct

from quantstream_contracts.enums import Side
from quantstream_contracts.events import Quote, Trade
from quantstream_contracts.serialization import (
    canonical_sort,
    serialize_event,
    stream_checksum,
)


def test_trade_byte_layout_is_exact():
    trade = Trade(
        seq=7,
        timestamp_ns=1_700_000_000_000_000_000,
        symbol="AAPL",
        price=100_070_000_000,
        size=5_000_000_000,
        side=Side.SELL,
        trade_id="t42",
        venue="XNAS",
    )
    expected = (
        struct.pack("<B", 1)  # event_type = TRADE
        + struct.pack("<Q", 7)  # seq
        + struct.pack("<q", 1_700_000_000_000_000_000)  # timestamp_ns
        + struct.pack("<H", 4) + b"AAPL"  # symbol
        + struct.pack("<q", 100_070_000_000)  # price
        + struct.pack("<q", 5_000_000_000)  # size
        + struct.pack("<B", 2)  # side = SELL
        + struct.pack("<H", 3) + b"t42"  # trade_id
        + struct.pack("<H", 4) + b"XNAS"  # venue
    )
    assert serialize_event(trade) == expected


def test_unicode_symbol_uses_utf8_byte_length():
    # "€" is 3 UTF-8 bytes, so the uint16 length prefix must read 3, not 1.
    quote = Quote(
        seq=0,
        timestamp_ns=1,
        symbol="€",
        bid_price=1,
        bid_size=1,
        ask_price=2,
        ask_size=1,
        venue="",
    )
    raw = serialize_event(quote)
    # header: uint8 + uint64 + int64 = 17 bytes, then uint16 length prefix
    length = struct.unpack("<H", raw[17:19])[0]
    assert length == 3


def _trades(n: int) -> list[Trade]:
    return [
        Trade(
            seq=i,
            timestamp_ns=1_000 + (i % 3),  # deliberate timestamp collisions
            symbol="AAPL",
            price=100_000_000_000 + i,
            size=1_000_000_000,
            side=Side.BUY,
            trade_id=f"t{i}",
            venue="XNAS",
        )
        for i in range(n)
    ]


def test_checksum_is_deterministic_across_calls():
    events = _trades(50)
    assert stream_checksum(events) == stream_checksum(events)


def test_checksum_is_independent_of_input_order():
    events = _trades(50)
    shuffled = events[:]
    random.Random(1234).shuffle(shuffled)
    assert stream_checksum(shuffled) == stream_checksum(events)


def test_canonical_order_breaks_timestamp_ties_by_seq():
    events = _trades(20)
    ordered = canonical_sort(events)
    keys = [(e.timestamp_ns, e.seq) for e in ordered]
    assert keys == sorted(keys)
    # Within one timestamp, seq is strictly increasing.
    by_ts: dict[int, list[int]] = {}
    for e in ordered:
        by_ts.setdefault(e.timestamp_ns, []).append(e.seq)
    for seqs in by_ts.values():
        assert seqs == sorted(seqs)


def test_checksum_changes_when_a_field_changes():
    events = _trades(10)
    baseline = stream_checksum(events)
    mutated = events[:]
    mutated[3] = Trade(
        seq=events[3].seq,
        timestamp_ns=events[3].timestamp_ns,
        symbol=events[3].symbol,
        price=events[3].price + 1,  # one nano-unit difference
        size=events[3].size,
        side=events[3].side,
        trade_id=events[3].trade_id,
        venue=events[3].venue,
    )
    assert stream_checksum(mutated) != baseline


def test_assume_sorted_matches_pre_sorted_input():
    events = _trades(30)
    ordered = canonical_sort(events)
    assert stream_checksum(ordered, assume_sorted=True) == stream_checksum(events)
