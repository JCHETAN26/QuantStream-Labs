"""Backtest performance statistics.

All Decimal-based and deterministic. Square roots use a fixed-precision context so
Sharpe is reproducible bit-for-bit. Sharpe here is per-step (not annualized): a
deliberate V1 simplification, documented so it is never mistaken for an annual
number.
"""

from __future__ import annotations

from decimal import Decimal, localcontext

_SQRT_PRECISION = 50


def mean(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal(0)
    return sum(values, Decimal(0)) / Decimal(len(values))


def pstdev(values: list[Decimal]) -> Decimal:
    """Population standard deviation, deterministic Decimal sqrt."""
    if len(values) < 2:
        return Decimal(0)
    mu = mean(values)
    variance = sum(((v - mu) ** 2 for v in values), Decimal(0)) / Decimal(len(values))
    with localcontext() as ctx:
        ctx.prec = _SQRT_PRECISION
        return variance.sqrt()


def sharpe(pnl_series: list[Decimal]) -> Decimal:
    """Per-step Sharpe: mean(pnl) / population-stdev(pnl). Zero if undefined."""
    if len(pnl_series) < 2:
        return Decimal(0)
    sd = pstdev(pnl_series)
    if sd == 0:
        return Decimal(0)
    return mean(pnl_series) / sd


def max_drawdown(pnl_series: list[Decimal]) -> Decimal:
    """Largest peak-to-trough drop of the cumulative PnL curve. Non-negative."""
    peak = Decimal(0)
    cumulative = Decimal(0)
    worst = Decimal(0)
    for pnl in pnl_series:
        cumulative += pnl
        peak = max(peak, cumulative)
        worst = max(worst, peak - cumulative)
    return worst


def hit_rate(pnl_series: list[Decimal], positions: list[int]) -> Decimal:
    """Fraction of active (non-flat) intervals that were profitable."""
    active = [pnl for pnl, pos in zip(pnl_series, positions, strict=True) if pos != 0]
    if not active:
        return Decimal(0)
    wins = sum(1 for pnl in active if pnl > 0)
    return Decimal(wins) / Decimal(len(active))
