"""The Alpha Mirage Detector.

Runs the same strategy twice: once on the raw events (defects included, PnL tainted)
and once on the cleaned events (flagged events removed). If the strategy's raw
performance depends materially on corrupted events, the cleaned run collapses and
the mirage score is high.

    mirage_score = tainted_pnl(raw) / total_pnl(raw)

A signal is "research-safe" only if that dependence is below a threshold. The score
is one auditable ratio, not a black box: a reviewer can recompute it from the raw
backtest's contributions.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from decimal import Decimal

from quantstream_contracts.events import Event

from .backtest import BacktestMetrics, BacktestResult, run_backtest
from .strategy import Strategy

DEFAULT_MIRAGE_THRESHOLD = Decimal("0.5")


@dataclass(frozen=True)
class MirageReport:
    raw: BacktestMetrics
    clean: BacktestMetrics
    mirage_score: Decimal
    research_safe: bool
    conclusion: str


@dataclass(frozen=True)
class MirageDetail:
    """A MirageReport plus the full raw/clean backtest results.

    The per-interval ``contributions`` on each result are what a UI needs to draw
    the raw-vs-cleaned equity curves and to mark which intervals were tainted.
    """

    report: MirageReport
    raw_result: BacktestResult
    clean_result: BacktestResult


def _conclusion(score: Decimal, research_safe: bool) -> str:
    if research_safe:
        return (
            "Signal is research-safe. Performance does not materially depend on "
            "corrupted market-data regions."
        )
    pct = (score * 100).quantize(Decimal("1"))
    return (
        "Signal is not research-safe. "
        f"{pct}% of simulated PnL came from corrupted market-data events."
    )


def detect_alpha_mirage_detailed(
    raw_events: list[Event],
    flagged_seqs: Collection[int],
    strategy: Strategy,
    *,
    threshold: Decimal = DEFAULT_MIRAGE_THRESHOLD,
) -> MirageDetail:
    """Run the raw and cleaned backtests and return both the verdict and the full
    per-interval results (for equity curves / attribution timelines)."""
    flagged = frozenset(flagged_seqs)

    raw_result = run_backtest(raw_events, flagged, strategy)
    clean_events = [e for e in raw_events if e.seq not in flagged]
    clean_result = run_backtest(clean_events, frozenset(), strategy)

    raw = raw_result.metrics
    clean = clean_result.metrics

    score = Decimal(0) if raw.total_pnl == 0 else raw.tainted_pnl / raw.total_pnl
    research_safe = abs(score) < threshold

    report = MirageReport(
        raw=raw,
        clean=clean,
        mirage_score=score,
        research_safe=research_safe,
        conclusion=_conclusion(score, research_safe),
    )
    return MirageDetail(report=report, raw_result=raw_result, clean_result=clean_result)


def detect_alpha_mirage(
    raw_events: list[Event],
    flagged_seqs: Collection[int],
    strategy: Strategy,
    *,
    threshold: Decimal = DEFAULT_MIRAGE_THRESHOLD,
) -> MirageReport:
    return detect_alpha_mirage_detailed(
        raw_events, flagged_seqs, strategy, threshold=threshold
    ).report
