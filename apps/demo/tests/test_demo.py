"""End-to-end demo: the mirage fires, and the whole run is deterministic."""

from __future__ import annotations

from decimal import Decimal

from quantstream_demo.cli import format_terminal, run_demo
from quantstream_demo.report import build_html


def test_demo_detects_the_mirage():
    result = run_demo()
    m = result.mirage
    # Raw looks profitable; cleaning collapses it.
    assert m.raw.total_pnl > m.clean.total_pnl
    assert m.raw.total_pnl > 0
    assert m.mirage_score > Decimal("0.5")
    assert m.research_safe is False
    assert result.flagged_events > 0


def test_demo_is_deterministic():
    a = run_demo()
    b = run_demo()
    assert a.raw_checksum == b.raw_checksum
    assert a.clean_checksum == b.clean_checksum
    assert a.mirage.mirage_score == b.mirage.mirage_score


def test_raw_and_clean_checksums_differ():
    # Cleaning removed events, so the two replays are not the same stream.
    result = run_demo()
    assert result.raw_checksum != result.clean_checksum


def test_terminal_output_has_verdict():
    text = format_terminal(run_demo())
    assert "Mirage Score:" in text
    assert "Conclusion:" in text


def test_html_report_renders_key_sections():
    html = build_html(run_demo())
    assert "Research Integrity Report" in html
    assert "Alpha Mirage" in html or "MIRAGE" in html
    assert "Raw vs Cleaned Performance" in html
    assert "Replay checksum" in html
