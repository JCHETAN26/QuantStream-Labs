"""Strategies.

A strategy decides a target position from the price history seen *so far*. The
critical contract is no lookahead: ``decide(prices, i)`` may only read
``prices[: i + 1]``. It also reports which indices it consulted, so the backtest can
build the causal chain for PnL attribution (a PnL contribution is tainted if any
event in that chain carries a defect flag).

Positions are unit-sized and directional: +1 long, -1 short, 0 flat.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Strategy(Protocol):
    def decide(self, prices: list[int], i: int) -> tuple[int, list[int]]:
        """Return (target_position, indices_consulted) using only prices[: i + 1]."""
        ...


@dataclass(frozen=True)
class MomentumStrategy:
    """Long if price rose over the lookback window, short if it fell, flat if equal
    or the window isn't full yet."""

    lookback: int = 1

    def __post_init__(self) -> None:
        if self.lookback < 1:
            raise ValueError(f"lookback must be >= 1, got {self.lookback}")

    def decide(self, prices: list[int], i: int) -> tuple[int, list[int]]:
        if i < self.lookback:
            return 0, [i]
        j = i - self.lookback
        if prices[i] > prices[j]:
            position = 1
        elif prices[i] < prices[j]:
            position = -1
        else:
            position = 0
        return position, [j, i]
