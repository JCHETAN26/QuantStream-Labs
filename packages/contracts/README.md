# quantstream-contracts

The single source of truth for QuantStream Labs' normalized market-data events.
Everything downstream (validation, replay, features, backtest) depends on this
package, and the C++ replay engine reproduces its serialization byte-for-byte.

Stdlib-only on purpose: the canonical serialization is determinism-critical, so no
third-party dependency is allowed to influence the byte layout or number
formatting.

## What's here

- **`fixed_point.py`** — prices and sizes as scaled int64 (`PRICE_SCALE` /
  `SIZE_SCALE` = 1e9). Parsing goes through `Decimal`; `float` input is rejected so
  precision loss can never sneak in.
- **`events.py`** — frozen dataclasses `Trade`, `Quote`, `OHLCV`, `L2Update`. Prices
  and sizes are already fixed-point ints. `seq` (source row index) is the tie-breaker
  in the system-wide total order `(timestamp_ns, seq)`.
- **`enums.py`** — `EventType`, `Side`, `BookAction`. Integer values are part of the
  wire contract; append only, never renumber.
- **`serialization.py`** — canonical little-endian byte layout, `canonical_sort`, and
  `stream_checksum` (BLAKE2b-256 over the ordered stream). This is the replay checksum.

## Determinism contract

1. Fixed-point integers, never float, in the canonical form.
2. A documented little-endian byte layout (see `serialization.py`).
3. A total order `(timestamp_ns, seq)` applied before hashing.

These three together mean the same input yields the same checksum on any platform,
and the future C++ engine matches Python by construction.

## Test

```bash
pip install -e "packages/contracts[dev]"
pytest packages/contracts -q
```

The golden snapshot in `tests/golden/expected.json` locks the exact bytes. Regenerate
intentionally after a deliberate format change:

```bash
QS_UPDATE_GOLDEN=1 pytest packages/contracts/tests/test_golden.py
```
