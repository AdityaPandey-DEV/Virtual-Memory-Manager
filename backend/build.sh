#!/bin/bash

# Virtual Memory Manager Simulator Build Script

set -e

echo "Building Virtual Memory Manager Simulator..."

# Create build directory
mkdir -p build
cd build

# Configure with CMake
echo "Configuring with CMake..."
cmake ..

# Build the project
echo "Building project..."
cmake --build . --config Release

echo "Build completed successfully!"
echo ""
echo "To run the simulator:"
echo "  ./bin/vmm_simulator"
echo ""
echo "To test the API:"
echo "  curl http://localhost:8080/metrics"
echo "  curl -X POST http://localhost:8080/simulate/start"
echo "  curl http://localhost:8080/events/stream"
