"""Transaction costs reduce net PnL and Sharpe."""

from __future__ import annotations

from decimal import Decimal

from quantstream_contracts.fixed_point import price_to_fixed

from quantstream_research import BacktestConfig, MomentumStrategy, run_backtest

from ._helpers import series

STRAT = MomentumStrategy(lookback=1)
EVENTS = series([100, 110, 120, 130])  # positions 0,+1,+1,+1; gross pnl 0,10,10


def test_zero_cost_is_frictionless():
    m = run_backtest(EVENTS, [], STRAT).metrics
    assert m.total_pnl == Decimal(20)
    assert m.gross_pnl == Decimal(20)
    assert m.total_cost == Decimal(0)


def test_cost_charged_on_position_change():
    # Enter the long once (turnover 1). Charge $2 per unit of position change.
    cfg = BacktestConfig(cost_per_unit=price_to_fixed("2"))
    m = run_backtest(EVENTS, [], STRAT, cfg).metrics
    assert m.gross_pnl == Decimal(20)
    assert m.total_cost == Decimal(2)
    assert m.total_pnl == Decimal(18)  # net = gross - cost


def test_cost_flows_into_tainted_pnl():
    cfg = BacktestConfig(cost_per_unit=price_to_fixed("2"))
    # Flag the middle event so both intervals are tainted; tainted PnL is net.
    m = run_backtest(EVENTS, [2], STRAT, cfg).metrics
    assert m.tainted_pnl == m.total_pnl == Decimal(18)


def test_higher_cost_lowers_net_pnl_monotonically():
    a = run_backtest(EVENTS, [], STRAT, BacktestConfig(price_to_fixed("1"))).metrics
    b = run_backtest(EVENTS, [], STRAT, BacktestConfig(price_to_fixed("3"))).metrics
    assert a.total_pnl > b.total_pnl
