// Same-origin proxy to the FastAPI backend so the browser avoids CORS.
// Configure the backend origin with VITE_API_BASE (server-side env: API_BASE).
import { createFileRoute } from "@tanstack/react-router";

function backendBase() {
  return (
    process.env.API_BASE ||
    process.env.VITE_API_BASE ||
    "http://localhost:8000"
  );
}

async function forward(request: Request, splat: string) {
  const base = backendBase().replace(/\/$/, "");
  const url = new URL(request.url);
  const target = `${base}/api/${splat}${url.search}`;

  const headers = new Headers(request.headers);
  headers.delete("host");

  const init: RequestInit = {
    method: request.method,
    headers,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
    // @ts-expect-error — undici accepts duplex for streaming bodies
    duplex: "half",
  };

  try {
    const upstream = await fetch(target, init);
    const respHeaders = new Headers(upstream.headers);
    respHeaders.delete("content-encoding");
    respHeaders.delete("content-length");
    return new Response(upstream.body, {
      status: upstream.status,
      headers: respHeaders,
    });
  } catch (err) {
    return new Response(
      JSON.stringify({
        error: "backend_unreachable",
        target,
        message: err instanceof Error ? err.message : String(err),
      }),
      { status: 502, headers: { "content-type": "application/json" } },
    );
  }
}

export const Route = createFileRoute("/api/backend/$")({
  server: {
    handlers: {
      GET: ({ request, params }) => forward(request, params._splat ?? ""),
      POST: ({ request, params }) => forward(request, params._splat ?? ""),
      PUT: ({ request, params }) => forward(request, params._splat ?? ""),
      DELETE: ({ request, params }) => forward(request, params._splat ?? ""),
    },
  },
});
