# src/CMakeLists.txt — firmware application sources
# Purpose: adds Core/ application code (and the MCU startup file from
#          platform/startup) to ${PROJECT_NAME}.

target_sources(${PROJECT_NAME} PRIVATE
    Core/main.c
    Core/uart_link.c
    Core/motor_control.c
    Core/app_tasks.c
    Core/stm32f4xx_it.c
    Core/stm32f4xx_hal_timebase_tim.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../platform/startup/startup_stm32f446xx.s
)
