#include "quantstream/csv_load.hpp"

#include <fstream>
#include <sstream>
#include <stdexcept>

namespace quantstream {
namespace {

constexpr int SCALE_DIGITS = 9;  // PRICE_SCALE / SIZE_SCALE == 1e9

std::vector<std::string> split(const std::string& line, char delim) {
    std::vector<std::string> out;
    std::string field;
    std::istringstream ss(line);
    while (std::getline(ss, field, delim)) out.push_back(field);
    // getline drops a trailing empty field; the canonical CSV has no trailing comma.
    return out;
}

Side parse_side(const std::string& s) {
    if (s == "buy") return Side::Buy;
    if (s == "sell") return Side::Sell;
    return Side::Unknown;
}

}  // namespace

int64_t parse_fixed(const std::string& text) {
    std::string s = text;
    bool neg = false;
    if (!s.empty() && (s[0] == '-' || s[0] == '+')) {
        neg = (s[0] == '-');
        s = s.substr(1);
    }

    std::string int_part, frac_part;
    const auto dot = s.find('.');
    if (dot == std::string::npos) {
        int_part = s;
    } else {
        int_part = s.substr(0, dot);
        frac_part = s.substr(dot + 1);
    }
    if (int_part.empty()) int_part = "0";
    if (static_cast<int>(frac_part.size()) > SCALE_DIGITS) {
        throw std::runtime_error("value exceeds fixed-point precision: " + text);
    }
    while (static_cast<int>(frac_part.size()) < SCALE_DIGITS) frac_part += '0';

    int64_t value = std::stoll(int_part) * 1000000000LL;
    if (!frac_part.empty()) value += std::stoll(frac_part);
    return neg ? -value : value;
}

std::vector<Event> load_trades_csv(const std::string& path) {
    std::ifstream f(path);
    if (!f.good()) throw std::runtime_error("cannot open CSV: " + path);

    std::vector<Event> events;
    std::string line;
    bool header = true;
    uint64_t seq = 0;
    while (std::getline(f, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        if (header) {
            header = false;
            continue;
        }
        const auto cols = split(line, ',');
        if (cols.size() < 7) {
            throw std::runtime_error("malformed trade row: " + line);
        }
        Trade trade{
            seq,
            std::stoll(cols[0]),  // timestamp_ns (integer)
            cols[1],              // symbol
            parse_fixed(cols[2]),  // price
            parse_fixed(cols[3]),  // size
            parse_side(cols[4]),   // side
            cols[5],               // trade_id
            cols[6],               // venue
        };
        events.push_back(trade);
        ++seq;
    }
    return events;
}

}  // namespace quantstream
