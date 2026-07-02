# Alpha Mirage

## What it is

An **alpha mirage** is apparent strategy performance that exists only because the
underlying market data is corrupted. Remove the bad events and the performance
collapses. QuantStream Labs detects this and attributes the false PnL to the specific
defects that caused it.

> **What this is not.** This is not a profitability engine and not a trading bot. It
> makes no claim that any strategy is profitable. The claim is narrow and testable:
> *simulated performance can be materially dependent on corrupted market-data
> regions, and that dependence is measurable.*

## Raw vs cleaned comparison

The detector runs the **same strategy twice**:

1. **Raw:** on all events, with defect-flagged events present. PnL contributions
   touching a flagged event are marked *tainted*.
2. **Cleaned:** on the events that survive `clean()` (flagged events removed).

If raw performance depends on corrupted events, the cleaned run collapses.

## Strategy and assumptions

The demo strategy is a unit-position **mean-reversion** rule (fade the last move:
short after a rise, long after a fall). It is intentionally the strategy that gets
fooled by bad data: it fades a spurious price spike and books the "reversion" that
is really just the bad tick correcting itself.

Assumptions, stated plainly:

- **No lookahead.** A strategy's `decide(prices, i)` may only read `prices[: i + 1]`,
  and it reports exactly which indices it consulted. This is enforced by the
  interface and is the basis for honest attribution.
- **Event-time processing** in canonical `(timestamp_ns, seq)` order, per symbol.
- **Unit positions** (+1 / 0 / −1). The demo measures *dependence on bad data*, not
  position sizing or capacity.
- **Per-step Sharpe**, not annualized (see below).

## PnL attribution to flagged events

Each holding interval `[t, t+1]` produces one PnL contribution. A contribution is
**tainted** iff any event in its causal chain carries a defect flag:

```text
causal chain = { indices the strategy consulted at t } ∪ { event t, event t+1 }
```

This is the honest basis for "N% of PnL came from corrupted events": we sum the PnL
of *tainted* contributions — where a flagged event is actually in the causal chain —
not PnL that merely correlates with defects in time. No lookahead, no correlation
hand-waving.

## Mirage score

```text
mirage_score = tainted_pnl(raw) / total_pnl(raw)
```

One auditable ratio. A reviewer can recompute it directly from the raw backtest's
per-interval contributions. If `total_pnl` is zero the score is defined as zero.

## research_safe threshold

```text
research_safe = |mirage_score| < threshold        (default threshold = 0.5)
```

A signal is flagged **not research-safe** when at least half of its simulated PnL is
attributable to corrupted events. The threshold is explicit and configurable so the
verdict is a policy choice a reviewer can see and change, not a hidden constant.

## The demo result

On the official dataset (`defective_trades.csv`), the mean-reversion strategy books
almost all of its PnL fading injected bad-tick spikes. Cleaning those events removes
the edge:

- Raw Sharpe ≈ 0.32, Clean Sharpe ≈ −0.10
- Raw PnL ≈ +\$3,001, Clean PnL ≈ −\$0.56
- Mirage score ≈ 1.0 → **not research-safe**

The exact, full-precision values are locked in `data/demo/expected_results.json`
and asserted by `make test-reproducibility`.

## What the system does *not* claim

- It does **not** claim the strategy is or could be profitable.
- It does **not** claim the raw performance is real alpha — it demonstrates the
  opposite.
- It does **not** annualize Sharpe or model capacity, borrow, or market impact.
- It does **not** assert detection quality; it *measures* it against injected ground
  truth (recall 1.0 on the injected set; a zero-defect control shows no false
  mirage).

## Failure modes and edge cases

- **No PnL at all** (`total_pnl == 0`): mirage score is 0, verdict research-safe;
  there is nothing to attribute.
- **Clean run also profitable:** low mirage score, verdict research-safe — the edge
  did not depend on the bad data. This is the outcome the zero-defect control checks.
- **Defects outside the causal chain:** not counted, by design. Correlation is not
  attribution.

## Current limitations

- Unit positions and per-step Sharpe are V1 simplifications, documented so they are
  never mistaken for a full performance model.
- A single strategy family (mean reversion / momentum) in V1.
- Attribution is causal-chain based at the interval level; it does not model
  higher-order interactions between multiple defects in one chain beyond "tainted or
  not".

## Future work

- Additional strategy families and configurable position sizing.
- Annualized, cost-adjusted metrics alongside the per-step figures.
- Per-defect-type PnL breakdown (how much false PnL each defect class contributed).
