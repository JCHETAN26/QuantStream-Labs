"""Orchestrator: report assembly, statuses, defect map, and cleaning."""

from __future__ import annotations

from quantstream_validation import Defect, Status, clean, validate

from ._helpers import clean_trades, quote


def test_clean_data_passes_everything():
    report = validate(clean_trades(20))
    assert all(r.status == Status.PASS for r in report.results)
    assert report.defect_map == {}
    assert report.flagged_events == 0
    assert report.research_readiness == 1.0


def test_crossed_quote_fails_that_check():
    events = [*clean_trades(5), quote(100, 10, bid="101", ask="100")]
    report = validate(events)
    crossed = report.result_for(Defect.CROSSED_BOOK)
    assert crossed is not None
    assert crossed.status == Status.FAIL
    assert crossed.count == 1
    assert crossed.example_seqs == (100,)
    assert Defect.CROSSED_BOOK in report.defect_map[100]


def test_duplicate_warns_not_fails():
    from ._helpers import trade

    events = [trade(0, 5, trade_id="t1"), trade(1, 5, trade_id="t1")]
    report = validate(events)
    dup = report.result_for(Defect.DUPLICATE)
    assert dup is not None
    assert dup.status == Status.WARN


def test_clean_removes_flagged_events():
    events = [*clean_trades(5), quote(100, 10, bid="101", ask="100")]
    report = validate(events)
    cleaned = clean(events, report)
    assert len(cleaned) == 5
    assert all(e.seq != 100 for e in cleaned)


def test_research_readiness_fraction():
    events = [*clean_trades(9), quote(100, 10, bid="101", ask="100")]
    report = validate(events)
    # 1 of 10 events flagged.
    assert report.total_events == 10
    assert report.flagged_events == 1
    assert report.research_readiness == 0.9


def test_cleaning_is_idempotent():
    events = [*clean_trades(5), quote(100, 10, bid="101", ask="100")]
    cleaned = clean(events, validate(events))
    # Re-validating cleaned data should surface no defects.
    assert validate(cleaned).flagged_events == 0
