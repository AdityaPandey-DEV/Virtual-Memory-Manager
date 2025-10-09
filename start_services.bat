@echo off
REM Virtual Memory Manager - Service Startup Script for Windows
REM This script starts all three services in the correct order

echo ========================================
echo Virtual Memory Manager - Service Startup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ and try again
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 16+ and try again
    pause
    exit /b 1
)

REM Check if CMake is available
cmake --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: CMake is not installed or not in PATH
    echo Please install CMake 3.16+ and try again
    pause
    exit /b 1
)

echo Starting services in order:
echo 1. Python AI Predictor (port 5000)
echo 2. C++ Backend Simulator (port 8080)
echo 3. React Frontend Dashboard (port 3000)
echo.

REM Start Python AI Predictor
echo [1/3] Starting Python AI Predictor...
start "AI Predictor" cmd /k "cd /d %~dp0 && python run_predictor.py --host 0.0.0.0 --port 5000"
timeout /t 3 /nobreak >nul

REM Build C++ Backend
echo [2/3] Building C++ Backend...
cd backend
if not exist build mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
if errorlevel 1 (
    echo ERROR: Failed to build C++ backend
    pause
    exit /b 1
)

REM Start C++ Backend
echo Starting C++ Backend Simulator...
start "VMM Backend" cmd /k "cd /d %~dp0\backend\build\bin\Release && vmm_simulator.exe"
cd ..\..
timeout /t 3 /nobreak >nul

REM Install and start React Frontend
echo [3/3] Starting React Frontend...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
)

echo Starting React development server...
start "VMM Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"
cd ..

echo.
echo ========================================
echo All services started successfully!
echo ========================================
echo.
echo Service URLs:
echo - AI Predictor: http://localhost:5000
echo - Backend API:  http://localhost:8080
echo - Frontend:     http://localhost:3000
echo.
echo Test connectivity:
echo - curl http://localhost:5000/health
echo - curl http://localhost:8080/metrics
echo - curl http://localhost:3000
echo.
echo Press any key to continue...
pause >nul

