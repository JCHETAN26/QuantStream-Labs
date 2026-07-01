"""Individual validation checks.

Each check is a pure function: it takes the event list and returns the set of
``seq`` values it flags. Keeping them independent and side-effect-free makes every
check trivially unit-testable (true path and false path) and lets the engine run
them in any order. The engine (engine.py) wires each check to its Defect, severity,
and impact text.

Ordering-sensitive checks (out-of-order, stale, bad-tick) work per symbol in the
system canonical order (timestamp_ns, seq), so their results are deterministic and
independent of the input list's order.
"""

from __future__ import annotations

import dataclasses
from collections import defaultdict
from decimal import Decimal

from quantstream_contracts.events import OHLCV, Event, L2Update, Quote, Trade
from quantstream_contracts.serialization import canonical_key, serialize_event

# A 20% move between consecutive trades is treated as a suspicious tick by default.
DEFAULT_MAX_TICK_RETURN = Decimal("0.2")
# A quote unchanged for longer than this is treated as stale by default (5s).
DEFAULT_STALE_NS = 5_000_000_000


def _by_symbol_in_order(events: list[Event]) -> dict[str, list[Event]]:
    grouped: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        grouped[event.symbol].append(event)
    for symbol in grouped:
        grouped[symbol].sort(key=canonical_key)
    return grouped


def check_invalid_price(events: list[Event]) -> set[int]:
    flagged: set[int] = set()
    for event in events:
        if isinstance(event, Trade | L2Update):
            if event.price <= 0:
                flagged.add(event.seq)
        elif isinstance(event, Quote):
            if event.bid_price <= 0 or event.ask_price <= 0:
                flagged.add(event.seq)
        elif isinstance(event, OHLCV):
            if min(event.open, event.high, event.low, event.close) <= 0:
                flagged.add(event.seq)
    return flagged


def check_invalid_size(events: list[Event]) -> set[int]:
    flagged: set[int] = set()
    for event in events:
        if isinstance(event, Trade | L2Update):
            if event.size <= 0:
                flagged.add(event.seq)
        elif isinstance(event, Quote):
            if event.bid_size <= 0 or event.ask_size <= 0:
                flagged.add(event.seq)
        elif isinstance(event, OHLCV):
            if event.volume < 0:
                flagged.add(event.seq)
    return flagged


def check_crossed_book(events: list[Event]) -> set[int]:
    """Quote whose bid strictly exceeds its ask. A locked book (bid == ask) is not
    flagged: it is unusual but not impossible, and flagging it inflates false
    positives."""
    return {
        event.seq
        for event in events
        if isinstance(event, Quote) and event.bid_price > event.ask_price
    }


def _identity_without_seq(event: Event) -> bytes:
    """Content identity ignoring seq, so two rows carrying the same event are
    recognized as duplicates regardless of their file position."""
    return serialize_event(dataclasses.replace(event, seq=0))


def check_duplicates(events: list[Event]) -> set[int]:
    """Flag every occurrence of an event after its first. Order is the canonical
    (timestamp, seq) order, so 'first' is stable."""
    seen: set[bytes] = set()
    flagged: set[int] = set()
    for event in sorted(events, key=canonical_key):
        identity = _identity_without_seq(event)
        if identity in seen:
            flagged.add(event.seq)
        else:
            seen.add(identity)
    return flagged


def check_out_of_order(events: list[Event]) -> set[int]:
    """Flag events whose timestamp goes backwards relative to file order (seq) for
    their symbol: a later-arriving row with an earlier timestamp."""
    flagged: set[int] = set()
    max_ts: dict[str, int] = {}
    for event in sorted(events, key=lambda e: e.seq):
        prior = max_ts.get(event.symbol)
        if prior is not None and event.timestamp_ns < prior:
            flagged.add(event.seq)
        else:
            max_ts[event.symbol] = event.timestamp_ns
    return flagged


def check_bad_tick(
    events: list[Event], *, max_return: Decimal = DEFAULT_MAX_TICK_RETURN
) -> set[int]:
    """Flag a trade whose price moves more than ``max_return`` (fractional) from the
    previous trade in the same symbol."""
    flagged: set[int] = set()
    for symbol_events in _by_symbol_in_order(events).values():
        prev_price: int | None = None
        for event in symbol_events:
            if not isinstance(event, Trade) or event.price <= 0:
                continue
            if prev_price is not None and prev_price > 0:
                move = abs(Decimal(event.price - prev_price) / Decimal(prev_price))
                if move > max_return:
                    flagged.add(event.seq)
            prev_price = event.price
    return flagged


def check_stale_quote(
    events: list[Event], *, stale_ns: int = DEFAULT_STALE_NS
) -> set[int]:
    """Flag quotes in a run of identical consecutive quotes (same bid/ask) that are
    more than ``stale_ns`` older than the start of the run."""
    flagged: set[int] = set()
    for symbol_events in _by_symbol_in_order(events).values():
        run_key: tuple[int, int, int, int] | None = None
        run_start_ts: int | None = None
        for event in symbol_events:
            if not isinstance(event, Quote):
                run_key = None
                run_start_ts = None
                continue
            key = (event.bid_price, event.bid_size, event.ask_price, event.ask_size)
            if key == run_key and run_start_ts is not None:
                if event.timestamp_ns - run_start_ts > stale_ns:
                    flagged.add(event.seq)
            else:
                run_key = key
                run_start_ts = event.timestamp_ns
    return flagged
