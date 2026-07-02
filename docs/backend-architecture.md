# Backend architecture

## Problem

A market-data research platform is only trustworthy if a skeptical engineer can
trace a headline result back through every transformation and reproduce it exactly.
QuantStream Labs is built so the Alpha Mirage verdict — "this signal's alpha is fake,
caused by bad data" — is reproducible byte-for-byte from a fixed, checksummed input.

The backend is a set of small, single-responsibility Python packages that share one
canonical event contract. There is no hidden global state and no service reaches
into another's internals; they compose through typed events and pure functions.

## Flow

```text
CSV (uploaded or official dataset)
      │
      ▼
schema-worker         infer event type + column mapping, load → canonical events
      │
      ▼
validation-engine     detect defects → per-event defect_map + human report
      │            └── clean(): drop flagged events → cleaned event set
      ▼
replay-engine         canonical ordering → source-side checksum → sink (transport)
      │
      ▼
research-engine       event-time backtest (raw + cleaned) → PnL taint → Alpha Mirage
      │
      ▼
demo / api            terminal verdict, HTML research-integrity report, JSON
```

The dataset registry sits beside this flow: it produces and verifies the fixed input
the whole pipeline runs on.

## Service boundaries

| Package | Responsibility | Depends on |
| --- | --- | --- |
| `packages/contracts` | Canonical events, fixed-point price/size, byte-stable serialization, replay checksum. | stdlib only |
| `services/schema-worker` | Infer schema from CSV headers/samples; load rows into canonical events; bad rows become structured errors. | contracts |
| `services/validation-engine` | Independent defect checks; per-event `defect_map`; `clean()`; seeded corruption injector. | contracts |
| `services/replay-engine` | Deterministic replay: filter → canonical order → source-side checksum → pluggable sink. | contracts |
| `services/research-engine` | No-lookahead event-time backtest, PnL taint attribution, Alpha Mirage detector. | contracts |
| `services/orderbook-lab` | L1/L2 book reconstruction, sequence-gap/crossed/stale detection, book confidence. | contracts |
| `services/dataset_registry` | Deterministic dataset generation, Hugging Face fetch, SHA-256 verification, `expected_results.json`. | contracts, validation, replay, research, schema |
| `apps/demo` | Wire the pipeline together; terminal verdict + HTML report. | registry, engines, schema |
| `apps/api` | FastAPI gateway over the same pipeline (no logic duplication). | demo, engines, orderbook, schema |

`contracts` is the only package everyone depends on, and it depends on nothing. That
keeps the serialization contract — the thing the C++ engine must match — small and
stable.

## The canonical contract

Every service speaks `Trade` / `Quote` / `OHLCV` / `L2Update` (see
`packages/contracts`). Two decisions make the rest of the system possible:

- **Fixed-point integers, never float.** Prices and sizes are `int64` scaled by 1e9.
  Float summation order and platform float formatting would break the replay
  checksum and make byte-for-byte cross-language equality impossible.
- **A single total order `(timestamp_ns, seq)`.** `seq` is the source row index and
  the deterministic tie-breaker, so events sharing a timestamp never reorder between
  runs or languages.

## Dataset registry and reproducibility

The pipeline runs on the official dataset (`JCHETAN26/quantstream-alpha-mirage`).
The registry acquires it in this order: valid local cache → Hugging Face (optional
extra + network) → deterministic offline generation. Every path ends in SHA-256
verification against the dataset's `SHA256SUMS`, and any mismatch raises.

`expected_results.json` is computed by actually running the pipeline at generation
time and committed. `test-reproducibility` re-runs the pipeline and asserts equality,
so a change that alters any headline number fails CI until the dataset is
deliberately regenerated. See `deterministic-replay.md` and `alpha-mirage.md`.

## Storage

- **Dataset files** live under `data/demo/` (committed; regeneratable byte-for-byte).
  The location is overridable via `QUANTSTREAM_DATA_DIR`.
- **Reports** are written to `quantstream-report.html` locally or `out/` in Docker.
- There is no database in this phase. The system is a deterministic batch pipeline;
  metadata that matters (checksums, config hash, expected results) is captured in
  files that travel with the dataset. The build plan's Postgres/object-store topology
  is future work for the multi-service, upload-driven deployment.

## Docker / local mode

`docker compose up --build` installs the packages in dependency order (contracts
first, for layer caching), pins `QUANTSTREAM_DATA_DIR`, pre-generates and verifies
the dataset at build time, and runs the demo — writing the report to a mounted
`out/`. The image therefore runs the demo fully offline. Locally, `make install`
does editable installs and `make demo-alpha-mirage` runs the same flow.

## Failure modes

- **Tampered/corrupted dataset file.** `ensure_dataset(strict=True)` (the demo
  default) raises `ChecksumError` and refuses to run. `--debug` regenerates instead.
- **Hugging Face unavailable.** The registry falls back to local generation; the
  demo never depends on the network.
- **Malformed CSV rows.** The loader turns each bad row into a structured `RowError`
  and continues, so a messy upload yields a report, not a stack trace.
- **Unknown/low-confidence schema.** Inference returns a confidence score and notes;
  the caller can require confirmation before trusting a mapping.

## Testing strategy

Each package has unit tests for its pure functions. Cross-cutting guarantees are
covered by: contract golden tests (serialization stability), replay checksum
stability tests, the corruption-injector precision/recall tests, and the
`test-reproducibility` regression that locks the end-to-end numbers to
`expected_results.json`.

## Current limitations

- Single-process, in-memory transport by default; the Kafka/Redpanda sink is a
  later PR (and, by design, not part of the determinism guarantee).
- No persistence layer yet; results are files, not database rows.
- Backtest is unit-position and per-step Sharpe (see `alpha-mirage.md`).

## Future work

- Redpanda transport on the single-partition canonical topic.
- CSV upload UI and the web dashboard (frontend is explicitly out of scope for this
  hardening pass).
- Postgres metadata store and object storage for the multi-tenant deployment.
