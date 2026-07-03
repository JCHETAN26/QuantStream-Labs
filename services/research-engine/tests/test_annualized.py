"""Annualized Sharpe: derived from per-step Sharpe and the data's trade frequency."""

from __future__ import annotations

from decimal import Decimal

from quantstream_contracts.enums import Side
from quantstream_contracts.events import Trade
from quantstream_contracts.fixed_point import price_to_fixed, size_to_fixed

from quantstream_research import MeanReversionStrategy, metrics, run_backtest


def _trade(seq, ts_ns, price):
    return Trade(seq, ts_ns, "X", price_to_fixed(price), size_to_fixed("1"),
                 Side.BUY, f"t{seq}", "V")


def test_annualized_helper_scales_by_sqrt_periods():
    # sharpe 2, 4 periods/year -> 2 * sqrt(4) = 4
    assert metrics.annualized_sharpe(Decimal(2), Decimal(4)) == Decimal(4)


def test_annualized_zero_when_no_periods():
    assert metrics.annualized_sharpe(Decimal(2), Decimal(0)) == Decimal(0)


def test_backtest_reports_annualized_from_timestamps():
    # 5 trades one second apart; annualized should be per-step * sqrt(periods/year).
    s = 1_000_000_000
    events = [_trade(i, i * s, str(100 + (i % 2))) for i in range(5)]
    m = run_backtest(events, [], MeanReversionStrategy(1)).metrics
    if m.sharpe == 0:
        assert m.sharpe_annualized == 0
    else:
        # annualized has the same sign and larger magnitude than per-step
        assert (m.sharpe_annualized > 0) == (m.sharpe > 0)
        assert abs(m.sharpe_annualized) > abs(m.sharpe)


def test_single_trade_has_no_annualization():
    m = run_backtest([_trade(0, 0, "100")], [], MeanReversionStrategy(1)).metrics
    assert m.sharpe_annualized == Decimal(0)
