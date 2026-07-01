"""Quote builder for orderbook tests."""

from __future__ import annotations

from quantstream_contracts.events import Quote
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed


def q(seq, ts, bid, ask, *, symbol="X") -> Quote:
    return Quote(
        seq=seq,
        timestamp_ns=ts,
        symbol=symbol,
        bid_price=price_to_fixed(bid),
        bid_size=size_to_fixed("1"),
        ask_price=price_to_fixed(ask),
        ask_size=size_to_fixed("1"),
        venue="V",
    )
