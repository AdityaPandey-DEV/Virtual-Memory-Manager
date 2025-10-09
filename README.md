# Virtual Memory Manager

An AI-enhanced Virtual Memory Manager (VMM) simulator with real-time dashboard visualization.

## Overview

This project implements a comprehensive Virtual Memory Management system with three main components:

1. **C++ Backend Simulator** - Core VMM logic with HTTP API
2. **Python AI Predictor** - Machine learning-based page prediction service
3. **React Frontend Dashboard** - Real-time visualization and control interface

## Features

- **Virtual Memory Management**: Page tables, page replacement algorithms (FIFO, LRU, Clock)
- **AI-Enhanced Predictions**: Machine learning models for page prefetching and eviction hints
- **Real-time Dashboard**: Live metrics, charts, and simulation control
- **Multiple Workload Types**: Sequential, Random, Strided, DB-like access patterns
- **Server-Sent Events**: Real-time log streaming and event updates

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  C++ Backend    │    │ Python AI       │
│   (Port 3000)   │◄──►│  (Port 8080)    │◄──►│ Predictor       │
│                 │    │                 │    │ (Port 5000)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- **C++ Compiler** (MSVC on Windows, GCC/Clang on Linux/macOS)
- **CMake** (3.10 or higher)
- **Python 3.8+** with pip
- **Node.js 16+** with npm

### 1. Start AI Predictor

```bash
cd predictor
pip install -r requirements.txt
python -m uvicorn predictor.service:app --host 0.0.0.0 --port 5000
```

### 2. Build and Start C++ Backend

```bash
cd backend
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
cd bin/Release
./vmm_simulator.exe  # Windows
# or
./vmm_simulator      # Linux/macOS
```

### 3. Start React Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Access Dashboard

Open your browser and navigate to:
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **AI Predictor**: http://localhost:5000

## API Endpoints

### Backend (Port 8080)

- `GET /metrics` - Get simulation metrics
- `POST /simulate/start` - Start simulation
- `POST /simulate/stop` - Stop simulation
- `GET /events/stream` - Server-Sent Events stream

### AI Predictor (Port 5000)

- `GET /health` - Health check
- `POST /predict` - Get page predictions
- `GET /model/info` - Model information

## Docker Deployment

For easy deployment, use Docker Compose:

```bash
docker-compose up --build
```

This will start all three services with proper networking and health checks.

## Configuration

### VMM Configuration

```cpp
VMMConfig vmm_config{
    .total_frames = 256,           // Number of physical frames
    .page_size = 4096,             // Page size in bytes
    .total_pages = 1024,           // Total virtual pages
    .replacement_policy = ReplacementPolicy::CLOCK,
    .enable_ai_predictions = true,
    .ai_predictor_url = "http://localhost:5000/predict"
};
```

### Workload Configuration

```cpp
WorkloadConfig workload_config{
    .type = WorkloadType::RANDOM,   // Workload pattern
    .total_requests = 1000,        // Number of memory accesses
    .page_range = 1000,            // Range of page numbers
    .stride = 1,                   // Stride for strided access
    .zipf_alpha = 1.0,            // Zipf distribution parameter
    .locality_factor = 0.8,        // Locality factor for webserver workload
    .working_set_size = 100        // Working set size
};
```

## Development

### Building from Source

1. **Backend**:
   ```bash
   cd backend
   mkdir build && cd build
   cmake .. -DCMAKE_BUILD_TYPE=Release
   cmake --build . --config Release
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. **AI Predictor**:
   ```bash
   cd predictor
   pip install -r requirements.txt
   ```

### Testing

Run the connectivity test:
```bash
python test_connectivity.py
```

Run the system validation:
```bash
python validate_system.py
```

## Project Structure

```
Virtual-Memory-Manager/
├── backend/                 # C++ VMM Simulator
│   ├── src/               # Source code
│   ├── include/          # Headers
│   ├── build/            # Build output
│   └── CMakeLists.txt    # Build configuration
├── frontend/              # React Dashboard
│   ├── src/              # React components
│   ├── public/           # Static assets
│   └── package.json      # Dependencies
├── predictor/            # Python AI Service
│   ├── models/           # ML models
│   ├── service.py        # FastAPI app
│   └── requirements.txt  # Python dependencies
├── docker-compose.yml    # Container orchestration
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- **Aditya Pandey** - Initial work and development

## Acknowledgments

- Virtual Memory Management concepts and algorithms
- React and FastAPI frameworks
- Machine Learning for page prediction
- Real-time web technologies (SSE, WebSockets)