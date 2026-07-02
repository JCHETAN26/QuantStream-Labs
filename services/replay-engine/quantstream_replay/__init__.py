"""QuantStream Labs replay engine (Python reference).

Deterministic replay of normalized events: canonical ordering, a source-side replay
checksum, and pluggable sinks. This is the reference implementation the C++ replay
engine must match byte-for-byte on the checksum.
"""

from __future__ import annotations

from .config import ReplayConfig
from .engine import ReplayResult, replay
from .sink import DEFAULT_TOPIC, InMemorySink, KafkaSink, Sink, kafka_producer

__all__ = [
    "ReplayConfig",
    "ReplayResult",
    "replay",
    "InMemorySink",
    "KafkaSink",
    "kafka_producer",
    "DEFAULT_TOPIC",
    "Sink",
]
