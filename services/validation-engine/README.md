# quantstream-validation

Detects market-data defects, cleans a dataset by dropping flagged events, and ships
a seeded corruption injector so the detector can be measured against ground truth.

Depends on `quantstream-contracts` (install it editable first).

## Checks

| Defect | Severity | Detection |
|--------|----------|-----------|
| invalid price | critical | non-positive price |
| invalid size | critical | non-positive size |
| crossed book | critical | quote bid above ask |
| duplicate | warning | repeated event content (ignoring seq) |
| out of order | warning | timestamp earlier than a prior row, per symbol |
| bad tick | warning | consecutive-trade move over threshold (default 20%) |
| stale quote | warning | identical quote run older than threshold (default 5s) |

## Pieces

- `validate(events)` -> `ValidationReport` (per-check results + per-event `defect_map`).
- `clean(events, report)` -> events with flagged ones removed (V1 drops, never "fixes").
- `corrupt(clean_events, CorruptionConfig(seed=...))` -> raw events + ground-truth map.

## Honesty

The detector runs independently of the injector. `test_precision_recall.py` injects
known defects and asserts **recall == 1.0** (nothing missed) and a **zero-defect
control** (clean data yields zero flags). That independence is what makes the eventual
Alpha Mirage number defensible instead of manufactured.

## Test

```bash
pip install -e "packages/contracts[dev]"
pip install -e "services/validation-engine[dev]"
pytest services/validation-engine -q
```
