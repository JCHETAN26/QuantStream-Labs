"""End-to-end: corrupt -> validate -> detect_alpha_mirage.

Wires the real validation engine to the research engine. The detector's own
defect_map (not injection ground truth) drives cleaning and attribution, which is
how the production pipeline works.
"""

from __future__ import annotations

from decimal import Decimal

from quantstream_validation import corrupt, validate
from quantstream_validation.injector import CorruptionConfig

from quantstream_research import MomentumStrategy, detect_alpha_mirage

from ._helpers import series


def _uptrend(n):
    prices = [100 + i for i in range(n)]
    return series(prices, start_ts=1_000_000_000, step=1_000_000)


def test_full_pipeline_runs_and_cleans_detected_defects():
    clean_events = _uptrend(60)
    raw = corrupt(clean_events, CorruptionConfig(seed=11, bad_tick_rate=0.1,
                                                 duplicate_rate=0.05))

    report_v = validate(raw.events)
    assert report_v.flagged_events > 0, "sanity: validation should catch injected defects"

    flagged = list(report_v.defect_map)
    mirage = detect_alpha_mirage(raw.events, flagged_seqs=flagged,
                                 strategy=MomentumStrategy(lookback=3))

    # Cleaning removed the detected events, so the cleaned run sees fewer intervals.
    assert mirage.clean.total_intervals < mirage.raw.total_intervals
    # Score is a well-formed, auditable ratio.
    assert isinstance(mirage.mirage_score, Decimal)
    assert isinstance(mirage.research_safe, bool)


def test_pipeline_on_clean_data_finds_no_mirage():
    clean_events = _uptrend(60)
    report_v = validate(clean_events)
    assert report_v.flagged_events == 0

    mirage = detect_alpha_mirage(clean_events, flagged_seqs=[],
                                 strategy=MomentumStrategy(lookback=3))
    assert mirage.mirage_score == Decimal(0)
    assert mirage.research_safe is True
