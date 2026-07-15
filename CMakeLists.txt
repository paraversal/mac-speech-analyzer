cmake_minimum_required(VERSION 3.26)
project(macspeechanalyzer LANGUAGES Swift)

add_library(macspeechanalyzer_core SHARED
    swift/core.swift
    swift/bridge.swift)

# Editable/inplace: no install step runs, so aim the linker output
# directly at the package. $<0:> keeps multi-config generators happy.
if(SKBUILD_STATE STREQUAL "editable")
    set_target_properties(macspeechanalyzer_core PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY
            "${CMAKE_CURRENT_SOURCE_DIR}/src/macspeechanalyzer/$<0:>")
endif()

# Wheel builds: install step runs, destination is relative to the wheel root
install(TARGETS macspeechanalyzer_core
        LIBRARY DESTINATION macspeechanalyzer
        RUNTIME DESTINATION macspeechanalyzer)