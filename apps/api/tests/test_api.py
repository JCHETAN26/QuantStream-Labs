"""API gateway endpoint tests (FastAPI TestClient, no network)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from quantstream_demo import run_demo
from quantstream_demo.sample_data import sample_csv_path

from quantstream_api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_index_is_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "QuantStream Labs" in r.text


def test_demo_json_matches_pipeline():
    r = client.get("/api/demo")
    assert r.status_code == 200
    body = r.json()
    expected = run_demo()
    assert body["symbol"] == expected.symbol
    assert body["research_safe"] is False
    assert body["mirage_score"] == float(expected.mirage.mirage_score)
    assert body["raw_checksum"] == expected.raw_checksum
    assert len(body["validation"]) > 0


def test_demo_report_is_html():
    r = client.get("/api/demo/report")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Research Integrity Report" in r.text


def test_demo_series_reconciles_with_headline():
    r = client.get("/api/demo/series")
    assert r.status_code == 200
    body = r.json()
    expected = run_demo()
    assert body["symbol"] == expected.symbol
    assert body["total_events"] == expected.total_events
    assert body["flagged_events"] == expected.flagged_events
    assert body["raw_curve"] and body["clean_curve"]
    # The curve endpoints reconcile exactly with the reported PnL.
    assert body["raw_curve"][-1]["cum_pnl"] == float(expected.mirage.raw.total_pnl)
    assert body["clean_curve"][-1]["cum_pnl"] == float(expected.mirage.clean.total_pnl)
    # Flagged timeline matches the validation count and carries defect labels.
    assert len(body["flagged"]) == expected.flagged_events
    assert all(pt["defects"] for pt in body["flagged"])


def test_analyze_series_uploaded_csv_matches_bundled():
    with open(sample_csv_path(), "rb") as f:
        data = f.read()
    r = client.post("/api/analyze/series", files={"file": ("acme.csv", data, "text/csv")})
    assert r.status_code == 200
    body = r.json()
    expected = run_demo()
    assert body["raw_curve"][-1]["cum_pnl"] == float(expected.mirage.raw.total_pnl)
    assert body["flagged_events"] == expected.flagged_events


def test_analyze_uploaded_csv_matches_bundled():
    with open(sample_csv_path(), "rb") as f:
        data = f.read()
    r = client.post("/api/analyze", files={"file": ("acme.csv", data, "text/csv")})
    assert r.status_code == 200
    body = r.json()
    # The sample CSV is the bundled data, so results match the bundled run.
    assert body["raw_checksum"] == run_demo().raw_checksum
    assert body["mirage_score"] == float(run_demo().mirage.mirage_score)
    assert body["inferred_schema"]["event_type"] == "TRADE"
    assert body["inferred_schema"]["confidence"] == 1.0


def test_analyze_report_uploaded_csv_is_html():
    with open(sample_csv_path(), "rb") as f:
        data = f.read()
    r = client.post("/api/analyze/report", files={"file": ("acme.csv", data, "text/csv")})
    assert r.status_code == 200
    assert "Research Integrity Report" in r.text


def test_analyze_empty_csv_returns_422():
    r = client.post("/api/analyze", files={"file": ("empty.csv", b"a,b\n", "text/csv")})
    assert r.status_code == 422


def test_orderbook_demo():
    r = client.get("/api/orderbook/demo")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "BOOK"
    assert body["crossed_count"] == 1
    assert body["stale_count"] == 1
    assert body["final_confidence"] == "healthy"
    assert set(body["confidence_states_seen"]) == {
        "healthy", "degraded", "unreliable", "recovering"
    }
    assert len(body["snapshots"]) == 12


def test_orderbook_l2_demo():
    r = client.get("/api/orderbook/l2/demo")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "L2BOOK"
    assert body["sequence_gap_count"] == 1
    assert body["total_missing"] == 1
    assert body["crossed_count"] == 1
    assert body["final_confidence"] == "healthy"
    assert set(body["confidence_states_seen"]) == {
        "healthy", "degraded", "unreliable", "recovering"
    }
