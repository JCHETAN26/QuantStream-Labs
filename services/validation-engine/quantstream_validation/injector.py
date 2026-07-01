"""Seeded corruption injector.

Takes a clean, valid event set and injects realistic market-data defects, tagging
each affected event with ground truth. This exists so we can prove the validation
engine's honesty: the detector runs *independently* of this ground truth, and the
overlap (precision / recall) is a reported quality metric rather than a claim.

Everything is driven by a single seed, so a given (clean data, config) always
produces the identical raw data and identical ground truth. That reproducibility is
part of the honesty argument: the corruption is documented and repeatable, not a
one-off fudge.

Injected defects and how each is later detected:

    INVALID_PRICE   price set to 0            -> check_invalid_price
    INVALID_SIZE    size set to 0             -> check_invalid_size
    CROSSED_BOOK    bid set above ask         -> check_crossed_book
    OUT_OF_ORDER    timestamp pushed earlier  -> check_out_of_order
    BAD_TICK        price multiplied up       -> check_bad_tick
    DUPLICATE       event copied with new seq -> check_duplicates
"""

from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass

from quantstream_contracts.events import Event, Quote, Trade

from .defects import Defect

_BAD_TICK_MULTIPLIER = 5
_CROSS_TICKS = 10  # fixed-point units to push a bid above its ask


@dataclass(frozen=True)
class CorruptionConfig:
    seed: int = 0
    duplicate_rate: float = 0.0
    invalid_price_rate: float = 0.0
    invalid_size_rate: float = 0.0
    crossed_rate: float = 0.0
    out_of_order_rate: float = 0.0
    bad_tick_rate: float = 0.0


@dataclass(frozen=True)
class CorruptionResult:
    events: list[Event]  # raw = clean events with injected defects
    truth: dict[int, frozenset[Defect]]  # seq -> injected defects


def corrupt(clean_events: list[Event], config: CorruptionConfig) -> CorruptionResult:
    rng = random.Random(config.seed)
    events: list[Event] = list(clean_events)
    index: dict[int, int] = {e.seq: i for i, e in enumerate(events)}
    truth: dict[int, set[Defect]] = {}
    touched: set[int] = set()
    next_seq = max((e.seq for e in events), default=-1) + 1

    # First seq per symbol: never pushed out of order (needs a prior event).
    first_seq_by_symbol: dict[str, int] = {}
    for event in sorted(clean_events, key=lambda e: e.seq):
        first_seq_by_symbol.setdefault(event.symbol, event.seq)

    symbol_min_ts: dict[str, int] = {}
    for event in clean_events:
        ts = symbol_min_ts.get(event.symbol)
        if ts is None or event.timestamp_ns < ts:
            symbol_min_ts[event.symbol] = event.timestamp_ns

    def current(seq: int) -> Event:
        return events[index[seq]]

    def apply(seq: int, **changes) -> None:
        events[index[seq]] = dataclasses.replace(current(seq), **changes)

    def mark(seq: int, defect: Defect) -> None:
        truth.setdefault(seq, set()).add(defect)
        touched.add(seq)

    trade_seqs = [e.seq for e in sorted(clean_events, key=lambda e: e.seq)
                  if isinstance(e, Trade)]
    quote_seqs = [e.seq for e in sorted(clean_events, key=lambda e: e.seq)
                  if isinstance(e, Quote)]
    all_seqs = [e.seq for e in sorted(clean_events, key=lambda e: e.seq)]

    # In-place field corruptions: at most one per original event.
    for seq in trade_seqs:
        if seq in touched:
            continue
        if rng.random() < config.invalid_price_rate:
            apply(seq, price=0)
            mark(seq, Defect.INVALID_PRICE)

    for seq in trade_seqs:
        if seq in touched:
            continue
        if rng.random() < config.invalid_size_rate:
            apply(seq, size=0)
            mark(seq, Defect.INVALID_SIZE)

    for seq in quote_seqs:
        if seq in touched:
            continue
        if rng.random() < config.crossed_rate:
            quote = current(seq)
            assert isinstance(quote, Quote)
            apply(seq, bid_price=quote.ask_price + _CROSS_TICKS)
            mark(seq, Defect.CROSSED_BOOK)

    for seq in all_seqs:
        if seq in touched:
            continue
        symbol = current(seq).symbol
        if seq == first_seq_by_symbol[symbol]:
            continue
        if rng.random() < config.out_of_order_rate:
            apply(seq, timestamp_ns=symbol_min_ts[symbol] - 1)
            mark(seq, Defect.OUT_OF_ORDER)

    for seq in trade_seqs:
        if seq in touched:
            continue
        if rng.random() < config.bad_tick_rate:
            trade = current(seq)
            assert isinstance(trade, Trade)
            apply(seq, price=trade.price * _BAD_TICK_MULTIPLIER)
            mark(seq, Defect.BAD_TICK)

    # Duplicates append new events; they copy a still-clean original so the copy
    # carries exactly one defect (DUPLICATE) and nothing spurious.
    for seq in trade_seqs:
        if seq in touched:
            continue
        if rng.random() < config.duplicate_rate:
            original = current(seq)
            copy = dataclasses.replace(original, seq=next_seq)
            events.append(copy)
            index[next_seq] = len(events) - 1
            truth.setdefault(next_seq, set()).add(Defect.DUPLICATE)
            next_seq += 1

    frozen_truth = {seq: frozenset(defects) for seq, defects in truth.items()}
    return CorruptionResult(events=events, truth=frozen_truth)
