# compile_options_stm32f4.cmake — MCU defines, compile and link options
# Purpose: all STM32F446-specific flags for ${PROJECT_NAME}.
# Usage: included from the root CMakeLists; LINKER_SCRIPT comes from the preset.

target_compile_definitions(${PROJECT_NAME} PRIVATE
    STM32F446xx
    USE_HAL_DRIVER
)

target_compile_options(${PROJECT_NAME} PRIVATE
    -std=gnu11
    -ffreestanding
    -ffunction-sections
    -fdata-sections
    -Wall
    -Wextra
    $<$<CONFIG:Debug>:-g3 -Og>
    $<$<CONFIG:Release>:-g0 -Os>
    $<$<CONFIG:RelWithDebInfo>:-g3 -O2>
    $<$<CONFIG:MinSizeRel>:-g0 -Os>
)

target_link_options(${PROJECT_NAME} PRIVATE
    -T${LINKER_SCRIPT}
    -Wl,--gc-sections
    -Wl,-Map=${CMAKE_BINARY_DIR}/${PROJECT_NAME}.map
    --specs=nano.specs
    --specs=nosys.specs
)
