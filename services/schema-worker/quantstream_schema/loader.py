"""CSV loading into canonical events.

Given a schema (inferred or explicit), build Trade/Quote events row by row. A row
that fails to parse becomes a structured RowError and is skipped, never an unhandled
exception: a reviewer feeding a messy file gets a report, not a stack trace.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from quantstream_contracts.enums import EventType, Side
from quantstream_contracts.events import Event, Quote, Trade
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed

from .infer import infer_schema
from .mapping import ColumnMapping, InferredSchema
from .parsing import parse_side, parse_timestamp

_SAMPLE_ROWS_FOR_INFERENCE = 20


@dataclass(frozen=True)
class RowError:
    row_index: int
    reason: str


@dataclass(frozen=True)
class LoadResult:
    events: list[Event]
    errors: list[RowError]


def _req(row: Mapping[str, str], column: str | None) -> str:
    if column is None:
        raise ValueError("required field is not mapped")
    if column not in row:
        raise ValueError(f"missing column {column!r}")
    value = row[column]
    if value is None:
        raise ValueError(f"null value in column {column!r}")
    return value


def _opt(row: Mapping[str, str], column: str | None) -> str:
    if column is None:
        return ""
    return (row.get(column) or "").strip()


def _build_trade(seq: int, row: Mapping[str, str], m: ColumnMapping) -> Trade:
    return Trade(
        seq=seq,
        timestamp_ns=parse_timestamp(_req(row, m.timestamp), m.timestamp_unit),
        symbol=_req(row, m.symbol).strip(),
        price=price_to_fixed(_req(row, m.price).strip()),
        size=size_to_fixed(_req(row, m.size).strip()),
        side=parse_side(_opt(row, m.side)) if m.side else Side.UNKNOWN,
        trade_id=_opt(row, m.trade_id),
        venue=_opt(row, m.venue),
    )


def _build_quote(seq: int, row: Mapping[str, str], m: ColumnMapping) -> Quote:
    return Quote(
        seq=seq,
        timestamp_ns=parse_timestamp(_req(row, m.timestamp), m.timestamp_unit),
        symbol=_req(row, m.symbol).strip(),
        bid_price=price_to_fixed(_req(row, m.bid_price).strip()),
        bid_size=size_to_fixed(_req(row, m.bid_size).strip()),
        ask_price=price_to_fixed(_req(row, m.ask_price).strip()),
        ask_size=size_to_fixed(_req(row, m.ask_size).strip()),
        venue=_opt(row, m.venue),
    )


def load_events(
    rows: Sequence[Mapping[str, str]], schema: InferredSchema
) -> LoadResult:
    builder = _build_quote if schema.event_type == EventType.QUOTE else _build_trade
    events: list[Event] = []
    errors: list[RowError] = []
    for i, row in enumerate(rows):
        try:
            events.append(builder(i, row, schema.mapping))
        except Exception as exc:  # noqa: BLE001 - any bad row becomes a structured error
            errors.append(RowError(row_index=i, reason=str(exc)))
    return LoadResult(events=events, errors=errors)


def load_csv_text(text: str) -> tuple[InferredSchema, LoadResult]:
    """Infer the schema from the header + a sample of rows, then load every row."""
    reader = csv.DictReader(io.StringIO(text))
    headers = list(reader.fieldnames or [])
    rows = list(reader)
    schema = infer_schema(headers, rows[:_SAMPLE_ROWS_FOR_INFERENCE])
    return schema, load_events(rows, schema)


def load_csv_path(path: str | Path) -> tuple[InferredSchema, LoadResult]:
    return load_csv_text(Path(path).read_text(encoding="utf-8"))
