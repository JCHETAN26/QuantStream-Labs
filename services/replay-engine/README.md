# quantstream-replay

Deterministic replay of normalized events: canonical ordering, a source-side replay
checksum, and pluggable sinks. This is the **Python reference** the C++ replay engine
will be verified against.

Depends on `quantstream-contracts` (install it editable first).

## Determinism (the D2 decision, concrete)

- The checksum is computed **at the source**, over the canonically-ordered stream,
  before any transport. It never depends on what a consumer observes.
- A full-dataset replay (no filter) yields the **identical** checksum as
  `quantstream_contracts.stream_checksum`. That is the anchor the C++ engine must
  match byte-for-byte.
- Sinks are transport. `InMemorySink` is the reference; a `KafkaSink` publishing to
  the single-partition canonical topic implements the same `Sink` protocol in a later
  PR. Swapping transport cannot change the checksum.

## API

```python
from quantstream_replay import replay, ReplayConfig, InMemorySink

sink = InMemorySink()
result = replay(events, ReplayConfig(symbols=frozenset({"AAPL"})), sink=sink)
result.checksum        # source-side replay checksum (hex)
result.config_hash     # stable hash of the run config
result.event_count     # events after filtering
result.dropped_by_filter
```

A run's provenance is fully captured by `(input checksum, config_hash)`.

## Test

```bash
pip install -e "packages/contracts[dev]"
pip install -e "services/replay-engine[dev]"
pytest services/replay-engine -q
```
