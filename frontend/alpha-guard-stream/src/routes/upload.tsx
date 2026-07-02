import { createFileRoute } from "@tanstack/react-router";
import { useState, useCallback, type DragEvent } from "react";
import { UploadCloud, FileText, ExternalLink } from "lucide-react";

import { api, fmtPct } from "@/lib/api";
import type { AnalysisReport, SeriesReport } from "@/lib/api";
import { Shell } from "@/components/quant/Shell";
import { Panel, CopyField, StatusPill, Stat } from "@/components/quant/primitives";

export const Route = createFileRoute("/upload")({
  component: UploadStudio,
});

function UploadStudio() {
  const [drag, setDrag] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [series, setSeries] = useState<SeriesReport | null>(null);
  const [source, setSource] = useState<"live" | "mock" | undefined>();
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (f: File) => {
    setBusy(true);
    setError(null);
    try {
      const [r, s] = await Promise.all([api.analyzeUpload(f), api.analyzeUploadSeries(f)]);
      setReport(r.data);
      setSeries(s.data);
      setSource(r.source);
      if (r.error) setError(`Backend unreachable — showing mock analysis (${r.error})`);
    } finally {
      setBusy(false);
    }
  }, []);

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files?.[0];
    if (f) {
      setFile(f);
      analyze(f);
    }
  };

  return (
    <Shell source={source}>
      <div className="px-4 py-4 space-y-4">
        <div>
          <div className="label-xs">module · upload studio</div>
          <h1 className="text-[15px] font-semibold mt-0.5">
            Analyze a CSV against the reliability engine
          </h1>
        </div>

        <Panel title="Input · CSV upload">
          <div
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={onDrop}
            className={`m-3 border border-dashed rounded-sm p-8 text-center transition-colors ${
              drag ? "border-accent-cyan bg-accent-cyan/5" : "border-border bg-background"
            }`}
          >
            <UploadCloud className="h-6 w-6 mx-auto text-muted-fg" strokeWidth={1.5} />
            <div className="mt-2 mono text-[12px]">
              Drop a CSV here, or{" "}
              <label className="text-accent-cyan cursor-pointer hover:underline">
                browse
                <input
                  type="file"
                  accept=".csv,text/csv"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) { setFile(f); analyze(f); }
                  }}
                />
              </label>
            </div>
            <div className="mono text-[10px] text-muted-fg mt-1">
              quote / trade / book snapshot CSVs · timestamps in ns or ms
            </div>
            {file && (
              <div className="mt-3 mono text-[11px] text-foreground flex items-center justify-center gap-2">
                <FileText className="h-3 w-3" /> {file.name} · {(file.size / 1024).toFixed(1)} KB
                {busy && <span className="text-accent-cyan">· analyzing…</span>}
              </div>
            )}
          </div>
        </Panel>

        {error && (
          <div className="border border-warn/50 bg-warn/10 rounded-sm px-3 py-2 mono text-[11px] text-warn">
            {error}
          </div>
        )}

        {report && (
          <div className="grid grid-cols-12 gap-4">
            <div className="col-span-8 space-y-4">
              <Panel title="Inferred schema">
                <div className="flex divide-x divide-border">
                  <Stat label="Event type" value={report.inferred_schema.event_type} />
                  <Stat
                    label="Confidence"
                    value={fmtPct(report.inferred_schema.confidence)}
                    tone={report.inferred_schema.confidence > 0.8 ? "success" : "warn"}
                  />
                  <Stat label="Timestamp unit" value={report.inferred_schema.timestamp_unit} />
                  <Stat
                    label="Load errors"
                    value={report.load_errors}
                    tone={report.load_errors > 0 ? "warn" : "success"}
                  />
                </div>
                <div className="border-t border-border p-3 space-y-2">
                  <div className="label-xs">unmatched columns</div>
                  <div className="mono text-[11px] text-muted-fg">
                    {report.inferred_schema.unmatched_columns.length > 0
                      ? report.inferred_schema.unmatched_columns.join(", ")
                      : "— none —"}
                  </div>
                  <div className="label-xs pt-1">notes</div>
                  <div className="mono text-[11px]">{report.inferred_schema.notes}</div>
                </div>
              </Panel>

              <Panel title="Validation">
                <table className="w-full mono text-[12px]">
                  <thead>
                    <tr className="text-left border-b border-border label-xs">
                      <th className="px-3 py-2 font-normal">check</th>
                      <th className="px-3 py-2 font-normal">status</th>
                      <th className="px-3 py-2 font-normal text-right">count</th>
                      <th className="px-3 py-2 font-normal">severity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.validation.map((v) => (
                      <tr key={v.name} className="border-b border-border last:border-b-0">
                        <td className="px-3 py-2">{v.name}</td>
                        <td className="px-3 py-2"><StatusPill status={v.status} /></td>
                        <td className="px-3 py-2 text-right">{v.count.toLocaleString()}</td>
                        <td className="px-3 py-2 text-muted-fg">{v.severity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Panel>
            </div>

            <div className="col-span-4 space-y-4">
              <Panel title={report.research_safe ? "verdict · safe" : "verdict · mirage"}>
                <div className={`p-4 border-l-2 ${report.research_safe ? "border-success" : "border-danger"}`}>
                  <div className={`mono text-[13px] font-semibold tracking-widest ${report.research_safe ? "text-success" : "text-danger"}`}>
                    {report.research_safe ? "SIGNAL RESEARCH-SAFE" : "ALPHA MIRAGE DETECTED"}
                  </div>
                  <div className="mt-2 mono text-3xl">
                    <span className={report.research_safe ? "text-success" : "text-danger"}>
                      {(report.mirage_score * 100).toFixed(1)}
                    </span>
                    <span className="text-muted-fg text-base">%</span>
                  </div>
                  <p className="mt-3 text-[12px] leading-relaxed">{report.conclusion}</p>
                  <a
                    href={api.reportUrlForUpload()}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 mono text-[11px] mt-3 text-accent-cyan hover:underline"
                  >
                    open full HTML report <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </Panel>

              <Panel title="Reproducibility · sha256">
                <div className="p-3 space-y-3">
                  <CopyField label="raw dataset checksum" value={report.raw_checksum} />
                  <CopyField label="cleaned dataset checksum" value={report.clean_checksum} />
                </div>
              </Panel>

              {series && (
                <Panel title="Series summary">
                  <div className="p-3 mono text-[12px] space-y-1">
                    <div className="flex justify-between"><span className="text-muted-fg">events</span><span>{series.total_events}</span></div>
                    <div className="flex justify-between"><span className="text-muted-fg">flagged</span><span className="text-danger">{series.flagged_events}</span></div>
                    <div className="flex justify-between"><span className="text-muted-fg">taint rate</span><span>{fmtPct(series.flagged_events / Math.max(1, series.total_events))}</span></div>
                  </div>
                </Panel>
              )}
            </div>
          </div>
        )}

        {!report && !busy && (
          <div className="mono text-[11px] text-muted-fg text-center py-10">
            Awaiting CSV. Uploaded files are analyzed against the same engine that
            powers /api/demo.
          </div>
        )}
      </div>
    </Shell>
  );
}
