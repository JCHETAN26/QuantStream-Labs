"""L2 order-book reconstruction from order-book updates.

Maintains full price-level depth per symbol by applying add/update/delete events,
tracks best bid/ask, total depth and depth imbalance, and detects sequence gaps
(missing updates) and crossed books. Sequence gaps degrade book confidence; a
crossed book makes it unreliable. Reuses the shared confidence state machine.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from quantstream_contracts.enums import BookAction, Side
from quantstream_contracts.events import Event, L2Update
from quantstream_contracts.serialization import canonical_key

from .book import DEFAULT_RECOVERY_THRESHOLD
from .confidence import ConfidenceTracker
from .state import BookConfidence


@dataclass(frozen=True)
class L2Config:
    recovery_threshold: int = DEFAULT_RECOVERY_THRESHOLD


@dataclass(frozen=True)
class L2Snapshot:
    seq: int
    symbol: str
    timestamp_ns: int
    best_bid: int | None
    best_ask: int | None
    bid_depth: int
    ask_depth: int
    depth_imbalance: Decimal  # (bid_depth - ask_depth) / (bid_depth + ask_depth)
    sequence_gap: bool
    missing: int
    is_crossed: bool
    confidence: BookConfidence


@dataclass(frozen=True)
class L2Summary:
    symbol: str
    updates: int
    sequence_gap_count: int
    total_missing: int
    crossed_count: int
    final_confidence: BookConfidence
    bid_levels: int
    ask_levels: int


class L2Book:
    """Per-symbol price-level book."""

    def __init__(self, symbol: str, config: L2Config) -> None:
        self.symbol = symbol
        self._conf = ConfidenceTracker(config.recovery_threshold)
        self._bids: dict[int, int] = {}  # price -> size
        self._asks: dict[int, int] = {}
        self._expected_seq: int | None = None
        self.updates = 0
        self.sequence_gap_count = 0
        self.total_missing = 0
        self.crossed_count = 0

    @property
    def confidence(self) -> BookConfidence:
        return self._conf.confidence

    def apply(self, update: L2Update) -> L2Snapshot:
        gap, missing = self._check_sequence(update.sequence_number)
        self._expected_seq = update.sequence_number + 1

        levels = self._bids if update.side == Side.BUY else self._asks
        if update.action == BookAction.DELETE or update.size <= 0:
            levels.pop(update.price, None)
        else:  # ADD or UPDATE both set the level
            levels[update.price] = update.size

        best_bid = max(self._bids) if self._bids else None
        best_ask = min(self._asks) if self._asks else None
        is_crossed = (
            best_bid is not None and best_ask is not None and best_bid > best_ask
        )
        bid_depth = sum(self._bids.values())
        ask_depth = sum(self._asks.values())
        total = bid_depth + ask_depth
        imbalance = (
            Decimal(bid_depth - ask_depth) / Decimal(total) if total > 0 else Decimal(0)
        )

        self._conf.observe(severe=is_crossed, mild=gap)

        self.updates += 1
        if gap:
            self.sequence_gap_count += 1
            self.total_missing += missing
        if is_crossed:
            self.crossed_count += 1

        return L2Snapshot(
            seq=update.seq,
            symbol=self.symbol,
            timestamp_ns=update.timestamp_ns,
            best_bid=best_bid,
            best_ask=best_ask,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            depth_imbalance=imbalance,
            sequence_gap=gap,
            missing=missing,
            is_crossed=is_crossed,
            confidence=self.confidence,
        )

    def _check_sequence(self, sequence_number: int) -> tuple[bool, int]:
        if self._expected_seq is None or sequence_number == self._expected_seq:
            return False, 0
        missing = (
            sequence_number - self._expected_seq
            if sequence_number > self._expected_seq
            else 0  # regression / duplicate: a gap, but no forward-missing count
        )
        return True, missing

    def summary(self) -> L2Summary:
        return L2Summary(
            symbol=self.symbol,
            updates=self.updates,
            sequence_gap_count=self.sequence_gap_count,
            total_missing=self.total_missing,
            crossed_count=self.crossed_count,
            final_confidence=self.confidence,
            bid_levels=len(self._bids),
            ask_levels=len(self._asks),
        )


def reconstruct_l2(
    events: Iterable[Event], config: L2Config | None = None
) -> tuple[list[L2Snapshot], dict[str, L2Summary]]:
    """Reconstruct L2 depth for every symbol from L2Update events."""
    config = config or L2Config()
    updates = sorted(
        (e for e in events if isinstance(e, L2Update)), key=canonical_key
    )
    books: dict[str, L2Book] = {}
    snapshots: list[L2Snapshot] = []
    for update in updates:
        book = books.get(update.symbol)
        if book is None:
            book = L2Book(update.symbol, config)
            books[update.symbol] = book
        snapshots.append(book.apply(update))
    return snapshots, {symbol: book.summary() for symbol, book in books.items()}
