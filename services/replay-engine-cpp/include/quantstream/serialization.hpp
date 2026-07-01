// Canonical byte-stable serialization and the deterministic replay checksum, the
// C++ side of the contract defined in packages/contracts/serialization.py. Byte
// layout, ordering, and hash must match the Python reference exactly.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "quantstream/events.hpp"

namespace quantstream {

// Append one event's canonical bytes to `out`.
void serialize_event(const Event& event, std::vector<uint8_t>& out);

// One event's canonical bytes.
std::vector<uint8_t> serialize_event(const Event& event);

// Sort into the system canonical order: (timestamp_ns, seq).
void canonical_sort(std::vector<Event>& events);

// BLAKE2b-256 hex digest over the canonically-ordered serialized stream.
std::string stream_checksum(std::vector<Event> events);

}  // namespace quantstream
