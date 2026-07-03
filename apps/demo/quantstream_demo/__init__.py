"""QuantStream Labs Alpha Mirage demo application.

Ties the whole pipeline together on a bundled sample dataset: validate -> replay ->
raw-vs-clean backtest -> Alpha Mirage, with a terminal verdict and an HTML report.
"""

from __future__ import annotations

from .cli import (
    DEMO_CONFIG,
    DEMO_STRATEGY,
    REAL_CONFIG,
    analyze_events,
    dataset_events,
    format_terminal,
    main,
    real_dataset_events,
    run_demo,
    run_real_demo,
)
from .report import DemoResult, QuotesSummary, build_html
from .sample_data import SAMPLE_SYMBOL, sample_events

__all__ = [
    "run_demo",
    "run_real_demo",
    "real_dataset_events",
    "analyze_events",
    "dataset_events",
    "DEMO_STRATEGY",
    "DEMO_CONFIG",
    "REAL_CONFIG",
    "main",
    "format_terminal",
    "DemoResult",
    "QuotesSummary",
    "build_html",
    "sample_events",
    "SAMPLE_SYMBOL",
]
