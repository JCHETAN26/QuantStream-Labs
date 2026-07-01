"""Validation orchestrator.

Runs every check, assembles the per-event ``defect_map`` and the human-facing
``CheckResult`` list, and provides ``clean()`` to drop flagged events for the
cleaned backtest run.

A check whose defect is CRITICAL (invalid price/size, crossed book) fails the
report; a WARNING defect (duplicate, out-of-order, stale, bad tick) warns. A clean
dataset passes every check.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantstream_contracts.events import Event

from . import checks
from .defects import Defect
from .report import CheckResult, Severity, Status, ValidationReport

_MAX_EXAMPLES = 5


@dataclass(frozen=True)
class ValidationConfig:
    max_tick_return: Decimal = checks.DEFAULT_MAX_TICK_RETURN
    stale_ns: int = checks.DEFAULT_STALE_NS


@dataclass(frozen=True)
class _CheckSpec:
    name: str
    defect: Defect
    severity: Severity
    impact: str
    run: object  # Callable[[list[Event], ValidationConfig], set[int]]


def _specs() -> list[_CheckSpec]:
    return [
        _CheckSpec(
            "Invalid price",
            Defect.INVALID_PRICE,
            Severity.CRITICAL,
            "Non-positive price; the event cannot be trusted for pricing or PnL.",
            lambda ev, cfg: checks.check_invalid_price(ev),
        ),
        _CheckSpec(
            "Invalid size",
            Defect.INVALID_SIZE,
            Severity.CRITICAL,
            "Non-positive size; volume and fills computed from it are wrong.",
            lambda ev, cfg: checks.check_invalid_size(ev),
        ),
        _CheckSpec(
            "Crossed book",
            Defect.CROSSED_BOOK,
            Severity.CRITICAL,
            "Bid above ask; spread and mid-price are nonsensical here.",
            lambda ev, cfg: checks.check_crossed_book(ev),
        ),
        _CheckSpec(
            "Duplicate events",
            Defect.DUPLICATE,
            Severity.WARNING,
            "Repeated event double-counts volume and can inflate signal PnL.",
            lambda ev, cfg: checks.check_duplicates(ev),
        ),
        _CheckSpec(
            "Out-of-order timestamps",
            Defect.OUT_OF_ORDER,
            Severity.WARNING,
            "Event arrives with an earlier timestamp than a prior row; risks lookahead.",
            lambda ev, cfg: checks.check_out_of_order(ev),
        ),
        _CheckSpec(
            "Bad ticks",
            Defect.BAD_TICK,
            Severity.WARNING,
            "Large price jump between consecutive trades; likely a bad print.",
            lambda ev, cfg: checks.check_bad_tick(ev, max_return=cfg.max_tick_return),
        ),
        _CheckSpec(
            "Stale quotes",
            Defect.STALE_QUOTE,
            Severity.WARNING,
            "Quote unchanged beyond the stale threshold; may misstate live spread.",
            lambda ev, cfg: checks.check_stale_quote(ev, stale_ns=cfg.stale_ns),
        ),
    ]


def _status(count: int, severity: Severity) -> Status:
    if count == 0:
        return Status.PASS
    return Status.FAIL if severity == Severity.CRITICAL else Status.WARN


def validate(
    events: list[Event], config: ValidationConfig | None = None
) -> ValidationReport:
    config = config or ValidationConfig()
    results: list[CheckResult] = []
    defect_map: dict[int, set[Defect]] = {}

    for spec in _specs():
        flagged = spec.run(events, config)  # type: ignore[operator]
        for seq in flagged:
            defect_map.setdefault(seq, set()).add(spec.defect)
        examples = tuple(sorted(flagged)[:_MAX_EXAMPLES])
        results.append(
            CheckResult(
                name=spec.name,
                defect=spec.defect,
                status=_status(len(flagged), spec.severity),
                severity=spec.severity,
                count=len(flagged),
                example_seqs=examples,
                impact=spec.impact,
            )
        )

    frozen_map = {seq: frozenset(defects) for seq, defects in defect_map.items()}
    return ValidationReport(
        results=tuple(results),
        defect_map=frozen_map,
        total_events=len(events),
    )


def clean(events: list[Event], report: ValidationReport) -> list[Event]:
    """Return events with every flagged event removed, preserving input order.

    V1 policy is remove, not correct: dropping a bad event is always defensible,
    whereas 'fixing' it invents data. Order is preserved so callers can re-derive
    the canonical order themselves.
    """
    return [event for event in events if event.seq not in report.defect_map]
