"""QuantStream Labs research engine: backtest, PnL attribution, Alpha Mirage.

Runs a simple strategy over event-time data with no lookahead, tracks per-interval
PnL and taints any contribution whose causal events carry a defect flag, and
compares raw vs cleaned performance to detect fake alpha caused by bad data.
"""

from __future__ import annotations

from .backtest import (
    BacktestMetrics,
    BacktestResult,
    Contribution,
    run_backtest,
)
from .mirage import DEFAULT_MIRAGE_THRESHOLD, MirageReport, detect_alpha_mirage
from .strategy import MeanReversionStrategy, MomentumStrategy, Strategy

__all__ = [
    "Contribution",
    "BacktestMetrics",
    "BacktestResult",
    "run_backtest",
    "MomentumStrategy",
    "MeanReversionStrategy",
    "Strategy",
    "MirageReport",
    "detect_alpha_mirage",
    "DEFAULT_MIRAGE_THRESHOLD",
]
