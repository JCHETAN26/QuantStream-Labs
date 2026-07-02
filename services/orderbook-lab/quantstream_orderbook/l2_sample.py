"""A bundled L2 update stream exercising sequence gaps, crossed books, and recovery."""

from __future__ import annotations

from decimal import Decimal

from quantstream_contracts.enums import BookAction, Side
from quantstream_contracts.events import L2Update
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed

SAMPLE_SYMBOL = "L2BOOK"


def _u(seq, ts, seqnum, side, action, price, size, level) -> L2Update:
    return L2Update(
        seq=seq,
        timestamp_ns=ts * 1_000_000_000,
        symbol=SAMPLE_SYMBOL,
        side=side,
        price=price_to_fixed(Decimal(price)),
        size=size_to_fixed(Decimal(size)),
        action=action,
        level=level,
        sequence_number=seqnum,
        venue="DEMO",
    )


def sample_l2_updates() -> list[L2Update]:
    B, S = Side.BUY, Side.SELL
    ADD, UPD, DEL = BookAction.ADD, BookAction.UPDATE, BookAction.DELETE
    return [
        _u(0, 0, 100, B, ADD, "100.00", "10", 0),
        _u(1, 1, 101, S, ADD, "100.05", "10", 0),
        _u(2, 2, 102, B, ADD, "99.99", "8", 1),
        _u(3, 3, 103, S, ADD, "100.06", "8", 1),
        _u(4, 4, 105, B, UPD, "100.00", "12", 0),  # seq 104 missing -> gap -> DEGRADED
        _u(5, 5, 106, S, UPD, "100.05", "9", 0),   # clean -> RECOVERING (1)
        _u(6, 6, 107, B, ADD, "100.01", "5", 0),   # clean -> RECOVERING (2)
        _u(7, 7, 108, S, UPD, "100.06", "7", 1),   # clean -> RECOVERING (3) -> HEALTHY
        _u(8, 8, 109, B, ADD, "100.10", "4", 0),   # bid above ask -> CROSSED -> UNRELIABLE
        _u(9, 9, 110, B, DEL, "100.10", "0", 0),   # remove crossing bid -> RECOVERING (1)
        _u(10, 10, 111, S, UPD, "100.05", "6", 0),  # clean -> RECOVERING (2)
        _u(11, 11, 112, B, UPD, "100.00", "15", 0),  # clean -> RECOVERING (3) -> HEALTHY
    ]
