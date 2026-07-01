"""Builders for clean, defect-free market data used across the validation tests."""

from __future__ import annotations

from decimal import Decimal

from quantstream_contracts.enums import Side
from quantstream_contracts.events import Quote, Trade
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed


def trade(seq, ts, *, symbol="AAPL", price="100", size="10", side=Side.BUY,
          trade_id=None, venue="XNAS") -> Trade:
    return Trade(
        seq=seq,
        timestamp_ns=ts,
        symbol=symbol,
        price=price_to_fixed(price),
        size=size_to_fixed(size),
        side=side,
        trade_id=trade_id if trade_id is not None else f"t{seq}",
        venue=venue,
    )


def quote(seq, ts, *, symbol="AAPL", bid="100", bid_sz="5", ask="101", ask_sz="5",
          venue="XNAS") -> Quote:
    return Quote(
        seq=seq,
        timestamp_ns=ts,
        symbol=symbol,
        bid_price=price_to_fixed(bid),
        bid_size=size_to_fixed(bid_sz),
        ask_price=price_to_fixed(ask),
        ask_size=size_to_fixed(ask_sz),
        venue=venue,
    )


def clean_trades(n, *, symbol="AAPL", start_ts=1_000_000_000, step=1_000_000,
                 base_price="100.00", start_seq=0):
    """Monotonic timestamps, a gentle price walk (well under any bad-tick threshold),
    positive sizes, no duplicates."""
    out = []
    price = Decimal(base_price)
    for i in range(n):
        out.append(
            trade(start_seq + i, start_ts + i * step, symbol=symbol,
                  price=price, size="10")
        )
        price += Decimal("0.01")
    return out


def clean_quotes(n, *, symbol="AAPL", start_ts=1_000_000_000, step=1_000_000,
                 start_seq=0):
    """Monotonic timestamps, bid strictly below ask, values change each step so no
    stale run forms."""
    out = []
    bid = Decimal("100.00")
    for i in range(n):
        ask = bid + Decimal("0.02")
        out.append(
            quote(start_seq + i, start_ts + i * step, symbol=symbol,
                  bid=bid, ask=ask)
        )
        bid += Decimal("0.01")
    return out
