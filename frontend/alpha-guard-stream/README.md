# QuantStream Labs — Frontend

A TanStack Start (React + Vite + Tailwind + shadcn/radix) web UI for the QuantStream
Labs backend. Pages:

- **`/`** — Alpha Mirage dashboard: raw vs cleaned equity curves, the mirage verdict,
  and the flagged-event timeline.
- **`/validation`** — the validation report (per-check status/count/severity).
- **`/orderbook`** — OrderBookLab L1 top-of-book confidence and L2 depth / sequence gaps.
- **`/upload`** — upload a CSV and run the full pipeline on it.

## How it talks to the backend

There is no CORS setup and no hard-coded backend URL in the browser. A server-side
proxy route (`src/routes/api/backend/$.ts`) forwards `/api/backend/*` to the FastAPI
backend, so every request is same-origin:

```
browser  ->  /api/backend/demo        (same origin)
proxy    ->  http://localhost:8000/api/demo
```

Point it at a different backend with the `API_BASE` env var (defaults to
`http://localhost:8000`). Every endpoint has a mock fallback, so the UI still renders
if the backend is down.

## Run it (with the backend)

```bash
# 1. Backend on :8000 (from the repo root)
make install && quantstream-api

# 2. Frontend
cd frontend/alpha-guard-stream
npm install
npm run dev            # http://localhost:8080 (or the next free port)
```

To target a deployed backend:

```bash
API_BASE=https://your-backend.example.com npm run dev
```

## Live replay (Server-Sent Events)

The backend streams the replay tick-by-tick at `GET /api/stream/replay` (proxied to
`/api/backend/stream/replay`). Consume it with `EventSource` for a real-time monitor:

```ts
const es = new EventSource("/api/backend/stream/replay?delay_ms=20");
es.onmessage = (ev) => {
  const tick = JSON.parse(ev.data);
  if (tick.type === "summary") { es.close(); return; }
  // tick: { seq, timestamp_ns, price, processed, flagged, defects }
  updateLiveView(tick);
};
```

The proxy streams the response body, so SSE works same-origin with no CORS.

## Verified wiring

With the backend running, the proxy reaches every endpoint the UI uses:
`/api/demo`, `/api/demo/series`, `/api/analyze`, `/api/analyze/series`,
`/api/orderbook/demo`, `/api/orderbook/l2/demo`, `/api/demo/report`.
