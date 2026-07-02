# Local demo

Two ways to run the Alpha Mirage demo on a clean clone.

## Docker (one command)

```bash
git clone https://github.com/JCHETAN26/QuantStream-Labs
cd QuantStream-Labs
docker compose up --build
```

The image installs the packages, pins `QUANTSTREAM_DATA_DIR`, pre-generates and
verifies the official dataset at build time, then runs the demo — printing the
mirage verdict to the compose logs and writing `out/quantstream-report.html` on the
host. The `demo` service runs once and exits; the demo is a self-contained pipeline
run, not a long-lived server. It needs no network access.

## Local (no Docker)

Requires Python 3.10+.

```bash
make install            # editable-install every package
make fetch-hf-demo      # fetch + verify the official dataset (or regenerate offline)
make demo-alpha-mirage  # run the pipeline
```

The HTML report is written to `quantstream-report.html` in the current directory.
Use `quantstream-demo --output <path>` to choose a location, or `--no-report` to
skip it.

## The dataset

`make fetch-hf-demo` acquires `JCHETAN26/quantstream-alpha-mirage` in this order:
valid local cache → Hugging Face (if the `hf` extra + network are available) →
deterministic offline generation. Every path verifies SHA-256 against the dataset's
`SHA256SUMS` and fails loudly on any mismatch.

```bash
quantstream-fetch-dataset --offline   # never touch the network
quantstream-fetch-dataset --force     # ignore the local cache
```

Verify the checksums yourself:

```bash
cd data/demo && sha256sum -c SHA256SUMS   # or: shasum -a 256 -c SHA256SUMS
```

## Determinism

Both paths produce the identical verdict and the identical raw/clean replay
checksums on every run:

```text
Replay checksum (raw):   7c517a403b20c3b2068215bb2fef5bc66f19b33677041ed6f605f193afe25b06
Replay checksum (clean): 8987f19a0eacecb232e3efa897e27b217b4d567321381f1319dce9df1d440622
```

`make test-reproducibility` asserts these — and every other headline number —
against the committed `data/demo/expected_results.json`.

## Privacy

The demo uses bundled synthetic data, so nothing sensitive is involved. For
proprietary files, run in local mode: they stay inside the local Docker environment
(or your local process) and are never sent to any external service.
