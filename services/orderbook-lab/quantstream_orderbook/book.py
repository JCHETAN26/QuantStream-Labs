"""L1 order-book reconstruction from quotes.

Processes quotes per symbol in canonical order, tracking top-of-book, spread, mid,
and quote age, detecting crossed and stale books, and running the confidence state
machine (see state.py). Deterministic: same quotes in, same snapshots out.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from quantstream_contracts.events import Event, Quote
from quantstream_contracts.serialization import canonical_key

from .state import BookConfidence, BookSnapshot, BookSummary

DEFAULT_STALE_NS = 5_000_000_000  # 5s
DEFAULT_RECOVERY_THRESHOLD = 3  # clean quotes needed to return to HEALTHY


@dataclass(frozen=True)
class OrderBookConfig:
    stale_ns: int = DEFAULT_STALE_NS
    recovery_threshold: int = DEFAULT_RECOVERY_THRESHOLD


class OrderBook:
    """Per-symbol top-of-book state machine."""

    def __init__(self, symbol: str, config: OrderBookConfig) -> None:
        self.symbol = symbol
        self._config = config
        self.confidence = BookConfidence.HEALTHY
        self._run_key: tuple[int, int] | None = None
        self._run_start_ts: int = 0
        self._recovery_count = 0
        self.quotes = 0
        self.crossed_count = 0
        self.stale_count = 0
        self.min_spread: int | None = None
        self.max_spread: int | None = None

    def update(self, quote: Quote) -> BookSnapshot:
        bid, ask = quote.bid_price, quote.ask_price
        key = (bid, ask)
        if key != self._run_key:
            self._run_key = key
            self._run_start_ts = quote.timestamp_ns
        quote_age = quote.timestamp_ns - self._run_start_ts

        is_crossed = bid > ask
        is_stale = quote_age > self._config.stale_ns
        spread = ask - bid
        mid = (bid + ask) // 2

        self._advance_confidence(is_crossed, is_stale)

        self.quotes += 1
        if is_crossed:
            self.crossed_count += 1
        if is_stale:
            self.stale_count += 1
        self.min_spread = spread if self.min_spread is None else min(self.min_spread, spread)
        self.max_spread = spread if self.max_spread is None else max(self.max_spread, spread)

        return BookSnapshot(
            seq=quote.seq,
            symbol=self.symbol,
            timestamp_ns=quote.timestamp_ns,
            best_bid=bid,
            best_ask=ask,
            spread=spread,
            mid_price=mid,
            quote_age_ns=quote_age,
            is_crossed=is_crossed,
            is_stale=is_stale,
            confidence=self.confidence,
        )

    def _advance_confidence(self, is_crossed: bool, is_stale: bool) -> None:
        if is_crossed:
            self.confidence = BookConfidence.UNRELIABLE
            self._recovery_count = 0
        elif is_stale:
            if self.confidence in (BookConfidence.HEALTHY, BookConfidence.RECOVERING):
                self.confidence = BookConfidence.DEGRADED
            self._recovery_count = 0
        else:  # a clean, fresh quote
            if self.confidence in (BookConfidence.DEGRADED, BookConfidence.UNRELIABLE):
                self.confidence = BookConfidence.RECOVERING
                self._recovery_count = 1
            elif self.confidence == BookConfidence.RECOVERING:
                self._recovery_count += 1
            if (
                self.confidence == BookConfidence.RECOVERING
                and self._recovery_count >= self._config.recovery_threshold
            ):
                self.confidence = BookConfidence.HEALTHY
                self._recovery_count = 0

    def summary(self) -> BookSummary:
        return BookSummary(
            symbol=self.symbol,
            quotes=self.quotes,
            crossed_count=self.crossed_count,
            stale_count=self.stale_count,
            final_confidence=self.confidence,
            min_spread=self.min_spread,
            max_spread=self.max_spread,
        )


def reconstruct(
    events: Iterable[Event], config: OrderBookConfig | None = None
) -> tuple[list[BookSnapshot], dict[str, BookSummary]]:
    """Reconstruct top-of-book for every symbol. Returns per-quote snapshots (in
    canonical order) and a per-symbol summary."""
    config = config or OrderBookConfig()
    quotes = sorted(
        (e for e in events if isinstance(e, Quote)), key=canonical_key
    )
    books: dict[str, OrderBook] = {}
    snapshots: list[BookSnapshot] = []
    for quote in quotes:
        book = books.get(quote.symbol)
        if book is None:
            book = OrderBook(quote.symbol, config)
            books[quote.symbol] = book
        snapshots.append(book.update(quote))
    summaries = {symbol: book.summary() for symbol, book in books.items()}
    return snapshots, summaries
