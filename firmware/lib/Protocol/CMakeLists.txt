# lib/Protocol/CMakeLists.txt — pure UART protocol parser + CRC-8
# Purpose: byte-wise frame parser (hardware-independent, host-testable).

target_sources(${PROJECT_NAME} PRIVATE
    protocol.c
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../../inc
)
