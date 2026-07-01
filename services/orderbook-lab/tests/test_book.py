"""Top-of-book analytics: spread, mid, crossed, stale, quote age, multi-symbol."""

from __future__ import annotations

from quantstream_contracts.enums import Side
from quantstream_contracts.events import Trade
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed

from quantstream_orderbook import BookConfidence, OrderBook, OrderBookConfig, reconstruct

from ._helpers import q


def test_spread_and_mid():
    book = OrderBook("X", OrderBookConfig())
    snap = book.update(q(0, 0, "100.00", "100.02"))
    assert snap.best_bid == price_to_fixed("100.00")
    assert snap.best_ask == price_to_fixed("100.02")
    assert snap.spread == price_to_fixed("100.02") - price_to_fixed("100.00")
    assert snap.mid_price == (snap.best_bid + snap.best_ask) // 2
    assert not snap.is_crossed and not snap.is_stale
    assert snap.confidence == BookConfidence.HEALTHY


def test_crossed_detection():
    snap = OrderBook("X", OrderBookConfig()).update(q(0, 0, "100.05", "100.01"))
    assert snap.is_crossed
    assert snap.confidence == BookConfidence.UNRELIABLE


def test_stale_detection():
    book = OrderBook("X", OrderBookConfig(stale_ns=5_000_000_000))
    book.update(q(0, 0, "100.00", "100.02"))
    snap = book.update(q(1, 6_000_000_000, "100.00", "100.02"))  # same book, 6s later
    assert snap.quote_age_ns == 6_000_000_000
    assert snap.is_stale
    assert snap.confidence == BookConfidence.DEGRADED


def test_quote_age_resets_when_book_changes():
    book = OrderBook("X", OrderBookConfig())
    book.update(q(0, 0, "100.00", "100.02"))
    snap = book.update(q(1, 3_000_000_000, "100.01", "100.03"))  # changed -> fresh
    assert snap.quote_age_ns == 0


def test_multi_symbol_independent():
    events = [q(0, 0, "100.00", "100.02", symbol="A"),
              q(1, 0, "50.00", "49.00", symbol="B")]  # B is crossed
    _snaps, summaries = reconstruct(events)
    assert summaries["A"].final_confidence == BookConfidence.HEALTHY
    assert summaries["B"].final_confidence == BookConfidence.UNRELIABLE
    assert summaries["B"].crossed_count == 1


def test_reconstruct_ignores_non_quotes():
    trade = Trade(0, 0, "X", price_to_fixed("100"), size_to_fixed("1"),
                  Side.BUY, "t", "V")
    snaps, summaries = reconstruct([trade])
    assert snaps == []
    assert summaries == {}


def test_summary_tracks_spread_range():
    _snaps, summaries = reconstruct([
        q(0, 0, "100.00", "100.02"),
        q(1, 1, "100.00", "100.10"),
    ])
    s = summaries["X"]
    assert s.min_spread == price_to_fixed("0.02")
    assert s.max_spread == price_to_fixed("0.10")
    assert s.quotes == 2
