"""MomentumStrategy decisions and the no-lookahead guarantee."""

from __future__ import annotations

import pytest

from quantstream_research import MeanReversionStrategy, MomentumStrategy


def test_flat_until_window_is_full():
    s = MomentumStrategy(lookback=2)
    assert s.decide([100], 0) == (0, [0])
    assert s.decide([100, 110], 1) == (0, [1])


def test_long_short_flat():
    s = MomentumStrategy(lookback=1)
    assert s.decide([100, 110], 1)[0] == 1  # rose
    assert s.decide([100, 90], 1)[0] == -1  # fell
    assert s.decide([100, 100], 1)[0] == 0  # equal


def test_consulted_indices():
    s = MomentumStrategy(lookback=2)
    _, consulted = s.decide([100, 90, 110], 2)
    assert consulted == [0, 2]


def test_lookback_must_be_positive():
    with pytest.raises(ValueError):
        MomentumStrategy(lookback=0)


def test_no_lookahead():
    # The decision at i must be identical whether or not future prices exist.
    s = MomentumStrategy(lookback=2)
    prices = [100, 90, 110, 80, 120, 130]
    for i in range(len(prices)):
        assert s.decide(prices, i) == s.decide(prices[: i + 1], i)


def test_mean_reversion_fades_the_last_move():
    s = MeanReversionStrategy(lookback=1)
    assert s.decide([100, 110], 1)[0] == -1  # rose -> short
    assert s.decide([100, 90], 1)[0] == 1  # fell -> long
    assert s.decide([100, 100], 1)[0] == 0


def test_mean_reversion_no_lookahead():
    s = MeanReversionStrategy(lookback=1)
    prices = [100, 150, 100, 100, 60, 100]
    for i in range(len(prices)):
        assert s.decide(prices, i) == s.decide(prices[: i + 1], i)
