"""The bundled CSV round-trips to the same events, and --csv reproduces the demo."""

from __future__ import annotations

from quantstream_contracts.serialization import stream_checksum
from quantstream_schema import load_csv_path

from quantstream_demo.cli import run_demo
from quantstream_demo.sample_data import sample_csv_path, sample_events


def test_sample_csv_roundtrips_to_bundled_events():
    _schema, result = load_csv_path(sample_csv_path())
    assert not result.errors
    assert len(result.events) == len(sample_events())
    # Loading the CSV yields byte-identical events (same replay checksum).
    assert stream_checksum(result.events) == stream_checksum(sample_events())


def test_demo_from_csv_matches_bundled_run():
    bundled = run_demo()
    from_csv = run_demo(csv_path=sample_csv_path())
    assert from_csv.raw_checksum == bundled.raw_checksum
    assert from_csv.clean_checksum == bundled.clean_checksum
    assert from_csv.mirage.mirage_score == bundled.mirage.mirage_score
    assert from_csv.load_errors == 0
