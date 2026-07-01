// BLAKE2b vectors, header byte layout, and checksum determinism / order-independence.
#include <algorithm>
#include <string>
#include <vector>

#include "check.hpp"
#include "quantstream/blake2b.hpp"
#include "quantstream/serialization.hpp"

using namespace quantstream;

static std::vector<uint8_t> bytes(const std::string& s) {
    return {s.begin(), s.end()};
}

static Trade mk(uint64_t seq, int64_t ts) {
    return Trade{seq, ts, "AAPL", 100000000000LL + static_cast<int64_t>(seq),
                 1000000000LL, Side::Buy, "t" + std::to_string(seq), "XNAS"};
}

int main() {
    // Known BLAKE2b-256 vectors (match hashlib.blake2b(digest_size=32)).
    CHECK(blake2b_256_hex(bytes("")) ==
          "0e5751c026e543b2e8ab2eb06099daa1d1e5df47778f7787faab45cdf12fe3a8");
    CHECK(blake2b_256_hex(bytes("abc")) ==
          "bddd813c634239723171ef3fee98579b94964e3bb1cb3e427262c8c068d52319");

    // Header layout: event_type(u8) seq(u64 LE) timestamp(i64 LE) symbol(u16 len + bytes).
    Trade t{7, 258, "AA", 5, 9, Side::Sell, "x", "V"};
    auto raw = serialize_event(Event{t});
    CHECK(raw[0] == 1);                       // EventType::Trade
    CHECK(raw[1] == 7 && raw[2] == 0);        // seq low bytes (LE)
    CHECK(raw[9] == 2 && raw[10] == 1);       // timestamp 258 == 0x0102 LE
    CHECK(raw[17] == 2 && raw[18] == 0);      // symbol length 2 (u16 LE)
    CHECK(raw[19] == 'A' && raw[20] == 'A');  // symbol bytes

    // Determinism and order-independence of the stream checksum.
    std::vector<Event> events;
    for (uint64_t i = 0; i < 40; ++i) events.push_back(Event{mk(i, 1000 + (i % 3))});
    const std::string a = stream_checksum(events);
    CHECK(a == stream_checksum(events));

    std::vector<Event> reversed(events.rbegin(), events.rend());
    CHECK(stream_checksum(reversed) == a);

    // A one-unit price change flips the checksum.
    auto mutated = events;
    Trade bumped = std::get<Trade>(mutated[3]);
    bumped.price += 1;
    mutated[3] = Event{bumped};
    CHECK(stream_checksum(mutated) != a);

    return qtest::failures == 0 ? 0 : 1;
}
