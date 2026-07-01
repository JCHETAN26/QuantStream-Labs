"""The defect taxonomy.

These are the market-data pathologies the validation engine detects and the
corruption injector injects. The same enum is used for both, which is what lets us
measure the detector's precision and recall against injection ground truth.

String values are stable identifiers (used in reports and the eventual
`defect_flags` that travel with events into PnL attribution). Append only.
"""

from __future__ import annotations

from enum import Enum


class Defect(str, Enum):
    DUPLICATE = "duplicate"
    OUT_OF_ORDER = "out_of_order"
    INVALID_PRICE = "invalid_price"
    INVALID_SIZE = "invalid_size"
    CROSSED_BOOK = "crossed_book"
    STALE_QUOTE = "stale_quote"
    BAD_TICK = "bad_tick"
