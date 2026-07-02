"""QuantStream Labs research engine: backtest, PnL attribution, Alpha Mirage.

Runs a simple strategy over event-time data with no lookahead, tracks per-interval
PnL and taints any contribution whose causal events carry a defect flag, and
compares raw vs cleaned performance to detect fake alpha caused by bad data.
"""

from __future__ import annotations

from .backtest import (
    BacktestConfig,
    BacktestMetrics,
    BacktestResult,
    Contribution,
    run_backtest,
)
from .mirage import (
    DEFAULT_MIRAGE_THRESHOLD,
    MirageDetail,
    MirageReport,
    detect_alpha_mirage,
    detect_alpha_mirage_detailed,
)
from .strategy import MeanReversionStrategy, MomentumStrategy, Strategy

__all__ = [
    "Contribution",
    "BacktestConfig",
    "BacktestMetrics",
    "BacktestResult",
    "run_backtest",
    "MomentumStrategy",
    "MeanReversionStrategy",
    "Strategy",
    "MirageReport",
    "MirageDetail",
    "detect_alpha_mirage",
    "detect_alpha_mirage_detailed",
    "DEFAULT_MIRAGE_THRESHOLD",
]
