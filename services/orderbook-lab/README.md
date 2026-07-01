# quantstream-orderbook

OrderBookLab (L1): reconstructs top-of-book from quotes and, crucially, does not
blindly trust it. Depends on `quantstream-contracts`.

## What it computes

Per quote, per symbol (in canonical order):

- best bid / best ask, **spread**, **mid-price**
- **quote age** — how long the current top-of-book has stood
- **crossed** book (bid > ask) and **stale** book (age past a threshold) detection
- a **book-confidence** state: `HEALTHY`, `DEGRADED`, `UNRELIABLE`, `RECOVERING`

## Confidence state machine

```
HEALTHY ──stale──▶ DEGRADED
HEALTHY ──crossed─▶ UNRELIABLE
DEGRADED / UNRELIABLE ──clean quote──▶ RECOVERING
RECOVERING ──N clean quotes──▶ HEALTHY      (N = recovery_threshold)
```

A crossed book during recovery drops straight back to UNRELIABLE. The point: a book
that has seen bad data is marked untrustworthy until it has demonstrably settled.

## Use

```python
from quantstream_orderbook import reconstruct

snapshots, summaries = reconstruct(quote_events)
summaries["AAPL"].final_confidence   # BookConfidence
summaries["AAPL"].crossed_count, summaries["AAPL"].stale_count
```

## Test

```bash
pip install -e "packages/contracts[dev]"
pip install -e "services/orderbook-lab[dev]"
pytest services/orderbook-lab -q
```
