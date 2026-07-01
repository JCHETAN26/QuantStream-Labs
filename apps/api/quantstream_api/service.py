"""Service layer: reuse the exact demo/CLI pipeline, no duplication."""

from __future__ import annotations

from quantstream_demo import DemoResult, analyze_events, run_demo
from quantstream_orderbook import (
    SAMPLE_SYMBOL,
    BookSnapshot,
    BookSummary,
    reconstruct,
    sample_quotes,
)
from quantstream_schema import InferredSchema, load_csv_text


def bundled() -> DemoResult:
    """Run the pipeline on the bundled sample dataset."""
    return run_demo()


def orderbook_demo() -> tuple[list[BookSnapshot], BookSummary]:
    """Reconstruct top-of-book for the bundled quote sample."""
    snapshots, summaries = reconstruct(sample_quotes())
    return snapshots, summaries[SAMPLE_SYMBOL]


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
