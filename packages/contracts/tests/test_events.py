"""Event construction and validation invariants."""

from __future__ import annotations

import dataclasses

import pytest

from quantstream_contracts.enums import BookAction, EventType, Side
from quantstream_contracts.events import OHLCV, L2Update, Quote, Trade


def make_trade(**overrides):
    base = dict(
        seq=0,
        timestamp_ns=1,
        symbol="AAPL",
        price=100_000_000_000,
        size=10_000_000_000,
        side=Side.BUY,
        trade_id="t1",
        venue="XNAS",
    )
    base.update(overrides)
    return Trade(**base)


def test_valid_trade():
    trade = make_trade()
    assert trade.event_type == EventType.TRADE
    assert trade.side is Side.BUY


def test_side_coerced_from_int():
    trade = make_trade(side=2)
    assert trade.side is Side.SELL


def test_invalid_side_rejected():
    with pytest.raises(ValueError):
        make_trade(side=99)


def test_empty_symbol_rejected():
    with pytest.raises(ValueError):
        make_trade(symbol="")


def test_negative_seq_rejected():
    with pytest.raises(ValueError):
        make_trade(seq=-1)


def test_price_int64_overflow_rejected():
    with pytest.raises(ValueError):
        make_trade(price=2**63)


def test_float_price_rejected():
    with pytest.raises(TypeError):
        make_trade(price=100.5)


def test_empty_venue_allowed():
    trade = make_trade(venue="")
    assert trade.venue == ""


def test_events_are_frozen():
    trade = make_trade()
    with pytest.raises(dataclasses.FrozenInstanceError):
        trade.price = 1  # type: ignore[misc]


def test_events_are_hashable():
    assert len({make_trade(), make_trade()}) == 1


def test_valid_quote():
    quote = Quote(
        seq=1,
        timestamp_ns=5,
        symbol="MSFT",
        bid_price=100,
        bid_size=1,
        ask_price=101,
        ask_size=2,
        venue="XNAS",
    )
    assert quote.event_type == EventType.QUOTE


def test_valid_ohlcv():
    bar = OHLCV(
        seq=2,
        timestamp_ns=9,
        symbol="SPY",
        open=1,
        high=4,
        low=1,
        close=3,
        volume=1000,
        venue="",
    )
    assert bar.event_type == EventType.OHLCV


def test_valid_l2_update():
    update = L2Update(
        seq=3,
        timestamp_ns=11,
        symbol="AAPL",
        side=Side.BUY,
        price=100,
        size=5,
        action=BookAction.ADD,
        level=0,
        sequence_number=781_244,
        venue="XNAS",
    )
    assert update.event_type == EventType.L2_UPDATE
    assert update.action is BookAction.ADD


def test_l2_level_int32_overflow_rejected():
    with pytest.raises(ValueError):
        L2Update(
            seq=3,
            timestamp_ns=11,
            symbol="AAPL",
            side=Side.BUY,
            price=100,
            size=5,
            action=BookAction.ADD,
            level=2**31,
            sequence_number=1,
            venue="",
        )
