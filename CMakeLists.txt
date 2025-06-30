cmake_minimum_required(VERSION 3.15...4.0)

project(
  enc
  VERSION 0.3.1
  LANGUAGES CXX)

set_property(TARGET enc PROPERTY CXX_STANDARD 20)

add_executable(enc-cpp src/enc.cpp)

find_library(CPR_LIBRARY cpr)
if(CPR_LIBRARY)
	target_link_libraries(enc-cpp PUBLIC ${CPR_LIBRARY})
endif()
