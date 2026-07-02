# Deterministic replay

## Problem

The product's central claim — "same input and config reproduce the same result" —
is only credible if there is a single, cheap, auditable number that pins a replay
run. That number is the **replay checksum**. It must be identical across runs,
across machines, and eventually across languages (the C++ engine must match the
Python reference byte-for-byte).

## Design stance

> The replay engine computes the checksum over its canonically ordered,
> fixed-serialization stream **before publishing**. Redpanda/Kafka is used as
> transport only. Determinism is engineered source-side.

Everything below follows from that one sentence.

## Canonical event ordering

The system has one total order, applied everywhere:

```text
key(event) = (timestamp_ns, seq)
```

`seq` is the source row index, assigned at load time. It is the deterministic
tie-breaker for events that share a timestamp, so ordering never depends on hash
iteration, dict order, or the language's sort stability. `canonical_sort` (in
`packages/contracts/serialization.py`) is a plain `sorted()` on this key — total and
reproducible.

## Fixed serialization

Each event serializes to a fixed byte record (see `serialization.py`):

- little-endian, fixed-width integers (no native-endianness surprises),
- strings as a `uint16` byte-length prefix followed by raw UTF-8,
- enums as fixed `uint8` values that are part of the contract (append-only, never
  renumbered),
- prices/sizes as `int64` fixed-point — **never** float.

The record layout is documented field-by-field in `serialization.py` precisely so a
second implementation (C++) can reproduce it. Float anywhere in this path would make
byte-for-byte equality impossible; that is why the contract rejects float inputs at
the fixed-point boundary rather than silently rounding.

## The checksum

```text
checksum = BLAKE2b-256( concat( serialize_event(e) for e in canonical_sort(events) ) )
```

A full-dataset replay (no filter) produces exactly the checksum you would get from
`stream_checksum` in the contracts package directly. That equivalence is the anchor
the C++ engine is verified against: match this hex digest, or the build fails.

## Why the checksum is computed before publishing

The checksum is a property of the **ordered event stream**, not of any transport.
`replay()` computes it over the in-memory canonical order and only then emits to a
`Sink`. Consequences:

- The checksum is independent of the sink, of delivery timing, of partition
  assignment, and of retries.
- Swapping the transport (in-memory → Kafka/Redpanda) cannot change the checksum.
- A consumer can recompute the checksum from what it received and compare.

## Why Redpanda/Kafka is transport, not the determinism layer

Kafka-family systems provide ordering guarantees only *within a partition*, and
delivery is at-least-once with consumer-visible retries and rebalances. Relying on
the broker for determinism would make the guarantee depend on partitioning,
timing, and delivery semantics — exactly the fragile, environment-dependent behavior
this project avoids. Instead, the ordered, hashed stream is the source of truth; the
broker just moves bytes.

## Why V1 uses a single-partition canonical topic

Ordering across partitions is not guaranteed by Kafka/Redpanda. The canonical topic
is single-partition (partition key = symbol) so that consumed order matches the
source canonical order for the demo dataset. This trades throughput for a clean,
demonstrable ordering property in V1; multi-partition sharding with per-symbol
ordering is future work and does not affect the source-side checksum either way.

## How replay config affects determinism

A run is defined by `(input events, ReplayConfig)`. The config carries filters
(symbols, time window) and a `speed` multiplier, and exposes its own stable
`config_hash`:

- Filters change *which* events are in the stream, so they change the checksum — as
  they should. A symbol- or window-filtered replay is a different stream.
- `speed` is an integer multiplier (0 = max). It affects pacing, not content, so it
  does not change the checksum. It is deliberately not a float, to keep floats out
  of anything determinism-adjacent and to keep `config_hash` stable.

Provenance of a run is therefore fully captured by `(input checksum, config_hash)`.

## How checksum stability is tested

- **Order independence:** shuffling the input list yields the same checksum.
- **Run-to-run identity:** repeated replays of the same input match.
- **Filter semantics:** filtered replays differ from the full run in the expected
  way, and equal a direct `stream_checksum` over the filtered set.
- **Golden vectors:** the contracts package ships golden serialization tests; the
  C++ engine's CI job runs a cross-language golden match against them.
- **End-to-end lock:** `test-reproducibility` asserts the demo dataset's raw and
  clean checksums equal the committed `expected_results.json`.

## Failure modes

- **Float sneaks in.** Rejected at the fixed-point boundary (`to_fixed` refuses
  float/bool) rather than silently rounding.
- **Enum renumbered.** Would silently change bytes; prevented by the append-only
  rule documented on the enums and covered by golden tests.
- **Non-UTF-8 or oversized strings.** Rejected at event construction (uint16 length
  cap) so serialization can never be ambiguous.

## Current limitations

- The C++ engine is verified on the checksum/serialization contract, not on wall-
  clock replay pacing.
- Single-partition topic caps transport throughput in V1.

## Future work

- Multi-partition transport with per-symbol ordering, leaving the source-side
  checksum unchanged.
- A published cross-language golden corpus beyond the demo dataset.
