# QuantStream Labs

A deterministic market-data replay and validation engine that proves when a trading
signal's "alpha" is actually caused by bad data.

The engine validates a feed, replays events deterministically (same input → same
checksum), and runs a strategy on the raw data versus the cleaned data. The **Alpha
Mirage Detector** shows when performance collapses after corrupted events are
removed, and attributes the false PnL to the specific bad events that caused it.

## One-command demo

```bash
make install            # editable-install every package (first time only)
make fetch-hf-demo      # fetch + verify the official dataset (or regenerate offline)
make demo-alpha-mirage  # run the pipeline, print the verdict, write the report
```

```text
QuantStream Labs — Alpha Mirage Demo
====================================================
Dataset:          alpha_mirage_demo_v1
Source:           cache   revision: local
Checksum status:  PASS (6/6 files verified)

Input:            defective_trades.csv   Symbol: ACME   Events: 400
Validation failures:   198
High-severity defects: 0
Companion quotes:      defective_quotes.csv  (10 failures, 5 high-severity)
                       crossed_book 3, invalid_price 2, stale_quote 5

Replay checksum (raw):   7c517a403b20c3b2068215bb2fef5bc66f19b33677041ed6f605f193afe25b06
Replay checksum (clean): 8987f19a0eacecb232e3efa897e27b217b4d567321381f1319dce9df1d440622

Raw Sharpe:   0.32      Raw PnL:   +$3,001.34
Clean Sharpe: -0.10      Clean PnL: -$0.56
Mirage Score: 100%

Conclusion: ALPHA MIRAGE DETECTED
Signal is not research-safe. 100% of simulated PnL came from corrupted market-data events.
```

It also writes `quantstream-report.html` (or `out/quantstream-report.html` under
Docker), a static research-integrity report. Or run everything in a container:

```bash
docker compose up --build
```

## What problem this solves

Most market-data-driven signals are trusted before the data behind them is checked.
Bad data — out-of-order timestamps, duplicates, stale/crossed quotes, bad ticks —
can make a strategy look profitable for reasons that have nothing to do with real
edge. QuantStream Labs answers one question: **is this signal real, or is the alpha
fake because the data is broken?**

## Why bad data creates fake alpha

The bundled demo is a tiny random walk with no real edge, plus periodic bad-tick
spikes. A mean-reversion strategy fades each spike and books the "reversion" — which
is just the bad tick correcting. Cleaning the flagged events collapses the apparent
profit. That is the mirage. Full design: [`docs/alpha-mirage.md`](docs/alpha-mirage.md).

## The official demo dataset

The demo runs on `JCHETAN26/quantstream-alpha-mirage`, a fixed, checksummed dataset:

| File | Purpose |
| --- | --- |
| `defective_trades.csv` | Trades with injected bad-tick spikes (drives the mirage). |
| `clean_trades.csv` | Pristine control (no defects, no mirage). |
| `defective_quotes.csv` | Quotes with crossed books, bad prices, and a stale block. |
| `clean_quotes.csv` | Pristine control quotes. |
| `defect_manifest.json` | Ground-truth injected defects per file. |
| `expected_results.json` | Canonical expected pipeline output (the regression lock). |
| `SHA256SUMS` | SHA-256 of the six files above. |

`make fetch-hf-demo` acquires it in this order: **valid local cache → Hugging Face
→ deterministic offline generation**. Every path ends in SHA-256 verification and
**fails loudly on any mismatch**. Hugging Face is a dataset registry, not a runtime
dependency — the dataset is committed to the repo and regenerates byte-for-byte
offline, so the demo never needs the network.

### Verify checksums yourself

```bash
cd data/demo && sha256sum -c SHA256SUMS      # or: shasum -a 256 -c SHA256SUMS
```

### Reproduce the result

```bash
make test-reproducibility
```

This re-runs the full pipeline and asserts the validation counts, both replay
checksums, raw/clean Sharpe and PnL, the mirage score, and the research-safe verdict
all equal the committed `expected_results.json`. If any headline number drifts, this
fails.

## How deterministic replay works

The replay engine computes the checksum over its canonically ordered,
fixed-serialization stream **before publishing**. Redpanda/Kafka is transport only;
determinism is engineered source-side. Ordering is the total order
`(timestamp_ns, seq)`; prices/sizes are fixed-point `int64` (never float); the
checksum is BLAKE2b-256 over the serialized stream. Same input and config reproduce
the same checksum on any platform, in any language that reproduces the byte layout —
including the C++ engine. Full design:
[`docs/deterministic-replay.md`](docs/deterministic-replay.md).

## Backend guarantees

- **Deterministic replay** — same input + config → same output.
- **Canonical event ordering** — one total order `(timestamp_ns, seq)`, everywhere.
- **Source-side replay checksum** — computed over the ordered stream before any
  transport.
- **Checksum verification** — the dataset ships `SHA256SUMS`; every fetch verifies
  and fails loudly on mismatch; the demo refuses to run on an unverified dataset.
- **Structured defect attribution** — PnL is tainted only when a defect-flagged
  event sits in that PnL's causal chain (no lookahead, no correlation hand-waving).
- **Raw-vs-cleaned signal comparison** — the mirage score is one auditable ratio,
  `tainted PnL / total PnL`.
- **Expected-results regression** — `make test-reproducibility` locks the end-to-end
  numbers to `expected_results.json`.
- **Local reproducibility** — regenerates the dataset byte-for-byte offline; runs
  with no network.

## What this project does not claim

- It does **not** claim to generate profitable strategies. The demo strategy is
  deliberately edgeless; the point is that its apparent profit is fake.
- It does **not** claim to be a production trading system.
- It does **not** claim Redpanda/Kafka guarantees determinism — determinism is
  source-side; the broker is transport only.
- It does **not** use hidden demo hacks — the dataset is checksummed, the expected
  results are committed, and the numbers are reproducible.
- It **does** demonstrate reproducible market-data validation and fake-alpha
  detection.

## Repository layout

```text
packages/
  contracts/            canonical events, fixed-point price/size, deterministic serialization
services/
  schema-worker/        schema inference + CSV loading into canonical events
  validation-engine/    defect detection + seeded corruption injector
  replay-engine/        deterministic replay, source-side checksum, pluggable sinks
  replay-engine-cpp/    C++20 replay engine (matches the Python checksum byte-for-byte)
  research-engine/      backtest, PnL taint attribution, Alpha Mirage Detector
  orderbook-lab/        L1/L2 book reconstruction, sequence-gap/crossed/stale detection
  dataset_registry/     dataset generation, Hugging Face fetch, SHA-256 verification
apps/
  demo/                 official-dataset CLI + HTML research-integrity report
  api/                  FastAPI gateway over the same pipeline
docs/
  backend-architecture.md, deterministic-replay.md, validation-rules.md, alpha-mirage.md
```

## Develop

```bash
make install    # editable-install every package
make test       # run every package's test suite
make lint       # ruff
```

## Design docs

- [Backend architecture](docs/backend-architecture.md)
- [Deterministic replay](docs/deterministic-replay.md)
- [Validation rules](docs/validation-rules.md)
- [Alpha Mirage](docs/alpha-mirage.md)
- [Local demo & privacy](docs/local-demo.md)

## Privacy

The demo runs on bundled synthetic data. For proprietary datasets, run QuantStream
Labs locally: uploaded files stay inside the local environment and are not sent to
any external service. See [`docs/local-demo.md`](docs/local-demo.md).
