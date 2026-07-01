"""The bundled quote sample exercises every confidence state."""

from __future__ import annotations

from quantstream_orderbook import (
    SAMPLE_SYMBOL,
    BookConfidence,
    reconstruct,
    sample_quotes,
)


def test_sample_hits_all_confidence_states():
    snaps, _summaries = reconstruct(sample_quotes())
    seen = {s.confidence for s in snaps}
    assert seen == {
        BookConfidence.HEALTHY,
        BookConfidence.UNRELIABLE,
        BookConfidence.RECOVERING,
        BookConfidence.DEGRADED,
    }


def test_sample_summary():
    _snaps, summaries = reconstruct(sample_quotes())
    s = summaries[SAMPLE_SYMBOL]
    assert s.quotes == 12
    assert s.crossed_count == 1
    assert s.stale_count == 1
    assert s.final_confidence == BookConfidence.HEALTHY


def test_sample_is_deterministic():
    a, _ = reconstruct(sample_quotes())
    b, _ = reconstruct(sample_quotes())
    assert [s.confidence for s in a] == [s.confidence for s in b]
