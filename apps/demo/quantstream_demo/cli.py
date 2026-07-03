"""`make demo-alpha-mirage`: run the whole backend flow on the official demo dataset
and print the Alpha Mirage verdict, then write the HTML research-integrity report.

Pipeline: ensure/verify dataset -> load normalized events -> validate -> deterministic
replay (raw + cleaned) -> raw-vs-cleaned backtest -> Alpha Mirage. Everything is
deterministic, so the verdict and both replay checksums are identical on every run.

The dataset is the checksummed ``data/demo`` set produced by the dataset registry
(fetched from Hugging Face or regenerated offline). The demo verifies SHA-256 before
running and, by default, refuses to continue on a checksum mismatch.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from quantstream_dataset_registry import (
    ChecksumError,
    demo_backtest_config,
    ensure_dataset,
)
from quantstream_replay import replay
from quantstream_research import MeanReversionStrategy, detect_alpha_mirage
from quantstream_schema import load_csv_path
from quantstream_validation import clean as clean_events
from quantstream_validation import validate

from .report import (
    DemoResult,
    QuotesSummary,
    build_html,
    fmt_money,
    fmt_pct,
    fmt_sharpe,
    high_severity_count,
)

_STRATEGY = MeanReversionStrategy(lookback=1)
# Public aliases so other services (the API series endpoint) reuse the exact strategy
# and transaction-cost config, keeping their numbers identical to the headline verdict.
DEMO_STRATEGY = _STRATEGY
DEMO_CONFIG = demo_backtest_config()

PRIMARY_TRADES = "defective_trades.csv"
COMPANION_QUOTES = "defective_quotes.csv"


def dataset_events(*, strict: bool = True) -> list:
    """Ensure/verify the official dataset and load its primary trade events.

    Shared by the demo and by the API so the equity-curve series is computed from
    exactly the same events and ordering as the headline verdict.
    """
    status = ensure_dataset(strict=strict)
    return _load_events(status.data_dir / PRIMARY_TRADES)


def analyze_events(
    events,
    *,
    symbol: str,
    injected_spikes: int = 0,
    load_errors: int = 0,
) -> DemoResult:
    """Run validate -> replay(raw+clean) -> Alpha Mirage on a set of events.

    The shared pipeline used by the CLI, the dataset demo, and the API gateway.
    """
    report = validate(events)
    cleaned = clean_events(events, report)

    raw_replay = replay(events)
    clean_replay = replay(cleaned)

    mirage = detect_alpha_mirage(
        events, list(report.defect_map), _STRATEGY, config=DEMO_CONFIG
    )

    return DemoResult(
        symbol=symbol,
        total_events=len(events),
        injected_spikes=injected_spikes,
        flagged_events=report.flagged_events,
        validation_results=report.results,
        raw_checksum=raw_replay.checksum,
        clean_checksum=clean_replay.checksum,
        raw_config_hash=raw_replay.config_hash,
        mirage=mirage,
        load_errors=load_errors,
        high_severity=high_severity_count(report.results),
    )


def _load_events(csv_path: Path) -> list:
    _schema, load = load_csv_path(str(csv_path))
    if not load.events:
        raise ValueError(
            f"no events loaded from {csv_path} ({len(load.errors)} row errors)"
        )
    return load.events


def _quotes_summary(data_dir: Path) -> QuotesSummary | None:
    path = data_dir / COMPANION_QUOTES
    if not path.is_file():
        return None
    _schema, load = load_csv_path(str(path))
    report = validate(load.events)
    counts = {r.defect.value: r.count for r in report.results if r.count}
    return QuotesSummary(
        input_file=COMPANION_QUOTES,
        total_events=len(load.events),
        flagged_events=report.flagged_events,
        high_severity=high_severity_count(report.results),
        defect_counts=counts,
    )


def run_dataset_demo(*, strict: bool = True) -> DemoResult:
    """The official demo: ensure + verify the dataset, then run the pipeline."""
    status = ensure_dataset(strict=strict)
    data_dir = status.data_dir

    events = _load_events(data_dir / PRIMARY_TRADES)
    result = analyze_events(events, symbol=events[0].symbol)

    quotes = _quotes_summary(data_dir)
    return DemoResult(
        **{
            **result.__dict__,
            "dataset_id": _dataset_id(data_dir),
            "source": status.source,
            "revision": status.revision,
            "checksum_summary": status.verify.summary(),
            "input_file": PRIMARY_TRADES,
            "quotes": quotes,
        }
    )


def _dataset_id(data_dir: Path) -> str:
    import json

    path = data_dir / "expected_results.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8")).get(
                "dataset_id", "alpha_mirage_demo_v2"
            )
        except (ValueError, OSError):
            pass
    return "alpha_mirage_demo_v2"


def run_demo(csv_path: str | None = None, *, strict: bool = True) -> DemoResult:
    """Run the pipeline on the official dataset, or on a user CSV if given."""
    if csv_path is None:
        return run_dataset_demo(strict=strict)
    events = _load_events(Path(csv_path))
    return analyze_events(
        events, symbol=events[0].symbol, load_errors=_count_load_errors(csv_path)
    )


def _count_load_errors(csv_path: str) -> int:
    _schema, load = load_csv_path(csv_path)
    return len(load.errors)


def format_terminal(result: DemoResult) -> str:
    m = result.mirage
    verdict = (
        "ALPHA MIRAGE DETECTED" if not m.research_safe else "SIGNAL RESEARCH-SAFE"
    )
    lines = [
        "QuantStream Labs — Alpha Mirage Demo",
        "=" * 52,
    ]
    if result.dataset_id:
        lines += [
            f"Dataset:          {result.dataset_id}",
            f"Source:           {result.source}   revision: {result.revision}",
            f"Checksum status:  PASS ({result.checksum_summary} files verified)",
            "",
        ]
    lines += [
        f"Input:            {result.input_file or 'CSV'}   "
        f"Symbol: {result.symbol}   Events: {result.total_events}",
        f"Validation failures:   {result.flagged_events}",
        f"High-severity defects: {result.high_severity}",
    ]
    if result.quotes is not None:
        q = result.quotes
        detail = ", ".join(f"{k} {v}" for k, v in sorted(q.defect_counts.items()))
        lines += [
            f"Companion quotes:      {q.input_file}  "
            f"({q.flagged_events} failures, {q.high_severity} high-severity)",
            f"                       {detail}",
        ]
    lines += [
        "",
        f"Replay checksum (raw):   {result.raw_checksum}",
        f"Replay checksum (clean): {result.clean_checksum}",
        "",
        f"Raw Sharpe:   {fmt_sharpe(m.raw.sharpe)}"
        f"      Raw PnL:   {fmt_money(m.raw.total_pnl)}",
        f"Clean Sharpe: {fmt_sharpe(m.clean.sharpe)}"
        f"      Clean PnL: {fmt_money(m.clean.total_pnl)}",
        f"Mirage Score: {fmt_pct(m.mirage_score)}",
        "",
        f"Conclusion: {verdict}",
        m.conclusion,
    ]
    if result.report_path:
        lines += ["", f"Report: {result.report_path}"]
    if result.load_errors:
        lines.append(f"\nNote: {result.load_errors} CSV rows skipped (parse errors).")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QuantStream Labs Alpha Mirage demo")
    parser.add_argument(
        "--output",
        default="quantstream-report.html",
        help="path for the HTML research-integrity report",
    )
    parser.add_argument(
        "--no-report", action="store_true", help="skip writing the HTML report"
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="load trades from a CSV instead of the official dataset",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="regenerate the dataset instead of failing on a checksum mismatch",
    )
    args = parser.parse_args(argv)

    try:
        result = run_demo(csv_path=args.csv, strict=not args.debug)
    except ChecksumError as exc:
        print(f"Checksum status: FAIL\nERROR: {exc}", file=sys.stderr)
        print(
            "Refusing to run on an unverified dataset. Re-fetch with "
            "`make fetch-hf-demo`, or pass --debug to regenerate.",
            file=sys.stderr,
        )
        return 1

    report_path: str | None = None
    if not args.no_report:
        out = Path(args.output)
        out.write_text(build_html(result), encoding="utf-8")
        report_path = str(out)
        result = DemoResult(**{**result.__dict__, "report_path": report_path})

    print(format_terminal(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
