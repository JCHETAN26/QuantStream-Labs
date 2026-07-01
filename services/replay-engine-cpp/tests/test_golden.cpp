// Cross-language determinism proof: the C++ serialization reproduces the exact bytes
// and stream checksum that the Python reference recorded in expected.json.
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>

#include "check.hpp"
#include "golden_events.hpp"
#include "quantstream/serialization.hpp"

#ifndef GOLDEN_JSON
#define GOLDEN_JSON ""
#endif

using namespace quantstream;

static std::string to_hex(const std::vector<uint8_t>& bytes) {
    static const char* h = "0123456789abcdef";
    std::string out;
    out.reserve(bytes.size() * 2);
    for (uint8_t b : bytes) {
        out.push_back(h[b >> 4]);
        out.push_back(h[b & 0xf]);
    }
    return out;
}

int main() {
    const std::string path = GOLDEN_JSON;
    std::ifstream f(path);
    CHECK_MSG(f.good(), std::string("golden file readable: ") + path);
    if (!f.good()) return 1;

    std::stringstream ss;
    ss << f.rdbuf();
    const std::string golden = ss.str();

    // Every event's canonical hex (in canonical order) must appear in the Python
    // golden's per_event_hex array.
    auto events = golden_events();
    canonical_sort(events);
    for (const Event& e : events) {
        const std::string hex = to_hex(serialize_event(e));
        CHECK_MSG(golden.find(hex) != std::string::npos,
                  std::string("per-event hex present in golden: ") + hex.substr(0, 16) + "...");
    }

    // The stream checksum must match byte-for-byte.
    const std::string checksum = stream_checksum(golden_events());
    std::printf("cpp stream_checksum: %s\n", checksum.c_str());
    CHECK_MSG(golden.find(checksum) != std::string::npos,
              "stream_checksum matches Python golden");

    return qtest::failures == 0 ? 0 : 1;
}
