"""Vercel Python serverless entrypoint for the QuantStream Labs API.

Vercel's Python runtime serves the ASGI ``app`` exported here. All backend routes
(``/api/demo``, ``/api/demo/series``, ``/health``, ...) are handled by the FastAPI
app; the root ``vercel.json`` rewrites every path to this function.

The dataset is generated + SHA-verified into ``$QUANTSTREAM_DATA_DIR`` (a writable
/tmp path on Vercel) on the first request, so no data files need to be bundled.
"""

from quantstream_api.app import app

__all__ = ["app"]
