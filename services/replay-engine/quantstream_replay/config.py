"""Replay configuration and its reproducibility hash.

A run is defined by its input events plus this config. Two runs with the same
events and the same config must produce the same replay checksum; the config also
has its own stable ``config_hash`` so a run's provenance is fully captured by
(input checksum, config hash).

Speed is an integer multiplier (1x, 10x, 100x, ...) with 0 meaning "as fast as
possible". It is intentionally not a float: it feeds ``config_hash`` and the whole
engine is built to keep floats out of anything determinism-critical.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from quantstream_contracts.events import Event


@dataclass(frozen=True)
class ReplayConfig:
    speed: int = 1  # multiplier; 0 == unbounded ("max")
    symbols: frozenset[str] | None = None  # None == all symbols
    start_ns: int | None = None  # inclusive lower bound
    end_ns: int | None = None  # inclusive upper bound

    def __post_init__(self) -> None:
        if self.speed < 0:
            raise ValueError(f"speed must be >= 0 (0 == max), got {self.speed}")
        if (
            self.start_ns is not None
            and self.end_ns is not None
            and self.start_ns > self.end_ns
        ):
            raise ValueError(
                f"start_ns {self.start_ns} is after end_ns {self.end_ns}"
            )

    def accepts(self, event: Event) -> bool:
        if self.symbols is not None and event.symbol not in self.symbols:
            return False
        if self.start_ns is not None and event.timestamp_ns < self.start_ns:
            return False
        if self.end_ns is not None and event.timestamp_ns > self.end_ns:
            return False
        return True

    def config_hash(self) -> str:
        symbols = "*" if self.symbols is None else ",".join(sorted(self.symbols))
        parts = [
            f"speed={self.speed}",
            f"symbols={symbols}",
            f"start={'-' if self.start_ns is None else self.start_ns}",
            f"end={'-' if self.end_ns is None else self.end_ns}",
        ]
        digest = hashlib.blake2b(digest_size=16)
        digest.update(b"\x00".join(p.encode("utf-8") for p in parts))
        return digest.hexdigest()
