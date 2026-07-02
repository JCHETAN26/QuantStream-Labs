// `replay` — the C++20 replay engine CLI.
//
// Reads a normalized trades CSV, applies the canonical (timestamp, seq) order, and
// computes the deterministic replay checksum. On the same input it produces the
// identical checksum as the Python replay engine, byte-for-byte.
//
//     replay <trades.csv>
#include <cstdio>
#include <exception>

#include "quantstream/csv_load.hpp"
#include "quantstream/events.hpp"
#include "quantstream/serialization.hpp"

using namespace quantstream;

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: replay <trades.csv>\n");
        return 2;
    }
    try {
        std::vector<Event> events = load_trades_csv(argv[1]);
        canonical_sort(events);
        const std::string checksum = stream_checksum(events);

        const long long first =
            events.empty() ? 0 : static_cast<long long>(timestamp_of(events.front()));
        const long long last =
            events.empty() ? 0 : static_cast<long long>(timestamp_of(events.back()));

        std::printf("events: %zu\n", events.size());
        std::printf("first_timestamp_ns: %lld\n", first);
        std::printf("last_timestamp_ns: %lld\n", last);
        std::printf("replay_checksum: %s\n", checksum.c_str());
        return 0;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "error: %s\n", e.what());
        return 1;
    }
}
