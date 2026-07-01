"""QuantStream Labs API gateway (FastAPI).

A thin HTTP surface over the Alpha Mirage pipeline: run the bundled demo or upload a
CSV, and get JSON or the HTML research-integrity report.
"""

from __future__ import annotations

from .app import app

__all__ = ["app"]
