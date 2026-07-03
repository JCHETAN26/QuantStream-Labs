# Real market-data snapshot

`btcusd_coinbase.csv` is a committed snapshot of **real** BTC-USD trades from the
Coinbase Exchange public API (`api.exchange.coinbase.com/products/BTC-USD/trades`),
normalized into the canonical schema (integer-nanosecond timestamps, fixed-point
prices/sizes). 500 consecutive prints spanning ~72 seconds.

Public market-data prints are factual data; this small snapshot is included for
reproducible demonstration and attribution to Coinbase.

## What it demonstrates

The platform is not tied to synthetic data. On this real tape:

- **Schema inference** parses it straight from the exchange (ISO-8601 `...Z`
  timestamps, `BTC-USD` symbol) with zero load errors.
- **Validation** finds **0 naturally-occurring defects** in this clean window.
- **Deterministic replay** produces a stable checksum — and the **C++ replay engine
  reproduces it byte-for-byte** (`expected.json`, enforced in CI). Cross-language
  determinism holds on a real exchange tape, not just synthetic data.
- The no-edge mean-reversion strategy honestly **loses money** on the clean tape
  (Sharpe -0.63, PnL -$220) — as a strategy with no real edge should.

`expected.json` locks these results.

## Regenerate the snapshot (optional)

```bash
curl -s "https://api.exchange.coinbase.com/products/BTC-USD/trades?limit=500" > raw.json
# sort ascending by trade_id, map to timestamp,symbol,price,size,side,trade_id,venue,
# then normalize via schema inference (see docs). The committed file is a fixed
# snapshot so results stay reproducible.
```
