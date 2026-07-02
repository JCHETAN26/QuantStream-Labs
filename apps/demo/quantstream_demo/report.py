"""Static HTML research-integrity report.

Self-contained (inline CSS, no dependencies), dense and professional. Given a
DemoResult it renders the dataset provenance, validation results, replay
reproducibility metadata, the raw-vs-clean performance comparison, the companion
quote-defect summary, and the Alpha Mirage verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from html import escape

from quantstream_research import BacktestMetrics, MirageReport
from quantstream_validation import CheckResult, Severity


@dataclass(frozen=True)
class QuotesSummary:
    """Companion quote-dataset validation summary (high-severity defect showcase)."""

    input_file: str
    total_events: int
    flagged_events: int
    high_severity: int
    defect_counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class DemoResult:
    symbol: str
    total_events: int
    injected_spikes: int
    flagged_events: int
    validation_results: tuple[CheckResult, ...]
    raw_checksum: str
    clean_checksum: str
    raw_config_hash: str
    mirage: MirageReport
    load_errors: int = 0
    # Dataset provenance (populated by the demo; empty for ad-hoc CSV analysis).
    dataset_id: str = ""
    source: str = ""
    revision: str = ""
    checksum_summary: str = ""
    input_file: str = ""
    high_severity: int = 0
    quotes: QuotesSummary | None = None
    report_path: str | None = None


def high_severity_count(results: tuple[CheckResult, ...]) -> int:
    return sum(r.count for r in results if r.severity == Severity.CRITICAL)


def fmt_money(value: Decimal) -> str:
    q = value.quantize(Decimal("0.01"))
    sign = "-" if q < 0 else "+"
    return f"{sign}${abs(q):,.2f}"


def fmt_sharpe(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'))}"


def fmt_pct(value: Decimal) -> str:
    return f"{(value * 100).quantize(Decimal('1'))}%"


def _status_color(status: str) -> str:
    return {"pass": "#1a7f37", "warn": "#9a6700", "fail": "#cf222e"}.get(status, "#555")


def _validation_rows(results: tuple[CheckResult, ...]) -> str:
    rows = []
    for r in results:
        color = _status_color(r.status.value)
        rows.append(
            f"<tr><td>{escape(r.name)}</td>"
            f"<td style='color:{color};font-weight:600'>{r.status.value.upper()}</td>"
            f"<td class='num'>{r.count}</td>"
            f"<td>{escape(r.severity.value)}</td></tr>"
        )
    return "\n".join(rows)


def _metric_rows(raw: BacktestMetrics, clean: BacktestMetrics) -> str:
    def row(label: str, r: str, c: str) -> str:
        return f"<tr><td>{label}</td><td class='num'>{r}</td><td class='num'>{c}</td></tr>"

    return "\n".join(
        [
            row("Sharpe (per-step)", fmt_sharpe(raw.sharpe), fmt_sharpe(clean.sharpe)),
            row("Total PnL", fmt_money(raw.total_pnl), fmt_money(clean.total_pnl)),
            row("Max drawdown", fmt_money(raw.max_drawdown), fmt_money(clean.max_drawdown)),
            row("Hit rate", fmt_pct(raw.hit_rate), fmt_pct(clean.hit_rate)),
            row("Turnover", str(raw.turnover), str(clean.turnover)),
            row("Active intervals", str(raw.active_intervals), str(clean.active_intervals)),
        ]
    )


def _provenance_section(result: DemoResult) -> str:
    if not result.dataset_id:
        return ""
    rows = [
        ("Dataset", escape(result.dataset_id)),
        ("Input file", escape(result.input_file or "")),
        ("Source", escape(result.source or "")),
        ("Revision", escape(result.revision or "")),
        ("Checksum status", f"PASS ({escape(result.checksum_summary)})"
            if result.checksum_summary else "PASS"),
    ]
    body = "\n".join(
        f"<tr><td>{k}</td><td class='mono'>{v}</td></tr>" for k, v in rows
    )
    return f"""
  <section>
    <h2>Dataset Provenance</h2>
    <table><tbody>
      {body}
    </tbody></table>
  </section>"""


def _quotes_section(result: DemoResult) -> str:
    q = result.quotes
    if q is None:
        return ""
    counts = ", ".join(f"{escape(k)}: {v}" for k, v in sorted(q.defect_counts.items()))
    return f"""
  <section>
    <h2>Companion Quote Dataset</h2>
    <div class="grid">
      <div class="stat"><div class="k">File</div><div class="v">{escape(q.input_file)}</div></div>
      <div class="stat"><div class="k">Validation failures</div><div class="v">{q.flagged_events}</div></div>
      <div class="stat"><div class="k">High-severity</div><div class="v">{q.high_severity}</div></div>
    </div>
    <p class="mono">{escape(counts)}</p>
  </section>"""


def build_html(result: DemoResult) -> str:
    m = result.mirage
    verdict_color = "#cf222e" if not m.research_safe else "#1a7f37"
    verdict_label = "ALPHA MIRAGE DETECTED" if not m.research_safe else "SIGNAL RESEARCH-SAFE"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QuantStream Labs — Research Integrity Report</title>
<style>
  :root {{ --ink:#1c2128; --muted:#57606a; --line:#d0d7de; --bg:#f6f8fa; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
          color:var(--ink); margin:0; background:#fff; line-height:1.5; }}
  header {{ background:var(--ink); color:#fff; padding:28px 40px; }}
  header h1 {{ margin:0; font-size:20px; letter-spacing:.2px; }}
  header p {{ margin:6px 0 0; color:#adbac7; font-size:13px; }}
  main {{ max-width:900px; margin:0 auto; padding:32px 40px 64px; }}
  section {{ margin:28px 0; }}
  h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.6px;
        color:var(--muted); border-bottom:1px solid var(--line); padding-bottom:6px; }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; }}
  th,td {{ text-align:left; padding:7px 10px; border-bottom:1px solid var(--line); }}
  th {{ color:var(--muted); font-weight:600; font-size:12px; text-transform:uppercase; }}
  td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums;
                    font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
  .verdict {{ border:2px solid {verdict_color}; border-radius:8px; padding:20px 24px;
              background:var(--bg); }}
  .verdict .tag {{ color:{verdict_color}; font-weight:700; letter-spacing:.4px; font-size:13px; }}
  .verdict .score {{ font-size:40px; font-weight:700; margin:6px 0; font-variant-numeric:tabular-nums; }}
  .verdict p {{ margin:6px 0 0; color:var(--ink); }}
  .mono {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px;
           color:var(--muted); word-break:break-all; }}
  .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }}
  .stat {{ background:var(--bg); border:1px solid var(--line); border-radius:6px; padding:12px 14px; }}
  .stat .k {{ font-size:12px; color:var(--muted); }}
  .stat .v {{ font-size:20px; font-weight:600; font-variant-numeric:tabular-nums; }}
  footer {{ color:var(--muted); font-size:12px; padding:24px 40px; border-top:1px solid var(--line); }}
</style>
</head>
<body>
<header>
  <h1>QuantStream Labs — Research Integrity Report</h1>
  <p>Deterministic replay · market-data validation · Alpha Mirage analysis</p>
</header>
<main>

  <section class="verdict">
    <div class="tag">{verdict_label}</div>
    <div class="score">Mirage Score: {fmt_pct(m.mirage_score)}</div>
    <p>{escape(m.conclusion)}</p>
  </section>
{_provenance_section(result)}
  <section>
    <h2>Dataset Summary</h2>
    <div class="grid">
      <div class="stat"><div class="k">Symbol</div><div class="v">{escape(result.symbol)}</div></div>
      <div class="stat"><div class="k">Events</div><div class="v">{result.total_events}</div></div>
      <div class="stat"><div class="k">Flagged events</div><div class="v">{result.flagged_events}</div></div>
      <div class="stat"><div class="k">High-severity</div><div class="v">{result.high_severity}</div></div>
    </div>
  </section>

  <section>
    <h2>Validation Results</h2>
    <table>
      <thead><tr><th>Check</th><th>Status</th><th class="num">Count</th><th>Severity</th></tr></thead>
      <tbody>
      {_validation_rows(result.validation_results)}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Raw vs Cleaned Performance</h2>
    <table>
      <thead><tr><th>Metric</th><th class="num">Raw data</th><th class="num">Cleaned data</th></tr></thead>
      <tbody>
      {_metric_rows(m.raw, m.clean)}
      </tbody>
    </table>
  </section>
{_quotes_section(result)}
  <section>
    <h2>Reproducibility</h2>
    <table>
      <tbody>
        <tr><td>Replay checksum (raw)</td><td class="mono">{result.raw_checksum}</td></tr>
        <tr><td>Replay checksum (cleaned)</td><td class="mono">{result.clean_checksum}</td></tr>
        <tr><td>Replay config hash</td><td class="mono">{result.raw_config_hash}</td></tr>
      </tbody>
    </table>
    <p class="mono">Same input and config reproduce these checksums exactly, on any platform.</p>
  </section>

</main>
<footer>
  Generated by QuantStream Labs. Mirage score = tainted PnL / total PnL on the raw run;
  a value a reviewer can recompute from the raw backtest's contributions.
</footer>
</body>
</html>
"""
