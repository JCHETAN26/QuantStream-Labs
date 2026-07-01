"""Golden serialization snapshot.

This locks the exact bytes of the canonical serialization. Two jobs:

  1. Regression guard: if anyone changes the byte layout, this fails loudly.
  2. Cross-language contract: the C++ replay engine (Lane C) will run against this
     same golden file and must reproduce every per-event hex string and the stream
     checksum exactly. That match is the "determinism across two languages" proof.

Regenerate intentionally after a deliberate format change:

    QS_UPDATE_GOLDEN=1 pytest packages/contracts/tests/test_golden.py

then commit the updated expected.json.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from quantstream_contracts.enums import BookAction, Side
from quantstream_contracts.events import OHLCV, L2Update, Quote, Trade
from quantstream_contracts.serialization import (
    canonical_sort,
    serialize_event,
    stream_checksum,
)

GOLDEN_PATH = Path(__file__).parent / "golden" / "expected.json"


def build_golden_events():
    """A fixed, diverse set of events. Order is deliberately not canonical so the
    snapshot also exercises canonical sorting."""
    return [
        Trade(
            seq=0,
            timestamp_ns=1_700_000_000_000_000_000,
            symbol="AAPL",
            price=100_070_000_000,
            size=5_000_000_000,
            side=Side.BUY,
            trade_id="t1",
            venue="XNAS",
        ),
        Quote(
            seq=1,
            timestamp_ns=1_700_000_000_000_000_050,
            symbol="MSFT",
            bid_price=420_000_000_000,
            bid_size=3_000_000_000,
            ask_price=420_010_000_000,
            ask_size=2_000_000_000,
            venue="XNAS",
        ),
        Trade(
            seq=2,
            timestamp_ns=1_700_000_000_000_000_000,  # ties with seq=0 by timestamp
            symbol="€STOXX",  # multi-byte UTF-8 symbol
            price=-3_500_000_000,  # negative price exercises signed int64
            size=1,
            side=Side.SELL,
            trade_id="",
            venue="",
        ),
        OHLCV(
            seq=3,
            timestamp_ns=1_700_000_000_000_001_000,
            symbol="SPY",
            open=450_000_000_000,
            high=451_500_000_000,
            low=449_250_000_000,
            close=451_000_000_000,
            volume=1_234_567_000_000_000,
            venue="ARCX",
        ),
        L2Update(
            seq=4,
            timestamp_ns=1_700_000_000_000_000_500,
            symbol="AAPL",
            side=Side.SELL,
            price=100_080_000_000,
            size=4_000_000_000,
            action=BookAction.DELETE,
            level=3,
            sequence_number=781_248,
            venue="XNAS",
        ),
    ]


def _current_snapshot() -> dict:
    events = build_golden_events()
    ordered = canonical_sort(events)
    return {
        "per_event_hex": [serialize_event(e).hex() for e in ordered],
        "stream_checksum": stream_checksum(events),
    }


def test_golden_snapshot():
    snapshot = _current_snapshot()

    if os.environ.get("QS_UPDATE_GOLDEN"):
        GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN_PATH.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        return

    assert GOLDEN_PATH.exists(), (
        "golden file missing; regenerate with QS_UPDATE_GOLDEN=1 pytest"
    )
    expected = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert snapshot == expected
