"""CSV loading into canonical events, including malformed-row handling."""

from __future__ import annotations

from quantstream_contracts.enums import Side
from quantstream_contracts.events import Quote, Trade
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed

from quantstream_schema import load_csv_text

TRADES_CSV = """ts,ticker,px,qty,side
1700000000000000000,AAPL,100.5,10,B
1700000000000000001,AAPL,100.6,5,S
"""


def test_load_trades():
    schema, result = load_csv_text(TRADES_CSV)
    assert not result.errors
    assert len(result.events) == 2
    first = result.events[0]
    assert isinstance(first, Trade)
    assert first.seq == 0
    assert first.timestamp_ns == 1700000000000000000
    assert first.symbol == "AAPL"
    assert first.price == price_to_fixed("100.5")
    assert first.size == size_to_fixed("10")
    assert first.side == Side.BUY
    assert result.events[1].side == Side.SELL


def test_malformed_row_becomes_error_not_crash():
    csv = "ts,ticker,px,qty\n1,AAPL,100,10\n2,AAPL,notanumber,5\n3,AAPL,101,7\n"
    schema, result = load_csv_text(csv)
    # Two good rows load; the bad one is reported.
    assert len(result.events) == 2
    assert len(result.errors) == 1
    assert result.errors[0].row_index == 1


def test_missing_required_column_errors_every_row():
    csv = "ts,ticker,qty\n1,AAPL,10\n2,AAPL,5\n"  # no price column
    schema, result = load_csv_text(csv)
    assert result.events == []
    assert len(result.errors) == 2


def test_load_quotes():
    csv = ("timestamp,symbol,bid,bid_size,ask,ask_size\n"
           "1700000000000,MSFT,100,5,101,6\n")
    schema, result = load_csv_text(csv)
    assert not result.errors
    assert len(result.events) == 1
    q = result.events[0]
    assert isinstance(q, Quote)
    assert q.bid_price == price_to_fixed("100")
    assert q.ask_size == size_to_fixed("6")
    # 13-digit epoch inferred as milliseconds -> nanoseconds
    assert q.timestamp_ns == 1700000000000 * 1_000_000
