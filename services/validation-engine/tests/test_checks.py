"""Each check: true path (defect present -> flagged) and false path (clean -> not)."""

from __future__ import annotations

from decimal import Decimal

from quantstream_contracts.enums import Side

from quantstream_validation import checks

from ._helpers import clean_quotes, clean_trades, quote, trade


def test_invalid_price_true_and_false():
    events = [trade(0, 1, price="100"), trade(1, 2, price="0")]
    assert checks.check_invalid_price(events) == {1}
    assert checks.check_invalid_price([trade(0, 1, price="100")]) == set()


def test_invalid_size_true_and_false():
    bad = trade(1, 2)
    good = trade(0, 1)
    from quantstream_contracts.events import Trade
    zero_size = Trade(seq=bad.seq, timestamp_ns=bad.timestamp_ns, symbol=bad.symbol,
                      price=bad.price, size=0, side=Side.BUY, trade_id="x", venue="X")
    assert checks.check_invalid_size([good, zero_size]) == {1}
    assert checks.check_invalid_size([good]) == set()


def test_crossed_book_true_and_false():
    crossed = quote(1, 2, bid="101", ask="100")
    ok = quote(0, 1, bid="100", ask="101")
    assert checks.check_crossed_book([ok, crossed]) == {1}
    assert checks.check_crossed_book([ok]) == set()


def test_locked_book_is_not_crossed():
    locked = quote(0, 1, bid="100", ask="100")
    assert checks.check_crossed_book([locked]) == set()


def test_duplicates_flag_second_occurrence():
    first = trade(0, 5, trade_id="t1")
    dup = trade(9, 5, trade_id="t1")  # same content, later seq
    flagged = checks.check_duplicates([first, dup])
    assert flagged == {9}


def test_no_duplicates_when_unique():
    events = clean_trades(5)
    assert checks.check_duplicates(events) == set()


def test_out_of_order_true_and_false():
    # seq order 0,1,2 but event seq=2 carries an earlier timestamp than seq=1.
    events = [trade(0, 100), trade(1, 200), trade(2, 150)]
    assert checks.check_out_of_order(events) == {2}
    assert checks.check_out_of_order(clean_trades(5)) == set()


def test_out_of_order_is_per_symbol():
    events = [trade(0, 100, symbol="AAA"), trade(1, 50, symbol="BBB")]
    # BBB's first event can't be out of order; different symbol from AAA.
    assert checks.check_out_of_order(events) == set()


def test_bad_tick_true_and_false():
    big_jump = [trade(0, 1, price="100"), trade(1, 2, price="130")]  # +30%
    assert checks.check_bad_tick(big_jump) == {1}
    gentle = [trade(0, 1, price="100"), trade(1, 2, price="100.5")]  # +0.5%
    assert checks.check_bad_tick(gentle) == set()


def test_bad_tick_threshold_is_configurable():
    events = [trade(0, 1, price="100"), trade(1, 2, price="105")]  # +5%
    assert checks.check_bad_tick(events, max_return=Decimal("0.10")) == set()
    assert checks.check_bad_tick(events, max_return=Decimal("0.01")) == {1}


def test_stale_quote_true_and_false():
    # Three identical quotes; the third is > stale_ns after the run start.
    q0 = quote(0, 0)
    q1 = quote(1, 1_000_000_000)
    q2 = quote(2, 6_000_000_000)  # 6s after run start, > 5s default
    assert checks.check_stale_quote([q0, q1, q2]) == {2}


def test_changing_quotes_are_not_stale():
    assert checks.check_stale_quote(clean_quotes(10)) == set()
