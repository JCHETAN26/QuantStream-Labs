"""Backtest mechanics on a hand-computed series."""

from __future__ import annotations

from decimal import Decimal

from quantstream_research import MomentumStrategy, run_backtest

from ._helpers import series, trade

# prices 100 -> 110 -> 120 -> 130, momentum lookback 1:
#   positions: i0=flat, i1=+1, i2=+1, i3=+1 (no interval after)
#   pnl: i0 = 0, i1 = +1*(120-110)=10, i2 = +1*(130-120)=10  => total 20
STRAT = MomentumStrategy(lookback=1)


def test_pnl_and_positions():
    result = run_backtest(series([100, 110, 120, 130]), [], STRAT)
    m = result.metrics
    assert m.total_pnl == Decimal(20)
    assert m.tainted_pnl == Decimal(0)
    assert m.total_intervals == 3
    assert m.active_intervals == 2  # i1 and i2 held +1


def test_turnover_counts_position_changes():
    # flat -> long is one change; then long held (no further change).
    result = run_backtest(series([100, 110, 120, 130]), [], STRAT)
    assert result.metrics.turnover == 1


def test_hit_rate_all_wins():
    result = run_backtest(series([100, 110, 120, 130]), [], STRAT)
    assert result.metrics.hit_rate == Decimal(1)


def test_short_side_pnl():
    # falling series, momentum goes short and profits as price drops.
    result = run_backtest(series([130, 120, 110, 100]), [], STRAT)
    # i1=-1*(110-120)=10, i2=-1*(100-110)=10 => 20
    assert result.metrics.total_pnl == Decimal(20)


def test_multi_symbol_pooled():
    events = [
        *series([100, 110, 120], symbol="AAPL", start_seq=0),
        *series([50, 40, 30], symbol="MSFT", start_seq=100),
    ]
    result = run_backtest(events, [], STRAT)
    # AAPL: i1=+1*(120-110)=10. MSFT: i1=-1*(30-40)=10. total 20.
    assert result.metrics.total_pnl == Decimal(20)
    assert result.metrics.total_intervals == 4  # 2 per symbol


def test_last_trade_has_no_interval():
    result = run_backtest([trade(0, 1, "100")], [], STRAT)
    assert result.metrics.total_intervals == 0
    assert result.metrics.total_pnl == Decimal(0)
