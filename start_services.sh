#!/bin/bash
# Virtual Memory Manager - Service Startup Script for Linux/macOS
# This script starts all three services in the correct order

set -e

echo "========================================"
echo "Virtual Memory Manager - Service Startup"
echo "========================================"
echo

# Check dependencies
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "ERROR: $1 is not installed or not in PATH"
        echo "Please install $1 and try again"
        exit 1
    fi
}

echo "Checking dependencies..."
check_dependency python3
check_dependency node
check_dependency npm
check_dependency cmake

echo "Starting services in order:"
echo "1. Python AI Predictor (port 5000)"
echo "2. C++ Backend Simulator (port 8080)"
echo "3. React Frontend Dashboard (port 3000)"
echo

# Start Python AI Predictor
echo "[1/3] Starting Python AI Predictor..."
python3 run_predictor.py --host 0.0.0.0 --port 5000 &
PREDICTOR_PID=$!
sleep 3

# Build C++ Backend
echo "[2/3] Building C++ Backend..."
cd backend
mkdir -p build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build C++ backend"
    exit 1
fi

# Start C++ Backend
echo "Starting C++ Backend Simulator..."
./bin/vmm_simulator &
BACKEND_PID=$!
cd ../..
sleep 3

# Install and start React Frontend
echo "[3/3] Starting React Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install frontend dependencies"
        exit 1
    fi
fi

echo "Starting React development server..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo
echo "========================================"
echo "All services started successfully!"
echo "========================================"
echo
echo "Service URLs:"
echo "- AI Predictor: http://localhost:5000"
echo "- Backend API:  http://localhost:8080"
echo "- Frontend:     http://localhost:3000"
echo
echo "Process IDs:"
echo "- Predictor PID: $PREDICTOR_PID"
echo "- Backend PID:   $BACKEND_PID"
echo "- Frontend PID:  $FRONTEND_PID"
echo
echo "Test connectivity:"
echo "- curl http://localhost:5000/health"
echo "- curl http://localhost:8080/metrics"
echo "- curl http://localhost:3000"
echo
echo "To stop all services, run: kill $PREDICTOR_PID $BACKEND_PID $FRONTEND_PID"
echo
echo "Press Ctrl+C to stop all services..."

# Function to cleanup on exit
cleanup() {
    echo
    echo "Stopping all services..."
    kill $PREDICTOR_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait

