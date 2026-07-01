"""Alpha Mirage Detector: fake alpha, honest control, and the auditable score."""

from __future__ import annotations

from decimal import Decimal

from quantstream_research import MomentumStrategy, detect_alpha_mirage

from ._helpers import series

STRAT = MomentumStrategy(lookback=1)


def test_terminal_bad_tick_creates_a_mirage():
    # A corrupted final print (500 instead of ~103) books a huge fake gain while
    # the position is long. Cleaning removes it and the edge evaporates.
    raw = series([100, 101, 102, 500])  # seq 3 is the bad tick
    report = detect_alpha_mirage(raw, flagged_seqs=[3], strategy=STRAT)

    # Raw books the fake gain (398); cleaned run keeps only the real +1.
    assert report.raw.total_pnl == Decimal(399)
    assert report.clean.total_pnl == Decimal(1)
    assert report.raw.total_pnl > report.clean.total_pnl

    # The tainted interval is the one whose realized return used the bad tick.
    assert report.raw.tainted_pnl == Decimal(398)
    assert report.mirage_score > Decimal("0.9")
    assert report.research_safe is False
    assert "not research-safe" in report.conclusion


def test_zero_defect_control_is_research_safe():
    # Same data, but nothing flagged: no PnL can be attributed to corruption.
    raw = series([100, 101, 102, 500])
    report = detect_alpha_mirage(raw, flagged_seqs=[], strategy=STRAT)
    assert report.mirage_score == Decimal(0)
    assert report.research_safe is True
    assert "research-safe" in report.conclusion


def test_clean_data_produces_no_mirage():
    # No corruption anywhere: a gentle uptrend, nothing flagged.
    raw = series([100, 101, 102, 103])
    report = detect_alpha_mirage(raw, flagged_seqs=[], strategy=STRAT)
    assert report.mirage_score == Decimal(0)
    assert report.research_safe is True


def test_mirage_score_is_recomputable_from_contributions():
    raw = series([100, 101, 102, 500])
    report = detect_alpha_mirage(raw, flagged_seqs=[3], strategy=STRAT)
    # score == tainted / total, an auditable ratio
    assert report.mirage_score == report.raw.tainted_pnl / report.raw.total_pnl
