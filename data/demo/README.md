# QuantStream Labs — Alpha Mirage reproducibility dataset

`alpha_mirage_demo_v2` · canonical demo dataset for
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
- Replay checksum (raw): `6deb77e9f4187597d0127592900e0b5ef36ce8f199e807bdc96891c74365dd29`
- Raw Sharpe / Clean Sharpe:
  `0.4174283771712361142213535120` / `-0.002279627586494221590963274134`
- Mirage score: `0.9999192893155195884831233959`
- Research-safe: **false**

Companion `defective_quotes.csv`: 10 validation
failures, 5 high-severity
(`{"crossed_book": 3, "invalid_price": 2, "stale_quote": 5}`).

## Checksums

| File | SHA-256 |
| --- | --- |
| `clean_quotes.csv` | `8d56c624950ad8a76e9761e2c41646b1a163337d2b3e747c4579207266669896` |
| `clean_trades.csv` | `0699f07208636ef5dfd5ab44837f466a315ecbd7df69d78c8cedc5a5e24ec762` |
| `defect_manifest.json` | `8a561c6b6aa813437aee7228fb02cf07b259394620451f8970cd929f3c664a4d` |
| `defective_quotes.csv` | `fb184f2d3d9c32525406dd8075169cd03692514a4bdb2032de1839cc19d5e689` |
| `defective_trades.csv` | `89a902afac189bd8e632e53be3701d7564768350a447c9d684ed1f0dbfab5248` |
| `expected_results.json` | `9ba80b4fe045a35e1925b7a00d642e5359a6d4b59be9433cb917535fb41fc7f6` |

## Reproduce

```bash
make fetch-hf-demo        # fetch + verify (or regenerate offline)
make demo-alpha-mirage    # run the pipeline, print the verdict
make test-reproducibility # assert the numbers above
```
