cmake_minimum_required(VERSION 3.16)

project(raytracer-omp
  VERSION 0.1.0
  DESCRIPTION "A simple OpenMP-parallelized ray tracer in C++"
  LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compile_commands.json for clangd / tooling.
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Help CMake find Homebrew's libomp on macOS (AppleClang ships no OpenMP runtime).
if(APPLE AND NOT DEFINED OpenMP_ROOT)
  find_program(BREW_EXECUTABLE brew)
  if(BREW_EXECUTABLE)
    execute_process(COMMAND ${BREW_EXECUTABLE} --prefix libomp
      OUTPUT_VARIABLE OpenMP_ROOT
      OUTPUT_STRIP_TRAILING_WHITESPACE
      ERROR_QUIET)
  endif()
endif()

find_package(OpenMP)

add_executable(raytracer src/main.cpp)

target_include_directories(raytracer PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

if(OpenMP_CXX_FOUND)
  target_link_libraries(raytracer PRIVATE OpenMP::OpenMP_CXX)
else()
  message(WARNING
    "OpenMP not found - building serial version only. "
    "On macOS install it with: brew install libomp")
endif()

target_compile_options(raytracer PRIVATE
  $<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall -Wextra -O0>)
