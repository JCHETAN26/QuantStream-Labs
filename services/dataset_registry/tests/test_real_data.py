"""The platform processes a real Coinbase tape deterministically."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from quantstream_replay import replay
from quantstream_schema import load_csv_path
from quantstream_validation import validate

from quantstream_dataset_registry import generate

_REPO = Path(__file__).resolve().parents[3]
_REAL = _REPO / "data" / "real"


def _expected() -> dict:
    return json.loads((_REAL / "expected.json").read_text())


def test_real_tape_loads_and_is_clean():
    _schema, load = load_csv_path(str(_REAL / "btcusd_coinbase.csv"))
    expected = _expected()
    assert not load.errors
    assert len(load.events) == expected["events"]
    assert validate(load.events).flagged_events == expected["natural_defects"]


def test_real_tape_replay_checksum_is_locked():
    _schema, load = load_csv_path(str(_REAL / "btcusd_coinbase.csv"))
    assert replay(load.events).checksum == _expected()["replay_checksum"]


def test_no_edge_strategy_loses_on_the_clean_real_tape():
    from quantstream_contracts.fixed_point import price_to_fixed
    from quantstream_research import (
        BacktestConfig,
        MeanReversionStrategy,
        detect_alpha_mirage,
    )

    _schema, load = load_csv_path(str(_REAL / "btcusd_coinbase.csv"))
    report = validate(load.events)
    m = detect_alpha_mirage(
        load.events, list(report.defect_map), MeanReversionStrategy(1),
        config=BacktestConfig(cost_per_unit=price_to_fixed("0.50")),
    )
    assert m.clean.total_pnl == Decimal(_expected()["clean_strategy_pnl"])
    assert m.clean.total_pnl < 0  # no real edge -> loses after costs


def test_fmt_never_uses_scientific_notation():
    # The bug real data exposed: tiny sizes must render "0.00000026", not "2.6E-7".
    assert generate._fmt(260, 1_000_000_000) == "0.00000026"
    assert "E" not in generate._fmt(1, 1_000_000_000)
