# quantstream-schema

Turns an uploaded CSV into canonical events. Infers the event type and column
mapping from the header and a sample of rows, then loads every row, converting
malformed rows into structured errors instead of crashing.

Depends on `quantstream-contracts`.

## Inference

`infer_schema(headers, sample_rows)` returns an `InferredSchema`:

- **event type** — QUOTE if bid/ask columns are present, otherwise TRADE.
- **column mapping** — each canonical field matched to a source column by normalized
  header aliases (`ts`/`time`/`timestamp`, `ticker`/`sym`/`symbol`, `px`/`price`, …).
- **timestamp unit** — inferred from a sample value's magnitude (ns/us/ms/s) or ISO
  shape.
- **confidence** — fraction of the event type's required fields that matched, so a
  caller can decide whether to trust it or confirm with the user.

## Loading

```python
from quantstream_schema import load_csv_path

schema, result = load_csv_path("trades.csv")
result.events   # list of canonical Trade/Quote events, seq = row index
result.errors   # RowError(row_index, reason) for any row that failed
```

All parsing is exact and deterministic (Decimal for prices, timedelta components for
ISO timestamps — never float), so the same CSV always produces the same events and
therefore the same replay checksum.

## Test

```bash
pip install -e "packages/contracts[dev]"
pip install -e "services/schema-worker[dev]"
pytest services/schema-worker -q
```
