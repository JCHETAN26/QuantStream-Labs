"""PnL taint attribution: tainted PnL matches hand computation."""

from __future__ import annotations

from decimal import Decimal

from quantstream_research import MomentumStrategy, run_backtest

from ._helpers import series

# prices 100,110,120,130 (seqs 0..3), momentum lookback 1.
# contributions:
#   pnl1 (seq1->seq2)=10, causal {seq0,seq1,seq2}
#   pnl2 (seq2->seq3)=10, causal {seq1,seq2,seq3}
STRAT = MomentumStrategy(lookback=1)
EVENTS = series([100, 110, 120, 130])


def test_flagging_middle_event_taints_both_intervals():
    # seq2 appears in both causal chains -> all PnL tainted.
    result = run_backtest(EVENTS, [2], STRAT)
    assert result.metrics.total_pnl == Decimal(20)
    assert result.metrics.tainted_pnl == Decimal(20)


def test_flagging_first_event_taints_one_interval():
    # seq0 appears only in pnl1's causal chain; pnl2 stays clean.
    result = run_backtest(EVENTS, [0], STRAT)
    assert result.metrics.total_pnl == Decimal(20)
    assert result.metrics.tainted_pnl == Decimal(10)


def test_flagging_unrelated_event_taints_nothing():
    # A seq not present in the data flags nothing.
    result = run_backtest(EVENTS, [999], STRAT)
    assert result.metrics.tainted_pnl == Decimal(0)


def test_taint_is_causal_per_contribution():
    result = run_backtest(EVENTS, [3], STRAT)
    tainted = [c for c in result.contributions if c.tainted]
    # seq3 only in the last interval's causal chain.
    assert len(tainted) == 1
    assert tainted[0].to_seq == 3
