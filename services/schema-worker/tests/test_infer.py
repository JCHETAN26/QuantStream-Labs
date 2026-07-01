"""Schema inference from headers + sample rows."""

from __future__ import annotations

from quantstream_contracts.enums import EventType

from quantstream_schema import TimestampUnit, infer_schema


def test_infer_trade_schema():
    headers = ["ts", "ticker", "px", "qty", "side", "exchange"]
    rows = [{"ts": "1700000000000000000", "ticker": "AAPL", "px": "100.5",
             "qty": "10", "side": "B", "exchange": "XNAS"}]
    s = infer_schema(headers, rows)
    assert s.event_type == EventType.TRADE
    assert s.mapping.timestamp == "ts"
    assert s.mapping.symbol == "ticker"
    assert s.mapping.price == "px"
    assert s.mapping.size == "qty"
    assert s.mapping.side == "side"
    assert s.mapping.venue == "exchange"
    assert s.confidence == 1.0


def test_infer_quote_schema():
    headers = ["timestamp", "symbol", "bid", "bid_size", "ask", "ask_size"]
    rows = [{"timestamp": "1700000000000", "symbol": "MSFT", "bid": "100",
             "bid_size": "5", "ask": "101", "ask_size": "5"}]
    s = infer_schema(headers, rows)
    assert s.event_type == EventType.QUOTE
    assert s.confidence == 1.0
    assert s.mapping.bid_price == "bid"
    assert s.mapping.ask_price == "ask"


def test_timestamp_unit_inference():
    def unit(sample):
        return infer_schema(["ts", "sym", "px", "qty"],
                            [{"ts": sample, "sym": "X", "px": "1", "qty": "1"}]
                            ).mapping.timestamp_unit

    assert unit("1700000000000000000") == TimestampUnit.NS
    assert unit("1700000000000") == TimestampUnit.MS
    assert unit("1700000000") == TimestampUnit.S
    assert unit("2023-11-14T22:13:20+00:00") == TimestampUnit.ISO


def test_unmatched_columns_reported():
    headers = ["ts", "ticker", "px", "qty", "mystery_col"]
    rows = [{"ts": "1", "ticker": "A", "px": "1", "qty": "1", "mystery_col": "?"}]
    s = infer_schema(headers, rows)
    assert "mystery_col" in s.unmatched_columns


def test_low_confidence_when_size_missing():
    headers = ["ts", "ticker", "px"]
    rows = [{"ts": "1", "ticker": "A", "px": "1"}]
    s = infer_schema(headers, rows)
    assert s.confidence < 1.0
    assert any("missing" in n for n in s.notes)
