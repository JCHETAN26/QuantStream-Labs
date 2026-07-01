// BLAKE2b-256 per RFC 7693. Unkeyed, 32-byte output, to match
// hashlib.blake2b(digest_size=32).
#include "quantstream/blake2b.hpp"

#include <cstring>

namespace quantstream {
namespace {

constexpr uint64_t IV[8] = {
    0x6a09e667f3bcc908ULL, 0xbb67ae8584caa73bULL, 0x3c6ef372fe94f82bULL,
    0xa54ff53a5f1d36f1ULL, 0x510e527fade682d1ULL, 0x9b05688c2b3e6c1fULL,
    0x1f83d9abfb41bd6bULL, 0x5be0cd19137e2179ULL};

constexpr uint8_t SIGMA[12][16] = {
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15},
    {14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3},
    {11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4},
    {7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8},
    {9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13},
    {2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9},
    {12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11},
    {13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10},
    {6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5},
    {10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0},
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15},
    {14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3}};

inline uint64_t rotr64(uint64_t x, unsigned n) {
    return (x >> n) | (x << (64 - n));
}

inline uint64_t load64_le(const uint8_t* p) {
    uint64_t v = 0;
    for (int i = 0; i < 8; ++i) v |= static_cast<uint64_t>(p[i]) << (8 * i);
    return v;
}

struct State {
    uint64_t h[8];
    uint64_t t[2];  // 128-bit byte counter (low, high)
};

inline void mix(uint64_t v[16], int a, int b, int c, int d, uint64_t x, uint64_t y) {
    v[a] = v[a] + v[b] + x;
    v[d] = rotr64(v[d] ^ v[a], 32);
    v[c] = v[c] + v[d];
    v[b] = rotr64(v[b] ^ v[c], 24);
    v[a] = v[a] + v[b] + y;
    v[d] = rotr64(v[d] ^ v[a], 16);
    v[c] = v[c] + v[d];
    v[b] = rotr64(v[b] ^ v[c], 63);
}

void compress(State& s, const uint8_t block[128], bool last) {
    uint64_t m[16];
    for (int i = 0; i < 16; ++i) m[i] = load64_le(block + i * 8);

    uint64_t v[16];
    for (int i = 0; i < 8; ++i) v[i] = s.h[i];
    for (int i = 0; i < 8; ++i) v[8 + i] = IV[i];
    v[12] ^= s.t[0];
    v[13] ^= s.t[1];
    if (last) v[14] ^= 0xffffffffffffffffULL;

    for (int r = 0; r < 12; ++r) {
        const uint8_t* sg = SIGMA[r];
        mix(v, 0, 4, 8, 12, m[sg[0]], m[sg[1]]);
        mix(v, 1, 5, 9, 13, m[sg[2]], m[sg[3]]);
        mix(v, 2, 6, 10, 14, m[sg[4]], m[sg[5]]);
        mix(v, 3, 7, 11, 15, m[sg[6]], m[sg[7]]);
        mix(v, 0, 5, 10, 15, m[sg[8]], m[sg[9]]);
        mix(v, 1, 6, 11, 12, m[sg[10]], m[sg[11]]);
        mix(v, 2, 7, 8, 13, m[sg[12]], m[sg[13]]);
        mix(v, 3, 4, 9, 14, m[sg[14]], m[sg[15]]);
    }

    for (int i = 0; i < 8; ++i) s.h[i] ^= v[i] ^ v[8 + i];
}

}  // namespace

std::array<uint8_t, 32> blake2b_256(const std::vector<uint8_t>& data) {
    constexpr uint64_t outlen = 32;
    State s{};
    for (int i = 0; i < 8; ++i) s.h[i] = IV[i];
    // Parameter block: digest_length=outlen, key_length=0, fanout=1, depth=1.
    s.h[0] ^= 0x01010000ULL ^ outlen;
    s.t[0] = 0;
    s.t[1] = 0;

    const size_t len = data.size();
    size_t offset = 0;
    // Process all but the final block with last=false.
    while (len - offset > 128) {
        s.t[0] += 128;
        if (s.t[0] < 128) s.t[1] += 1;  // carry
        compress(s, data.data() + offset, false);
        offset += 128;
    }

    // Final block: remaining bytes (0..128), zero-padded, last=true.
    uint8_t block[128];
    std::memset(block, 0, sizeof(block));
    const size_t remaining = len - offset;
    if (remaining > 0) std::memcpy(block, data.data() + offset, remaining);
    s.t[0] += remaining;
    if (s.t[0] < remaining) s.t[1] += 1;  // carry
    compress(s, block, true);

    std::array<uint8_t, 32> out{};
    for (size_t i = 0; i < outlen; ++i) {
        out[i] = static_cast<uint8_t>(s.h[i >> 3] >> (8 * (i & 7)));
    }
    return out;
}

std::string blake2b_256_hex(const std::vector<uint8_t>& data) {
    static const char* hexd = "0123456789abcdef";
    auto digest = blake2b_256(data);
    std::string out;
    out.reserve(64);
    for (uint8_t b : digest) {
        out.push_back(hexd[b >> 4]);
        out.push_back(hexd[b & 0xf]);
    }
    return out;
}

}  // namespace quantstream
