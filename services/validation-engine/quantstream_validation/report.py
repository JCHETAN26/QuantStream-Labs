"""Validation result types.

A ``ValidationReport`` carries two things downstream:

  * ``results`` - one ``CheckResult`` per check, the human-facing summary
    (status / count / severity / example offenders / impact).
  * ``defect_map`` - seq -> the set of defects flagged on that event. This is the
    machine-facing output: the cleaning step drops flagged events, and PnL
    attribution later taints any trade whose causal events appear here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .defects import Defect


class Status(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CheckResult:
    name: str
    defect: Defect
    status: Status
    severity: Severity
    count: int
    example_seqs: tuple[int, ...]
    impact: str


@dataclass(frozen=True)
class ValidationReport:
    results: tuple[CheckResult, ...]
    defect_map: dict[int, frozenset[Defect]]
    total_events: int

    @property
    def flagged_events(self) -> int:
        return len(self.defect_map)

    @property
    def research_readiness(self) -> float:
        """Fraction of events with no defect flag. 1.0 == pristine."""
        if self.total_events == 0:
            return 1.0
        return 1.0 - (self.flagged_events / self.total_events)

    def result_for(self, defect: Defect) -> CheckResult | None:
        for result in self.results:
            if result.defect == defect:
                return result
        return None
