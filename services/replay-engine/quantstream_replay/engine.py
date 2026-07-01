"""Deterministic replay.

Applies the config's filters, orders events canonically, computes the replay
checksum at the source (over the ordered stream, before any transport), and emits
to a sink in that same order.

The checksum comes from ``quantstream_contracts.stream_checksum`` over the exact
ordered stream, so a full-dataset replay (no filter) yields the identical checksum
you'd get from the contracts package directly. That single fact is the anchor the
C++ replay engine will be verified against: match this checksum, byte for byte.
"""

from __future__ import annotations

from dataclasses import dataclass

from quantstream_contracts.events import Event
from quantstream_contracts.serialization import canonical_sort, stream_checksum

from .config import ReplayConfig
from .sink import Sink


@dataclass(frozen=True)
class ReplayResult:
    checksum: str
    config_hash: str
    event_count: int
    dropped_by_filter: int
    first_timestamp_ns: int | None
    last_timestamp_ns: int | None


def replay(
    events: list[Event],
    config: ReplayConfig | None = None,
    sink: Sink | None = None,
) -> ReplayResult:
    """Replay events deterministically and return the run's checksum + metadata.

    The checksum depends only on the (filtered) event set and is independent of the
    input list's order and of the sink.
    """
    config = config or ReplayConfig()

    filtered = [event for event in events if config.accepts(event)]
    dropped = len(events) - len(filtered)
    ordered = canonical_sort(filtered)

    checksum = stream_checksum(ordered, assume_sorted=True)

    if sink is not None:
        for event in ordered:
            sink.emit(event)

    return ReplayResult(
        checksum=checksum,
        config_hash=config.config_hash(),
        event_count=len(ordered),
        dropped_by_filter=dropped,
        first_timestamp_ns=ordered[0].timestamp_ns if ordered else None,
        last_timestamp_ns=ordered[-1].timestamp_ns if ordered else None,
    )
