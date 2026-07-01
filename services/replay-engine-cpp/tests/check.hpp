// Minimal dependency-free test harness: CHECK counts failures; main returns
// non-zero if any failed (CTest reads the exit code).
#pragma once

#include <cstdio>
#include <string>

namespace qtest {
inline int failures = 0;

inline void check(bool cond, const std::string& label) {
    if (cond) {
        std::printf("ok:   %s\n", label.c_str());
    } else {
        ++failures;
        std::printf("FAIL: %s\n", label.c_str());
    }
}
}  // namespace qtest

#define CHECK(cond) ::qtest::check((cond), #cond)
#define CHECK_MSG(cond, msg) ::qtest::check((cond), (msg))
