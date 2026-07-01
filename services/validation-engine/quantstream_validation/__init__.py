"""QuantStream Labs validation engine.

Detects market-data defects (duplicates, out-of-order, invalid price/size, crossed
books, stale quotes, bad ticks), produces a per-event defect map plus a human-facing
report, and cleans a dataset by dropping flagged events. The paired corruption
injector lets us measure the detector's precision and recall against ground truth.
"""

from __future__ import annotations

from .defects import Defect
from .engine import ValidationConfig, clean, validate
from .injector import CorruptionConfig, CorruptionResult, corrupt
from .report import CheckResult, Severity, Status, ValidationReport

__all__ = [
    "Defect",
    "ValidationConfig",
    "validate",
    "clean",
    "CorruptionConfig",
    "CorruptionResult",
    "corrupt",
    "CheckResult",
    "Severity",
    "Status",
    "ValidationReport",
]
