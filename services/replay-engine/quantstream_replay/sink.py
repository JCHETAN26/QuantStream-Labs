"""Replay sinks: where the ordered event stream goes.

The replay checksum is computed at the source (see engine.py), independent of any
sink, so the transport can be swapped without touching determinism. This is the
D2 decision made concrete: Kafka/Redpanda is transport, not the source of truth.

`InMemorySink` is the reference sink used in tests and by the in-process pipeline.
A `KafkaSink` publishing to the single-partition canonical topic lands in a later
PR and implements the same `Sink` protocol.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from quantstream_contracts.events import Event


@runtime_checkable
class Sink(Protocol):
    def emit(self, event: Event) -> None: ...


class InMemorySink:
    """Collects emitted events in order. The reference transport."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def emit(self, event: Event) -> None:
        self.events.append(event)
