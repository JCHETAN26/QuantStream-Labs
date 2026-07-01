# quantstream-api

A thin FastAPI gateway over the Alpha Mirage pipeline, so the demo is a URL a
reviewer can click, not just a terminal command.

Reuses the exact CLI pipeline (`quantstream_demo.analyze_events`); no logic is
duplicated.

## Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/` | HTML landing page |
| GET | `/health` | `{"status":"ok"}` |
| GET | `/api/demo` | bundled demo result as JSON |
| GET | `/api/demo/report` | bundled demo as the HTML research-integrity report |
| POST | `/api/analyze` | upload a CSV → analysis JSON (with inferred schema) |
| POST | `/api/analyze/report` | upload a CSV → HTML report |
| GET | `/docs` | interactive API docs |

An upload that yields no loadable events returns HTTP 422.

## Run

```bash
make install
quantstream-api           # serves on http://localhost:8000
# or: uvicorn quantstream_api.app:app --reload
```

With Docker: `docker compose up --build api`, then open http://localhost:8000.

## Test

```bash
pip install -e "apps/api[dev]"   # plus the internal packages
pytest apps/api -q
```
