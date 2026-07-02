import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { Severity, ValidationStatus } from "@/lib/api";
import { Shell } from "@/components/quant/Shell";
import { Panel, Skeleton, Stat, StatusPill } from "@/components/quant/primitives";

export const Route = createFileRoute("/validation")({
  component: ValidationPage,
});

const STATUSES: ValidationStatus[] = ["FAIL", "WARN", "PASS"];

function ValidationPage() {
  const q = useQuery({ queryKey: ["demo"], queryFn: api.demo });
  const [filter, setFilter] = useState<Severity | "all">("all");
  const [statusFilter, setStatusFilter] = useState<ValidationStatus | "all">("all");

  const data = q.data?.data;
  const summary = useMemo(() => {
    if (!data) return null;
    const failures = data.validation.filter((v) => v.status === "FAIL");
    const highSev = failures.filter((v) => v.severity === "high").length;
    const warns = data.validation.filter((v) => v.status === "WARN").length;
    return { failures: failures.length, highSev, warns, total: data.validation.length };
  }, [data]);

  const rows = useMemo(() => {
    if (!data) return [];
    return data.validation
      .filter((v) => filter === "all" || v.severity === filter)
      .filter((v) => statusFilter === "all" || v.status === statusFilter)
      .sort((a, b) => STATUSES.indexOf(a.status) - STATUSES.indexOf(b.status));
  }, [data, filter, statusFilter]);

  return (
    <Shell source={q.data?.source}>
      <div className="px-4 py-4 space-y-4">
        <div>
          <div className="label-xs">module · validation report</div>
          <h1 className="text-[15px] font-semibold mt-0.5">Data-Integrity Checks</h1>
        </div>

        {summary ? (
          <Panel>
            <div className="flex divide-x divide-border">
              <Stat label="Total checks" value={summary.total.toString().padStart(2, "0")} />
              <Stat
                label="Failures"
                value={summary.failures.toString().padStart(2, "0")}
                tone={summary.failures > 0 ? "danger" : "success"}
              />
              <Stat
                label="High severity"
                value={summary.highSev.toString().padStart(2, "0")}
                tone={summary.highSev > 0 ? "danger" : "success"}
              />
              <Stat
                label="Warnings"
                value={summary.warns.toString().padStart(2, "0")}
                tone={summary.warns > 0 ? "warn" : "success"}
              />
            </div>
          </Panel>
        ) : (
          <Skeleton className="h-16" />
        )}

        <Panel
          title="Checks"
          right={
            <div className="flex items-center gap-3">
              <FilterGroup
                label="severity"
                value={filter}
                options={["all", "high", "medium", "low"] as const}
                onChange={(v) => setFilter(v as Severity | "all")}
              />
              <FilterGroup
                label="status"
                value={statusFilter}
                options={["all", "FAIL", "WARN", "PASS"] as const}
                onChange={(v) => setStatusFilter(v as ValidationStatus | "all")}
              />
            </div>
          }
        >
          {data ? (
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
                {rows.map((v) => (
                  <tr key={v.name} className="border-b border-border last:border-b-0 hover:bg-panel-elevated/60">
                    <td className="px-3 py-2 text-foreground">{v.name}</td>
                    <td className="px-3 py-2"><StatusPill status={v.status} /></td>
                    <td className="px-3 py-2 text-right tabular-nums">{v.count.toLocaleString()}</td>
                    <td className="px-3 py-2 text-muted-fg">{v.severity}</td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-3 py-6 text-center text-muted-fg">
                      no checks match filter
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          ) : (
            <Skeleton className="h-60 m-3" />
          )}
        </Panel>
      </div>
    </Shell>
  );
}

function FilterGroup<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: readonly T[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <span className="label-xs mr-1">{label}</span>
      {options.map((o) => (
        <button
          key={o}
          onClick={() => onChange(o)}
          className={`mono text-[10px] px-1.5 py-0.5 rounded-sm border transition-colors ${
            value === o
              ? "border-accent-cyan text-accent-cyan bg-accent-cyan/10"
              : "border-border text-muted-fg hover:text-foreground"
          }`}
        >
          {o}
        </button>
      ))}
    </div>
  );
}
