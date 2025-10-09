# AI-Enhanced Virtual Memory Manager - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the AI-Enhanced Virtual Memory Manager system. The system consists of three main components:

1. **AI Predictor Service** (Python/FastAPI) - Port 5000
2. **C++ Backend Simulator** - Port 8080  
3. **React Frontend Dashboard** - Port 3000

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate to the project
cd "Virtual Memory Manager"

# Start all services with Docker Compose
docker-compose up --build

# Or run in background
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Option 2: Manual Startup

#### Windows
```cmd
# Run the automated startup script
start_all_services.bat
```

#### Linux/macOS
```bash
# Make scripts executable
chmod +x start_all_services.sh stop_all_services.sh

# Start all services
./start_all_services.sh

# Stop all services
./stop_all_services.sh
```

## Service Details

### 1. AI Predictor Service

**Port:** 5000  
**Technology:** Python/FastAPI  
**Endpoints:**
- `GET /health` - Health check
- `POST /predict` - Get page predictions
- `GET /model/info` - Model information
- `GET /docs` - API documentation

**Start manually:**
```bash
cd predictor
python -m uvicorn service:app --host 0.0.0.0 --port 5000 --reload
```

### 2. C++ Backend Simulator

**Port:** 8080  
**Technology:** C++ with custom HTTP server  
**Endpoints:**
- `GET /metrics` - Simulation metrics
- `POST /simulate/start` - Start simulation
- `POST /simulate/stop` - Stop simulation
- `GET /events/stream` - SSE event stream

**Build and start manually:**
```bash
cd backend
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
./vmm_simulator
```

### 3. React Frontend Dashboard

**Port:** 3000  
**Technology:** React + TypeScript + Tailwind CSS  
**Features:**
- Real-time metrics display
- Event log streaming
- AI prediction visualization
- Control panel for simulations

**Start manually:**
```bash
cd frontend
npm install
npm run dev
```

## Testing and Validation

### Connectivity Testing

```bash
# Run comprehensive connectivity tests
python test_connectivity.py

# Run system validation
python validate_system.py

# Run workload simulation
python simulate_workload.py
```

### Manual Testing

```bash
# Test AI Predictor
curl http://localhost:5000/health
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"recent_accesses": [1,2,3,4,5], "top_k": 5}'

# Test C++ Backend
curl http://localhost:8080/metrics
curl -X POST http://localhost:8080/simulate/start
curl -X POST http://localhost:8080/simulate/stop

# Test SSE streaming
curl -N http://localhost:8080/events/stream
```

## Production Deployment

### Docker Compose Production Setup

1. **Environment Variables**
```bash
# Create .env file
cat > .env << EOF
# AI Predictor
PREDICTOR_MODEL_PATH=/app/models
PREDICTOR_HOST=0.0.0.0
PREDICTOR_PORT=5000

# Backend
VMM_LOG_LEVEL=INFO
VMM_PREDICTOR_ENABLED=true
VMM_PREDICTOR_URL=http://predictor:5000/predict

# Frontend
REACT_APP_API_URL=http://localhost:8080
REACT_APP_PREDICTOR_URL=http://localhost:5000
EOF
```

2. **Production Docker Compose**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  predictor:
    build:
      context: .
      dockerfile: Dockerfile.predictor
    environment:
      - PREDICTOR_MODEL_PATH=/app/models
    volumes:
      - ./models:/app/models
    restart: always
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
  
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - VMM_LOG_LEVEL=INFO
      - VMM_PREDICTOR_ENABLED=true
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'
```

3. **Deploy with Production Config**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

1. **Create Namespace**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vmm-system
```

2. **Deploy Services**
```yaml
# predictor-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: predictor
  namespace: vmm-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: predictor
  template:
    metadata:
      labels:
        app: predictor
    spec:
      containers:
      - name: predictor
        image: vmm-predictor:latest
        ports:
        - containerPort: 5000
        env:
        - name: PREDICTOR_MODEL_PATH
          value: "/app/models"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: predictor-service
  namespace: vmm-system
spec:
  selector:
    app: predictor
  ports:
  - port: 5000
    targetPort: 5000
  type: ClusterIP
```

### Reverse Proxy Setup (Nginx)

```nginx
# nginx.conf
upstream predictor {
    server predictor:5000;
}

upstream backend {
    server backend:8080;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # SSE Events
    location /events/ {
        proxy_pass http://backend/events/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
        proxy_cache off;
    }
    
    # AI Predictor
    location /predictor/ {
        proxy_pass http://predictor/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Logging

### Health Checks

```bash
# Check all services
curl http://localhost:5000/health  # AI Predictor
curl http://localhost:8080/metrics # Backend
curl http://localhost:3000         # Frontend

# Docker health checks
docker-compose ps
```

### Logging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f predictor
docker-compose logs -f backend
docker-compose logs -f frontend

# Save logs to file
docker-compose logs > vmm-logs.txt
```

### Metrics Collection

The system provides built-in metrics:
- Total memory accesses
- Page fault rate
- AI prediction accuracy
- Processing latency
- System resource usage

Access metrics via: `http://localhost:8080/metrics`

## Troubleshooting

### Common Issues

1. **Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep :5000
netstat -tulpn | grep :8080
netstat -tulpn | grep :3000

# Kill processes using ports
sudo fuser -k 5000/tcp
sudo fuser -k 8080/tcp
sudo fuser -k 3000/tcp
```

2. **Service Dependencies**
```bash
# Check service startup order
docker-compose ps

# Restart specific service
docker-compose restart predictor
```

3. **Build Issues**
```bash
# Clean build
docker-compose down
docker-compose build --no-cache
docker-compose up --build
```

4. **Permission Issues**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x *.sh
```

### Debug Mode

```bash
# Run with debug logging
VMM_LOG_LEVEL=DEBUG docker-compose up

# Enable verbose output
docker-compose up --build --force-recreate
```

## Performance Tuning

### Resource Limits

```yaml
# docker-compose.override.yml
services:
  predictor:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
  
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### Scaling

```bash
# Scale AI Predictor
docker-compose up --scale predictor=3

# Scale with load balancer
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up
```

## Security Considerations

1. **Network Security**
   - Use internal Docker networks
   - Implement firewall rules
   - Enable HTTPS with SSL certificates

2. **Authentication**
   - Add API authentication
   - Implement rate limiting
   - Use secure headers

3. **Data Protection**
   - Encrypt sensitive data
   - Implement backup strategies
   - Monitor access logs

## Backup and Recovery

```bash
# Backup volumes
docker run --rm -v vmm_predictor_logs:/data -v $(pwd):/backup alpine tar czf /backup/predictor_logs.tar.gz -C /data .

# Restore volumes
docker run --rm -v vmm_predictor_logs:/data -v $(pwd):/backup alpine tar xzf /backup/predictor_logs.tar.gz -C /data
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review service logs
3. Run connectivity tests
4. Check system requirements

## System Requirements

- **Minimum:**
  - 4GB RAM
  - 2 CPU cores
  - 10GB disk space
  - Docker 20.10+

- **Recommended:**
  - 8GB RAM
  - 4 CPU cores
  - 20GB disk space
  - Docker 24.0+

