# Deploying QuantStream Labs

Two moving parts: the **frontend** (TanStack Start → Vercel) and the **backend**
(FastAPI). The frontend proxies `/api/backend/*` to the backend via `API_BASE`, so the
browser stays same-origin — no CORS.

```
recruiter → Vercel (UI) → /api/backend/* proxy → backend (API_BASE)
```

## Backend — Option A: Vercel (all-Vercel)

The repo root is set up to deploy the FastAPI app as a Vercel Python function
(`api/index.py`, `requirements.txt`, root `vercel.json`). The dataset is generated +
SHA-verified into `/tmp` on first request, so nothing needs bundling.

1. vercel.com → Add New → Project → import the repo, **Root Directory = repo root**.
2. Deploy. The API is at `https://<backend-project>.vercel.app` (check `/health`,
   `/api/demo`, `/docs`).

Note: Vercel Python functions are serverless — cold starts, and the SSE endpoint
(`/api/stream/replay`) is bounded by `maxDuration` (30s). Fine for a demo.

## Backend — Option B: Fly.io (Docker, more robust)

Uses the repo `Dockerfile` (which pre-generates + verifies the dataset). No cold
starts on the SSE feed.

```bash
fly auth login
fly deploy                      # reads fly.toml (app: quantstream-labs-api)
# URL: https://quantstream-labs-api.fly.dev
```

`run()` reads `$PORT` (Fly/Render/Railway inject it), defaulting to 8000.

## Frontend — Vercel

1. vercel.com → Add New → Project → import the repo, **Root Directory =
   `frontend/alpha-guard-stream`**.
2. Env var **`API_BASE`** = your backend URL (from Option A or B).
3. Deploy.

`frontend/vercel.json` forces `NITRO_PRESET=vercel` so Nitro emits `.vercel/output`
(without it you get a 404 — the default preset is Cloudflare).

## Verify

Open the frontend URL, click `/`, `/validation`, `/orderbook`, `/upload`. Each page's
data comes from the backend through the proxy. The UI has mock fallbacks, so it still
renders during a backend cold start.
