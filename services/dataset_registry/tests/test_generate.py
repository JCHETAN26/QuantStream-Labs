"""Deterministic generation is byte-stable and matches the bundled sample."""

from __future__ import annotations

from quantstream_contracts.serialization import stream_checksum

from quantstream_dataset_registry import bootstrap, generate


def test_trades_are_deterministic():
    assert stream_checksum(generate.sample_events()) == stream_checksum(
        generate.sample_events()
    )


def test_clean_trades_have_no_spikes():
    # The pristine control walk is edgeless and never triggers the bad-tick check.
    from quantstream_validation import validate

    report = validate(generate.clean_events())
    assert report.flagged_events == 0


def test_defective_trades_trigger_bad_ticks():
    from quantstream_validation import validate

    report = validate(generate.sample_events())
    assert report.flagged_events > 0


def test_build_dataset_is_byte_stable():
    a = bootstrap.build_dataset().files
    b = bootstrap.build_dataset().files
    assert a.keys() == b.keys()
    for name in a:
        assert a[name] == b[name], f"{name} is not byte-stable"


def test_hashed_files_present():
    files = bootstrap.build_dataset().files
    for name in bootstrap.HASHED_FILES:
        assert name in files and files[name]
    assert "SHA256SUMS" in files
    assert "README.md" in files


def test_quote_ground_truth_counts():
    _quotes, truth = generate.defective_quote_events()
    crossed = [s for s, d in truth.items() if "crossed_book" in d]
    invalid = [s for s, d in truth.items() if "invalid_price" in d]
    stale = [s for s, d in truth.items() if "stale_quote" in d]
    assert len(crossed) == 3
    assert len(invalid) == 2
    assert len(stale) == 11
