"""Sink protocol and the in-memory reference sink."""

from __future__ import annotations

from quantstream_replay import InMemorySink
from quantstream_replay.sink import Sink

from ._helpers import trade


def test_in_memory_sink_collects_in_emit_order():
    sink = InMemorySink()
    events = [trade(0, 1), trade(1, 2), trade(2, 3)]
    for event in events:
        sink.emit(event)
    assert sink.events == events


def test_in_memory_sink_satisfies_protocol():
    assert isinstance(InMemorySink(), Sink)
