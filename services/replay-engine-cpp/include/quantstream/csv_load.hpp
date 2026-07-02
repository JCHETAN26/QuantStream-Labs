// Load a canonical trades CSV into events, with exact decimal->fixed-point parsing
// that matches Python's price_to_fixed / size_to_fixed byte-for-byte.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "quantstream/events.hpp"

namespace quantstream {

// Parse a decimal string ("100.07", "-3.5", "100") to a scaled int64 (scale 1e9).
// Exact: throws if the value has more than 9 fractional digits.
int64_t parse_fixed(const std::string& text);

// Load a trades CSV with header: timestamp,symbol,price,size,side,trade_id,venue.
// seq is the 0-based row index.
std::vector<Event> load_trades_csv(const std::string& path);

}  // namespace quantstream
