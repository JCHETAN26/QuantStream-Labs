"""Shared book-confidence state machine.

Both L1 (top-of-book) and L2 (full-depth) books trust their state the same way: a
severe anomaly (a crossed book) is UNRELIABLE, a mild one (stale quote for L1, a
sequence gap for L2) is DEGRADED, and the book only returns to HEALTHY after a run
of clean updates.

    severe            -> UNRELIABLE
    mild              -> DEGRADED (unless already UNRELIABLE)
    clean (from bad)  -> RECOVERING
    clean x threshold -> HEALTHY
"""

from __future__ import annotations

from .state import BookConfidence


class ConfidenceTracker:
    def __init__(self, recovery_threshold: int) -> None:
        self.confidence = BookConfidence.HEALTHY
        self._threshold = recovery_threshold
        self._recovery_count = 0

    def observe(self, *, severe: bool, mild: bool) -> BookConfidence:
        if severe:
            self.confidence = BookConfidence.UNRELIABLE
            self._recovery_count = 0
        elif mild:
            if self.confidence in (BookConfidence.HEALTHY, BookConfidence.RECOVERING):
                self.confidence = BookConfidence.DEGRADED
            self._recovery_count = 0
        else:
            if self.confidence in (BookConfidence.DEGRADED, BookConfidence.UNRELIABLE):
                self.confidence = BookConfidence.RECOVERING
                self._recovery_count = 1
            elif self.confidence == BookConfidence.RECOVERING:
                self._recovery_count += 1
            if (
                self.confidence == BookConfidence.RECOVERING
                and self._recovery_count >= self._threshold
            ):
                self.confidence = BookConfidence.HEALTHY
                self._recovery_count = 0
        return self.confidence
