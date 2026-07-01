"""Corruption injector: determinism and per-defect injection behavior."""

from __future__ import annotations

from quantstream_contracts.events import Trade

from quantstream_validation import Defect
from quantstream_validation.injector import CorruptionConfig, corrupt

from ._helpers import clean_quotes, clean_trades


def test_zero_config_is_a_no_op():
    events = clean_trades(20)
    result = corrupt(events, CorruptionConfig())
    assert result.events == events
    assert result.truth == {}


def test_same_seed_is_deterministic():
    events = clean_trades(50)
    cfg = CorruptionConfig(seed=7, invalid_price_rate=0.3, duplicate_rate=0.2)
    a = corrupt(events, cfg)
    b = corrupt(events, cfg)
    assert a.events == b.events
    assert a.truth == b.truth


def test_different_seed_changes_result():
    events = clean_trades(50)
    a = corrupt(events, CorruptionConfig(seed=1, invalid_price_rate=0.3))
    b = corrupt(events, CorruptionConfig(seed=2, invalid_price_rate=0.3))
    assert a.truth != b.truth


def test_invalid_price_rate_one_hits_every_trade():
    events = clean_trades(10)
    result = corrupt(events, CorruptionConfig(seed=0, invalid_price_rate=1.0))
    corrupted = [e for e in result.events if isinstance(e, Trade) and e.price == 0]
    assert len(corrupted) == 10
    assert all(Defect.INVALID_PRICE in defects for defects in result.truth.values())


def test_duplicate_appends_new_events():
    events = clean_trades(10)
    result = corrupt(events, CorruptionConfig(seed=0, duplicate_rate=1.0))
    assert len(result.events) == 20  # every trade duplicated
    dup_seqs = [s for s, d in result.truth.items() if Defect.DUPLICATE in d]
    assert len(dup_seqs) == 10
    # duplicate seqs are new, above the originals
    assert min(dup_seqs) >= 10


def test_crossed_injection_makes_bid_exceed_ask():
    from quantstream_contracts.events import Quote

    events = clean_quotes(10)
    result = corrupt(events, CorruptionConfig(seed=0, crossed_rate=1.0))
    crossed = [e for e in result.events if isinstance(e, Quote) and e.bid_price > e.ask_price]
    assert len(crossed) == 10
