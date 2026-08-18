# ext/middlewares/CMakeLists.txt — vendored FreeRTOS-Kernel V11.3.0
# Purpose: adds kernel sources (static allocation only — no heap file) to
#          ${PROJECT_NAME}. FreeRTOSConfig.h lives in inc/.

target_sources(${PROJECT_NAME} PRIVATE
    Third_Party/FreeRTOS/Source/tasks.c
    Third_Party/FreeRTOS/Source/queue.c
    Third_Party/FreeRTOS/Source/list.c
    Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F/port.c
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/Third_Party/FreeRTOS/Source/include
    ${CMAKE_CURRENT_SOURCE_DIR}/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F
)
