// BLAKE2b-256, matching Python's hashlib.blake2b(digest_size=32) (unkeyed).
//
// Self-contained, no dependencies: the whole point of this engine is to reproduce
// the Python reference checksum byte-for-byte, so nothing here may depend on a
// third-party crypto library whose parameters we don't fully control.
#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace quantstream {

// One-shot BLAKE2b with a 32-byte digest. Returns the raw digest bytes.
std::array<uint8_t, 32> blake2b_256(const std::vector<uint8_t>& data);

// Lowercase hex of blake2b_256.
std::string blake2b_256_hex(const std::vector<uint8_t>& data);

}  // namespace quantstream
