#!/bin/bash

echo "==============================================="
echo "AI-Enhanced Virtual Memory Manager"
echo "Starting All Services"
echo "==============================================="

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "WARNING: Port $port is already in use"
        return 1
    fi
    return 0
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    echo "Waiting for $service_name to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo "✓ $service_name is ready"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo "✗ $service_name failed to start after $max_attempts seconds"
    return 1
}

echo
echo "[1/4] Starting AI Predictor Service..."
if ! check_port 5001; then
    echo "Port 5001 is in use. Please stop the service using port 5001 first."
    exit 1
fi

# Start AI Predictor in background
python3 simple_predictor.py &
PREDICTOR_PID=$!
echo "AI Predictor PID: $PREDICTOR_PID"

# Wait for predictor to be ready
if ! wait_for_service "http://localhost:5001/health" "AI Predictor"; then
    echo "Failed to start AI Predictor"
    kill $PREDICTOR_PID 2>/dev/null
    exit 1
fi

echo
echo "[2/4] Building C++ Backend..."
cd backend

# Create build directory if it doesn't exist
mkdir -p build
cd build

# Configure and build
cmake .. -DCMAKE_BUILD_TYPE=Release
if [ $? -ne 0 ]; then
    echo "ERROR: CMake configuration failed"
    exit 1
fi

make -j$(sysctl -n hw.ncpu)
if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

cd ../..
echo "✓ C++ Backend built successfully"

echo
echo "[3/4] Starting C++ Backend Service..."
if ! check_port 8080; then
    echo "Port 8080 is in use. Please stop the service using port 8080 first."
    kill $PREDICTOR_PID 2>/dev/null
    exit 1
fi

# Start C++ Backend in background
./backend/build/bin/vmm_simulator &
BACKEND_PID=$!
echo "C++ Backend PID: $BACKEND_PID"

# Wait for backend to be ready
if ! wait_for_service "http://localhost:8080/metrics" "C++ Backend"; then
    echo "Failed to start C++ Backend"
    kill $PREDICTOR_PID $BACKEND_PID 2>/dev/null
    exit 1
fi

echo
echo "[4/4] Starting React Frontend..."
if ! check_port 3000; then
    echo "Port 3000 is in use. Please stop the service using port 3000 first."
    kill $PREDICTOR_PID $BACKEND_PID 2>/dev/null
    exit 1
fi

cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install frontend dependencies"
        kill $PREDICTOR_PID $BACKEND_PID 2>/dev/null
        exit 1
    fi
fi

# Start React Frontend in background
npm run dev &
FRONTEND_PID=$!
echo "React Frontend PID: $FRONTEND_PID"

cd ..

# Wait for frontend to be ready
if ! wait_for_service "http://localhost:3000" "React Frontend"; then
    echo "Failed to start React Frontend"
    kill $PREDICTOR_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo
echo "==============================================="
echo "All services started successfully!"
echo "==============================================="
echo
echo "Services:"
echo "- AI Predictor:    http://localhost:5001"
echo "- C++ Backend:     http://localhost:8080"
echo "- React Frontend:  http://localhost:3000"
echo
echo "Process IDs:"
echo "- AI Predictor:    $PREDICTOR_PID"
echo "- C++ Backend:     $BACKEND_PID"
echo "- React Frontend:  $FRONTEND_PID"
echo
echo "To stop all services, run: ./stop_all_services.sh"
echo "To open the dashboard: open http://localhost:3000"
echo

# Save PIDs for stop script
echo "$PREDICTOR_PID $BACKEND_PID $FRONTEND_PID" > .service_pids

# Open dashboard
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:3000
elif command -v open >/dev/null 2>&1; then
    open http://localhost:3000
fi

