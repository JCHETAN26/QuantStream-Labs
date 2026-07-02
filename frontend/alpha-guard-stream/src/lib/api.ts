// Typed API client for the QuantStream backend.
// All requests go through the same-origin proxy at /api/backend/* to avoid CORS.
// On network failure the client transparently falls back to bundled fixtures.

import {
  mockDemo,
  mockOrderBookL1,
  mockOrderBookL2,
  mockSeries,
} from "./fixtures";

export type ValidationStatus = "PASS" | "WARN" | "FAIL";
export type Severity = "low" | "medium" | "high";
export type BookConfidence = "HEALTHY" | "DEGRADED" | "UNRELIABLE" | "RECOVERING";

export interface StrategyStats {
  sharpe: number;
  total_pnl: number;
  max_drawdown: number;
  hit_rate: number;
  turnover: number;
  active_intervals: number;
  total_intervals: number;
}

export interface ValidationCheck {
  name: string;
  status: ValidationStatus;
  count: number;
  severity: Severity;
}

export interface InferredSchema {
  event_type: string;
  confidence: number;
  timestamp_unit: string;
  unmatched_columns: string[];
  notes: string;
}

export interface AnalysisReport {
  symbol: string;
  total_events: number;
  flagged_events: number;
  load_errors: number;
  mirage_score: number;
  research_safe: boolean;
  conclusion: string;
  raw: StrategyStats;
  clean: StrategyStats;
  raw_checksum: string;
  clean_checksum: string;
  validation: ValidationCheck[];
  inferred_schema: InferredSchema;
}

export interface CurvePoint {
  seq: number;
  timestamp_ns: string;
  pnl: number;
  cum_pnl: number;
  tainted: boolean;
}

export interface FlaggedEvent {
  seq: number;
  defects: string[];
}

export interface SeriesReport {
  symbol: string;
  total_events: number;
  flagged_events: number;
  raw_curve: CurvePoint[];
  clean_curve: CurvePoint[];
  flagged: FlaggedEvent[];
}

export interface OrderBookL1Snapshot {
  seq: number;
  timestamp_ns: string;
  best_bid: number;
  best_ask: number;
  spread: number;
  mid_price: number;
  quote_age_ns: number;
  is_crossed: boolean;
  is_stale: boolean;
  confidence: BookConfidence;
}

export interface OrderBookL1Report {
  symbol: string;
  quotes: number;
  crossed_count: number;
  stale_count: number;
  final_confidence: BookConfidence;
  confidence_states_seen: BookConfidence[];
  snapshots: OrderBookL1Snapshot[];
}

export interface OrderBookL2Snapshot {
  seq: number;
  timestamp_ns: string;
  best_bid: number;
  best_ask: number;
  bid_depth: number;
  ask_depth: number;
  depth_imbalance: number;
  sequence_gap: number;
  missing: number;
  is_crossed: boolean;
  confidence: BookConfidence;
}

export interface OrderBookL2Report {
  symbol: string;
  updates: number;
  sequence_gap_count: number;
  total_missing: number;
  crossed_count: number;
  final_confidence: BookConfidence;
  bid_levels: number;
  ask_levels: number;
  snapshots: OrderBookL2Snapshot[];
}

export type FetchResult<T> = { data: T; source: "live" | "mock"; error?: string };

const PROXY_BASE = "/api/backend";

async function safeJson<T>(path: string, fallback: () => T): Promise<FetchResult<T>> {
  try {
    const res = await fetch(`${PROXY_BASE}${path}`, {
      headers: { accept: "application/json" },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = (await res.json()) as T;
    return { data, source: "live" };
  } catch (err) {
    return {
      data: fallback(),
      source: "mock",
      error: err instanceof Error ? err.message : String(err),
    };
  }
}

export const api = {
  demo: () => safeJson<AnalysisReport>("/demo", mockDemo),
  demoSeries: () => safeJson<SeriesReport>("/demo/series", mockSeries),
  orderbookL1: () => safeJson<OrderBookL1Report>("/orderbook/demo", mockOrderBookL1),
  orderbookL2: () => safeJson<OrderBookL2Report>("/orderbook/l2/demo", mockOrderBookL2),
  reportUrl: () => `${PROXY_BASE}/demo/report`,
  reportUrlForUpload: () => `${PROXY_BASE}/analyze/report`,

  async analyzeUpload(file: File): Promise<FetchResult<AnalysisReport>> {
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${PROXY_BASE}/analyze`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return { data: (await res.json()) as AnalysisReport, source: "live" };
    } catch (err) {
      return {
        data: mockDemo(),
        source: "mock",
        error: err instanceof Error ? err.message : String(err),
      };
    }
  },

  async analyzeUploadSeries(file: File): Promise<FetchResult<SeriesReport>> {
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${PROXY_BASE}/analyze/series`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return { data: (await res.json()) as SeriesReport, source: "live" };
    } catch (err) {
      return {
        data: mockSeries(),
        source: "mock",
        error: err instanceof Error ? err.message : String(err),
      };
    }
  },
};

export function fmtNum(n: number, digits = 2) {
  return n.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function fmtPct(n: number, digits = 1) {
  return `${(n * 100).toFixed(digits)}%`;
}

export function fmtSigned(n: number, digits = 2) {
  const s = fmtNum(Math.abs(n), digits);
  return n >= 0 ? `+${s}` : `-${s}`;
}
