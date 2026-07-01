"""API response models.

Decimals from the pipeline are surfaced as floats here: this is the display/JSON
boundary, and the exact values remain available via the deterministic checksums.
"""

from __future__ import annotations

from pydantic import BaseModel
from quantstream_demo import DemoResult
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
