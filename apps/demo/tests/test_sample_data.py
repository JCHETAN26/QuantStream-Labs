"""The bundled sample dataset is deterministic and well-formed."""

from __future__ import annotations

from quantstream_contracts.serialization import stream_checksum

from quantstream_demo.sample_data import injected_spike_count, sample_events


def test_sample_is_deterministic():
    assert stream_checksum(sample_events()) == stream_checksum(sample_events())


def test_sample_has_expected_shape():
    events = sample_events()
    assert len(events) == 400
    assert all(e.symbol == "ACME" for e in events)
    assert injected_spike_count() > 0


def test_timestamps_are_monotonic():
    events = sample_events()
    ts = [e.timestamp_ns for e in events]
    assert ts == sorted(ts)
