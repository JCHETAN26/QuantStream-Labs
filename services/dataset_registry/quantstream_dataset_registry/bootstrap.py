"""Build the official demo dataset directory from deterministic generators.

This produces the exact set of files that live under ``data/demo`` and that are
published to Hugging Face:

    clean_trades.csv        pristine control trades (no defects)
    defective_trades.csv    trades with injected bad-tick spikes (drives the mirage)
    clean_quotes.csv        pristine control quotes
    defective_quotes.csv    quotes with crossed books, bad prices, and a stale block
    defect_manifest.json    ground-truth injected defects per file
    expected_results.json   canonical expected pipeline output (the regression lock)
    SHA256SUMS              sha256 of the six files above
    README.md               dataset card

``expected_results.json`` is computed by actually running the pipeline here, so the
committed values are never hand-typed. Everything is byte-stable: no timestamps, no
wall-clock, sorted JSON keys, LF line endings.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from quantstream_contracts.fixed_point import price_to_fixed
from quantstream_replay import replay
from quantstream_research import (
    DEFAULT_MIRAGE_THRESHOLD,
    BacktestConfig,
    MeanReversionStrategy,
    detect_alpha_mirage,
)
from quantstream_validation import Severity, validate
from quantstream_validation import clean as clean_events

from . import generate
from .checksums import SHA256SUMS_NAME, render_sha256sums, sha256_bytes

DATASET_ID = "alpha_mirage_demo_v2"
HF_REPO = "JCHETAN26/quantstream-alpha-mirage"
STRATEGY_LOOKBACK = 1
# Transaction cost per unit of position change (commission + half-spread), ~2 bps at
# $100. The single source of truth for the demo cost, shared by the demo CLI and API.
DEMO_COST_PER_UNIT = price_to_fixed("0.02")


def demo_backtest_config() -> BacktestConfig:
    return BacktestConfig(cost_per_unit=DEMO_COST_PER_UNIT)

# Files covered by SHA256SUMS ("N/N files verified").
HASHED_FILES = (
    "clean_trades.csv",
    "defective_trades.csv",
    "clean_quotes.csv",
    "defective_quotes.csv",
    "defect_manifest.json",
    "expected_results.json",
)


@dataclass(frozen=True)
class BuiltDataset:
    files: dict[str, bytes]  # filename -> exact bytes (includes SHA256SUMS, README)
    expected_results: dict
    manifest: dict


def _json_bytes(obj: dict) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _strategy() -> MeanReversionStrategy:
    return MeanReversionStrategy(lookback=STRATEGY_LOOKBACK)


def _high_severity_count(report) -> int:
    return sum(
        r.count for r in report.results if r.severity == Severity.CRITICAL
    )


def _defect_counts(report) -> dict[str, int]:
    return {r.defect.value: r.count for r in report.results if r.count}


def compute_expected_results() -> dict:
    """Run the full pipeline on the generated data and return the canonical result."""
    trades = generate.sample_events()
    report = validate(trades)
    cleaned = clean_events(trades, report)

    raw_replay = replay(trades)
    clean_replay = replay(cleaned)
    mirage = detect_alpha_mirage(
        trades, list(report.defect_map), _strategy(), config=demo_backtest_config()
    )

    quotes, _truth = generate.defective_quote_events()
    quote_report = validate(quotes)

    return {
        "dataset_id": DATASET_ID,
        "hf_repo": HF_REPO,
        "strategy": {"name": "mean_reversion", "lookback": STRATEGY_LOOKBACK},
        "mirage_threshold": str(DEFAULT_MIRAGE_THRESHOLD),
        # Primary result: the Alpha Mirage flow runs on the defective trades.
        "input_file": "defective_trades.csv",
        "symbol": generate.SAMPLE_SYMBOL,
        "event_count": len(trades),
        "expected_validation_failures": report.flagged_events,
        "expected_high_severity_defects": _high_severity_count(report),
        "expected_defect_counts": _defect_counts(report),
        "expected_replay_checksum": raw_replay.checksum,
        "expected_replay_checksum_clean": clean_replay.checksum,
        "expected_replay_config_hash": raw_replay.config_hash,
        "expected_raw_sharpe": str(mirage.raw.sharpe),
        "expected_clean_sharpe": str(mirage.clean.sharpe),
        "expected_raw_sharpe_annualized": str(mirage.raw.sharpe_annualized),
        "expected_clean_sharpe_annualized": str(mirage.clean.sharpe_annualized),
        "expected_raw_gross_pnl": str(mirage.raw.gross_pnl),
        "expected_raw_cost": str(mirage.raw.total_cost),
        "expected_raw_pnl": str(mirage.raw.total_pnl),
        "expected_clean_pnl": str(mirage.clean.total_pnl),
        "expected_tainted_pnl": str(mirage.raw.tainted_pnl),
        "expected_mirage_score": str(mirage.mirage_score),
        "expected_research_safe": mirage.research_safe,
        # Companion quote dataset: exercises the high-severity defect checks.
        "companion_quotes": {
            "input_file": "defective_quotes.csv",
            "event_count": len(quotes),
            "expected_validation_failures": quote_report.flagged_events,
            "expected_high_severity_defects": _high_severity_count(quote_report),
            "expected_defect_counts": _defect_counts(quote_report),
        },
    }
    # (mirage_threshold walrus keeps the value inline without an extra import line)
    # (mirage_threshold walrus keeps the value inline without an extra import line)


def _seqs_with(defect: str, truth: dict[int, list[str]]) -> list[int]:
    return sorted(seq for seq, defects in truth.items() if defect in defects)


def build_manifest() -> dict:
    """Ground-truth record of what was injected into each defective file."""
    spike_seqs = generate._spike_indices()
    _quotes, quote_truth = generate.defective_quote_events()

    return {
        "dataset_id": DATASET_ID,
        "description": (
            "Ground-truth injected defects for the QuantStream Labs Alpha Mirage "
            "demo dataset. Detection is measured against this file; the validation "
            "engine never reads it."
        ),
        "seeds": {"trades": generate.SAMPLE_SEED, "quotes": generate._Q_SEED},
        "files": {
            "clean_trades.csv": {
                "instrument": "trade",
                "symbol": generate.SAMPLE_SYMBOL,
                "event_count": generate._N,
                "injected_defects": {},
            },
            "defective_trades.csv": {
                "instrument": "trade",
                "symbol": generate.SAMPLE_SYMBOL,
                "event_count": generate._N,
                "injected_defects": {"bad_tick_spikes": spike_seqs},
                "injected_defect_counts": {"bad_tick_spikes": len(spike_seqs)},
                "note": (
                    "Each spike produces two >20% moves (into and out of the spike), "
                    "so the detector flags roughly twice the spike count as bad ticks."
                ),
            },
            "clean_quotes.csv": {
                "instrument": "quote",
                "symbol": generate.SAMPLE_SYMBOL,
                "event_count": generate._Q_N,
                "injected_defects": {},
            },
            "defective_quotes.csv": {
                "instrument": "quote",
                "symbol": generate.SAMPLE_SYMBOL,
                "event_count": generate._Q_N,
                "injected_defects": {
                    "crossed_book": _seqs_with("crossed_book", quote_truth),
                    "invalid_price": _seqs_with("invalid_price", quote_truth),
                    "stale_quote": _seqs_with("stale_quote", quote_truth),
                },
                "injected_defect_counts": {
                    "crossed_book": len(_seqs_with("crossed_book", quote_truth)),
                    "invalid_price": len(_seqs_with("invalid_price", quote_truth)),
                    "stale_quote": len(_seqs_with("stale_quote", quote_truth)),
                },
            },
        },
    }


def _readme(expected: dict, sums: dict[str, str]) -> str:
    q = expected["companion_quotes"]
    rows = "\n".join(f"| `{name}` | `{sums[name]}` |" for name in sorted(sums))
    return f"""# QuantStream Labs — Alpha Mirage reproducibility dataset

`{DATASET_ID}` · canonical demo dataset for
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

- Validation failures: **{expected['expected_validation_failures']}**
- High-severity defects: **{expected['expected_high_severity_defects']}**
- Replay checksum (raw): `{expected['expected_replay_checksum']}`
- Raw Sharpe / Clean Sharpe:
  `{expected['expected_raw_sharpe']}` / `{expected['expected_clean_sharpe']}`
- Mirage score: `{expected['expected_mirage_score']}`
- Research-safe: **{str(expected['expected_research_safe']).lower()}**

Companion `defective_quotes.csv`: {q['expected_validation_failures']} validation
failures, {q['expected_high_severity_defects']} high-severity
(`{json.dumps(q['expected_defect_counts'], sort_keys=True)}`).

## Checksums

| File | SHA-256 |
| --- | --- |
{rows}

## Reproduce

```bash
make fetch-hf-demo        # fetch + verify (or regenerate offline)
make demo-alpha-mirage    # run the pipeline, print the verdict
make test-reproducibility # assert the numbers above
```
"""


def build_dataset() -> BuiltDataset:
    """Assemble every dataset file in memory (deterministic bytes)."""
    files: dict[str, bytes] = {}

    files["clean_trades.csv"] = generate.render_trades_csv(
        generate.clean_events()
    ).encode("utf-8")
    files["defective_trades.csv"] = generate.render_trades_csv(
        generate.sample_events()
    ).encode("utf-8")
    files["clean_quotes.csv"] = generate.render_quotes_csv(
        generate.clean_quote_events()
    ).encode("utf-8")
    defective_quotes, _truth = generate.defective_quote_events()
    files["defective_quotes.csv"] = generate.render_quotes_csv(
        defective_quotes
    ).encode("utf-8")

    manifest = build_manifest()
    files["defect_manifest.json"] = _json_bytes(manifest)

    expected = compute_expected_results()
    files["expected_results.json"] = _json_bytes(expected)

    sums = {name: sha256_bytes(files[name]) for name in HASHED_FILES}
    files[SHA256SUMS_NAME] = render_sha256sums(sums).encode("utf-8")
    files["README.md"] = _readme(expected, sums).encode("utf-8")

    return BuiltDataset(files=files, expected_results=expected, manifest=manifest)


def write_dataset(directory: Path) -> BuiltDataset:
    """Write the full dataset to ``directory`` (created if needed)."""
    built = build_dataset()
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in built.files.items():
        (directory / name).write_bytes(data)
    return built
