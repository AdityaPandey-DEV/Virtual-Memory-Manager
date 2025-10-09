cmake_minimum_required(VERSION 3.16)
project(VirtualMemoryManager)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(Threads REQUIRED)

# Include directories
include_directories(include)

# Source files
set(SOURCES
    src/main.cpp
    src/vmm/PageTable.cpp
    src/vmm/Replacement.cpp
    src/vmm/VMM.cpp
    src/workload/WorkloadGen.cpp
    src/api/Server.cpp
)

# Header files
set(HEADERS
    include/vmm/PageTable.h
    include/vmm/Replacement.h
    include/vmm/VMM.h
    include/workload/WorkloadGen.h
    include/api/Server.h
)

# Create executable
add_executable(vmm_simulator ${SOURCES} ${HEADERS})

# Link libraries
target_link_libraries(vmm_simulator 
    Threads::Threads
    ${CMAKE_THREAD_LIBS_INIT}
)

# Platform-specific libraries
if(WIN32)
    target_link_libraries(vmm_simulator ws2_32)
endif()

# Compiler-specific options
if(MSVC)
    target_compile_options(vmm_simulator PRIVATE /W4)
    target_compile_definitions(vmm_simulator PRIVATE _WIN32_WINNT=0x0601)
else()
    target_compile_options(vmm_simulator PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Set output directory
set_target_properties(vmm_simulator PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Add build instructions
message(STATUS "Build configuration:")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Install prefix: ${CMAKE_INSTALL_PREFIX}")

# Installation
install(TARGETS vmm_simulator
    RUNTIME DESTINATION bin
)
