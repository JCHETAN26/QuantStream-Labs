# Local demo

Two ways to run the Alpha Mirage demo on a clean clone.

## Docker (one command)

```bash
git clone https://github.com/JCHETAN26/QuantStream-Labs
cd QuantStream-Labs
docker compose up --build
```

This builds the image, runs the demo, prints the mirage verdict to the compose logs,
and writes `out/quantstream-report.html` on the host. The `demo` service runs once
and exits — the demo is a self-contained pipeline run, not a long-lived server.

## Local (no Docker)

Requires Python 3.10+.

```bash
make install            # editable-install every package
make demo-alpha-mirage  # runs quantstream-demo
```

The HTML report is written to `quantstream-report.html` in the current directory.
Use `quantstream-demo --output <path>` to choose a different location, or
`--no-report` to skip it.

## Determinism

Both paths produce the identical verdict and the identical raw/clean replay
checksums on every run:

```text
Replay checksum (raw):   7c517a403b20c3b2068215bb2fef5bc66f19b33677041ed6f605f193afe25b06
Replay checksum (clean): 8987f19a0eacecb232e3efa897e27b217b4d567321381f1319dce9df1d440622
```

## Privacy

The demo uses bundled synthetic data, so nothing sensitive is involved. When the
upload path lands, proprietary files run in local mode only: they stay inside the
local Docker environment (or your local process) and are never sent to any external
service.
