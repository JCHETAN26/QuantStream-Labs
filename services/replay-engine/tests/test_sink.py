"""Sink protocol and the in-memory reference sink."""

from __future__ import annotations

from quantstream_contracts.serialization import serialize_event

from quantstream_replay import InMemorySink, KafkaSink, replay
from quantstream_replay.sink import Sink

from ._helpers import mixed_stream, trade


class FakeProducer:
    """Records produce()/flush() calls; stands in for confluent_kafka.Producer."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.flushed = False

    def produce(self, topic, key, value, partition):
        self.calls.append((topic, key, value, partition))

    def flush(self):
        self.flushed = True


def test_in_memory_sink_collects_in_emit_order():
    sink = InMemorySink()
    events = [trade(0, 1), trade(1, 2), trade(2, 3)]
    for event in events:
        sink.emit(event)
    assert sink.events == events


def test_in_memory_sink_satisfies_protocol():
    assert isinstance(InMemorySink(), Sink)


def test_kafka_sink_publishes_canonical_bytes():
    producer = FakeProducer()
    sink = KafkaSink(producer, topic="t")
    ev = trade(0, 1)
    sink.emit(ev)
    topic, key, value, partition = producer.calls[0]
    assert topic == "t"
    assert key == ev.symbol.encode("utf-8")
    assert value == serialize_event(ev)  # exact canonical bytes
    assert partition == 0  # single-partition canonical stream
    assert sink.published == 1


def test_kafka_sink_satisfies_protocol_and_flushes():
    producer = FakeProducer()
    sink = KafkaSink(producer)
    assert isinstance(sink, Sink)
    sink.flush()
    assert producer.flushed is True


def test_replay_into_kafka_sink_publishes_in_canonical_order():
    events = mixed_stream()
    producer = FakeProducer()
    replay(events, sink=KafkaSink(producer))
    reference = InMemorySink()
    replay(events, sink=reference)
    assert len(producer.calls) == len(events)
    published_bytes = [value for (_t, _k, value, _p) in producer.calls]
    assert published_bytes == [serialize_event(e) for e in reference.events]
