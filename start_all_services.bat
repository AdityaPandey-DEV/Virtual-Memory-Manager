@echo off
echo ===============================================
echo AI-Enhanced Virtual Memory Manager
echo Starting All Services
echo ===============================================

echo.
echo [1/4] Starting AI Predictor Service...
start "AI Predictor" cmd /k "cd /d %~dp0 && python -m uvicorn predictor.service:app --host 0.0.0.0 --port 5000 --reload"
timeout /t 3 /nobreak > nul

echo.
echo [2/4] Building C++ Backend...
cd backend
if not exist build mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
if errorlevel 1 (
    echo ERROR: Failed to build C++ backend
    pause
    exit /b 1
)
cd ..\..
echo C++ Backend built successfully

echo.
echo [3/4] Starting C++ Backend Service...
start "VMM Backend" cmd /k "cd /d %~dp0\backend\build\bin\Release && vmm_simulator.exe"
timeout /t 3 /nobreak > nul

echo.
echo [4/4] Starting React Frontend...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
)
start "VMM Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"
cd ..

echo.
echo ===============================================
echo All services started!
echo ===============================================
echo.
echo Services:
echo - AI Predictor:    http://localhost:5000
echo - C++ Backend:     http://localhost:8080  
echo - React Frontend:  http://localhost:3000
echo.
echo Press any key to open the dashboard...
pause > nul
start http://localhost:3000

