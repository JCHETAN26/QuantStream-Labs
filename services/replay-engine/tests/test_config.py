"""ReplayConfig: validation, filtering, and a stable, field-sensitive config hash."""

from __future__ import annotations

import pytest

from quantstream_replay import ReplayConfig

from ._helpers import trade


def test_defaults_accept_everything():
    config = ReplayConfig()
    assert config.accepts(trade(0, 100))


def test_config_hash_is_deterministic():
    a = ReplayConfig(speed=10, symbols=frozenset({"AAPL", "MSFT"}), start_ns=1)
    b = ReplayConfig(speed=10, symbols=frozenset({"MSFT", "AAPL"}), start_ns=1)
    # symbol set order must not matter (sorted in the hash).
    assert a.config_hash() == b.config_hash()


def test_config_hash_changes_with_each_field():
    base = ReplayConfig()
    variants = [
        ReplayConfig(speed=10),
        ReplayConfig(symbols=frozenset({"AAPL"})),
        ReplayConfig(start_ns=5),
        ReplayConfig(end_ns=5),
    ]
    hashes = {base.config_hash()} | {v.config_hash() for v in variants}
    assert len(hashes) == 5  # all distinct


def test_symbols_none_differs_from_empty_meaning():
    # None means "all"; a concrete set means "only these".
    assert ReplayConfig().config_hash() != ReplayConfig(
        symbols=frozenset({"AAPL"})
    ).config_hash()


def test_negative_speed_rejected():
    with pytest.raises(ValueError):
        ReplayConfig(speed=-1)


def test_start_after_end_rejected():
    with pytest.raises(ValueError):
        ReplayConfig(start_ns=10, end_ns=5)


def test_accepts_applies_all_filters():
    config = ReplayConfig(symbols=frozenset({"AAPL"}), start_ns=100, end_ns=300)
    assert config.accepts(trade(0, 200, symbol="AAPL"))
    assert not config.accepts(trade(1, 200, symbol="MSFT"))  # wrong symbol
    assert not config.accepts(trade(2, 50, symbol="AAPL"))  # before start
    assert not config.accepts(trade(3, 400, symbol="AAPL"))  # after end
