// Canonical event model, mirroring packages/contracts. Field order and integer
// widths here are part of the serialization contract; they must match the Python
// package exactly.
#pragma once

#include <cstdint>
#include <string>
#include <variant>

namespace quantstream {

enum class EventType : uint8_t { Trade = 1, Quote = 2, OHLCV = 3, L2Update = 4 };
enum class Side : uint8_t { Unknown = 0, Buy = 1, Sell = 2 };
enum class BookAction : uint8_t { Unknown = 0, Add = 1, Update = 2, Delete = 3 };

// Prices and sizes are fixed-point int64 (PRICE_SCALE / SIZE_SCALE == 1e9), never
// floating point, so the serialized bytes are identical across languages.

struct Trade {
    uint64_t seq;
    int64_t timestamp_ns;
    std::string symbol;
    int64_t price;
    int64_t size;
    Side side;
    std::string trade_id;
    std::string venue;
};

struct Quote {
    uint64_t seq;
    int64_t timestamp_ns;
    std::string symbol;
    int64_t bid_price;
    int64_t bid_size;
    int64_t ask_price;
    int64_t ask_size;
    std::string venue;
};

struct OHLCV {
    uint64_t seq;
    int64_t timestamp_ns;
    std::string symbol;
    int64_t open;
    int64_t high;
    int64_t low;
    int64_t close;
    int64_t volume;
    std::string venue;
};

struct L2Update {
    uint64_t seq;
    int64_t timestamp_ns;
    std::string symbol;
    Side side;
    int64_t price;
    int64_t size;
    BookAction action;
    int32_t level;
    uint64_t sequence_number;
    std::string venue;
};

using Event = std::variant<Trade, Quote, OHLCV, L2Update>;

inline uint64_t seq_of(const Event& e) {
    return std::visit([](const auto& ev) { return ev.seq; }, e);
}

inline int64_t timestamp_of(const Event& e) {
    return std::visit([](const auto& ev) { return ev.timestamp_ns; }, e);
}

}  // namespace quantstream
