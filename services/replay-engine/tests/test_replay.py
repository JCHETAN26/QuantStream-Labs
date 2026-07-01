"""Replay determinism, filtering, and the contracts-checksum anchor."""

from __future__ import annotations

import random

from quantstream_contracts.serialization import stream_checksum

from quantstream_replay import InMemorySink, ReplayConfig, replay

from ._helpers import mixed_stream, trade


def test_full_replay_matches_contracts_checksum():
    events = mixed_stream()
    result = replay(events)
    # The anchor: no filter -> identical to the contracts-level checksum. This is
    # exactly what the C++ engine must reproduce.
    assert result.checksum == stream_checksum(events)
    assert result.event_count == len(events)
    assert result.dropped_by_filter == 0
    assert result.first_timestamp_ns == 100
    assert result.last_timestamp_ns == 400


def test_checksum_is_deterministic():
    events = mixed_stream()
    a = replay(events)
    b = replay(events)
    assert a.checksum == b.checksum
    assert a.config_hash == b.config_hash


def test_checksum_is_independent_of_input_order():
    events = mixed_stream()
    shuffled = events[:]
    random.Random(99).shuffle(shuffled)
    assert replay(shuffled).checksum == replay(events).checksum


def test_symbol_filter():
    events = mixed_stream()
    config = ReplayConfig(symbols=frozenset({"AAPL"}))
    result = replay(events, config)
    aapl = [e for e in events if e.symbol == "AAPL"]
    assert result.event_count == len(aapl)
    assert result.dropped_by_filter == len(events) - len(aapl)
    assert result.checksum == stream_checksum(aapl)


def test_time_range_is_inclusive():
    events = mixed_stream()
    result = replay(events, ReplayConfig(start_ns=200, end_ns=300))
    kept = [e for e in events if 200 <= e.timestamp_ns <= 300]
    assert result.event_count == len(kept)
    assert result.checksum == stream_checksum(kept)


def test_sink_receives_events_in_canonical_order():
    events = mixed_stream()
    sink = InMemorySink()
    replay(events, sink=sink)
    keys = [(e.timestamp_ns, e.seq) for e in sink.events]
    assert keys == sorted(keys)
    assert len(sink.events) == len(events)


def test_empty_result_has_stable_checksum():
    events = [trade(0, 100, symbol="AAPL")]
    result = replay(events, ReplayConfig(symbols=frozenset({"NONE"})))
    assert result.event_count == 0
    assert result.first_timestamp_ns is None
    assert result.last_timestamp_ns is None
    assert result.checksum == stream_checksum([])


def test_no_sink_still_returns_checksum():
    # Sink is optional; replay is useful purely for its checksum + metadata.
    result = replay(mixed_stream(), sink=None)
    assert result.checksum
