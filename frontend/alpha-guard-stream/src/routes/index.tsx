import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertOctagon, ShieldCheck, ExternalLink, FileDown } from "lucide-react";
import { useMemo } from "react";

import { api, fmtNum, fmtPct, fmtSigned } from "@/lib/api";
import type { SeriesReport } from "@/lib/api";
import { Shell } from "@/components/quant/Shell";
import {
  Panel,
  Stat,
  CopyField,
  Skeleton,
  StatusPill,
} from "@/components/quant/primitives";
import { useCountUp } from "@/lib/useCountUp";

export const Route = createFileRoute("/")({
  component: AlphaMiragePage,
});

function AlphaMiragePage() {
  const demoQ = useQuery({ queryKey: ["demo"], queryFn: api.demo });
  const seriesQ = useQuery({ queryKey: ["demo", "series"], queryFn: api.demoSeries });

  const source = demoQ.data?.source ?? seriesQ.data?.source;
  const d = demoQ.data?.data;
  const s = seriesQ.data?.data;

  return (
    <Shell source={source}>
      <div className="px-4 py-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="label-xs">module · alpha mirage detector</div>
            <h1 className="text-[15px] font-semibold mt-0.5">
              Raw vs Cleaned Strategy Divergence
              {d && (
                <span className="mono text-muted-fg font-normal ml-2">
                  / {d.symbol} · {d.total_events} events · {d.flagged_events} flagged
                </span>
              )}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <a
              href={api.reportUrl()}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 mono text-[11px] px-2.5 py-1.5 border border-border rounded-sm hover:border-accent-cyan hover:text-accent-cyan transition-colors"
            >
              <FileDown className="h-3 w-3" /> HTML report
              <ExternalLink className="h-3 w-3 opacity-60" />
            </a>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-8 space-y-4">
            <Panel title="Cumulative PnL · raw vs cleaned">
              {s ? (
                <DivergenceCharts series={s} />
              ) : (
                <Skeleton className="h-[340px] m-3" />
              )}
              {s && <DefectStrip series={s} />}
            </Panel>

            {d ? (
              <Panel title="Performance stats">
                <div className="grid grid-cols-4 divide-x divide-border">
                  <StatBlock label="Sharpe" raw={d.raw.sharpe} clean={d.clean.sharpe} kind="ratio" />
                  <StatBlock label="Total PnL" raw={d.raw.total_pnl} clean={d.clean.total_pnl} kind="pnl" />
                  <StatBlock label="Max drawdown" raw={d.raw.max_drawdown} clean={d.clean.max_drawdown} kind="pnl" />
                  <StatBlock label="Hit rate" raw={d.raw.hit_rate} clean={d.clean.hit_rate} kind="pct" />
                </div>
                <div className="grid grid-cols-4 divide-x divide-border border-t border-border">
                  <StatBlock label="Turnover" raw={d.raw.turnover} clean={d.clean.turnover} kind="ratio" />
                  <StatBlock
                    label="Active intervals"
                    raw={d.raw.active_intervals}
                    clean={d.clean.active_intervals}
                    kind="int"
                  />
                  <StatBlock
                    label="Total intervals"
                    raw={d.raw.total_intervals}
                    clean={d.clean.total_intervals}
                    kind="int"
                  />
                  <StatBlock
                    label="Flagged / total"
                    raw={d.flagged_events}
                    clean={d.total_events}
                    kind="ratio-frac"
                  />
                </div>
              </Panel>
            ) : (
              <Skeleton className="h-32" />
            )}
          </div>

          <div className="col-span-4 space-y-4">
            {d ? <Verdict report={d} /> : <Skeleton className="h-64" />}
            {d ? (
              <Panel title="Reproducibility · sha256">
                <div className="p-3 space-y-3">
                  <CopyField label="raw dataset checksum" value={d.raw_checksum} />
                  <CopyField label="cleaned dataset checksum" value={d.clean_checksum} />
                  <p className="mono text-[11px] text-muted-fg leading-relaxed pt-1 border-t border-border">
                    Same input + config reproduce this checksum on any platform.
                  </p>
                </div>
              </Panel>
            ) : (
              <Skeleton className="h-48" />
            )}

            {d ? (
              <Panel title="Top validation failures">
                <ul className="divide-y divide-border">
                  {d.validation
                    .filter((v) => v.status !== "PASS")
                    .slice(0, 5)
                    .map((v) => (
                      <li key={v.name} className="flex items-center justify-between px-3 py-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <StatusPill status={v.status} />
                          <span className="mono text-[12px] truncate">{v.name}</span>
                        </div>
                        <span className="mono text-[12px] text-muted-fg">{v.count}</span>
                      </li>
                    ))}
                </ul>
              </Panel>
            ) : null}
          </div>
        </div>
      </div>
    </Shell>
  );
}

function StatBlock({
  label,
  raw,
  clean,
  kind,
}: {
  label: string;
  raw: number;
  clean: number;
  kind: "ratio" | "pnl" | "pct" | "int" | "ratio-frac";
}) {
  const rawStr =
    kind === "pct" ? fmtPct(raw) :
    kind === "pnl" ? fmtSigned(raw) :
    kind === "int" ? Math.round(raw).toLocaleString() :
    kind === "ratio-frac" ? `${raw}/${clean}` :
    fmtNum(raw, 2);
  const cleanStr =
    kind === "pct" ? fmtPct(clean) :
    kind === "pnl" ? fmtSigned(clean) :
    kind === "int" ? Math.round(clean).toLocaleString() :
    kind === "ratio-frac" ? fmtPct(raw / clean) :
    fmtNum(clean, 2);

  const worse =
    kind === "pnl" || kind === "ratio" || kind === "pct" ? clean < raw : false;

  return (
    <div className="px-3 py-3">
      <div className="label-xs">{label}</div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="mono text-[16px] text-danger">{rawStr}</span>
        <span className="mono text-[10px] text-muted-fg">raw</span>
      </div>
      <div className="mt-0.5 flex items-baseline gap-2">
        <span className={`mono text-[16px] ${worse ? "text-warn" : "text-success"}`}>
          {cleanStr}
        </span>
        <span className="mono text-[10px] text-muted-fg">clean</span>
      </div>
    </div>
  );
}

function Verdict({ report }: { report: NonNullable<ReturnType<typeof useQuery<any>>["data"]>["data"] extends infer T ? any : any }) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const r = report as {
    mirage_score: number;
    research_safe: boolean;
    conclusion: string;
  };
  const score = useCountUp(r.mirage_score * 100, 1100);
  const mirage = !r.research_safe;
  return (
    <Panel
      title={mirage ? "verdict · mirage" : "verdict · safe"}
      right={
        mirage ? (
          <AlertOctagon className="h-3.5 w-3.5 text-danger" />
        ) : (
          <ShieldCheck className="h-3.5 w-3.5 text-success" />
        )
      }
    >
      <div className={`p-4 border-l-2 ${mirage ? "border-danger" : "border-success"}`}>
        <div
          className={`mono text-[13px] font-semibold tracking-widest ${
            mirage ? "text-danger" : "text-success"
          }`}
        >
          {mirage ? "ALPHA MIRAGE DETECTED" : "SIGNAL RESEARCH-SAFE"}
        </div>
        <div className="mt-3">
          <div className="label-xs">mirage score</div>
          <div className="flex items-baseline gap-2 mt-1">
            <span
              className={`mono text-4xl font-semibold tabular-nums ${
                mirage ? "text-danger" : "text-success"
              }`}
            >
              {score.toFixed(1)}
            </span>
            <span className="mono text-muted-fg text-lg">%</span>
          </div>
          <div className="mt-2 h-1 bg-panel-elevated rounded-sm overflow-hidden">
            <div
              className={mirage ? "h-full bg-danger" : "h-full bg-success"}
              style={{ width: `${Math.min(100, score)}%`, transition: "width 200ms linear" }}
            />
          </div>
        </div>
        <p className="mt-4 text-[12.5px] leading-relaxed text-foreground/90">
          {r.conclusion}
        </p>
      </div>
    </Panel>
  );
}

function DivergenceCharts({ series }: { series: SeriesReport }) {
  const data = useMemo(
    () =>
      series.raw_curve.map((r, i) => ({
        seq: r.seq,
        raw: r.cum_pnl,
        clean: series.clean_curve[i]?.cum_pnl ?? 0,
        taint: r.tainted ? r.cum_pnl : null,
      })),
    [series],
  );

  return (
    <div className="grid grid-cols-2 divide-x divide-border">
      <ChartPanel title="RAW DATA" data={data} lineKey="raw" color="var(--danger)" fillTaint />
      <ChartPanel title="CLEANED DATA" data={data} lineKey="clean" color="var(--success)" />
    </div>
  );
}

function ChartPanel({
  title,
  data,
  lineKey,
  color,
  fillTaint,
}: {
  title: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any[];
  lineKey: "raw" | "clean";
  color: string;
  fillTaint?: boolean;
}) {
  const last = data[data.length - 1]?.[lineKey] ?? 0;
  return (
    <div className="p-3">
      <div className="flex items-baseline justify-between mb-2">
        <div className="label-xs">{title}</div>
        <div className="mono text-[14px]" style={{ color }}>
          {fmtSigned(last)}
        </div>
      </div>
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 6, right: 8, left: -12, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
            <XAxis
              dataKey="seq"
              stroke="var(--muted-fg)"
              tick={{ fill: "var(--muted-fg)", fontSize: 10, fontFamily: "var(--font-mono)" }}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
            />
            <YAxis
              stroke="var(--muted-fg)"
              tick={{ fill: "var(--muted-fg)", fontSize: 10, fontFamily: "var(--font-mono)" }}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              width={56}
            />
            <Tooltip
              contentStyle={{
                background: "var(--panel-elevated)",
                border: "1px solid var(--border)",
                borderRadius: 3,
                fontSize: 11,
                fontFamily: "var(--font-mono)",
              }}
              labelStyle={{ color: "var(--muted-fg)" }}
            />
            {fillTaint && (
              <Area
                type="monotone"
                dataKey="taint"
                fill="var(--danger)"
                stroke="none"
                fillOpacity={0.18}
                isAnimationActive={false}
                connectNulls={false}
              />
            )}
            <Line
              type="monotone"
              dataKey={lineKey}
              stroke={color}
              strokeWidth={1.5}
              dot={false}
              isAnimationActive
              animationDuration={1400}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function DefectStrip({ series }: { series: SeriesReport }) {
  const total = series.total_events;
  const bySeq = new Map(series.flagged.map((f) => [f.seq, f.defects]));
  const defectColor = (d: string) =>
    d.includes("crossed")
      ? "var(--danger)"
      : d.includes("stale")
      ? "var(--warn)"
      : d.includes("timestamp")
      ? "var(--accent-cyan)"
      : "var(--danger)";
  return (
    <div className="border-t border-border">
      <div className="flex items-center justify-between px-3 pt-2">
        <div className="label-xs">defect timeline · {series.flagged.length} events</div>
        <div className="flex items-center gap-3 mono text-[10px] text-muted-fg">
          <LegendDot color="var(--danger)" label="crossed / gap" />
          <LegendDot color="var(--warn)" label="stale" />
          <LegendDot color="var(--accent-cyan)" label="timestamp" />
        </div>
      </div>
      <div className="relative h-8 mx-3 my-2 bg-panel-elevated rounded-sm overflow-hidden">
        {series.flagged.map((f) => {
          const d = f.defects[0] ?? "unknown";
          return (
            <div
              key={f.seq}
              title={`seq ${f.seq}: ${f.defects.join(", ")}`}
              className="absolute top-0 bottom-0 w-[2px]"
              style={{
                left: `${(f.seq / total) * 100}%`,
                background: defectColor(d),
                opacity: 0.85,
              }}
            />
          );
        })}
      </div>
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className="h-2 w-2 rounded-sm" style={{ background: color }} />
      {label}
    </span>
  );
}
