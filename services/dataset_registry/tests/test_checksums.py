"""SHA-256 manifest render/parse/verify, including the fail-loud path."""

from __future__ import annotations

import pytest

from quantstream_dataset_registry.checksums import (
    ChecksumError,
    parse_sha256sums,
    render_sha256sums,
    sha256_bytes,
    verify_directory,
    verify_or_raise,
)


def test_render_is_sorted_and_roundtrips():
    entries = {"b.csv": "22" * 32, "a.csv": "11" * 32}
    text = render_sha256sums(entries)
    # Sorted by filename for determinism.
    assert text.splitlines()[0].endswith("a.csv")
    assert parse_sha256sums(text) == entries


def test_parse_ignores_blank_and_comment_lines():
    text = "# comment\n\n" + ("aa" * 32) + "  file.csv\n"
    assert parse_sha256sums(text) == {"file.csv": "aa" * 32}


def test_verify_directory_pass(tmp_path):
    (tmp_path / "x.txt").write_bytes(b"hello")
    sums = {"x.txt": sha256_bytes(b"hello")}
    result = verify_directory(tmp_path, sums)
    assert result.ok
    assert result.summary() == "1/1"


def test_verify_directory_detects_mismatch(tmp_path):
    (tmp_path / "x.txt").write_bytes(b"tampered")
    sums = {"x.txt": sha256_bytes(b"original")}
    result = verify_directory(tmp_path, sums)
    assert not result.ok
    assert "x.txt" in result.mismatched


def test_verify_directory_detects_missing(tmp_path):
    sums = {"gone.txt": sha256_bytes(b"x")}
    result = verify_directory(tmp_path, sums)
    assert not result.ok
    assert "gone.txt" in result.missing


def test_verify_or_raise_fails_loudly(tmp_path):
    (tmp_path / "x.txt").write_bytes(b"tampered")
    with pytest.raises(ChecksumError):
        verify_or_raise(tmp_path, {"x.txt": sha256_bytes(b"original")})
