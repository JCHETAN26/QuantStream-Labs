"""Timestamp and side parsing."""

from __future__ import annotations

import pytest
from quantstream_contracts.enums import Side

from quantstream_schema import TimestampUnit, parse_side, parse_timestamp


def test_numeric_units():
    assert parse_timestamp("5", TimestampUnit.NS) == 5
    assert parse_timestamp("5", TimestampUnit.US) == 5_000
    assert parse_timestamp("5", TimestampUnit.MS) == 5_000_000
    assert parse_timestamp("5", TimestampUnit.S) == 5_000_000_000


def test_iso_seconds():
    assert parse_timestamp("1970-01-01T00:00:01+00:00", TimestampUnit.ISO) == 1_000_000_000


def test_iso_microseconds():
    got = parse_timestamp("1970-01-01T00:00:00.000001+00:00", TimestampUnit.ISO)
    assert got == 1_000


def test_iso_naive_assumed_utc():
    assert parse_timestamp("1970-01-01T00:00:00", TimestampUnit.ISO) == 0


def test_empty_timestamp_rejected():
    with pytest.raises(ValueError):
        parse_timestamp("  ", TimestampUnit.NS)


def test_sides():
    assert parse_side("buy") == Side.BUY
    assert parse_side("B") == Side.BUY
    assert parse_side("1") == Side.BUY
    assert parse_side("sell") == Side.SELL
    assert parse_side("S") == Side.SELL
    assert parse_side("-1") == Side.SELL
    assert parse_side("whatever") == Side.UNKNOWN
