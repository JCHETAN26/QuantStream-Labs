# quantstream-demo

The Alpha Mirage demo: one command runs the whole pipeline on a bundled sample and
shows fake alpha collapsing after the data is cleaned.

```bash
make install          # editable-install every package
make demo-alpha-mirage
```

Example output:

```text
QuantStream Labs — Alpha Mirage Demo
Symbol: ACME   Events: 400   Bad-tick events flagged: 198

Raw Sharpe:   0.32
Clean Sharpe: -0.10
Mirage Score: 100%

Raw PnL:   +$3,001.34
Clean PnL: -$0.56

Conclusion:
Signal is not research-safe.
100% of simulated PnL came from corrupted market-data events.
```

It also writes `quantstream-report.html`, a static research-integrity report.

## What the sample proves

The dataset (`sample_data.py`) is a tiny random walk (no real edge) with periodic
bad-tick spikes. A mean-reversion strategy fades each spike and books the
"reversion" — which is just the bad tick correcting. That apparent profit vanishes
once the validation engine flags and removes the bad ticks. The mirage score is the
fraction of raw PnL that came from flagged events.

The pipeline is deterministic: the verdict and both replay checksums are identical on
every run.

## Test

```bash
make install
pytest apps/demo -q
```
