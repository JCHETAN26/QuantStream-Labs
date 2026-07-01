"""Event builders for replay tests."""

from __future__ import annotations

from quantstream_contracts.enums import Side
from quantstream_contracts.events import Trade


def trade(seq, ts, *, symbol="AAPL", price=100_000_000_000, size=10_000_000_000):
    return Trade(
        seq=seq,
        timestamp_ns=ts,
        symbol=symbol,
        price=price,
        size=size,
        side=Side.BUY,
        trade_id=f"t{seq}",
        venue="XNAS",
    )


def mixed_stream():
    """A small multi-symbol stream with a deliberate timestamp tie."""
    return [
        trade(0, 100, symbol="AAPL"),
        trade(1, 100, symbol="MSFT"),  # ties AAPL@100 by timestamp; seq breaks it
        trade(2, 200, symbol="AAPL"),
        trade(3, 300, symbol="MSFT"),
        trade(4, 400, symbol="AAPL"),
    ]
