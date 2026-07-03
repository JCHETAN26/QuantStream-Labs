"""The reproducibility lock.

Given the committed official dataset and its ``expected_results.json``, the engine
must reproduce, exactly:

  * the validation failure count and high-severity count,
  * the raw and clean replay checksums,
  * the raw/clean Sharpe and PnL,
  * the Mirage score and the research_safe verdict,
  * the companion quote-dataset validation counts.

If any of these drift, this test fails — which is the whole point. A deliberate
pipeline change requires regenerating the dataset (`make regenerate-dataset`) and
committing the new expected_results.json.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from quantstream_replay import replay
from quantstream_research import MeanReversionStrategy, detect_alpha_mirage
from quantstream_schema import load_csv_path
from quantstream_validation import Severity, validate
from quantstream_validation import clean as clean_events

from quantstream_dataset_registry import ensure_dataset
from quantstream_dataset_registry.bootstrap import (
    STRATEGY_LOOKBACK,
    demo_backtest_config,
)


@pytest.fixture(scope="module")
def data_dir() -> Path:
    # strict=True verifies SHA-256 of the committed dataset before we trust it.
    return ensure_dataset(strict=True).data_dir


@pytest.fixture(scope="module")
def expected(data_dir: Path) -> dict:
    return json.loads((data_dir / "expected_results.json").read_text(encoding="utf-8"))


def _high_severity(report) -> int:
    return sum(r.count for r in report.results if r.severity == Severity.CRITICAL)


def _load(data_dir: Path, name: str) -> list:
    _schema, load = load_csv_path(str(data_dir / name))
    assert not load.errors, f"{name} had row errors: {load.errors[:3]}"
    return load.events


def test_trades_pipeline_matches_expected(data_dir: Path, expected: dict):
    events = _load(data_dir, expected["input_file"])
    assert len(events) == expected["event_count"]

    report = validate(events)
    assert report.flagged_events == expected["expected_validation_failures"]
    assert _high_severity(report) == expected["expected_high_severity_defects"]

    raw = replay(events)
    clean = replay(clean_events(events, report))
    assert raw.checksum == expected["expected_replay_checksum"]
    assert clean.checksum == expected["expected_replay_checksum_clean"]
    assert raw.config_hash == expected["expected_replay_config_hash"]

    mirage = detect_alpha_mirage(
        events,
        list(report.defect_map),
        MeanReversionStrategy(lookback=STRATEGY_LOOKBACK),
        config=demo_backtest_config(),
    )
    assert mirage.raw.sharpe == Decimal(expected["expected_raw_sharpe"])
    assert mirage.clean.sharpe == Decimal(expected["expected_clean_sharpe"])
    assert mirage.raw.total_pnl == Decimal(expected["expected_raw_pnl"])
    assert mirage.clean.total_pnl == Decimal(expected["expected_clean_pnl"])
    assert mirage.raw.tainted_pnl == Decimal(expected["expected_tainted_pnl"])
    assert mirage.mirage_score == Decimal(expected["expected_mirage_score"])
    assert mirage.research_safe == expected["expected_research_safe"]


def test_quotes_validation_matches_expected(data_dir: Path, expected: dict):
    q = expected["companion_quotes"]
    events = _load(data_dir, q["input_file"])
    assert len(events) == q["event_count"]

    report = validate(events)
    assert report.flagged_events == q["expected_validation_failures"]
    assert _high_severity(report) == q["expected_high_severity_defects"]

    counts = {r.defect.value: r.count for r in report.results if r.count}
    assert counts == q["expected_defect_counts"]


def test_expected_results_is_internally_consistent(expected: dict):
    # Mirage score is defined as tainted_pnl / raw_pnl on the raw run.
    score = Decimal(expected["expected_tainted_pnl"]) / Decimal(expected["expected_raw_pnl"])
    assert score == Decimal(expected["expected_mirage_score"])
    # Not research-safe iff the score is at/above the threshold.
    threshold = Decimal(expected["mirage_threshold"])
    assert expected["expected_research_safe"] == (abs(score) < threshold)
