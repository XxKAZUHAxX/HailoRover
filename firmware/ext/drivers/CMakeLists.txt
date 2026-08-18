# ext/drivers/CMakeLists.txt — vendored CMSIS + STM32F4 HAL
# Purpose: adds device/CMSIS/HAL sources to ${PROJECT_NAME}.
# Sources: stm32f4xx-hal-driver v1.8.5, cmsis-device-f4 v2.6.11,
#          CMSIS core headers from STM32CubeF4 v1.28.3.

# --- STM32F4 HAL (modules used by this firmware) ---
target_sources(${PROJECT_NAME} PRIVATE
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_cortex.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_gpio.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_rcc.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_rcc_ex.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_flash.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_flash_ex.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_pwr.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_pwr_ex.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_dma.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_dma_ex.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_tim.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_tim_ex.c
    STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_uart.c
)

# --- CMSIS device (system init; startup lives in platform/startup) ---
target_sources(${PROJECT_NAME} PRIVATE
    CMSIS/Device/ST/STM32F4xx/Source/Templates/system_stm32f4xx.c
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/CMSIS/Include
    ${CMAKE_CURRENT_SOURCE_DIR}/CMSIS/Device/ST/STM32F4xx/Include
    ${CMAKE_CURRENT_SOURCE_DIR}/STM32F4xx_HAL_Driver/Inc
)
