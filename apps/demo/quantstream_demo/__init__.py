"""QuantStream Labs Alpha Mirage demo application.

Ties the whole pipeline together on a bundled sample dataset: validate -> replay ->
raw-vs-clean backtest -> Alpha Mirage, with a terminal verdict and an HTML report.
"""

from __future__ import annotations

from .cli import (
    DEMO_STRATEGY,
    analyze_events,
    dataset_events,
    format_terminal,
    main,
    run_demo,
)
from .report import DemoResult, QuotesSummary, build_html
from .sample_data import SAMPLE_SYMBOL, sample_events

__all__ = [
    "run_demo",
    "analyze_events",
    "dataset_events",
    "DEMO_STRATEGY",
    "main",
    "format_terminal",
    "DemoResult",
    "QuotesSummary",
    "build_html",
    "sample_events",
    "SAMPLE_SYMBOL",
]
