import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
  BarChart,
} from "recharts";
import { useState } from "react";

import { api, fmtNum } from "@/lib/api";
import { Shell } from "@/components/quant/Shell";
import {
  ConfidenceBadge,
  Panel,
  Skeleton,
  Stat,
} from "@/components/quant/primitives";

export const Route = createFileRoute("/orderbook")({
  component: OrderBookLab,
});

function OrderBookLab() {
  const [tab, setTab] = useState<"l1" | "l2">("l1");
  const l1 = useQuery({ queryKey: ["ob", "l1"], queryFn: api.orderbookL1 });
  const l2 = useQuery({ queryKey: ["ob", "l2"], queryFn: api.orderbookL2 });

  const source = (tab === "l1" ? l1 : l2).data?.source;

  return (
    <Shell source={source}>
      <div className="px-4 py-4 space-y-4">
        <div className="flex items-end justify-between">
          <div>
            <div className="label-xs">module · orderbooklab</div>
            <h1 className="text-[15px] font-semibold mt-0.5">
              Order Book Health Monitor
            </h1>
          </div>
          <div className="flex items-center gap-1 border border-border rounded-sm p-0.5">
            {(["l1", "l2"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`mono text-[11px] px-3 py-1 rounded-sm transition-colors ${
                  tab === t
                    ? "bg-panel-elevated text-accent-cyan"
                    : "text-muted-fg hover:text-foreground"
                }`}
              >
                {t.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {tab === "l1" ? (
          l1.data ? <L1View data={l1.data.data} /> : <Skeleton className="h-96" />
        ) : l2.data ? (
          <L2View data={l2.data.data} />
        ) : (
          <Skeleton className="h-96" />
        )}
      </div>
    </Shell>
  );
}

function L1View({ data }: { data: NonNullable<ReturnType<typeof api.orderbookL1> extends Promise<infer R> ? R : never>["data"] }) {
  const chartData = data.snapshots.map((s) => ({
    seq: s.seq,
    bid: s.best_bid,
    ask: s.best_ask,
    mid: s.mid_price,
    spread: s.spread,
  }));
  return (
    <>
      <Panel>
        <div className="flex divide-x divide-border">
          <Stat label="Symbol" value={data.symbol} />
          <Stat label="Quotes" value={data.quotes.toLocaleString()} />
          <Stat
            label="Crossed"
            value={data.crossed_count}
            tone={data.crossed_count > 0 ? "danger" : "success"}
          />
          <Stat
            label="Stale"
            value={data.stale_count}
            tone={data.stale_count > 0 ? "warn" : "success"}
          />
          <div className="px-3 py-2.5 flex flex-col justify-center">
            <div className="label-xs">Book confidence</div>
            <div className="mt-1"><ConfidenceBadge value={data.final_confidence} /></div>
          </div>
        </div>
      </Panel>

      <div className="grid grid-cols-3 gap-4">
        <Panel title="Best bid / ask / mid" className="col-span-2">
          <div className="h-[320px] p-3">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 6, right: 8, left: -8, bottom: 0 }}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
                <XAxis dataKey="seq" stroke="var(--muted-fg)" tick={{ fill: "var(--muted-fg)", fontSize: 10, fontFamily: "var(--font-mono)" }} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
                <YAxis stroke="var(--muted-fg)" tick={{ fill: "var(--muted-fg)", fontSize: 10, fontFamily: "var(--font-mono)" }} tickLine={false} axisLine={{ stroke: "var(--border)" }} domain={["dataMin - 0.05", "dataMax + 0.05"]} width={64} />
                <Tooltip contentStyle={{ background: "var(--panel-elevated)", border: "1px solid var(--border)", borderRadius: 3, fontSize: 11, fontFamily: "var(--font-mono)" }} />
                <Line type="monotone" dataKey="bid" stroke="var(--success)" strokeWidth={1.2} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="ask" stroke="var(--danger)" strokeWidth={1.2} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="mid" stroke="var(--accent-cyan)" strokeWidth={1.5} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Confidence states seen">
          <div className="p-3 space-y-2">
            {data.confidence_states_seen.map((s) => (
              <div key={s} className="flex items-center justify-between">
                <ConfidenceBadge value={s} />
                <span className="mono text-[11px] text-muted-fg">
                  {data.snapshots.filter((x) => x.confidence === s).length}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="Recent snapshots · L1">
        <div className="max-h-[360px] overflow-auto">
          <table className="w-full mono text-[11px]">
            <thead className="sticky top-0 bg-panel">
              <tr className="text-left border-b border-border label-xs">
                <th className="px-3 py-2 font-normal">seq</th>
                <th className="px-3 py-2 font-normal text-right">bid</th>
                <th className="px-3 py-2 font-normal text-right">ask</th>
                <th className="px-3 py-2 font-normal text-right">spread</th>
                <th className="px-3 py-2 font-normal text-right">mid</th>
                <th className="px-3 py-2 font-normal text-right">age(ns)</th>
                <th className="px-3 py-2 font-normal">flags</th>
                <th className="px-3 py-2 font-normal">conf</th>
              </tr>
            </thead>
            <tbody>
              {data.snapshots.slice(-120).reverse().map((s) => (
                <tr key={s.seq} className="border-b border-border last:border-b-0">
                  <td className="px-3 py-1 text-muted-fg">{s.seq}</td>
                  <td className="px-3 py-1 text-right text-success">{fmtNum(s.best_bid, 4)}</td>
                  <td className="px-3 py-1 text-right text-danger">{fmtNum(s.best_ask, 4)}</td>
                  <td className="px-3 py-1 text-right">{fmtNum(s.spread, 4)}</td>
                  <td className="px-3 py-1 text-right">{fmtNum(s.mid_price, 4)}</td>
                  <td className="px-3 py-1 text-right text-muted-fg">{s.quote_age_ns.toLocaleString()}</td>
                  <td className="px-3 py-1">
                    {s.is_crossed && <span className="text-danger mr-1">crossed</span>}
                    {s.is_stale && <span className="text-warn">stale</span>}
                  </td>
                  <td className="px-3 py-1"><ConfidenceBadge value={s.confidence} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}

function L2View({ data }: { data: NonNullable<ReturnType<typeof api.orderbookL2> extends Promise<infer R> ? R : never>["data"] }) {
  const chartData = data.snapshots.map((s) => ({
    seq: s.seq,
    imbalance: s.depth_imbalance,
    bid: s.bid_depth,
    ask: -s.ask_depth,
    gap: s.sequence_gap,
  }));
  return (
    <>
      <Panel>
        <div className="flex divide-x divide-border">
          <Stat label="Symbol" value={data.symbol} />
          <Stat label="Updates" value={data.updates.toLocaleString()} />
          <Stat
            label="Sequence gaps"
            value={data.sequence_gap_count}
            tone={data.sequence_gap_count > 0 ? "warn" : "success"}
          />
          <Stat
            label="Missing msgs"
            value={data.total_missing}
            tone={data.total_missing > 0 ? "warn" : "success"}
          />
          <Stat label="Bid / Ask levels" value={`${data.bid_levels} / ${data.ask_levels}`} />
          <div className="px-3 py-2.5 flex flex-col justify-center">
            <div className="label-xs">Book confidence</div>
            <div className="mt-1"><ConfidenceBadge value={data.final_confidence} /></div>
          </div>
        </div>
      </Panel>

      {data.sequence_gap_count > 0 && (
        <div className="border border-warn/50 bg-warn/10 rounded-sm px-3 py-2 mono text-[12px] text-warn">
          ⚠ {data.total_missing} update{data.total_missing === 1 ? "" : "s"} missing across{" "}
          {data.sequence_gap_count} gap{data.sequence_gap_count === 1 ? "" : "s"} → book DEGRADED
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Panel title="Depth imbalance (bid − ask) / (bid + ask)">
          <div className="h-[280px] p-3">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 6, right: 8, left: -8, bottom: 0 }}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
                <XAxis dataKey="seq" stroke="var(--muted-fg)" tick={{ fill: "var(--muted-fg)", fontSize: 10, fontFamily: "var(--font-mono)" }} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
                <YAxis stroke="var(--muted-fg)" tick={{ fill: "var(--muted-fg)", fontSize: 10, fontFamily: "var(--font-mono)" }} tickLine={false} axisLine={{ stroke: "var(--border)" }} domain={[-1, 1]} width={56} />
                <ReferenceLine y={0} stroke="var(--border)" />
                <Tooltip contentStyle={{ background: "var(--panel-elevated)", border: "1px solid var(--border)", borderRadius: 3, fontSize: 11, fontFamily: "var(--font-mono)" }} />
                <Line type="monotone" dataKey="imbalance" stroke="var(--accent-cyan)" strokeWidth={1.2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Bid vs ask depth">
          <div className="h-[280px] p-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData.slice(-80)} margin={{ top: 6, right: 8, left: -8, bottom: 0 }} stackOffset="sign">
                <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
                <XAxis dataKey="seq" stroke="var(--muted-fg)" tick={{ fill: "var(--muted-fg)", fontSize: 10, fontFamily: "var(--font-mono)" }} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
                <YAxis stroke="var(--muted-fg)" tick={{ fill: "var(--muted-fg)", fontSize: 10, fontFamily: "var(--font-mono)" }} tickLine={false} axisLine={{ stroke: "var(--border)" }} width={56} />
                <ReferenceLine y={0} stroke="var(--border)" />
                <Tooltip contentStyle={{ background: "var(--panel-elevated)", border: "1px solid var(--border)", borderRadius: 3, fontSize: 11, fontFamily: "var(--font-mono)" }} />
                <Bar dataKey="bid" fill="var(--success)" isAnimationActive={false} />
                <Bar dataKey="ask" fill="var(--danger)" isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <Panel title="Recent snapshots · L2">
        <div className="max-h-[360px] overflow-auto">
          <table className="w-full mono text-[11px]">
            <thead className="sticky top-0 bg-panel">
              <tr className="text-left border-b border-border label-xs">
                <th className="px-3 py-2 font-normal">seq</th>
                <th className="px-3 py-2 font-normal text-right">bid</th>
                <th className="px-3 py-2 font-normal text-right">ask</th>
                <th className="px-3 py-2 font-normal text-right">bid depth</th>
                <th className="px-3 py-2 font-normal text-right">ask depth</th>
                <th className="px-3 py-2 font-normal text-right">imbalance</th>
                <th className="px-3 py-2 font-normal">gap</th>
                <th className="px-3 py-2 font-normal">conf</th>
              </tr>
            </thead>
            <tbody>
              {data.snapshots.slice(-150).reverse().map((s) => (
                <tr key={s.seq} className="border-b border-border last:border-b-0">
                  <td className="px-3 py-1 text-muted-fg">{s.seq}</td>
                  <td className="px-3 py-1 text-right text-success">{fmtNum(s.best_bid, 4)}</td>
                  <td className="px-3 py-1 text-right text-danger">{fmtNum(s.best_ask, 4)}</td>
                  <td className="px-3 py-1 text-right">{s.bid_depth.toLocaleString()}</td>
                  <td className="px-3 py-1 text-right">{s.ask_depth.toLocaleString()}</td>
                  <td className={`px-3 py-1 text-right ${s.depth_imbalance >= 0 ? "text-success" : "text-danger"}`}>
                    {fmtNum(s.depth_imbalance, 3)}
                  </td>
                  <td className="px-3 py-1">
                    {s.sequence_gap > 0 ? (
                      <span className="text-warn">gap +{s.missing}</span>
                    ) : (
                      <span className="text-muted-fg">—</span>
                    )}
                  </td>
                  <td className="px-3 py-1"><ConfidenceBadge value={s.confidence} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}
