# Validation rules

## Problem

Before any signal is trusted, the data behind it must be checked for the
pathologies that quietly manufacture fake results. The validation engine runs a set
of independent checks over canonical events and produces two outputs:

- a **`defect_map`**: `seq → {defects}`, the machine-facing record used to clean the
  data and to taint PnL, and
- a **report**: one `CheckResult` per check (status / count / severity / example
  offenders / impact), the human-facing summary.

## Design

Each check is a **pure function**: it takes the event list and returns the set of
`seq` values it flags. That makes every check independently unit-testable on both
its true and false paths, and lets the engine run them in any order. Ordering-
sensitive checks operate per symbol in the canonical `(timestamp_ns, seq)` order, so
results never depend on the input list's order.

Severity maps to report status: a `CRITICAL` defect fails the report, a `WARNING`
warns, and a clean dataset passes every check. Cleaning policy is **remove, not
correct** (`clean()` drops flagged events): dropping a bad event is always
defensible, whereas "fixing" it invents data.

## Rules

### Invalid price — CRITICAL
- **Detects:** non-positive price on a trade/L2 update, or non-positive bid/ask on a
  quote, or a non-positive OHLC value.
- **Why it matters:** a price of 0 (or negative) cannot be used for pricing or PnL;
  any metric derived from it is meaningless.
- **Example:** `Trade(price=0, …)` from a dropped/garbled field.
- **Research impact:** silently poisons returns and any spread/mid derived from it.

### Invalid size — CRITICAL
- **Detects:** non-positive size on a trade/L2 update or quote; negative OHLCV volume.
- **Why it matters:** volume and fill logic computed from a zero/negative size are
  wrong.
- **Example:** `Trade(size=0, …)`.
- **Research impact:** distorts volume-weighted features (VWAP) and fill assumptions.

### Crossed book — CRITICAL
- **Detects:** a quote whose bid strictly exceeds its ask (`bid_price > ask_price`).
  A locked book (`bid == ask`) is deliberately **not** flagged: unusual but not
  impossible, and flagging it inflates false positives.
- **Why it matters:** spread and mid-price are nonsensical on a crossed quote; this
  is the concrete form of a "negative spread".
- **Example:** `Quote(bid_price=100.05, ask_price=100.01)`.
- **Research impact:** a strategy reading mid/spread here trades on fiction.

### Duplicate events — WARNING
- **Detects:** every occurrence after the first of an event with identical content
  (identity computed ignoring `seq`, in canonical order, so "first" is stable).
- **Why it matters:** a repeated print double-counts volume and can inflate signal
  PnL.
- **Example:** the same trade delivered twice by a vendor with a new row id.
- **Research impact:** manufactures turnover and can create phantom edge.

### Out-of-order timestamps — WARNING
- **Detects:** an event that arrives (by file order / `seq`) with a timestamp earlier
  than a prior row for the same symbol.
- **Why it matters:** out-of-order data is a lookahead hazard — a naive consumer can
  "see" a later event before an earlier one.
- **Example:** row 100 has `timestamp_ns` below the max seen at row 99.
- **Research impact:** the classic source of accidental lookahead bias.

### Bad ticks — WARNING
- **Detects:** a trade whose price moves more than the threshold (default 20%) from
  the previous trade in the same symbol.
- **Why it matters:** a spurious spike that immediately corrects looks like a large
  move and a "reversion" — precisely the fake alpha this product exists to catch.
- **Example:** a print at 135.00 between neighbors near 100.00.
- **Research impact:** mean-reversion and breakout signals feed directly on bad
  ticks. This is the defect that drives the demo's Alpha Mirage.

### Stale quotes — WARNING
- **Detects:** within a run of identical consecutive quotes, the members more than
  the stale window (default 5s) after the run's start.
- **Why it matters:** a quote frozen far past its freshness window misstates the live
  spread.
- **Example:** the same bid/ask repeated for 10s while the market moved.
- **Research impact:** spread/mid features and quote-age logic silently drift.

## Rules that live elsewhere or are future work

Being explicit about scope matters more than a long checklist:

- **Sequence gaps** (L2 order-book update gaps) and **crossed L2 books** are detected
  in `services/orderbook-lab` during book reconstruction, not in this engine, because
  they require book state, not per-event predicates.
- **Schema violations / unparseable rows** are handled at load time by the
  schema-worker, which turns each bad row into a structured `RowError` rather than a
  validation flag.
- **Missing sampling intervals** (gaps in an expected cadence) are **not** implemented
  in V1. It needs a per-symbol expected interval, which the demo dataset does not
  carry; it is future work.

## Measuring detection honestly

The paired seeded **corruption injector** takes clean data and injects defects with
ground truth. The detector runs *independently* of that ground truth, so precision
and recall are measured, not asserted. On the injected set, recall is 1.0 for the
targeted defects; a zero-defect control confirms the engine does not manufacture
flags where none exist. The demo dataset's `defect_manifest.json` records the
injected ground truth for the same reason.

## Configuration

`ValidationConfig` exposes `max_tick_return` (bad-tick threshold) and `stale_ns`
(stale window). Thresholds are explicit and documented so a reviewer can see exactly
what "bad tick" means rather than trusting a magic number.

## Current limitations

- Thresholds are global, not per-symbol or volatility-scaled.
- No missing-interval / cadence check in V1.
- Cleaning removes events; it never repairs them.
