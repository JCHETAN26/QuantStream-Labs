"""Service layer: reuse the exact demo/CLI pipeline, no duplication."""

from __future__ import annotations

from decimal import Decimal

from quantstream_contracts.events import Event
from quantstream_contracts.fixed_point import PRICE_SCALE
from quantstream_demo import (
    DEMO_STRATEGY,
    DemoResult,
    analyze_events,
    dataset_events,
    run_demo,
)
from quantstream_orderbook import (
    L2_SAMPLE_SYMBOL,
    SAMPLE_SYMBOL,
    BookSnapshot,
    BookSummary,
    L2Snapshot,
    L2Summary,
    reconstruct,
    reconstruct_l2,
    sample_l2_updates,
    sample_quotes,
)
from quantstream_research import Contribution, detect_alpha_mirage_detailed
from quantstream_schema import InferredSchema, load_csv_text
from quantstream_validation import validate

from .models import FlaggedEvent, PnlPoint, SeriesResponse


def bundled() -> DemoResult:
    """Run the pipeline on the bundled sample dataset."""
    return run_demo()


def orderbook_demo() -> tuple[list[BookSnapshot], BookSummary]:
    """Reconstruct top-of-book (L1) for the bundled quote sample."""
    snapshots, summaries = reconstruct(sample_quotes())
    return snapshots, summaries[SAMPLE_SYMBOL]


def orderbook_l2_demo() -> tuple[list[L2Snapshot], L2Summary]:
    """Reconstruct L2 depth for the bundled order-book-update sample."""
    snapshots, summaries = reconstruct_l2(sample_l2_updates())
    return snapshots, summaries[L2_SAMPLE_SYMBOL]


def analyze_csv(text: str) -> tuple[InferredSchema, DemoResult]:
    """Infer schema from an uploaded CSV, load it, and run the pipeline.

    Raises ValueError if nothing loads (the app turns this into HTTP 422).
    """
    schema, load = load_csv_text(text)
    if not load.events:
        raise ValueError(
            f"no events could be loaded from the CSV ({len(load.errors)} row errors)"
        )
    result = analyze_events(
        load.events, symbol=load.events[0].symbol, load_errors=len(load.errors)
    )
    return schema, result


def _curve(contributions: tuple[Contribution, ...], ts: dict[int, int]) -> list[PnlPoint]:
    points: list[PnlPoint] = []
    cum = Decimal(0)
    for c in contributions:
        pnl = Decimal(c.pnl) / Decimal(PRICE_SCALE)
        cum += pnl
        points.append(
            PnlPoint(
                seq=c.from_seq,
                timestamp_ns=ts.get(c.from_seq, 0),
                pnl=float(pnl),
                cum_pnl=float(cum),
                tainted=c.tainted,
            )
        )
    return points


def _series_for(events: list[Event], symbol: str) -> SeriesResponse:
    """Build raw/clean cumulative-PnL curves and the flagged-event timeline.

    Uses the same strategy and validation as the headline verdict, so the curves
    reconcile exactly with the reported Sharpe/PnL/mirage numbers.
    """
    report = validate(events)
    detail = detect_alpha_mirage_detailed(events, list(report.defect_map), DEMO_STRATEGY)
    ts = {e.seq: e.timestamp_ns for e in events}

    flagged = [
        FlaggedEvent(seq=seq, defects=sorted(d.value for d in defects))
        for seq, defects in sorted(report.defect_map.items())
    ]
    return SeriesResponse(
        symbol=symbol,
        total_events=len(events),
        flagged_events=report.flagged_events,
        raw_curve=_curve(detail.raw_result.contributions, ts),
        clean_curve=_curve(detail.clean_result.contributions, ts),
        flagged=flagged,
    )


def demo_series() -> SeriesResponse:
    """Per-interval equity curves + flagged timeline for the official dataset."""
    events = dataset_events()
    return _series_for(events, events[0].symbol)


def analyze_series(text: str) -> SeriesResponse:
    """Per-interval equity curves + flagged timeline for an uploaded CSV."""
    _schema, load = load_csv_text(text)
    if not load.events:
        raise ValueError(
            f"no events could be loaded from the CSV ({len(load.errors)} row errors)"
        )
    return _series_for(load.events, load.events[0].symbol)
