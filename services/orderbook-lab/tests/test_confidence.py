"""The book-confidence state machine transitions."""

from __future__ import annotations

from quantstream_orderbook import BookConfidence, OrderBook, OrderBookConfig

from ._helpers import q

_S = 1_000_000_000  # one second in ns


def test_recovery_to_healthy_after_threshold():
    book = OrderBook("X", OrderBookConfig(recovery_threshold=3))
    book.update(q(0, 0, "100.05", "100.01"))  # crossed -> UNRELIABLE
    assert book.confidence == BookConfidence.UNRELIABLE

    s1 = book.update(q(1, 1 * _S, "100.00", "100.02"))  # clean -> RECOVERING
    assert s1.confidence == BookConfidence.RECOVERING
    s2 = book.update(q(2, 2 * _S, "100.01", "100.03"))
    assert s2.confidence == BookConfidence.RECOVERING
    s3 = book.update(q(3, 3 * _S, "100.02", "100.04"))  # 3rd clean -> HEALTHY
    assert s3.confidence == BookConfidence.HEALTHY


def test_crossed_during_recovery_resets_to_unreliable():
    book = OrderBook("X", OrderBookConfig(recovery_threshold=3))
    book.update(q(0, 0, "100.05", "100.01"))       # UNRELIABLE
    book.update(q(1, 1 * _S, "100.00", "100.02"))  # RECOVERING
    s = book.update(q(2, 2 * _S, "100.09", "100.01"))  # crossed again
    assert s.confidence == BookConfidence.UNRELIABLE


def test_healthy_stays_healthy_on_clean_quotes():
    book = OrderBook("X", OrderBookConfig())
    for i in range(5):
        snap = book.update(q(i, i * _S, f"100.0{i}", f"100.1{i}"))
    assert snap.confidence == BookConfidence.HEALTHY


def test_stale_degrades_then_recovers():
    book = OrderBook("X", OrderBookConfig(stale_ns=5 * _S, recovery_threshold=1))
    book.update(q(0, 0, "100.00", "100.02"))
    s_stale = book.update(q(1, 6 * _S, "100.00", "100.02"))  # stale -> DEGRADED
    assert s_stale.confidence == BookConfidence.DEGRADED
    s_rec = book.update(q(2, 7 * _S, "100.10", "100.12"))  # fresh, threshold 1 -> HEALTHY
    assert s_rec.confidence == BookConfidence.HEALTHY
