# CMakeToolchain-STM32F4.cmake — bare-metal ARM Cortex-M4F toolchain
# Purpose: cross-compile setup for STM32F446 (arm-none-eabi-gcc on PATH).
# Usage: referenced by the STM32F4-Default configure preset.

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR STM32F4)

set(CMAKE_C_COMPILER   arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_OBJCOPY      arm-none-eabi-objcopy)
set(CMAKE_OBJDUMP      arm-none-eabi-objdump)
set(CMAKE_SIZE         arm-none-eabi-size)

set(ARCHITECTURE_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")

# Injected via _INIT cache vars so compiler detection works with these flags
set(CMAKE_ASM_FLAGS_INIT        "${ARCHITECTURE_FLAGS}")
set(CMAKE_C_FLAGS_INIT          "${ARCHITECTURE_FLAGS}")
set(CMAKE_EXE_LINKER_FLAGS_INIT "${ARCHITECTURE_FLAGS}")

set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
