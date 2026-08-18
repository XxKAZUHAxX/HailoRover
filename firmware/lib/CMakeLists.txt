# lib/CMakeLists.txt — hardware-independent logic
# Purpose: business logic modules with zero HAL/MCU dependencies; the same
#          sources are compilable into host tests (BUILD_TESTING).

add_subdirectory(Protocol)
