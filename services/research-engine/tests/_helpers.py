"""Trade builders for research-engine tests."""

from __future__ import annotations

from quantstream_contracts.enums import Side
from quantstream_contracts.events import Trade
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed


def trade(seq, ts, price, *, symbol="AAPL") -> Trade:
    return Trade(
        seq=seq,
        timestamp_ns=ts,
        symbol=symbol,
        price=price_to_fixed(price),
        size=size_to_fixed("1"),
        side=Side.BUY,
        trade_id=f"t{seq}",
        venue="XNAS",
    )


def series(prices, *, symbol="AAPL", start_seq=0, start_ts=1000, step=10):
    """Build a trade series with monotonically increasing timestamps."""
    return [
        trade(start_seq + i, start_ts + i * step, str(p), symbol=symbol)
        for i, p in enumerate(prices)
    ]
