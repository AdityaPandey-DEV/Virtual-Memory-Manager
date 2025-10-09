#!/bin/bash

echo "==============================================="
echo "Stopping All Services"
echo "==============================================="

# Read PIDs from file if it exists
if [ -f ".service_pids" ]; then
    read -r PREDICTOR_PID BACKEND_PID FRONTEND_PID < .service_pids
    echo "Stopping services using saved PIDs..."
    
    # Stop services gracefully
    if [ ! -z "$PREDICTOR_PID" ] && kill -0 $PREDICTOR_PID 2>/dev/null; then
        echo "Stopping AI Predictor (PID: $PREDICTOR_PID)..."
        kill -TERM $PREDICTOR_PID
        sleep 2
        if kill -0 $PREDICTOR_PID 2>/dev/null; then
            echo "Force killing AI Predictor..."
            kill -KILL $PREDICTOR_PID
        fi
    fi
    
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        echo "Stopping C++ Backend (PID: $BACKEND_PID)..."
        kill -TERM $BACKEND_PID
        sleep 2
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "Force killing C++ Backend..."
            kill -KILL $BACKEND_PID
        fi
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Stopping React Frontend (PID: $FRONTEND_PID)..."
        kill -TERM $FRONTEND_PID
        sleep 2
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "Force killing React Frontend..."
            kill -KILL $FRONTEND_PID
        fi
    fi
    
    rm -f .service_pids
fi

# Also kill any remaining processes by port
echo "Checking for any remaining processes on ports 3000, 5000, 8080..."

for port in 3000 5000 8080; do
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "Killing process on port $port (PID: $PID)..."
        kill -TERM $PID 2>/dev/null
        sleep 1
        if kill -0 $PID 2>/dev/null; then
            kill -KILL $PID 2>/dev/null
        fi
    fi
done

echo "All services stopped."
