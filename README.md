# QuantStream Labs

A deterministic market-data replay and validation engine that proves when a trading
signal's "alpha" is actually caused by bad data.

Upload trades / quotes, the engine validates the feed, replays events
deterministically (same input -> same checksum), and runs a strategy on the raw data
versus the cleaned data. The **Alpha Mirage Detector** shows when performance
collapses after corrupted events are removed, and attributes the false PnL to the
specific bad events that caused it.

```text
Raw Sharpe:   2.41
Clean Sharpe: 0.38
Mirage Score: 83%

Conclusion: signal is not research-safe.
83% of simulated PnL came from corrupted market-data events.
```

## Status

Early build. The foundation (`packages/contracts`) is in place: canonical typed
events, fixed-point price/size, and the deterministic byte-stable serialization that
backs the replay checksum. See `build-plan.md` for the full plan.

## Repository layout

```text
packages/
  contracts/        canonical events, fixed-point, deterministic serialization
```

More services (validation engine, C++ replay engine, feature engine, backtest /
Alpha Mirage) land in subsequent PRs.

## Develop

```bash
pip install -e "packages/contracts[dev]"
make test
```
