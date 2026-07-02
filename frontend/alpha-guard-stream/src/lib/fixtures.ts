// Deterministic mock fixtures matching the FastAPI response shapes.
// Used when the backend proxy is unreachable so the terminal still renders.

import type {
  AnalysisReport,
  SeriesReport,
  OrderBookL1Report,
  OrderBookL2Report,
} from "./api";

// Deterministic PRNG (mulberry32) so fixtures are stable between renders.
function rng(seed: number) {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function buildCurves(seed: number, points = 480) {
  const rand = rng(seed);
  const raw: SeriesReport["raw_curve"] = [];
  const clean: SeriesReport["clean_curve"] = [];
  const flagged: SeriesReport["flagged"] = [];
  let rawCum = 0;
  let cleanCum = 0;
  const t0 = 1_735_000_000_000_000_000n; // ns

  for (let i = 0; i < points; i++) {
    const tainted = rand() < 0.14;
    // Raw data: drifts upward, tainted bars add "fake" profit
    const rawPnl = (rand() - 0.42) * 12 + (tainted ? 40 + rand() * 30 : 0);
    // Clean data: mean-reverting noise, no free lunch
    const cleanPnl = (rand() - 0.5) * 9;
    rawCum += rawPnl;
    cleanCum += cleanPnl;
    const ts = (t0 + BigInt(i) * 60_000_000_000n).toString();
    raw.push({ seq: i, timestamp_ns: ts, pnl: +rawPnl.toFixed(4), cum_pnl: +rawCum.toFixed(2), tainted });
    clean.push({ seq: i, timestamp_ns: ts, pnl: +cleanPnl.toFixed(4), cum_pnl: +cleanCum.toFixed(2), tainted: false });
    if (tainted) {
      const defects: string[] = [];
      const roll = rand();
      if (roll < 0.35) defects.push("stale_quote");
      else if (roll < 0.6) defects.push("crossed_book");
      else if (roll < 0.8) defects.push("timestamp_regression");
      else defects.push("sequence_gap");
      if (rand() < 0.2) defects.push("outlier_price");
      flagged.push({ seq: i, defects });
    }
  }
  return { raw, clean, flagged };
}

export function mockDemo(): AnalysisReport {
  return {
    symbol: "AAPL",
    total_events: 480,
    flagged_events: 67,
    load_errors: 0,
    mirage_score: 0.827,
    research_safe: false,
    conclusion:
      "Simulated alpha collapses from +$4,812 to -$312 after removing 67 corrupted market-data events. Signal is a data artifact, not a tradable edge.",
    raw: {
      sharpe: 2.94,
      total_pnl: 4812.37,
      max_drawdown: -218.4,
      hit_rate: 0.618,
      turnover: 1.42,
      active_intervals: 413,
      total_intervals: 480,
    },
    clean: {
      sharpe: -0.11,
      total_pnl: -312.08,
      max_drawdown: -487.2,
      hit_rate: 0.492,
      turnover: 1.31,
      active_intervals: 346,
      total_intervals: 480,
    },
    raw_checksum: "sha256:b7c9f1a2e4d63a08c9f1d2b3e4f56789abcdef0123456789abcdef0123456789",
    clean_checksum: "sha256:1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f809",
    validation: [
      { name: "monotonic_timestamps", status: "FAIL", count: 14, severity: "high" },
      { name: "no_crossed_book", status: "FAIL", count: 22, severity: "high" },
      { name: "quote_freshness_lt_500ms", status: "FAIL", count: 31, severity: "medium" },
      { name: "sequence_gap_lt_2", status: "WARN", count: 6, severity: "medium" },
      { name: "price_z_score_lt_6", status: "PASS", count: 480, severity: "low" },
      { name: "no_negative_spread", status: "PASS", count: 480, severity: "high" },
      { name: "instrument_symbol_stable", status: "PASS", count: 480, severity: "low" },
      { name: "no_lookahead_leak", status: "PASS", count: 480, severity: "high" },
    ],
    inferred_schema: {
      event_type: "quote",
      confidence: 0.94,
      timestamp_unit: "nanoseconds",
      unmatched_columns: ["venue_lat", "reserved_flag"],
      notes: "Detected bid/ask/mid columns. Timestamp parsed as ns since epoch.",
    },
  };
}

export function mockSeries(): SeriesReport {
  const { raw, clean, flagged } = buildCurves(42);
  return {
    symbol: "AAPL",
    total_events: raw.length,
    flagged_events: flagged.length,
    raw_curve: raw,
    clean_curve: clean,
    flagged,
  };
}

function buildL1(seed: number, n = 240): OrderBookL1Report["snapshots"] {
  const rand = rng(seed);
  const out: OrderBookL1Report["snapshots"] = [];
  const t0 = 1_735_000_000_000_000_000n;
  let mid = 187.42;
  for (let i = 0; i < n; i++) {
    mid += (rand() - 0.5) * 0.04;
    const spread = 0.01 + rand() * 0.03;
    const bid = +(mid - spread / 2).toFixed(4);
    const ask = +(mid + spread / 2).toFixed(4);
    const crossed = rand() < 0.03;
    const stale = rand() < 0.06;
    const conf = crossed ? "UNRELIABLE" : stale ? "DEGRADED" : rand() < 0.05 ? "RECOVERING" : "HEALTHY";
    out.push({
      seq: i,
      timestamp_ns: (t0 + BigInt(i) * 500_000_000n).toString(),
      best_bid: crossed ? ask + 0.005 : bid,
      best_ask: ask,
      spread: +spread.toFixed(4),
      mid_price: +mid.toFixed(4),
      quote_age_ns: stale ? 800_000_000 + Math.floor(rand() * 400_000_000) : Math.floor(rand() * 200_000_000),
      is_crossed: crossed,
      is_stale: stale,
      confidence: conf,
    });
  }
  return out;
}

export function mockOrderBookL1(): OrderBookL1Report {
  const snapshots = buildL1(7);
  const crossed = snapshots.filter((s) => s.is_crossed).length;
  const stale = snapshots.filter((s) => s.is_stale).length;
  return {
    symbol: "AAPL",
    quotes: snapshots.length,
    crossed_count: crossed,
    stale_count: stale,
    final_confidence: "DEGRADED",
    confidence_states_seen: ["HEALTHY", "DEGRADED", "RECOVERING", "UNRELIABLE"],
    snapshots,
  };
}

export function mockOrderBookL2(): OrderBookL2Report {
  const rand = rng(11);
  const n = 240;
  const snapshots: OrderBookL2Report["snapshots"] = [];
  const t0 = 1_735_000_000_000_000_000n;
  let mid = 187.42;
  let seqGaps = 0;
  let missing = 0;
  let crossed = 0;
  for (let i = 0; i < n; i++) {
    mid += (rand() - 0.5) * 0.04;
    const bid = +(mid - 0.01).toFixed(4);
    const ask = +(mid + 0.01).toFixed(4);
    const bidDepth = Math.floor(1200 + rand() * 4200);
    const askDepth = Math.floor(1200 + rand() * 4200);
    const gap = rand() < 0.02 ? 1 : 0;
    const miss = gap;
    const isCrossed = rand() < 0.02;
    if (gap) seqGaps++;
    missing += miss;
    if (isCrossed) crossed++;
    snapshots.push({
      seq: i,
      timestamp_ns: (t0 + BigInt(i) * 500_000_000n).toString(),
      best_bid: bid,
      best_ask: ask,
      bid_depth: bidDepth,
      ask_depth: askDepth,
      depth_imbalance: +((bidDepth - askDepth) / (bidDepth + askDepth)).toFixed(4),
      sequence_gap: gap,
      missing: miss,
      is_crossed: isCrossed,
      confidence: isCrossed ? "UNRELIABLE" : gap ? "DEGRADED" : "HEALTHY",
    });
  }
  return {
    symbol: "AAPL",
    updates: n,
    sequence_gap_count: seqGaps,
    total_missing: missing,
    crossed_count: crossed,
    final_confidence: "DEGRADED",
    bid_levels: 10,
    ask_levels: 10,
    snapshots,
  };
}
