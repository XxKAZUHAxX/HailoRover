# STM32F446RE Motor Controller Firmware
# Phase 6 — to be implemented after Raspberry Pi stack is stable.
#
# Build:
#   cmake --preset STM32F4-Release
#   cmake --build build/Release

cmake_minimum_required(VERSION 3.22)
project(motor-controller C ASM)

# TODO: Full STM32 CMake toolchain setup
# - CMSIS + HAL drivers
# - FreeRTOS
# - UART protocol handler
# - PWM motor control (TIM peripherals)
# - TB6612FNG / DRV8871 interface
