#include "quantstream/serialization.hpp"

#include <algorithm>
#include <stdexcept>

#include "quantstream/blake2b.hpp"

namespace quantstream {
namespace {

void append_u8(std::vector<uint8_t>& out, uint8_t v) { out.push_back(v); }

void append_u16(std::vector<uint8_t>& out, uint16_t v) {
    out.push_back(static_cast<uint8_t>(v & 0xff));
    out.push_back(static_cast<uint8_t>((v >> 8) & 0xff));
}

void append_i32(std::vector<uint8_t>& out, int32_t v) {
    uint32_t u = static_cast<uint32_t>(v);
    for (int i = 0; i < 4; ++i) out.push_back(static_cast<uint8_t>((u >> (8 * i)) & 0xff));
}

void append_u64(std::vector<uint8_t>& out, uint64_t v) {
    for (int i = 0; i < 8; ++i) out.push_back(static_cast<uint8_t>((v >> (8 * i)) & 0xff));
}

void append_i64(std::vector<uint8_t>& out, int64_t v) {
    append_u64(out, static_cast<uint64_t>(v));
}

void append_str(std::vector<uint8_t>& out, const std::string& s) {
    if (s.size() > 0xffff) throw std::runtime_error("string too long to serialize");
    append_u16(out, static_cast<uint16_t>(s.size()));
    out.insert(out.end(), s.begin(), s.end());
}

template <typename T>
void append_header(std::vector<uint8_t>& out, EventType type, const T& ev) {
    append_u8(out, static_cast<uint8_t>(type));
    append_u64(out, ev.seq);
    append_i64(out, ev.timestamp_ns);
    append_str(out, ev.symbol);
}

struct Serializer {
    std::vector<uint8_t>& out;

    void operator()(const Trade& ev) const {
        append_header(out, EventType::Trade, ev);
        append_i64(out, ev.price);
        append_i64(out, ev.size);
        append_u8(out, static_cast<uint8_t>(ev.side));
        append_str(out, ev.trade_id);
        append_str(out, ev.venue);
    }
    void operator()(const Quote& ev) const {
        append_header(out, EventType::Quote, ev);
        append_i64(out, ev.bid_price);
        append_i64(out, ev.bid_size);
        append_i64(out, ev.ask_price);
        append_i64(out, ev.ask_size);
        append_str(out, ev.venue);
    }
    void operator()(const OHLCV& ev) const {
        append_header(out, EventType::OHLCV, ev);
        append_i64(out, ev.open);
        append_i64(out, ev.high);
        append_i64(out, ev.low);
        append_i64(out, ev.close);
        append_i64(out, ev.volume);
        append_str(out, ev.venue);
    }
    void operator()(const L2Update& ev) const {
        append_header(out, EventType::L2Update, ev);
        append_u8(out, static_cast<uint8_t>(ev.side));
        append_i64(out, ev.price);
        append_i64(out, ev.size);
        append_u8(out, static_cast<uint8_t>(ev.action));
        append_i32(out, ev.level);
        append_u64(out, ev.sequence_number);
        append_str(out, ev.venue);
    }
};

}  // namespace

void serialize_event(const Event& event, std::vector<uint8_t>& out) {
    std::visit(Serializer{out}, event);
}

std::vector<uint8_t> serialize_event(const Event& event) {
    std::vector<uint8_t> out;
    serialize_event(event, out);
    return out;
}

void canonical_sort(std::vector<Event>& events) {
    std::stable_sort(events.begin(), events.end(), [](const Event& a, const Event& b) {
        if (timestamp_of(a) != timestamp_of(b)) return timestamp_of(a) < timestamp_of(b);
        return seq_of(a) < seq_of(b);
    });
}

std::string stream_checksum(std::vector<Event> events) {
    canonical_sort(events);
    std::vector<uint8_t> buffer;
    for (const Event& e : events) serialize_event(e, buffer);
    return blake2b_256_hex(buffer);
}

}  // namespace quantstream
