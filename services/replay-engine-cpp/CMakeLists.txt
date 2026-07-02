cmake_minimum_required(VERSION 3.16)
project(quantstream_replay_cpp CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

add_library(quantstream_replay STATIC
  src/blake2b.cpp
  src/serialization.cpp
  src/csv_load.cpp)
target_include_directories(quantstream_replay PUBLIC include)
target_compile_options(quantstream_replay PRIVATE -Wall -Wextra)

# The replay engine CLI: reads a trades CSV, prints the deterministic checksum.
add_executable(replay src/replay_main.cpp)
target_link_libraries(replay PRIVATE quantstream_replay)

enable_testing()

set(GOLDEN_JSON
  "${CMAKE_CURRENT_SOURCE_DIR}/../../packages/contracts/tests/golden/expected.json")

add_executable(test_serialization tests/test_serialization.cpp)
target_link_libraries(test_serialization PRIVATE quantstream_replay)
target_include_directories(test_serialization PRIVATE tests)
add_test(NAME serialization COMMAND test_serialization)

add_executable(test_golden tests/test_golden.cpp)
target_link_libraries(test_golden PRIVATE quantstream_replay)
target_include_directories(test_golden PRIVATE tests)
target_compile_definitions(test_golden PRIVATE GOLDEN_JSON="${GOLDEN_JSON}")
add_test(NAME golden COMMAND test_golden)
