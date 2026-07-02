"""L2 reconstruction: depth, sequence gaps, crossed books, confidence, sample."""

from __future__ import annotations

from decimal import Decimal

from quantstream_contracts.enums import BookAction, Side
from quantstream_contracts.events import L2Update
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed

from quantstream_orderbook import (
    L2_SAMPLE_SYMBOL,
    BookConfidence,
    L2Book,
    L2Config,
    reconstruct_l2,
    sample_l2_updates,
)


def u(seq, seqnum, side, action, price, size, *, symbol="X"):
    return L2Update(
        seq=seq,
        timestamp_ns=seq,
        symbol=symbol,
        side=side,
        price=price_to_fixed(price),
        size=size_to_fixed(size),
        action=action,
        level=0,
        sequence_number=seqnum,
        venue="V",
    )


def test_adds_build_depth_and_top_of_book():
    book = L2Book("X", L2Config())
    book.apply(u(0, 1, Side.BUY, BookAction.ADD, "100.00", "10"))
    snap = book.apply(u(1, 2, Side.SELL, BookAction.ADD, "100.05", "6"))
    assert snap.best_bid == price_to_fixed("100.00")
    assert snap.best_ask == price_to_fixed("100.05")
    assert snap.bid_depth == size_to_fixed("10")
    assert snap.ask_depth == size_to_fixed("6")
    assert not snap.is_crossed


def test_delete_removes_level():
    book = L2Book("X", L2Config())
    book.apply(u(0, 1, Side.BUY, BookAction.ADD, "100.00", "10"))
    snap = book.apply(u(1, 2, Side.BUY, BookAction.DELETE, "100.00", "0"))
    assert snap.best_bid is None
    assert snap.bid_depth == 0


def test_sequence_gap_detected():
    book = L2Book("X", L2Config())
    book.apply(u(0, 100, Side.BUY, BookAction.ADD, "100.00", "10"))
    snap = book.apply(u(1, 105, Side.SELL, BookAction.ADD, "100.05", "10"))  # expected 101
    assert snap.sequence_gap
    assert snap.missing == 4
    assert snap.confidence == BookConfidence.DEGRADED


def test_no_gap_on_consecutive():
    book = L2Book("X", L2Config())
    book.apply(u(0, 100, Side.BUY, BookAction.ADD, "100.00", "10"))
    snap = book.apply(u(1, 101, Side.SELL, BookAction.ADD, "100.05", "10"))
    assert not snap.sequence_gap
    assert snap.confidence == BookConfidence.HEALTHY


def test_crossed_book_is_unreliable():
    book = L2Book("X", L2Config())
    book.apply(u(0, 1, Side.SELL, BookAction.ADD, "100.05", "10"))
    snap = book.apply(u(1, 2, Side.BUY, BookAction.ADD, "100.10", "10"))  # bid > ask
    assert snap.is_crossed
    assert snap.confidence == BookConfidence.UNRELIABLE


def test_depth_imbalance_sign():
    book = L2Book("X", L2Config())
    book.apply(u(0, 1, Side.BUY, BookAction.ADD, "100.00", "30"))
    snap = book.apply(u(1, 2, Side.SELL, BookAction.ADD, "100.05", "10"))
    # more bid depth -> positive imbalance = (30-10)/40 = 0.5
    assert snap.depth_imbalance == Decimal("0.5")


def test_reconstruct_ignores_non_l2():
    from quantstream_contracts.enums import Side as S
    from quantstream_contracts.events import Trade

    trade = Trade(0, 0, "X", price_to_fixed("100"), size_to_fixed("1"), S.BUY, "t", "V")
    snaps, summaries = reconstruct_l2([trade])
    assert snaps == [] and summaries == {}


def test_sample_hits_all_states():
    snaps, summaries = reconstruct_l2(sample_l2_updates())
    seen = {s.confidence for s in snaps}
    assert seen == {
        BookConfidence.HEALTHY,
        BookConfidence.DEGRADED,
        BookConfidence.UNRELIABLE,
        BookConfidence.RECOVERING,
    }
    s = summaries[L2_SAMPLE_SYMBOL]
    assert s.sequence_gap_count == 1
    assert s.total_missing == 1
    assert s.crossed_count == 1
    assert s.final_confidence == BookConfidence.HEALTHY


def test_sample_is_deterministic():
    a, _ = reconstruct_l2(sample_l2_updates())
    b, _ = reconstruct_l2(sample_l2_updates())
    assert [s.confidence for s in a] == [s.confidence for s in b]


def test_incremental_best_and_depth_match_bruteforce():
    # The O(1) incremental best/depth tracking must equal a full recompute after a
    # random mix of adds, updates, and deletes (including deleting the best level).
    import random

    from quantstream_contracts.enums import BookAction, Side

    rng = random.Random(2024)
    book = L2Book("X", L2Config())
    live: dict[tuple[int, int], int] = {}  # (side, price) -> size
    prices = [price_to_fixed(str(100 + i)) for i in range(8)]
    for seq in range(300):
        side = rng.choice([Side.BUY, Side.SELL])
        price = rng.choice(prices)
        if rng.random() < 0.3 and (side.value, price) in live:
            action, size = BookAction.DELETE, 0
        else:
            action, size = BookAction.ADD, rng.randint(1, 5) * 1_000_000_000
        snap = book.apply(
            L2Update(seq, seq, "X", side, price, size, action, 0, seq + 1, "V")
        )
        # brute-force truth
        if action == BookAction.DELETE or size <= 0:
            live.pop((side.value, price), None)
        else:
            live[(side.value, price)] = size
        bids = [p for (s, p), _ in live.items() if s == Side.BUY.value]
        asks = [p for (s, p), _ in live.items() if s == Side.SELL.value]
        assert snap.best_bid == (max(bids) if bids else None)
        assert snap.best_ask == (min(asks) if asks else None)
        assert snap.bid_depth == sum(v for (s, _), v in live.items() if s == Side.BUY.value)
        assert snap.ask_depth == sum(v for (s, _), v in live.items() if s == Side.SELL.value)
