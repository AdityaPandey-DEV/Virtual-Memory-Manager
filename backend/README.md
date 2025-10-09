# Virtual Memory Manager Simulator

A C++ Virtual Memory Manager (VMM) simulator enhanced with AI predictions and REST API backend.

## Features

- **Core VMM Simulation**: Page table management, frame allocation, page replacement policies (CLOCK/LRU/FIFO)
- **AI Integration**: External predictor service integration for prefetching and replacement hints
- **REST API**: HTTP endpoints for metrics and simulation control
- **Real-time Events**: Server-Sent Events (SSE) streaming for live simulation data
- **Workload Generation**: Multiple access patterns (sequential, random, strided, Zipf, webserver-like)
- **Thread-safe**: Multi-threaded simulation with proper synchronization

## Project Structure

```
backend/
├── CMakeLists.txt
├── README.md
├── src/
│   ├── main.cpp
│   ├── vmm/
│   │   ├── PageTable.cpp
│   │   ├── Replacement.cpp
│   │   └── VMM.cpp
│   ├── workload/
│   │   └── WorkloadGen.cpp
│   └── api/
│       └── Server.cpp
└── include/
    ├── vmm/
    │   ├── PageTable.h
    │   ├── Replacement.h
    │   └── VMM.h
    ├── workload/
    │   └── WorkloadGen.h
    └── api/
        └── Server.h
```

## Building

### Prerequisites

- C++17 compatible compiler (GCC 7+, Clang 5+, MSVC 2017+)
- CMake 3.16+
- Threading support

### Build Instructions

```bash
# Create build directory
mkdir build
cd build

# Configure with CMake
cmake ../backend

# Build the project
cmake --build . --config Release

# Run the simulator
./bin/vmm_simulator
```

### Windows Build

```cmd
mkdir build
cd build
cmake ../backend -G "Visual Studio 16 2019"
cmake --build . --config Release
```

## Usage

### Starting the Simulator

```bash
./bin/vmm_simulator
```

The simulator will start an HTTP server on port 8080.

### API Endpoints

#### GET /metrics
Returns current simulation metrics in JSON format.

**Response:**
```json
{
  "total_accesses": 1000,
  "page_faults": 150,
  "page_fault_rate": 0.15,
  "swap_ins": 120,
  "swap_outs": 100,
  "ai_predictions": 50,
  "ai_hit_rate": 0.8,
  "free_frames": 200,
  "used_frames": 56
}
```

#### POST /simulate/start
Starts the simulation with the current workload configuration.

**Response:**
```json
{
  "status": "started",
  "workload_type": "random"
}
```

#### POST /simulate/stop
Stops the current simulation.

**Response:**
```json
{
  "status": "stopped"
}
```

#### GET /events/stream
Server-Sent Events endpoint for real-time simulation events.

**Event Format:**
```
data: {"type": "ACCESS", "message": "Page 42", "timestamp": 1234567890}
data: {"type": "FAULT", "message": "Page fault for page 100", "timestamp": 1234567891}
data: {"type": "AI", "message": "Predicted pages: [101, 102]", "timestamp": 1234567892}
```

### Configuration

The simulator can be configured by modifying the default values in `main.cpp`:

```cpp
VMMConfig vmm_config{
    .total_frames = 256,           // Number of physical frames
    .page_size = 4096,             // Page size in bytes
    .total_pages = 1024,           // Total virtual pages
    .replacement_policy = ReplacementPolicy::CLOCK,
    .enable_ai_predictions = true,
    .ai_predictor_url = "http://localhost:5000/predict"
};

WorkloadConfig workload_config{
    .type = WorkloadType::RANDOM,   // Workload pattern
    .total_requests = 1000,        // Number of memory accesses
    .page_range = 1000,            // Range of page numbers
    .stride = 1,                    // Stride for strided access
    .zipf_alpha = 1.0,             // Zipf distribution parameter
    .locality_factor = 0.8,        // Locality factor for webserver workload
    .working_set_size = 100        // Working set size
};
```

## Workload Types

1. **SEQUENTIAL**: Sequential page access pattern
2. **RANDOM**: Random page access pattern
3. **STRIDED**: Strided access pattern with configurable stride
4. **ZIPF**: Zipf distribution access pattern
5. **WEBSERVER**: Webserver-like access pattern with locality

## Page Replacement Policies

1. **FIFO**: First-In-First-Out
2. **LRU**: Least Recently Used
3. **CLOCK**: Clock replacement algorithm

## AI Integration

The simulator can integrate with an external AI predictor service:

- **Endpoint**: `http://localhost:5000/predict`
- **Request**: `{"recent_accesses": [1, 2, 3, 4, 5]}`
- **Response**: `{"predicted_pages": [6, 7, 8]}`

The AI predictions are used for:
- Prefetching predicted pages
- Replacement hints (kernel always validates)

## Thread Safety

The simulator is fully thread-safe with:
- Mutex-protected data structures
- Atomic operations for metrics
- Thread-safe event streaming
- Proper synchronization between components

## Performance

The simulator is designed for high performance:
- Efficient page table operations
- Minimal memory overhead
- Fast replacement algorithms
- Non-blocking event streaming

## Testing

You can test the API using curl:

```bash
# Get metrics
curl http://localhost:8080/metrics

# Start simulation
curl -X POST http://localhost:8080/simulate/start

# Stop simulation
curl -X POST http://localhost:8080/simulate/stop

# Stream events
curl http://localhost:8080/events/stream
```

## Integration with Frontend

The simulator is designed to work with a React frontend:
- CORS headers are included for cross-origin requests
- SSE events are formatted for easy consumption
- JSON responses follow consistent format
- Real-time metrics and events for live visualization

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `main.cpp` or kill the process using the port
2. **Compilation errors**: Ensure you have a C++17 compatible compiler
3. **Windows socket errors**: Make sure to link with `ws2_32` library

### Debug Mode

To enable debug output, modify the CMake configuration:

```bash
cmake ../backend -DCMAKE_BUILD_TYPE=Debug
```

## License

This project is provided as-is for educational and research purposes.
