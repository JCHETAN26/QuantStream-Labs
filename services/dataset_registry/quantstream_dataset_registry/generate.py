"""Deterministic generation of the official reproducibility dataset.

This module is the single source of truth for the QuantStream Labs demo dataset.
The exact same bytes are produced on every platform, which is what lets us:

  * commit the dataset to the repo and regenerate it identically offline,
  * publish it to Hugging Face and verify the download against committed SHA-256s,
  * lock the Alpha Mirage result into ``expected_results.json``.

Two instrument families are generated:

  Trades (drive the Alpha Mirage demo). A flat-ish random walk with no real edge,
  plus periodic bad-tick spikes. A mean-reversion strategy fades each spike and
  books the "reversion" that is really just the bad tick correcting — fake alpha
  caused entirely by bad data. ``defective_trades.csv`` carries the spikes;
  ``clean_trades.csv`` is the pristine control (no defects, no mirage).

  Quotes (exercise the L1 / validation defect taxonomy). A tight-spread series with
  injected crossed books, non-positive prices, and a stale block.
  ``defective_quotes.csv`` carries the defects; ``clean_quotes.csv`` is pristine.

Nothing here reads the wall clock or any external state, so regeneration is
byte-stable.
"""

from __future__ import annotations

import csv
import io
import random
from decimal import Decimal

from quantstream_contracts.enums import Side
from quantstream_contracts.events import Quote, Trade
from quantstream_contracts.fixed_point import (
    PRICE_SCALE,
    SIZE_SCALE,
    from_fixed,
    price_to_fixed,
    size_to_fixed,
)

SAMPLE_SYMBOL = "ACME"
SAMPLE_SEED = 20260701
_START_TS = 1_700_000_000_000_000_000

# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------
_BASE_PRICE = Decimal("100.00")
_N = 400

# A geometric (multiplicative) random walk over a realistic ~6.5h session.
# Symmetric per-trade returns of ~0.1-0.3% -> no real edge for a mean-reversion
# strategy (a martingale), realistic intraday vol, prices that wander like a real
# tape rather than a bounded flat line. Everything is Decimal + integer RNG (no
# libm), so the dataset regenerates byte-for-byte on any machine.
_RETURN_TICKS = (
    Decimal("-0.003"), Decimal("-0.002"), Decimal("-0.001"),
    Decimal("0.001"), Decimal("0.002"), Decimal("0.003"),
)
# Irregular trade arrivals: gaps drawn uniformly from 10ms..120s (integer ns).
_MIN_GAP_NS = 10_000_000
_MAX_GAP_NS = 120_000_000_000

# Bad ticks every _SPIKE_EVERY trades, alternating up/down, big enough that the
# validation engine's 20% bad-tick threshold catches them.
_SPIKE_EVERY = 4
_FIRST_SPIKE = 5
_UP_FACTOR = Decimal("1.35")
_DOWN_FACTOR = Decimal("0.65")


def _spike_indices() -> list[int]:
    return list(range(_FIRST_SPIKE, _N - 2, _SPIKE_EVERY))


def injected_spike_count() -> int:
    return len(_spike_indices())


def _timestamps() -> list[int]:
    """Irregular, strictly-increasing trade timestamps over a trading session."""
    rng = random.Random(SAMPLE_SEED + 777)
    ts = _START_TS
    out: list[int] = []
    for _ in range(_N):
        out.append(ts)
        ts += rng.randint(_MIN_GAP_NS, _MAX_GAP_NS)
    return out


def _base_walk() -> list[Decimal]:
    rng = random.Random(SAMPLE_SEED)
    price = _BASE_PRICE
    prices: list[Decimal] = []
    for _ in range(_N):
        prices.append(price.quantize(Decimal("0.01")))
        ret = _RETURN_TICKS[rng.randrange(len(_RETURN_TICKS))]
        price = price * (Decimal(1) + ret)
        if price < Decimal("1"):
            price = Decimal("1")
    return prices


def clean_prices() -> list[Decimal]:
    """The pristine geometric walk, no spikes."""
    return _base_walk()


def sample_prices() -> list[Decimal]:
    """The geometric walk with injected bad-tick spikes."""
    prices = _base_walk()
    for n, idx in enumerate(_spike_indices()):
        factor = _UP_FACTOR if n % 2 == 0 else _DOWN_FACTOR
        prices[idx] = (prices[idx] * factor).quantize(Decimal("0.01"))
    return prices


def _trades_from_prices(prices: list[Decimal]) -> list[Trade]:
    timestamps = _timestamps()
    events: list[Trade] = []
    for i, price in enumerate(prices):
        events.append(
            Trade(
                seq=i,
                timestamp_ns=timestamps[i],
                symbol=SAMPLE_SYMBOL,
                price=price_to_fixed(price),
                size=size_to_fixed("100"),
                side=Side.BUY,
                trade_id=f"e{i}",
                venue="DEMO",
            )
        )
    return events


def sample_events() -> list[Trade]:
    """The raw (defective) demo trades: flat base with injected bad-tick spikes."""
    return _trades_from_prices(sample_prices())


def clean_events() -> list[Trade]:
    """The pristine control trades: base walk with no spikes."""
    return _trades_from_prices(clean_prices())


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------
_Q_N = 120
_Q_STEP_NS = 1_000_000_000  # 1s between quotes
_Q_SEED = 20260702
_Q_HALF_SPREAD = Decimal("0.01")
_Q_WALK_STEP = Decimal("0.02")
_Q_SIZE = "500"

# Injected quote-defect positions (ground truth).
_Q_CROSSED = (10, 40, 70)
_Q_INVALID = (25, 55)
_Q_STALE_RUN = tuple(range(90, 101))  # 11 identical consecutive quotes (>5s span)


def _quote_mids() -> list[Decimal]:
    rng = random.Random(_Q_SEED)
    mid = _BASE_PRICE
    mids: list[Decimal] = []
    for _ in range(_Q_N):
        mids.append(mid)
        mid += _Q_WALK_STEP if rng.random() < 0.5 else -_Q_WALK_STEP
        if mid < Decimal("2"):
            mid = Decimal("2")
    return mids


def clean_quote_events() -> list[Quote]:
    mids = _quote_mids()
    quotes: list[Quote] = []
    for i, mid in enumerate(mids):
        quotes.append(
            Quote(
                seq=i,
                timestamp_ns=_START_TS + i * _Q_STEP_NS,
                symbol=SAMPLE_SYMBOL,
                bid_price=price_to_fixed(mid - _Q_HALF_SPREAD),
                bid_size=size_to_fixed(_Q_SIZE),
                ask_price=price_to_fixed(mid + _Q_HALF_SPREAD),
                ask_size=size_to_fixed(_Q_SIZE),
                venue="DEMO",
            )
        )
    return quotes


def defective_quote_events() -> tuple[list[Quote], dict[int, list[str]]]:
    """Defective quotes plus the ground-truth {seq: [defect,...]} of what we inject."""
    quotes = clean_quote_events()
    truth: dict[int, list[str]] = {}

    def replace(i: int, **changes) -> None:
        import dataclasses

        quotes[i] = dataclasses.replace(quotes[i], **changes)

    # Crossed book: push bid strictly above ask.
    for i in _Q_CROSSED:
        replace(i, bid_price=quotes[i].ask_price + price_to_fixed("0.02"))
        truth.setdefault(i, []).append("crossed_book")

    # Invalid price: non-positive bid.
    for i in _Q_INVALID:
        replace(i, bid_price=0)
        truth.setdefault(i, []).append("invalid_price")

    # Stale block: force an identical run so its tail exceeds the 5s stale window.
    anchor = clean_quote_events()[_Q_STALE_RUN[0]]
    for i in _Q_STALE_RUN:
        replace(
            i,
            bid_price=anchor.bid_price,
            bid_size=anchor.bid_size,
            ask_price=anchor.ask_price,
            ask_size=anchor.ask_size,
        )
    # The engine flags the run members more than 5s after the run start; record the
    # whole injected run as ground truth (detection is measured against it).
    for i in _Q_STALE_RUN:
        truth.setdefault(i, []).append("stale_quote")

    return quotes, {seq: sorted(set(v)) for seq, v in truth.items()}


# ---------------------------------------------------------------------------
# CSV rendering (deterministic: LF line endings, minimal decimal formatting)
# ---------------------------------------------------------------------------
def _fmt(fixed: int, scale: int) -> str:
    # Plain fixed-point notation, never scientific: tiny crypto sizes like 0.00000026
    # render as "0.00000026", not "2.6E-7" (which the C++ CSV parser can't read).
    return format(from_fixed(fixed, scale), "f")


def render_trades_csv(trades: list[Trade]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["timestamp", "symbol", "price", "size", "side", "trade_id", "venue"])
    side_name = {Side.BUY: "buy", Side.SELL: "sell", Side.UNKNOWN: "unknown"}
    for t in trades:
        writer.writerow(
            [
                t.timestamp_ns,
                t.symbol,
                _fmt(t.price, PRICE_SCALE),
                _fmt(t.size, SIZE_SCALE),
                side_name[t.side],
                t.trade_id,
                t.venue,
            ]
        )
    return buf.getvalue()


def render_quotes_csv(quotes: list[Quote]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        ["timestamp", "symbol", "bid_price", "bid_size", "ask_price", "ask_size", "venue"]
    )
    for q in quotes:
        writer.writerow(
            [
                q.timestamp_ns,
                q.symbol,
                _fmt(q.bid_price, PRICE_SCALE),
                _fmt(q.bid_size, SIZE_SCALE),
                _fmt(q.ask_price, PRICE_SCALE),
                _fmt(q.ask_size, SIZE_SCALE),
                q.venue,
            ]
        )
    return buf.getvalue()
