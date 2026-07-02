# replay-engine-cpp

The C++20 replay engine's serialization core, built to reproduce the Python
reference (`packages/contracts`) **byte-for-byte**. That match is the cross-language
determinism proof: the same events produce the same replay checksum in Python and in
C++.

Dependency-free on purpose — including a hand-written BLAKE2b-256 — because the whole
point is to control every byte. Nothing here may depend on a library whose hash
parameters or number formatting we don't fully own.

## What's here

- `blake2b.{hpp,cpp}` — BLAKE2b-256 (RFC 7693), matching
  `hashlib.blake2b(digest_size=32)`. Verified against known vectors in the tests.
- `events.hpp` — the canonical event model (Trade/Quote/OHLCV/L2Update), fixed-point
  int64 prices/sizes, field order identical to the Python contract.
- `serialization.{hpp,cpp}` — the canonical little-endian byte layout, `canonical_sort`
  by `(timestamp_ns, seq)`, and `stream_checksum` (BLAKE2b over the ordered stream).

## The proof

`tests/test_golden.cpp` rebuilds the exact fixture from
`packages/contracts/tests/test_golden.py`, serializes it, and asserts that every
per-event hex and the stream checksum appear in the committed
`packages/contracts/tests/golden/expected.json`. If a single byte of the layout
diverges from Python, this test fails.

## Build & test

```bash
cmake -S services/replay-engine-cpp -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

## The `replay` CLI

A runnable C++20 replay engine: it reads a normalized trades CSV, applies the
canonical `(timestamp, seq)` order, and prints the deterministic replay checksum.

```bash
cmake -S services/replay-engine-cpp -B build-cpp && cmake --build build-cpp
./build-cpp/replay data/demo/defective_trades.csv
# events: 400
# replay_checksum: 6deb77e9f4187597d0127592900e0b5ef36ce8f199e807bdc96891c74365dd29
```

That checksum equals the Python replay engine's checksum on the same file,
byte-for-byte — CI asserts it against `data/demo/expected_results.json`. Decimal
prices are parsed to fixed-point exactly (`parse_fixed`), matching Python's
`price_to_fixed`.

## Not here yet

- Publishing the replayed stream to the bus (a `KafkaSink` on the single-partition
  canonical topic). Determinism does not depend on it — the checksum is source-side.
