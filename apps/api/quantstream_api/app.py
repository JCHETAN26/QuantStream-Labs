"""FastAPI gateway.

Exposes the Alpha Mirage pipeline over HTTP: run the bundled demo, upload a CSV for
analysis, and get either JSON or the HTML research-integrity report. Interactive API
docs are at /docs.
"""

from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from quantstream_demo import build_html

from . import service
from .models import AnalysisResponse, to_response

app = FastAPI(
    title="QuantStream Labs",
    version="0.1.0",
    description="Market-data reliability and Alpha Mirage analysis.",
)

_INDEX = """<!doctype html><html><head><meta charset="utf-8">
<title>QuantStream Labs</title>
<style>body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px;
margin:60px auto;padding:0 20px;color:#1c2128;line-height:1.6}a{color:#0969da}
code{background:#f6f8fa;padding:2px 6px;border-radius:4px}</style></head><body>
<h1>QuantStream Labs</h1>
<p>Deterministic market-data replay and Alpha Mirage analysis.</p>
<ul>
<li><a href="/api/demo/report">Run the Alpha Mirage demo (HTML report)</a></li>
<li><a href="/api/demo">Demo result as JSON</a></li>
<li><a href="/docs">API docs</a> &mdash; upload a CSV to <code>POST /api/analyze</code></li>
</ul></body></html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/demo", response_model=AnalysisResponse)
def demo() -> AnalysisResponse:
    return to_response(service.bundled())


@app.get("/api/demo/report", response_class=HTMLResponse)
def demo_report() -> str:
    return build_html(service.bundled())


async def _read_csv(file: UploadFile) -> str:
    raw = await file.read()
    return raw.decode("utf-8", errors="replace")


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(file: UploadFile = File(...)) -> AnalysisResponse:
    text = await _read_csv(file)
    try:
        schema, result = service.analyze_csv(text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return to_response(result, schema)


@app.post("/api/analyze/report", response_class=HTMLResponse)
async def analyze_report(file: UploadFile = File(...)) -> str:
    text = await _read_csv(file)
    try:
        _schema, result = service.analyze_csv(text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return build_html(result)


def run() -> None:  # pragma: no cover - convenience entry point
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
