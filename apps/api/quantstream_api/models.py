"""API response models.

Decimals from the pipeline are surfaced as floats here: this is the display/JSON
boundary, and the exact values remain available via the deterministic checksums.
"""

from __future__ import annotations

from pydantic import BaseModel
from quantstream_contracts.fixed_point import price_from_fixed, size_from_fixed
from quantstream_demo import DemoResult
from quantstream_orderbook import (
    BookSnapshot,
    BookSummary,
    L2Snapshot,
    L2Summary,
)
from quantstream_research import BacktestMetrics
from quantstream_schema import InferredSchema


class MetricsModel(BaseModel):
    sharpe: float
    total_pnl: float
    max_drawdown: float
    hit_rate: float
    turnover: int
    active_intervals: int
    total_intervals: int


class ValidationCheckModel(BaseModel):
    name: str
    status: str
    count: int
    severity: str


class SchemaModel(BaseModel):
    event_type: str
    confidence: float
    timestamp_unit: str
    unmatched_columns: list[str]
    notes: list[str]


class AnalysisResponse(BaseModel):
    symbol: str
    total_events: int
    flagged_events: int
    load_errors: int
    mirage_score: float
    research_safe: bool
    conclusion: str
    raw: MetricsModel
    clean: MetricsModel
    raw_checksum: str
    clean_checksum: str
    validation: list[ValidationCheckModel]
    inferred_schema: SchemaModel | None = None


def _metrics(m: BacktestMetrics) -> MetricsModel:
    return MetricsModel(
        sharpe=float(m.sharpe),
        total_pnl=float(m.total_pnl),
        max_drawdown=float(m.max_drawdown),
        hit_rate=float(m.hit_rate),
        turnover=m.turnover,
        active_intervals=m.active_intervals,
        total_intervals=m.total_intervals,
    )


def _schema(schema: InferredSchema) -> SchemaModel:
    return SchemaModel(
        event_type=schema.event_type.name,
        confidence=schema.confidence,
        timestamp_unit=schema.mapping.timestamp_unit.value,
        unmatched_columns=list(schema.unmatched_columns),
        notes=list(schema.notes),
    )


class BookSnapshotModel(BaseModel):
    seq: int
    timestamp_ns: int
    best_bid: float
    best_ask: float
    spread: float
    mid_price: float
    quote_age_ns: int
    is_crossed: bool
    is_stale: bool
    confidence: str


class OrderBookResponse(BaseModel):
    symbol: str
    quotes: int
    crossed_count: int
    stale_count: int
    final_confidence: str
    confidence_states_seen: list[str]
    snapshots: list[BookSnapshotModel]


def _snapshot(s: BookSnapshot) -> BookSnapshotModel:
    return BookSnapshotModel(
        seq=s.seq,
        timestamp_ns=s.timestamp_ns,
        best_bid=float(price_from_fixed(s.best_bid)),
        best_ask=float(price_from_fixed(s.best_ask)),
        spread=float(price_from_fixed(s.spread)),
        mid_price=float(price_from_fixed(s.mid_price)),
        quote_age_ns=s.quote_age_ns,
        is_crossed=s.is_crossed,
        is_stale=s.is_stale,
        confidence=s.confidence.value,
    )


def orderbook_to_response(
    snapshots: list[BookSnapshot], summary: BookSummary
) -> OrderBookResponse:
    return OrderBookResponse(
        symbol=summary.symbol,
        quotes=summary.quotes,
        crossed_count=summary.crossed_count,
        stale_count=summary.stale_count,
        final_confidence=summary.final_confidence.value,
        confidence_states_seen=sorted({s.confidence.value for s in snapshots}),
        snapshots=[_snapshot(s) for s in snapshots],
    )


class L2SnapshotModel(BaseModel):
    seq: int
    timestamp_ns: int
    best_bid: float | None
    best_ask: float | None
    bid_depth: float
    ask_depth: float
    depth_imbalance: float
    sequence_gap: bool
    missing: int
    is_crossed: bool
    confidence: str


class L2Response(BaseModel):
    symbol: str
    updates: int
    sequence_gap_count: int
    total_missing: int
    crossed_count: int
    final_confidence: str
    bid_levels: int
    ask_levels: int
    confidence_states_seen: list[str]
    snapshots: list[L2SnapshotModel]


def _l2_snapshot(s: L2Snapshot) -> L2SnapshotModel:
    return L2SnapshotModel(
        seq=s.seq,
        timestamp_ns=s.timestamp_ns,
        best_bid=float(price_from_fixed(s.best_bid)) if s.best_bid is not None else None,
        best_ask=float(price_from_fixed(s.best_ask)) if s.best_ask is not None else None,
        bid_depth=float(size_from_fixed(s.bid_depth)),
        ask_depth=float(size_from_fixed(s.ask_depth)),
        depth_imbalance=float(s.depth_imbalance),
        sequence_gap=s.sequence_gap,
        missing=s.missing,
        is_crossed=s.is_crossed,
        confidence=s.confidence.value,
    )


def l2_to_response(snapshots: list[L2Snapshot], summary: L2Summary) -> L2Response:
    return L2Response(
        symbol=summary.symbol,
        updates=summary.updates,
        sequence_gap_count=summary.sequence_gap_count,
        total_missing=summary.total_missing,
        crossed_count=summary.crossed_count,
        final_confidence=summary.final_confidence.value,
        bid_levels=summary.bid_levels,
        ask_levels=summary.ask_levels,
        confidence_states_seen=sorted({s.confidence.value for s in snapshots}),
        snapshots=[_l2_snapshot(s) for s in snapshots],
    )


class PnlPoint(BaseModel):
    seq: int
    timestamp_ns: int
    pnl: float
    cum_pnl: float
    tainted: bool


class FlaggedEvent(BaseModel):
    seq: int
    defects: list[str]


class SeriesResponse(BaseModel):
    symbol: str
    total_events: int
    flagged_events: int
    raw_curve: list[PnlPoint]
    clean_curve: list[PnlPoint]
    flagged: list[FlaggedEvent]


def to_response(
    result: DemoResult, schema: InferredSchema | None = None
) -> AnalysisResponse:
    m = result.mirage
    return AnalysisResponse(
        symbol=result.symbol,
        total_events=result.total_events,
        flagged_events=result.flagged_events,
        load_errors=result.load_errors,
        mirage_score=float(m.mirage_score),
        research_safe=m.research_safe,
        conclusion=m.conclusion,
        raw=_metrics(m.raw),
        clean=_metrics(m.clean),
        raw_checksum=result.raw_checksum,
        clean_checksum=result.clean_checksum,
        validation=[
            ValidationCheckModel(
                name=r.name,
                status=r.status.value,
                count=r.count,
                severity=r.severity.value,
            )
            for r in result.validation_results
        ],
        inferred_schema=_schema(schema) if schema is not None else None,
    )
