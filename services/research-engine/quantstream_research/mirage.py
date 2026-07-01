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

from .backtest import BacktestMetrics, run_backtest
from .strategy import Strategy

DEFAULT_MIRAGE_THRESHOLD = Decimal("0.5")


@dataclass(frozen=True)
class MirageReport:
    raw: BacktestMetrics
    clean: BacktestMetrics
    mirage_score: Decimal
    research_safe: bool
    conclusion: str


def detect_alpha_mirage(
    raw_events: list[Event],
    flagged_seqs: Collection[int],
    strategy: Strategy,
    *,
    threshold: Decimal = DEFAULT_MIRAGE_THRESHOLD,
) -> MirageReport:
    flagged = frozenset(flagged_seqs)

    raw = run_backtest(raw_events, flagged, strategy).metrics
    clean_events = [e for e in raw_events if e.seq not in flagged]
    clean = run_backtest(clean_events, frozenset(), strategy).metrics

    if raw.total_pnl == 0:
        score = Decimal(0)
    else:
        score = raw.tainted_pnl / raw.total_pnl

    research_safe = abs(score) < threshold
    if research_safe:
        conclusion = (
            "Signal is research-safe. Performance does not materially depend on "
            "corrupted market-data regions."
        )
    else:
        pct = (score * 100).quantize(Decimal("1"))
        conclusion = (
            "Signal is not research-safe. "
            f"{pct}% of simulated PnL came from corrupted market-data events."
        )

    return MirageReport(
        raw=raw,
        clean=clean,
        mirage_score=score,
        research_safe=research_safe,
        conclusion=conclusion,
    )
