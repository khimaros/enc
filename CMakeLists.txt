cmake_minimum_required(VERSION 3.15...4.0)

project(
  enc
  VERSION 0.3.1
  LANGUAGES CXX)

add_executable(enc-cpp src/enc.cpp)
target_compile_features(enc-cpp PRIVATE cxx_std_20)

find_package(cpr REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(CLI11 REQUIRED)
find_package(fmt REQUIRED)

target_link_libraries(enc-cpp PRIVATE
    cpr::cpr
    nlohmann_json::nlohmann_json
    CLI11::CLI11
    fmt::fmt
)
