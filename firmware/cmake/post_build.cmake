# post_build.cmake — artifact generation (objcopy + size + versioned copies)
# Purpose: produce artifacts/<name>_<version>.{bin,hex} after each build.
# Usage: included from the root CMakeLists.

add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/artifacts
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:${PROJECT_NAME}>
            ${CMAKE_BINARY_DIR}/artifacts/${PROJECT_NAME}_${GIT_VERSION}.bin
    COMMAND ${CMAKE_OBJCOPY} -O ihex $<TARGET_FILE:${PROJECT_NAME}>
            ${CMAKE_BINARY_DIR}/artifacts/${PROJECT_NAME}_${GIT_VERSION}.hex
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:${PROJECT_NAME}>
    COMMENT "Artifacts -> ${CMAKE_BINARY_DIR}/artifacts/"
)

set_directory_properties(PROPERTIES ADDITIONAL_CLEAN_FILES
    "${CMAKE_BINARY_DIR}/artifacts;${CMAKE_BINARY_DIR}/generated"
)
