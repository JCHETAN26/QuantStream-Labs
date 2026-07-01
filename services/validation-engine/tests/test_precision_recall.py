"""The honesty test.

The validation engine runs independently of the injector's ground truth. Here we
inject known defects and measure how well the detector recovers them. Two claims the
Alpha Mirage story depends on:

  * Recall: every injected defect is caught (the cleaning step won't miss corruption).
  * Zero-defect control: clean data produces zero flags (we don't manufacture defects
    where none exist).

The injected defect types here are the ones with unambiguous detection. Bad ticks
and stale quotes are threshold/heuristic checks covered in test_checks.py.
"""

from __future__ import annotations

from quantstream_validation import clean, validate
from quantstream_validation.injector import CorruptionConfig, corrupt

from ._helpers import clean_quotes, clean_trades


def _clean_dataset():
    trades = clean_trades(120, symbol="AAPL", start_seq=0)
    quotes = clean_quotes(120, symbol="MSFT", start_seq=1000)
    return [*trades, *quotes]


def test_zero_defect_control_produces_no_flags():
    report = validate(_clean_dataset())
    assert report.flagged_events == 0
    assert report.research_readiness == 1.0


def test_detector_recall_and_precision_on_injected_defects():
    clean_events = _clean_dataset()
    cfg = CorruptionConfig(
        seed=42,
        invalid_price_rate=0.10,
        invalid_size_rate=0.10,
        crossed_rate=0.15,
        out_of_order_rate=0.10,
        duplicate_rate=0.10,
    )
    result = corrupt(clean_events, cfg)
    report = validate(result.events)

    truth_seqs = set(result.truth)
    detected_seqs = set(report.defect_map)
    assert truth_seqs, "sanity: the injector should have produced some defects"

    caught = truth_seqs & detected_seqs
    recall = len(caught) / len(truth_seqs)
    precision = len(caught) / len(detected_seqs)

    assert recall == 1.0, f"missed defects: {sorted(truth_seqs - detected_seqs)}"
    assert precision == 1.0, f"false positives: {sorted(detected_seqs - truth_seqs)}"


def test_cleaning_corrupted_data_yields_clean_report():
    clean_events = _clean_dataset()
    cfg = CorruptionConfig(seed=3, invalid_price_rate=0.2, crossed_rate=0.2,
                           duplicate_rate=0.1, out_of_order_rate=0.1)
    result = corrupt(clean_events, cfg)
    report = validate(result.events)
    cleaned = clean(result.events, report)
    assert validate(cleaned).flagged_events == 0
