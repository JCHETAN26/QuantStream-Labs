# dataset-registry

Deterministic generation, Hugging Face fetch, and SHA-256 verification of the
official QuantStream Labs reproducibility dataset
(`JCHETAN26/quantstream-alpha-mirage`).

## Why it exists

A reproducibility claim needs a fixed, checksummed input. This service produces that
input byte-for-byte on any machine, so a reviewer can fetch the dataset, verify its
checksums, and reproduce the Alpha Mirage result exactly.

Hugging Face is treated as a *dataset registry*, not a runtime dependency: the
dataset is committed to the repo and can be regenerated offline. The demo never
requires network access.

## Commands

```bash
quantstream-fetch-dataset            # cache -> Hugging Face -> offline generation
quantstream-fetch-dataset --offline  # never touch the network
quantstream-fetch-dataset --force    # ignore the local cache
```

## Files produced (under `data/demo/`)

| File | Purpose |
| --- | --- |
| `defective_trades.csv` | Trades with injected bad-tick spikes (drives the mirage). |
| `clean_trades.csv` | Pristine control trades. |
| `defective_quotes.csv` | Quotes with crossed books, bad prices, and a stale block. |
| `clean_quotes.csv` | Pristine control quotes. |
| `defect_manifest.json` | Ground-truth injected defects per file. |
| `expected_results.json` | Canonical expected pipeline output (regression lock). |
| `SHA256SUMS` | SHA-256 of the six files above. |
| `README.md` | Dataset card. |

## Determinism

Generation reads no wall-clock or external state. CSVs use LF line endings and
minimal decimal formatting; JSON is emitted with sorted keys. Regeneration is
byte-identical, so committed files, regenerated files, and the Hugging Face copy all
share the same SHA-256s.
