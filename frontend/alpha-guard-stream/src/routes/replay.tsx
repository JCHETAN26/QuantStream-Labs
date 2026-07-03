import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Play, Square, AlertOctagon } from "lucide-react";

import { api, fmtNum } from "@/lib/api";
import type { DataSource } from "@/lib/api";
import { Shell } from "@/components/quant/Shell";

export const Route = createFileRoute("/replay")({
  component: ReplayPage,
});

interface Tick {
  seq: number;
  price: number;
  processed: number;
  flagged: boolean;
  defects: string[];
}

const EXPECTED: Record<DataSource, number> = { synthetic: 400, real: 500 };

function ReplayPage() {
  const [ds, setDs] = useState<DataSource>("synthetic");
  const [running, setRunning] = useState(false);
  const [ticks, setTicks] = useState<Tick[]>([]);
  const [processed, setProcessed] = useState(0);
  const [flaggedCount, setFlaggedCount] = useState(0);
  const [total, setTotal] = useState<number | null>(null);
  const [price, setPrice] = useState<number | null>(null);
  const esRef = useRef<EventSource | null>(null);

  function stop() {
    esRef.current?.close();
    esRef.current = null;
    setRunning(false);
  }

  function start() {
    stop();
    setTicks([]);
    setProcessed(0);
    setFlaggedCount(0);
    setTotal(null);
    setPrice(null);
    setRunning(true);
    const es = new EventSource(api.replayStreamUrl(ds, 10));
    esRef.current = es;
    es.onmessage = (ev) => {
      const msg = JSON.parse(ev.data) as Tick & { type?: string; events?: number };
      if (msg.type === "summary") {
        setTotal(msg.events ?? null);
        stop();
        return;
      }
      setProcessed(msg.processed);
      setPrice(msg.price);
      if (msg.flagged) setFlaggedCount((c) => c + 1);
      setTicks((prev) => [msg, ...prev].slice(0, 40));
    };
    es.onerror = () => stop();
  }

  useEffect(() => () => stop(), []);

  const expected = EXPECTED[ds];
  const pct = Math.min(100, (processed / expected) * 100);

  return (
    <Shell>
      <div className="px-4 py-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="label-xs">module · live replay</div>
            <h1 className="text-[15px] font-semibold mt-0.5">
              Deterministic Replay Feed
              <span className="mono text-muted-fg font-normal ml-2">
                / SSE · tick-by-tick validation
              </span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <div className="inline-flex items-center border border-border rounded-sm overflow-hidden mono text-[11px]">
              {(["synthetic", "real"] as DataSource[]).map((opt) => (
                <button
                  key={opt}
                  type="button"
                  disabled={running}
                  onClick={() => setDs(opt)}
                  className={
                    "px-2.5 py-1.5 transition-colors disabled:opacity-40 " +
                    (ds === opt
                      ? "bg-accent-cyan/15 text-accent-cyan"
                      : "text-muted-fg hover:text-fg")
                  }
                >
                  {opt === "synthetic" ? "Synthetic ACME" : "Real BTC-USD"}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={running ? stop : start}
              className="inline-flex items-center gap-1.5 mono text-[11px] px-3 py-1.5 border border-border rounded-sm hover:border-accent-cyan hover:text-accent-cyan transition-colors"
            >
              {running ? (
                <>
                  <Square className="h-3 w-3" /> Stop
                </>
              ) : (
                <>
                  <Play className="h-3 w-3" /> Replay
                </>
              )}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="border border-border rounded-sm p-3">
            <div className="label-xs">processed</div>
            <div className="mono text-[18px] mt-1">
              {processed}
              <span className="text-muted-fg text-[12px]"> / {total ?? expected}</span>
            </div>
          </div>
          <div className="border border-border rounded-sm p-3">
            <div className="label-xs">last price</div>
            <div className="mono text-[18px] mt-1">
              {price === null ? "—" : fmtNum(price, 2)}
            </div>
          </div>
          <div className="border border-border rounded-sm p-3">
            <div className="label-xs">flagged (bad ticks)</div>
            <div className="mono text-[18px] mt-1 text-warn">{flaggedCount}</div>
          </div>
        </div>

        <div className="h-1.5 w-full bg-border rounded-full overflow-hidden">
          <div
            className="h-full bg-accent-cyan transition-[width] duration-100"
            style={{ width: `${pct}%` }}
          />
        </div>

        <div className="border border-border rounded-sm">
          <div className="label-xs px-3 py-2 border-b border-border">
            event stream {running ? "· streaming…" : total ? "· complete" : ""}
          </div>
          <div className="max-h-[380px] overflow-y-auto divide-y divide-border">
            {ticks.length === 0 ? (
              <div className="px-3 py-6 mono text-[12px] text-muted-fg">
                Press Replay to stream the tape through validation tick-by-tick.
              </div>
            ) : (
              ticks.map((t) => (
                <div
                  key={t.seq}
                  className={
                    "flex items-center gap-3 px-3 py-1.5 mono text-[12px] " +
                    (t.flagged ? "text-warn" : "text-fg")
                  }
                >
                  <span className="text-muted-fg w-14">#{t.seq}</span>
                  <span className="w-28">{fmtNum(t.price, 2)}</span>
                  {t.flagged ? (
                    <span className="inline-flex items-center gap-1">
                      <AlertOctagon className="h-3 w-3" />
                      {t.defects.join(", ") || "flagged"}
                    </span>
                  ) : (
                    <span className="text-muted-fg">ok</span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Shell>
  );
}
