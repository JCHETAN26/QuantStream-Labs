"""Event-time backtest with per-interval PnL and defect taint tracking.

Runs a strategy over trades in canonical order, per symbol, with no lookahead. Each
holding interval [t, t+1] produces one PnL contribution. A contribution is
*tainted* if any event in its causal chain carries a defect flag:

    causal chain = { indices the strategy consulted at t } + { event t, event t+1 }

That is the honest basis for "N% of PnL came from corrupted events": we sum the PnL
of tainted contributions, not the PnL that merely correlates with defects.

Positions are unit-sized; PnL is in fixed-point price units internally and exposed
as Decimal real units in the metrics.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection
from dataclasses import dataclass
from decimal import Decimal

from quantstream_contracts.events import Event, Trade
from quantstream_contracts.fixed_point import PRICE_SCALE
from quantstream_contracts.serialization import canonical_key

from . import metrics
from .strategy import Strategy


@dataclass(frozen=True)
class Contribution:
    symbol: str
    from_seq: int
    to_seq: int
    position: int
    pnl: int  # fixed-point price units
    tainted: bool
    causal_seqs: frozenset[int]


@dataclass(frozen=True)
class BacktestMetrics:
    total_pnl: Decimal
    tainted_pnl: Decimal
    sharpe: Decimal
    max_drawdown: Decimal
    hit_rate: Decimal
    turnover: int
    active_intervals: int
    total_intervals: int


@dataclass(frozen=True)
class BacktestResult:
    contributions: tuple[Contribution, ...]
    metrics: BacktestMetrics


def _trades_by_symbol(events: list[Event]) -> dict[str, list[Trade]]:
    grouped: dict[str, list[Trade]] = defaultdict(list)
    for event in events:
        if isinstance(event, Trade):
            grouped[event.symbol].append(event)
    for symbol in grouped:
        grouped[symbol].sort(key=canonical_key)
    return grouped


def run_backtest(
    events: list[Event],
    flagged_seqs: Collection[int],
    strategy: Strategy,
) -> BacktestResult:
    flagged = frozenset(flagged_seqs)
    contributions: list[Contribution] = []
    turnover = 0

    for symbol, trades in _trades_by_symbol(events).items():
        prices = [t.price for t in trades]
        seqs = [t.seq for t in trades]
        prev_position: int | None = None

        for i in range(len(trades)):
            position, consulted = strategy.decide(prices, i)
            if prev_position is not None and position != prev_position:
                turnover += 1
            prev_position = position

            if i + 1 >= len(trades):
                continue  # last trade: no interval to realize

            pnl = position * (prices[i + 1] - prices[i])
            causal = {seqs[k] for k in consulted} | {seqs[i], seqs[i + 1]}
            tainted = any(seq in flagged for seq in causal)
            contributions.append(
                Contribution(
                    symbol=symbol,
                    from_seq=seqs[i],
                    to_seq=seqs[i + 1],
                    position=position,
                    pnl=pnl,
                    tainted=tainted,
                    causal_seqs=frozenset(causal),
                )
            )

    return BacktestResult(
        contributions=tuple(contributions),
        metrics=_build_metrics(contributions, turnover),
    )


def _build_metrics(contributions: list[Contribution], turnover: int) -> BacktestMetrics:
    scale = Decimal(PRICE_SCALE)
    pnl_series = [Decimal(c.pnl) / scale for c in contributions]
    positions = [c.position for c in contributions]
    tainted_series = [
        pnl for pnl, c in zip(pnl_series, contributions, strict=True) if c.tainted
    ]
    active = sum(1 for p in positions if p != 0)

    return BacktestMetrics(
        total_pnl=sum(pnl_series, Decimal(0)),
        tainted_pnl=sum(tainted_series, Decimal(0)),
        sharpe=metrics.sharpe(pnl_series),
        max_drawdown=metrics.max_drawdown(pnl_series),
        hit_rate=metrics.hit_rate(pnl_series, positions),
        turnover=turnover,
        active_intervals=active,
        total_intervals=len(contributions),
    )
