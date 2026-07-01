"""QuantStream Labs OrderBookLab (L1).

Reconstructs top-of-book from quotes: best bid/ask, spread, mid-price, quote age,
crossed and stale detection, and a book-confidence state machine.
"""

from __future__ import annotations

from .book import (
    DEFAULT_RECOVERY_THRESHOLD,
    DEFAULT_STALE_NS,
    OrderBook,
    OrderBookConfig,
    reconstruct,
)
from .l2 import L2Book, L2Config, L2Snapshot, L2Summary, reconstruct_l2
from .l2_sample import SAMPLE_SYMBOL as L2_SAMPLE_SYMBOL
from .l2_sample import sample_l2_updates
from .sample import SAMPLE_SYMBOL, sample_quotes
from .state import BookConfidence, BookSnapshot, BookSummary

__all__ = [
    "OrderBook",
    "OrderBookConfig",
    "reconstruct",
    "DEFAULT_STALE_NS",
    "DEFAULT_RECOVERY_THRESHOLD",
    "BookConfidence",
    "BookSnapshot",
    "BookSummary",
    "sample_quotes",
    "SAMPLE_SYMBOL",
    "L2Book",
    "L2Config",
    "L2Snapshot",
    "L2Summary",
    "reconstruct_l2",
    "sample_l2_updates",
    "L2_SAMPLE_SYMBOL",
]
