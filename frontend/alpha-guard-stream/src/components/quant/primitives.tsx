import { Check, Copy } from "lucide-react";
import { useState, type ReactNode } from "react";

export function Panel({
  title,
  right,
  children,
  className = "",
}: {
  title?: ReactNode;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      {(title || right) && (
        <header className="flex items-center justify-between px-3 py-2 border-b border-border">
          <div className="label-xs">{title}</div>
          <div className="flex items-center gap-2">{right}</div>
        </header>
      )}
      <div>{children}</div>
    </section>
  );
}

export function Stat({
  label,
  value,
  sub,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: "default" | "danger" | "success" | "warn";
}) {
  const toneClass =
    tone === "danger"
      ? "text-danger"
      : tone === "success"
      ? "text-success"
      : tone === "warn"
      ? "text-warn"
      : "text-foreground";
  return (
    <div className="px-3 py-2.5 border-r border-border last:border-r-0 min-w-[130px]">
      <div className="label-xs">{label}</div>
      <div className={`mono text-lg leading-tight mt-0.5 ${toneClass}`}>{value}</div>
      {sub && <div className="mono text-[11px] text-muted-fg mt-0.5">{sub}</div>}
    </div>
  );
}

export function StatusPill({ status }: { status: "PASS" | "WARN" | "FAIL" }) {
  const map = {
    PASS: "text-success border-success/40 bg-success/10",
    WARN: "text-warn border-warn/40 bg-warn/10",
    FAIL: "text-danger border-danger/40 bg-danger/10",
  } as const;
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 mono text-[10px] font-medium border rounded-sm ${map[status]}`}
    >
      {status}
    </span>
  );
}

export function ConfidenceBadge({ value }: { value: string }) {
  const map: Record<string, string> = {
    HEALTHY: "text-success border-success/40 bg-success/10",
    RECOVERING: "text-accent-cyan border-accent-cyan/40 bg-accent-cyan/10",
    DEGRADED: "text-warn border-warn/40 bg-warn/10",
    UNRELIABLE: "text-danger border-danger/40 bg-danger/10",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-1 mono text-[11px] font-medium border rounded-sm ${
        map[value] ?? "text-muted-fg border-border"
      }`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {value}
    </span>
  );
}

export function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="label-xs">{label}</div>
        <span className="mono text-[10px] text-success flex items-center gap-1">
          <Check className="h-3 w-3" /> verified
        </span>
      </div>
      <div className="mt-1 flex items-stretch border border-border rounded-sm bg-background overflow-hidden">
        <div className="mono text-[11px] px-2 py-1.5 flex-1 truncate text-foreground">
          {value}
        </div>
        <button
          onClick={() => {
            navigator.clipboard.writeText(value);
            setCopied(true);
            setTimeout(() => setCopied(false), 1200);
          }}
          className="px-2 border-l border-border text-muted-fg hover:text-accent-cyan hover:bg-panel-elevated transition-colors"
          aria-label="Copy"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
      </div>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse bg-panel-elevated rounded-sm ${className}`} />;
}
