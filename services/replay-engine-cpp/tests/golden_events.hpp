// The same fixture as packages/contracts/tests/test_golden.py::build_golden_events,
// rebuilt in C++. If the serialization matches, these produce the identical bytes and
// stream checksum recorded in packages/contracts/tests/golden/expected.json.
#pragma once

#include <vector>

#include "quantstream/events.hpp"

namespace quantstream {

inline std::vector<Event> golden_events() {
    std::vector<Event> events;

    events.push_back(Trade{
        /*seq*/ 0,
        /*timestamp_ns*/ 1700000000000000000LL,
        /*symbol*/ "AAPL",
        /*price*/ 100070000000LL,
        /*size*/ 5000000000LL,
        /*side*/ Side::Buy,
        /*trade_id*/ "t1",
        /*venue*/ "XNAS"});

    events.push_back(Quote{
        1,
        1700000000000000050LL,
        "MSFT",
        420000000000LL,
        3000000000LL,
        420010000000LL,
        2000000000LL,
        "XNAS"});

    // Symbol "€STOXX": the euro sign is UTF-8 bytes E2 82 AC. Negative price
    // exercises signed int64.
    events.push_back(Trade{
        2,
        1700000000000000000LL,
        "\xe2\x82\xac" "STOXX",
        -3500000000LL,
        1LL,
        Side::Sell,
        "",
        ""});

    events.push_back(OHLCV{
        3,
        1700000000000001000LL,
        "SPY",
        450000000000LL,
        451500000000LL,
        449250000000LL,
        451000000000LL,
        1234567000000000LL,
        "ARCX"});

    events.push_back(L2Update{
        4,
        1700000000000000500LL,
        "AAPL",
        Side::Sell,
        100080000000LL,
        4000000000LL,
        BookAction::Delete,
        3,
        781248ULL,
        "XNAS"});

    return events;
}

}  // namespace quantstream
