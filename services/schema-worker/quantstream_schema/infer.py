"""Schema inference: guess the event type and column mapping from headers + samples.

Header matching is by normalized name against curated alias sets. The timestamp unit
is inferred from the magnitude (or ISO shape) of a sample value. Confidence is the
fraction of the chosen event type's required fields that were matched, so a caller
can decide whether to trust the guess or ask the user to confirm.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from quantstream_contracts.enums import EventType

from .mapping import ColumnMapping, InferredSchema, TimestampUnit

_ALIASES: dict[str, set[str]] = {
    "timestamp": {"timestamp", "ts", "time", "datetime", "date", "tsevent",
                  "exchtime", "tsns", "sendingtime"},
    "symbol": {"symbol", "sym", "ticker", "instrument", "name", "secid"},
    "price": {"price", "px", "last", "tradeprice", "p", "fillprice"},
    "size": {"size", "qty", "quantity", "amount", "shares", "volume", "vol"},
    "side": {"side", "direction", "buysell", "aggressor"},
    "trade_id": {"tradeid", "id", "execid", "seq"},
    "venue": {"venue", "exchange", "exch", "market", "mic"},
    "bid_price": {"bid", "bidprice", "bidpx", "b"},
    "bid_size": {"bidsize", "bidqty", "bsize"},
    "ask_price": {"ask", "askprice", "askpx", "offer", "a"},
    "ask_size": {"asksize", "askqty", "asize"},
}


def _normalize(name: str) -> str:
    return "".join(ch for ch in name.strip().lower() if ch.isalnum())


def _match_columns(headers: Sequence[str]) -> dict[str, str]:
    matched: dict[str, str] = {}
    for header in headers:
        norm = _normalize(header)
        for field, aliases in _ALIASES.items():
            if field not in matched and norm in aliases:
                matched[field] = header
                break
    return matched


def _infer_timestamp_unit(sample: str) -> TimestampUnit:
    text = sample.strip()
    if any(c in text for c in "-T:") and not text.lstrip("-").isdigit():
        return TimestampUnit.ISO
    try:
        magnitude = abs(int(text))
    except ValueError:
        return TimestampUnit.NS
    if magnitude >= 10**17:
        return TimestampUnit.NS
    if magnitude >= 10**14:
        return TimestampUnit.US
    if magnitude >= 10**11:
        return TimestampUnit.MS
    return TimestampUnit.S


def _first_value(rows: Sequence[Mapping[str, str]], column: str) -> str:
    for row in rows:
        value = row.get(column, "").strip()
        if value:
            return value
    return ""


def infer_schema(
    headers: Sequence[str], sample_rows: Sequence[Mapping[str, str]]
) -> InferredSchema:
    matched = _match_columns(headers)
    matched_headers = set(matched.values())
    unmatched = tuple(h for h in headers if h not in matched_headers)
    notes: list[str] = []

    has = matched.__contains__
    if has("bid_price") and has("ask_price"):
        event_type = EventType.QUOTE
        required = ("timestamp", "symbol", "bid_price", "ask_price", "bid_size", "ask_size")
    elif has("price") and has("size"):
        event_type = EventType.TRADE
        required = ("timestamp", "symbol", "price", "size")
    else:
        event_type = EventType.TRADE
        required = ("timestamp", "symbol", "price", "size")
        notes.append("no strong trade/quote signal; defaulting to trade")

    ts_unit = TimestampUnit.NS
    if has("timestamp"):
        ts_unit = _infer_timestamp_unit(_first_value(sample_rows, matched["timestamp"]))
        notes.append(f"timestamp unit inferred as {ts_unit.value}")

    present = sum(1 for field in required if has(field))
    confidence = round(present / len(required), 2)
    missing = [f for f in required if not has(f)]
    if missing:
        notes.append("missing required fields: " + ", ".join(missing))

    mapping = ColumnMapping(
        timestamp=matched.get("timestamp", ""),
        symbol=matched.get("symbol", ""),
        timestamp_unit=ts_unit,
        price=matched.get("price"),
        size=matched.get("size"),
        side=matched.get("side"),
        trade_id=matched.get("trade_id"),
        venue=matched.get("venue"),
        bid_price=matched.get("bid_price"),
        bid_size=matched.get("bid_size"),
        ask_price=matched.get("ask_price"),
        ask_size=matched.get("ask_size"),
    )
    return InferredSchema(
        event_type=event_type,
        mapping=mapping,
        confidence=confidence,
        unmatched_columns=unmatched,
        notes=tuple(notes),
    )
