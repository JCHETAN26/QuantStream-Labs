"""`make demo-alpha-mirage`: run the whole pipeline on the bundled sample and print
the Alpha Mirage verdict, then write the HTML research-integrity report.

Pipeline: sample events -> validate -> deterministic replay (raw + cleaned) ->
raw-vs-cleaned backtest -> Alpha Mirage. Everything is deterministic, so the verdict
and both replay checksums are identical on every run.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from quantstream_replay import replay
from quantstream_research import MeanReversionStrategy, detect_alpha_mirage
from quantstream_validation import clean as clean_events
from quantstream_validation import validate

from .report import DemoResult, build_html, fmt_money, fmt_pct, fmt_sharpe
from .sample_data import SAMPLE_SYMBOL, injected_spike_count, sample_events

_STRATEGY = MeanReversionStrategy(lookback=1)


def run_demo() -> DemoResult:
    events = sample_events()

    report = validate(events)
    cleaned = clean_events(events, report)

    raw_replay = replay(events)
    clean_replay = replay(cleaned)

    mirage = detect_alpha_mirage(events, list(report.defect_map), _STRATEGY)

    return DemoResult(
        symbol=SAMPLE_SYMBOL,
        total_events=len(events),
        injected_spikes=injected_spike_count(),
        flagged_events=report.flagged_events,
        validation_results=report.results,
        raw_checksum=raw_replay.checksum,
        clean_checksum=clean_replay.checksum,
        raw_config_hash=raw_replay.config_hash,
        mirage=mirage,
    )


def format_terminal(result: DemoResult) -> str:
    m = result.mirage
    lines = [
        "QuantStream Labs — Alpha Mirage Demo",
        f"Symbol: {result.symbol}   Events: {result.total_events}   "
        f"Bad-tick events flagged: {result.flagged_events}",
        "",
        f"Raw Sharpe:   {fmt_sharpe(m.raw.sharpe)}",
        f"Clean Sharpe: {fmt_sharpe(m.clean.sharpe)}",
        f"Mirage Score: {fmt_pct(m.mirage_score)}",
        "",
        f"Raw PnL:   {fmt_money(m.raw.total_pnl)}",
        f"Clean PnL: {fmt_money(m.clean.total_pnl)}",
        "",
        "Conclusion:",
        m.conclusion,
        "",
        f"Replay checksum (raw):   {result.raw_checksum}",
        f"Replay checksum (clean): {result.clean_checksum}",
    ]
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
    args = parser.parse_args(argv)

    result = run_demo()
    print(format_terminal(result))

    if not args.no_report:
        out = Path(args.output)
        out.write_text(build_html(result), encoding="utf-8")
        print(f"\nReport written to: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
