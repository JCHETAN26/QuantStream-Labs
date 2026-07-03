import { Link, useRouterState } from "@tanstack/react-router";
import {
  Activity,
  ShieldCheck,
  LayoutGrid,
  Upload,
  Circle,
  Radio,
} from "lucide-react";
import type { ReactNode } from "react";

const NAV = [
  { to: "/", label: "Alpha Mirage", icon: Activity },
  { to: "/replay", label: "Live Replay", icon: Radio },
  { to: "/validation", label: "Validation", icon: ShieldCheck },
  { to: "/orderbook", label: "OrderBookLab", icon: LayoutGrid },
  { to: "/upload", label: "Upload", icon: Upload },
] as const;

export function Shell({ children, source }: { children: ReactNode; source?: "live" | "mock" }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      <aside className="w-56 shrink-0 border-r border-border bg-background flex flex-col">
        <div className="px-4 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-sm bg-accent-cyan" />
            <div className="mono text-[13px] font-semibold tracking-tight">
              QuantStream<span className="text-muted-fg">/</span>Labs
            </div>
          </div>
          <div className="label-xs mt-1">market-data reliability</div>
        </div>

        <nav className="flex-1 py-3">
          {NAV.map((item) => {
            const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-2 px-4 py-2 text-[13px] border-l-2 transition-colors ${
                  active
                    ? "border-accent-cyan text-foreground bg-panel"
                    : "border-transparent text-muted-fg hover:text-foreground hover:bg-panel/50"
                }`}
              >
                <Icon className="h-3.5 w-3.5" strokeWidth={1.75} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="px-4 py-3 border-t border-border">
          <div className="label-xs">status</div>
          <div className="mt-1 flex items-center gap-2 text-[11px]">
            <Circle
              className={`h-2 w-2 fill-current ${
                source === "live" ? "text-success" : source === "mock" ? "text-warn" : "text-muted-fg"
              }`}
              strokeWidth={0}
            />
            <span className="mono text-muted-fg">
              {source === "live" ? "API LIVE" : source === "mock" ? "MOCK FIXTURES" : "…"}
            </span>
          </div>
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-11 border-b border-border flex items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <div className="mono text-[11px] text-muted-fg">
              <span className="text-foreground">quantstream</span>@labs:~$
            </div>
          </div>
          <div className="flex items-center gap-4 mono text-[11px] text-muted-fg">
            <span>SESSION {new Date().toISOString().slice(0, 10)}</span>
            <span className="text-success">● connected</span>
          </div>
        </header>

        <main className="flex-1 min-w-0">{children}</main>

        <footer className="border-t border-border px-4 py-2 mono text-[11px] text-muted-fg">
          Deterministic replay · source-side checksum · no lookahead. Not a trading
          system; detects when simulated performance depends on corrupted
          market-data.
        </footer>
      </div>
    </div>
  );
}
