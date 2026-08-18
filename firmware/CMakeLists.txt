# CMakeLists.txt — HailoRover motor-controller firmware (STM32F446RE)
# Purpose: single-target firmware build following the platform-control CMake
#          conventions: per-directory CMakeLists contribute sources to one
#          ${PROJECT_NAME} executable; no add_library modules in the firmware.
# Usage:
#   cmake --preset STM32F4-Release
#   cmake --build --preset STM32F4-Release
# Artifacts: build/<Config>/artifacts/motor-controller_<version>.{bin,hex}
# Update note: new directories contribute via add_subdirectory + target_sources.

cmake_minimum_required(VERSION 3.22)

# Firmware version from git describe (falls back gracefully outside a repo)
execute_process(
    COMMAND git describe --always --tags --dirty
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/..
    OUTPUT_VARIABLE GIT_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
)
if(GIT_VERSION STREQUAL "")
    set(GIT_VERSION "unknown")
endif()

if(NOT BUILD_TESTING)
    project(motor-controller LANGUAGES ASM C VERSION 0.1.0)

    set(APP_ENTRY src/Core/main.c)

    add_executable(${PROJECT_NAME} ${APP_ENTRY})

    set_target_properties(${PROJECT_NAME} PROPERTIES
        SUFFIX ".elf"
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    )

    # Version header (configure_file -> generated/version.h)
    configure_file(version.h.in ${CMAKE_BINARY_DIR}/generated/version.h @ONLY)

    # Central headers (HAL conf, FreeRTOS config, pin config, protocol headers)
    target_include_directories(${PROJECT_NAME} PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/inc
        ${CMAKE_BINARY_DIR}/generated
    )

    include(cmake/compile_options/compile_options_stm32f4.cmake)
    include(cmake/post_build.cmake)

    add_subdirectory(ext)        # vendored drivers + middlewares
    add_subdirectory(src)        # firmware application
else()
    # Host-test build (x86_64 preset, BUILD_TESTING=ON).
    # Requires a host C compiler — not installed on the current Windows machine.
    # Structure reserved so host-testable modules (lib/) can be gtest'd later.
    project(motor-controller-tests LANGUAGES C VERSION 0.1.0)
    message(WARNING "BUILD_TESTING requires a host C compiler (not installed here).")
endif()
