@echo off
REM Virtual Memory Manager Simulator Build Script for Windows

echo Building Virtual Memory Manager Simulator...

REM Create build directory
if not exist build mkdir build
cd build

REM Configure with CMake
echo Configuring with CMake...
cmake ../backend

REM Build the project
echo Building project...
cmake --build . --config Release

echo Build completed successfully!
echo.
echo To run the simulator:
echo   bin\Release\vmm_simulator.exe
echo.
echo To test the API:
echo   curl http://localhost:8080/metrics
echo   curl -X POST http://localhost:8080/simulate/start
echo   curl http://localhost:8080/events/stream

pause
