# quantstream-research

The payoff: a no-lookahead backtest, PnL taint attribution, and the **Alpha Mirage
Detector**. Depends on `quantstream-contracts` (and `quantstream-validation` for the
end-to-end integration test).

## How the mirage is measured honestly

1. Run a simple strategy over trades in event-time, per symbol, with no lookahead.
2. Each holding interval `[t, t+1]` produces one PnL contribution.
3. A contribution is **tainted** if any event in its causal chain carries a defect
   flag — the indices the strategy consulted at `t`, plus events `t` and `t+1`.
4. Run the same strategy on raw (defects in) and cleaned (flagged events removed).

```
mirage_score = tainted_pnl(raw) / total_pnl(raw)
```

A signal is research-safe only if that dependence is below a threshold. The score is
one ratio a reviewer can recompute from the raw backtest's contributions — not a
black box.

## No lookahead

`Strategy.decide(prices, i)` may only read `prices[: i + 1]`, and a test asserts the
decision at `i` is identical with or without future prices. This is the property a
quant reviewer looks for first.

## API

```python
from quantstream_research import detect_alpha_mirage, MomentumStrategy

report = detect_alpha_mirage(raw_events, flagged_seqs, MomentumStrategy(lookback=3))
report.raw.sharpe, report.clean.sharpe
report.mirage_score        # tainted / total
report.conclusion          # "... N% of simulated PnL came from corrupted events."
```

## Test

```bash
pip install -e "packages/contracts[dev]"
pip install -e "services/validation-engine[dev]"
pip install -e "services/research-engine[dev]"
pytest services/research-engine -q
```
