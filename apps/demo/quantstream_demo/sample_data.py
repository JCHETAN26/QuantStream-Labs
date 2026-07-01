"""The bundled demo dataset.

A deterministic trade series with an honest, documented flaw: a flat-ish base price
(no real edge for a mean-reversion strategy) plus periodic **bad ticks** — single
spurious prints that spike the price and immediately correct. A mean-reversion
strategy fades each spike and books the "reversion", which is really just the bad
tick correcting. That is fake alpha caused entirely by bad data.

Everything here is seeded and reproducible. The spike positions are known ground
truth, used only to report the validation engine's detection quality — the pipeline
itself cleans based on what the validator independently detects, not on this list.
"""

from __future__ import annotations

import random
from decimal import Decimal
from importlib.resources import files

from quantstream_contracts.enums import Side
from quantstream_contracts.events import Trade
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed

SAMPLE_SYMBOL = "ACME"
SAMPLE_SEED = 20260701
_BASE_PRICE = Decimal("100.00")
_N = 400
_START_TS = 1_700_000_000_000_000_000
_STEP_NS = 1_000_000  # 1ms between prints

# A tiny random walk: real but edgeless price movement. Steps are ~0.02%, far below
# the validation engine's 20% bad-tick threshold, so the base is never flagged.
_WALK_STEP = Decimal("0.02")

# Bad ticks every _SPIKE_EVERY events, alternating up/down, big enough that the
# validation engine's 20% bad-tick threshold catches them.
_SPIKE_EVERY = 4
_FIRST_SPIKE = 5
_UP_FACTOR = Decimal("1.35")
_DOWN_FACTOR = Decimal("0.65")


def _spike_indices() -> list[int]:
    return list(range(_FIRST_SPIKE, _N - 2, _SPIKE_EVERY))


def _base_walk() -> list[Decimal]:
    rng = random.Random(SAMPLE_SEED)
    price = _BASE_PRICE
    prices = []
    for _ in range(_N):
        prices.append(price)
        price += _WALK_STEP if rng.random() < 0.5 else -_WALK_STEP
        if price < Decimal("1"):
            price = Decimal("1")
    return prices


def sample_prices() -> list[Decimal]:
    prices = _base_walk()
    for n, idx in enumerate(_spike_indices()):
        factor = _UP_FACTOR if n % 2 == 0 else _DOWN_FACTOR
        prices[idx] = (prices[idx] * factor).quantize(Decimal("0.01"))
    return prices


def sample_events() -> list[Trade]:
    """The raw demo dataset: flat base with injected bad-tick spikes."""
    events = []
    for i, price in enumerate(sample_prices()):
        events.append(
            Trade(
                seq=i,
                timestamp_ns=_START_TS + i * _STEP_NS,
                symbol=SAMPLE_SYMBOL,
                price=price_to_fixed(price),
                size=size_to_fixed("100"),
                side=Side.BUY,
                trade_id=f"e{i}",
                venue="DEMO",
            )
        )
    return events


def injected_spike_count() -> int:
    return len(_spike_indices())


def sample_csv_path() -> str:
    """Path to the bundled sample CSV (the same data as sample_events)."""
    return str(files("quantstream_demo").joinpath("data/acme_trades.csv"))
