"""Metric helpers on known series."""

from __future__ import annotations

from decimal import Decimal

from quantstream_research import metrics


def test_sharpe_zero_when_no_variance():
    assert metrics.sharpe([Decimal(1), Decimal(1), Decimal(1)]) == Decimal(0)


def test_sharpe_known_value():
    # mean=1, population stdev = sqrt(((0-1)^2+(2-1)^2)/2)=1 -> sharpe 1
    assert metrics.sharpe([Decimal(0), Decimal(2)]) == Decimal(1)


def test_sharpe_short_series_is_zero():
    assert metrics.sharpe([Decimal(5)]) == Decimal(0)


def test_max_drawdown():
    # cumulative: 1, -1, 0. Peak 1, trough -1 -> drawdown 2.
    assert metrics.max_drawdown([Decimal(1), Decimal(-2), Decimal(1)]) == Decimal(2)


def test_max_drawdown_monotonic_up_is_zero():
    assert metrics.max_drawdown([Decimal(1), Decimal(1), Decimal(1)]) == Decimal(0)


def test_hit_rate_ignores_flat_intervals():
    # positions 1,1,0 -> active intervals are the first two; one win of two.
    rate = metrics.hit_rate([Decimal(1), Decimal(-1), Decimal(5)], [1, 1, 0])
    assert rate == Decimal("0.5")


def test_hit_rate_zero_when_all_flat():
    assert metrics.hit_rate([Decimal(1), Decimal(2)], [0, 0]) == Decimal(0)
