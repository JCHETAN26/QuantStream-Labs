# Research methodology & limitations

This document states exactly what the backtest and Alpha Mirage detector do and do
not do. The point of QuantStream Labs is data-integrity honesty, so the research
assumptions are stated plainly rather than buried.

## Backtest model

- **Event-time, no lookahead.** A strategy at trade `i` sees only prices `[0..i]`.
  This is enforced by a property test: `decide(prices, i)` returns the identical
  result whether or not future prices exist.
- **Unit positions** in `{-1, 0, +1}`. No position sizing or leverage.
- **Mark-to-next-trade.** The PnL of holding from trade `i` to `i+1` is
  `position_i * (price_{i+1} - price_i)`. This is a simplification: it marks to the
  next *trade* print, not to the mid, and assumes you can transact at the print.
- **Transaction costs.** A cost of `cost_per_unit` is charged per unit of position
  *change* (a flip from -1 to +1 is 2 units), modeling commission plus half-spread
  crossing. Net PnL = gross PnL - costs; Sharpe is computed on net PnL. The demo uses
  ~2 bps per unit — under which the no-edge clean strategy is a net *loser*, as it
  should be.

- **Sharpe.** The headline figure is the **per-trade** Sharpe (mean/stdev of
  per-interval net PnL). An **annualized** figure is also computed (per-trade Sharpe x
  sqrt(trades per trading-year, 252 x 6.5h)). Treat the annualized number with
  caution: annualizing a high-frequency, non-iid strategy (its "edge" is concentrated
  in rare bad-tick events) inflates it heavily. The absurd annualized Sharpe on the
  raw run is itself a tell that the performance is not real.

## Attribution

Two independent views of "how much alpha is fake", both reported:

1. **Causal taint.** An interval's PnL is tainted if any event in its causal chain
   (the prices the signal consulted, plus the two prices realizing the return)
   carries a defect flag. `mirage_score = tainted_pnl / total_pnl`.
2. **Counterfactual.** The raw run vs. the cleaned run (flagged events removed) — the
   Sharpe/PnL collapse between them.

Caveat: causal taint is binary at the interval level, so it can *over*-attribute — a
mostly-clean interval with one flagged event in its lookback is counted fully
tainted. The counterfactual (raw vs. clean) is the more conservative number; when the
two disagree, trust the counterfactual.

## Determinism

- Prices and sizes are fixed-point int64 (never float) in the canonical form.
- The replay checksum is BLAKE2b over a canonically-ordered, byte-stable serialization.
- The C++ engine reproduces that checksum byte-for-byte (golden test), so
  "deterministic" holds across languages.

## Data

The bundled demo dataset is **synthetic but documented and checksummed**: a price
walk with injected bad-tick spikes, generated deterministically by
`services/dataset_registry` and verified by SHA-256. It exists so the headline result
is reproducible, not so it looks like a real feed.

**Real data:** the engine is not tied to synthetic data. `data/real/btcusd_coinbase.csv`
is a committed snapshot of a **real Coinbase BTC-USD tape**: schema inference parses
it, validation finds zero defects in the clean window, and deterministic replay
produces a checksum the **C++ engine reproduces byte-for-byte** (CI-enforced). On the
clean real tape the no-edge strategy honestly loses money (Sharpe -0.63). Arbitrary
real data also works via CSV upload (`POST /api/analyze`).

## Known limitations (things a reviewer should push on)

- **No market impact or partial fills.** Fills are assumed at the print.
- **Mark-to-trade, not mid.** Overstates PnL when the spread is wide.
- **Annualized Sharpe is inflated by high-frequency, non-iid returns.** The per-trade
  figure is the honest headline; the annualized one is reported with the caveat above.
- **Synthetic demo data.** Realistic for the mechanism it demonstrates (fake alpha
  from fading bad ticks), but not a real market sample.
- **Kafka/Redpanda transport is a `Sink` interface, not yet a running broker
  integration.** The determinism story does not depend on it (checksum is source-side).
- **The C++ component is the serialization + checksum core**, not a full replay/
  producer binary.

The last three are on the roadmap; they are listed here so the claims never run
ahead of the code.
