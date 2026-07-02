# QuantStream Labs — Alpha Mirage reproducibility dataset

`alpha_mirage_demo_v1` · canonical demo dataset for
[QuantStream Labs](https://github.com/JCHETAN26/QuantStream-Labs).

This dataset exists to make one result reproducible byte-for-byte: **bad market
data can manufacture fake alpha, and QuantStream Labs detects it deterministically.**

## Files

| File | Purpose |
| --- | --- |
| `defective_trades.csv` | Trades with injected bad-tick spikes. Drives the Alpha Mirage demo. |
| `clean_trades.csv` | Pristine control trades (no defects, no mirage). |
| `defective_quotes.csv` | Quotes with crossed books, non-positive prices, and a stale block. |
| `clean_quotes.csv` | Pristine control quotes. |
| `defect_manifest.json` | Ground-truth injected defects per file. |
| `expected_results.json` | Canonical expected pipeline output (the regression lock). |
| `SHA256SUMS` | SHA-256 of the six files above. |

## Expected result (defective_trades.csv)

- Validation failures: **198**
- High-severity defects: **0**
- Replay checksum (raw): `7c517a403b20c3b2068215bb2fef5bc66f19b33677041ed6f605f193afe25b06`
- Raw Sharpe / Clean Sharpe:
  `0.3213646568975194640952630306` / `-0.1035022902775482425468481587`
- Mirage score: `1.000006663690218369128455956`
- Research-safe: **false**

Companion `defective_quotes.csv`: 10 validation
failures, 5 high-severity
(`{"crossed_book": 3, "invalid_price": 2, "stale_quote": 5}`).

## Checksums

| File | SHA-256 |
| --- | --- |
| `clean_quotes.csv` | `8d56c624950ad8a76e9761e2c41646b1a163337d2b3e747c4579207266669896` |
| `clean_trades.csv` | `67c27df843b73ad821a5113011e3ed4326f62603330bd04b71b157d104df6de0` |
| `defect_manifest.json` | `bd6c6bfd7a029c93018ad922aa917d597ffb0569cf3f96bede8656aebeffbefe` |
| `defective_quotes.csv` | `fb184f2d3d9c32525406dd8075169cd03692514a4bdb2032de1839cc19d5e689` |
| `defective_trades.csv` | `fc822fae1728a885387d8599f1550aa5075a456c20c652a4ab24a35a73da5e3c` |
| `expected_results.json` | `a2e2cdaabac0b3d34569190ad9d9b0f54abfcfdf00692f8606e8ebb1d8244b5c` |

## Reproduce

```bash
make fetch-hf-demo        # fetch + verify (or regenerate offline)
make demo-alpha-mirage    # run the pipeline, print the verdict
make test-reproducibility # assert the numbers above
```
