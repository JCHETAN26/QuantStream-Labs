"""Dataset acquisition: offline generation, cache reuse, and tamper detection."""

from __future__ import annotations

import pytest

from quantstream_dataset_registry import ChecksumError, ensure_dataset
from quantstream_dataset_registry.bootstrap import HASHED_FILES
from quantstream_dataset_registry.checksums import SHA256SUMS_NAME
from quantstream_dataset_registry.registry import fetch_dataset


def test_generate_offline_into_tmp(tmp_path):
    status = fetch_dataset(data_dir=tmp_path, prefer_hf=False)
    assert status.ready
    assert status.source == "generated"
    assert status.verify.summary() == f"{len(HASHED_FILES)}/{len(HASHED_FILES)}"
    for name in HASHED_FILES:
        assert (tmp_path / name).is_file()


def test_second_call_uses_cache(tmp_path):
    fetch_dataset(data_dir=tmp_path, prefer_hf=False)
    status = fetch_dataset(data_dir=tmp_path, prefer_hf=False)
    assert status.source == "cache"
    assert status.ready


def test_force_regenerates_but_is_byte_stable(tmp_path):
    fetch_dataset(data_dir=tmp_path, prefer_hf=False)
    before = (tmp_path / SHA256SUMS_NAME).read_bytes()
    fetch_dataset(data_dir=tmp_path, prefer_hf=False, force=True)
    after = (tmp_path / SHA256SUMS_NAME).read_bytes()
    assert before == after


def test_ensure_dataset_strict_fails_on_tamper(tmp_path):
    fetch_dataset(data_dir=tmp_path, prefer_hf=False)
    # Corrupt a data file without updating SHA256SUMS.
    (tmp_path / "defective_trades.csv").write_text("ts,sym\n1,X\n", encoding="utf-8")
    with pytest.raises(ChecksumError):
        ensure_dataset(data_dir=tmp_path, strict=True)


def test_ensure_dataset_debug_regenerates_on_tamper(tmp_path):
    fetch_dataset(data_dir=tmp_path, prefer_hf=False)
    (tmp_path / "defective_trades.csv").write_text("garbage", encoding="utf-8")
    # Non-strict (debug) mode repairs the dataset instead of raising.
    status = ensure_dataset(data_dir=tmp_path, strict=False)
    assert status.ready
    assert status.source == "generated"


def test_hf_unavailable_falls_back_to_generation(tmp_path, monkeypatch):
    from quantstream_dataset_registry import hf

    # Pretend the hub library is present but every attempt fails.
    monkeypatch.setattr(hf, "is_available", lambda: True)

    def _boom(*a, **k):
        raise hf.HFUnavailable("no network")

    monkeypatch.setattr(hf, "download_snapshot", _boom)

    status = fetch_dataset(data_dir=tmp_path, prefer_hf=True)
    assert status.ready
    assert status.source == "generated"


def test_hf_unavailable_without_generation_raises(tmp_path, monkeypatch):
    from quantstream_dataset_registry import hf

    monkeypatch.setattr(hf, "is_available", lambda: True)

    def _boom(*a, **k):
        raise hf.HFUnavailable("no network")

    monkeypatch.setattr(hf, "download_snapshot", _boom)

    with pytest.raises(hf.HFUnavailable):
        fetch_dataset(data_dir=tmp_path, prefer_hf=True, allow_generate=False)


def test_hf_missing_library_reports_unavailable():
    from quantstream_dataset_registry import hf

    # is_available reflects whether the optional extra is importable; either way it
    # must return a bool and never raise.
    assert isinstance(hf.is_available(), bool)
