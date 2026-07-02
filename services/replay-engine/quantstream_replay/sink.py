"""Replay sinks: where the ordered event stream goes.

The replay checksum is computed at the source (see engine.py), independent of any
sink, so the transport can be swapped without touching determinism. This is the
D2 decision made concrete: Kafka/Redpanda is transport, not the source of truth.

`InMemorySink` is the reference sink used in tests and by the in-process pipeline.
`KafkaSink` publishes the canonical serialized bytes to a single-partition Redpanda /
Kafka topic (partition 0), so global order is preserved on the wire — the D2 decision.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from quantstream_contracts.events import Event
from quantstream_contracts.serialization import serialize_event

DEFAULT_TOPIC = "market.events.normalized"


@runtime_checkable
class Sink(Protocol):
    def emit(self, event: Event) -> None: ...


class InMemorySink:
    """Collects emitted events in order. The reference transport."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def emit(self, event: Event) -> None:
        self.events.append(event)


class KafkaSink:
    """Publishes each event's canonical serialized bytes to a Kafka/Redpanda topic.

    Keyed by symbol; always partition 0 so the single-partition canonical stream
    keeps global order on the wire (the checksum is source-side and does not depend
    on this). The producer is injected (any object with `produce(topic, key, value,
    partition)` and `flush()`), so the sink is testable without a broker and works
    with `confluent_kafka.Producer` in production (see `kafka_producer`).
    """

    def __init__(
        self, producer: Any, topic: str = DEFAULT_TOPIC, *, partition: int = 0
    ) -> None:
        self._producer = producer
        self._topic = topic
        self._partition = partition
        self.published = 0

    def emit(self, event: Event) -> None:
        self._producer.produce(
            self._topic,
            key=event.symbol.encode("utf-8"),
            value=serialize_event(event),
            partition=self._partition,
        )
        self.published += 1

    def flush(self) -> None:
        self._producer.flush()


def kafka_producer(bootstrap_servers: str = "localhost:9092", **config: Any) -> Any:
    """Create a confluent_kafka Producer. Requires the `kafka` extra."""
    try:
        from confluent_kafka import Producer
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "confluent-kafka is not installed; install with "
            "pip install 'quantstream-replay[kafka]'"
        ) from exc
    return Producer({"bootstrap.servers": bootstrap_servers, **config})
