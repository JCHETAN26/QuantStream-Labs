# QuantStream Labs

A deterministic market-data replay and validation engine that proves when a trading
signal's "alpha" is actually caused by bad data.

Upload trades, and the engine validates the feed, replays events deterministically
(same input → same checksum), and runs a strategy on the raw data versus the cleaned
data. The **Alpha Mirage Detector** shows when performance collapses after corrupted
events are removed, and attributes the false PnL to the specific bad events that
caused it.

## The demo, in one command

```bash
docker compose up --build          # runs the demo in a container
# or, locally:
make install && make demo-alpha-mirage
```

```text
QuantStream Labs — Alpha Mirage Demo
Symbol: ACME   Events: 400   Bad-tick events flagged: 198

Raw Sharpe:   0.32
Clean Sharpe: -0.10
Mirage Score: 100%

Raw PnL:   +$3,001.34
Clean PnL: -$0.56

Conclusion:
Signal is not research-safe.
100% of simulated PnL came from corrupted market-data events.
```

It also writes `out/quantstream-report.html` (Docker) or `quantstream-report.html`
(local), a static research-integrity report.

The bundled sample is a tiny random walk with no real edge, plus periodic bad-tick
spikes. A mean-reversion strategy fades each spike and books the "reversion" — which
is just the bad tick correcting. Cleaning the flagged events collapses the apparent
profit. That is the mirage.

## Why it's trustworthy

- **Deterministic.** The replay checksum is computed over a canonically-ordered,
  fixed-point, byte-stable event stream. Same input and config reproduce the same
  checksum on any platform, in any language (the C++ engine, when it lands, must
  match the Python reference byte-for-byte).
- **Honest attribution.** PnL is attributed to corruption only when a defect-flagged
  event sits in that PnL's causal chain — no lookahead, no correlation hand-waving.
  The mirage score is one auditable ratio: `tainted PnL / total PnL`.
- **Independent detection.** The validation engine detects defects on its own; a
  seeded corruption injector lets us measure its precision and recall (recall == 1.0
  on the injected set) rather than assert it. A zero-defect control confirms we never
  manufacture a mirage where none exists.

## Repository layout

```text
packages/
  contracts/            canonical events, fixed-point price/size, deterministic serialization
services/
  validation-engine/    defect detection + seeded corruption injector
  replay-engine/         deterministic replay, source-side checksum, pluggable sinks
  research-engine/       backtest, PnL taint attribution, Alpha Mirage Detector
apps/
  demo/                  sample data, CLI, HTML research-integrity report
```

Each is a small, self-contained Python package (stdlib-only where determinism
matters). See each directory's README for details.

## Develop

```bash
make install    # editable-install every package
make test       # 116 tests across the repo
make lint       # ruff
```

## Privacy

The demo runs on bundled synthetic data. For proprietary datasets, run QuantStream
Labs locally: uploaded files stay inside the local environment and are not sent to
any external service. See `docs/local-demo.md`.

## Status

The core is built and tested end to end: contracts → validation → deterministic
replay → backtest + Alpha Mirage → demo. Next: `docker compose` service topology
(Redpanda transport on the single-partition canonical topic), CSV upload + schema
inference, and the web UI. See `build-plan.md` for the full plan.
