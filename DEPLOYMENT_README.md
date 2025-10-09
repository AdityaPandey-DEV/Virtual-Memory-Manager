# 🚀 AI-Enhanced Virtual Memory Manager - Deployment Guide

## Quick Start

### Option 1: Docker Compose (Recommended)
```bash
# One-command deployment
./deploy.sh  # Linux/macOS
# or
deploy.bat   # Windows
```

### Option 2: Manual Service Startup
```bash
# Start all services manually
./start_services.sh  # Linux/macOS
# or
start_services.bat  # Windows
```

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Predictor  │
│   (React)       │◄──►│   (C++)         │◄──►│   (Python)      │
│   Port: 3000    │    │   Port: 8080    │    │   Port: 5000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Load Balancer  │
                    │   (Nginx)        │
                    │   Port: 80/443  │
                    └─────────────────┘
```

## Service Endpoints

### AI Predictor (Port 5000)
- `GET /health` - Health check
- `POST /predict` - Get page predictions
- `GET /model/info` - Model information
- `POST /model/reload` - Reload model

### Backend API (Port 8080)
- `GET /metrics` - Simulation metrics
- `POST /simulate/start` - Start simulation
- `POST /simulate/stop` - Stop simulation
- `GET /events/stream` - SSE event stream

### Frontend Dashboard (Port 3000)
- `GET /` - Main dashboard
- Real-time metrics and logs
- Control panel for simulation

## Prerequisites

### Development Environment
- **Python 3.9+** with pip
- **Node.js 16+** with npm
- **CMake 3.16+**
- **C++17** compiler (GCC/Clang/MSVC)

### Production Environment
- **Docker 20.10+**
- **Docker Compose 2.0+**
- **4GB+ RAM**
- **2+ CPU cores**

## Step-by-Step Deployment

### 1. Development Setup

#### Start AI Predictor
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start predictor service
python run_predictor.py --host 0.0.0.0 --port 5000
```

#### Build and Start Backend
```bash
# Build C++ backend
cd backend
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)  # Linux/macOS
# or
cmake --build . --config Release  # Windows

# Start backend
./bin/vmm_simulator  # Linux/macOS
# or
bin\Release\vmm_simulator.exe  # Windows
```

#### Start Frontend
```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

### 2. Production Deployment

#### Docker Compose Deployment
```bash
# Build and start all services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n vmm-system

# View logs
kubectl logs -f deployment/backend -n vmm-system
```

## Testing and Validation

### Connectivity Testing
```bash
# Test all service endpoints
python test_connectivity.py

# Test AI prediction accuracy
python simulate_workload.py

# Comprehensive system validation
python validate_system.py
```

### Manual Testing
```bash
# Test AI Predictor
curl http://localhost:5000/health
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"recent_accesses": [1,2,3,4,5], "top_k": 5}'

# Test Backend API
curl http://localhost:8080/metrics
curl -X POST http://localhost:8080/simulate/start
curl -X POST http://localhost:8080/simulate/stop

# Test SSE Stream
curl -N http://localhost:8080/events/stream

# Test Frontend
curl http://localhost:3000
```

## Configuration

### Environment Variables

#### AI Predictor
```bash
PREDICTOR_HOST=0.0.0.0
PREDICTOR_PORT=5000
PREDICTOR_MODEL_PATH=/app/models
PREDICTOR_WORKERS=4
```

#### Backend
```bash
VMM_LOG_LEVEL=INFO
VMM_PREDICTOR_ENABLED=true
VMM_PREDICTOR_URL=http://predictor:5000/predict
VMM_TOTAL_FRAMES=256
VMM_PAGE_SIZE=4096
VMM_TOTAL_PAGES=1024
```

#### Frontend
```bash
REACT_APP_API_URL=http://localhost:8080
REACT_APP_PREDICTOR_URL=http://localhost:5000
REACT_APP_ENVIRONMENT=production
```

### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  predictor:
    build: .
    ports: ["5000:5000"]
    environment:
      - PREDICTOR_HOST=0.0.0.0
      - PREDICTOR_PORT=5000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build: ./backend
    ports: ["8080:8080"]
    environment:
      - VMM_PREDICTOR_URL=http://predictor:5000/predict
    depends_on:
      predictor:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - REACT_APP_API_URL=http://localhost:8080
    depends_on:
      backend:
        condition: service_healthy
```

## Monitoring and Logging

### Health Checks
```bash
# Check all services
curl http://localhost:5000/health  # AI Predictor
curl http://localhost:8080/metrics  # Backend
curl http://localhost:3000  # Frontend

# Docker health checks
docker-compose ps
```

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f predictor
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Metrics
- **Page Fault Rate**: Percentage of page faults
- **AI Hit Rate**: Accuracy of AI predictions
- **Swap I/O**: Disk I/O operations
- **Memory Usage**: Frame utilization
- **Prediction Latency**: AI response time

## Troubleshooting

### Common Issues

#### 1. Service Not Starting
```bash
# Check if ports are available
netstat -tulpn | grep :5000
netstat -tulpn | grep :8080
netstat -tulpn | grep :3000

# Check Docker containers
docker-compose ps
docker-compose logs
```

#### 2. AI Predictor Issues
```bash
# Check if model exists
ls -la model.pkl

# Train model if missing
python train_predictor.py

# Check predictor logs
docker-compose logs predictor
```

#### 3. Backend Connection Issues
```bash
# Test backend connectivity
curl http://localhost:8080/metrics

# Check backend logs
docker-compose logs backend

# Verify AI predictor is accessible
curl http://localhost:5000/health
```

#### 4. Frontend Issues
```bash
# Check frontend build
cd frontend && npm run build

# Check frontend logs
docker-compose logs frontend

# Verify API connectivity
curl http://localhost:8080/metrics
```

### Performance Issues

#### High CPU Usage
```bash
# Check resource usage
docker stats

# Scale services
docker-compose up --scale predictor=3
```

#### Memory Issues
```bash
# Check memory usage
docker stats

# Adjust memory limits in docker-compose.yml
```

#### Network Issues
```bash
# Test internal connectivity
docker-compose exec backend curl http://predictor:5000/health
docker-compose exec frontend curl http://backend:8080/metrics
```

## Production Deployment

### Scaling
```bash
# Scale AI Predictor
docker-compose up --scale predictor=3

# Scale Backend
docker-compose up --scale backend=2
```

### Load Balancing
```yaml
# nginx.conf
upstream backend {
    server backend:8080;
}

upstream predictor {
    server predictor:5000;
}

server {
    listen 80;
    
    location /api/ {
        proxy_pass http://backend;
    }
    
    location /predictor/ {
        proxy_pass http://predictor;
    }
}
```

### Security
```bash
# Use HTTPS
# Set up SSL certificates
# Configure firewall rules
# Use secrets management
```

## Maintenance

### Regular Tasks
- **Daily**: Check service health
- **Weekly**: Update dependencies
- **Monthly**: Security patches
- **Quarterly**: Performance review

### Backup
```bash
# Backup model files
cp -r models/ backup/models_$(date +%Y%m%d)/

# Backup configuration
cp docker-compose.yml backup/
```

### Updates
```bash
# Update services
docker-compose pull
docker-compose up -d

# Update dependencies
pip install -r requirements.txt --upgrade
npm update
```

## Support

### Getting Help
1. Check the logs: `docker-compose logs -f`
2. Run validation: `python validate_system.py`
3. Test connectivity: `python test_connectivity.py`
4. Check service health: `curl http://localhost:5000/health`

### Useful Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart services
docker-compose restart

# View service status
docker-compose ps

# View logs
docker-compose logs -f

# Scale services
docker-compose up --scale predictor=3

# Clean up
docker-compose down -v
docker system prune -a
```

## Next Steps

1. **Deploy to Production**: Follow the production deployment guide
2. **Set up Monitoring**: Configure Prometheus and Grafana
3. **Implement Security**: Set up SSL/TLS and authentication
4. **Scale Services**: Configure load balancing and auto-scaling
5. **Backup Strategy**: Implement regular backups and disaster recovery

---

**🎉 Congratulations!** Your AI-Enhanced Virtual Memory Manager is now deployed and ready for use. The system provides real-time monitoring, AI-powered predictions, and comprehensive simulation capabilities for virtual memory management research and development.

