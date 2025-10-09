# Quick Start Guide - AI-Enhanced VMM

## 🚀 One-Command Startup

### Windows
```cmd
start_all_services.bat
```

### Linux/macOS
```bash
chmod +x start_all_services.sh
./start_all_services.sh
```

### Docker (All Platforms)
```bash
docker-compose up --build
```

## 🔍 Verify System is Running

### Check Services
- **AI Predictor:** http://localhost:5000/health
- **C++ Backend:** http://localhost:8080/metrics  
- **React Frontend:** http://localhost:3000

### Run Tests
```bash
# Test connectivity
python test_connectivity.py

# Validate system
python validate_system.py

# Simulate workload
python simulate_workload.py
```

## 🎯 Key Endpoints

### AI Predictor (Port 5000)
```bash
# Health check
curl http://localhost:5000/health

# Get predictions
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"recent_accesses": [1,2,3,4,5], "top_k": 5}'

# API docs
open http://localhost:5000/docs
```

### C++ Backend (Port 8080)
```bash
# Get metrics
curl http://localhost:8080/metrics

# Start simulation
curl -X POST http://localhost:8080/simulate/start

# Stop simulation  
curl -X POST http://localhost:8080/simulate/stop

# Stream events
curl -N http://localhost:8080/events/stream
```

### React Frontend (Port 3000)
- **Dashboard:** http://localhost:3000
- **Real-time metrics and logs**
- **AI prediction visualization**
- **Control panel for simulations**

## 🛠️ Troubleshooting

### Stop All Services
```bash
# Windows
# Press Ctrl+C in each terminal

# Linux/macOS
./stop_all_services.sh

# Docker
docker-compose down
```

### Check Port Usage
```bash
# Windows
netstat -an | findstr :5000
netstat -an | findstr :8080
netstat -an | findstr :3000

# Linux/macOS
lsof -i :5000
lsof -i :8080
lsof -i :3000
```

### View Logs
```bash
# Docker
docker-compose logs -f

# Individual services
docker-compose logs -f predictor
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 📊 Demo Script

Run the comprehensive demo:
```bash
python demo_script.py
```

This will:
- Test all three services
- Demonstrate AI predictions
- Show system integration
- Validate performance

## 🎓 For Teachers

### What to Show
1. **AI Predictor API:** http://localhost:5000/docs
2. **React Dashboard:** http://localhost:3000
3. **Demo Script:** `python demo_script.py`
4. **System Architecture:** Microservices with AI integration

### Key Talking Points
- AI-enhanced virtual memory management
- Machine learning for page prediction
- Real-time monitoring and visualization
- Production-ready implementation
- Microservices architecture

## 🔧 Development

### Manual Service Startup
```bash
# 1. AI Predictor
cd predictor
python -m uvicorn service:app --host 0.0.0.0 --port 5000

# 2. C++ Backend  
cd backend
mkdir build && cd build
cmake .. && make
./vmm_simulator

# 3. React Frontend
cd frontend
npm install
npm run dev
```

### Testing Commands
```bash
# Test AI predictions
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"recent_accesses": [1,2,3,4,5], "top_k": 5}'

# Test backend metrics
curl http://localhost:8080/metrics

# Test SSE streaming
curl -N http://localhost:8080/events/stream
```

## 📈 Performance Monitoring

### Real-time Metrics
- **Page fault rate**
- **AI prediction accuracy** 
- **Processing latency**
- **Memory usage**
- **System throughput**

### Access via:
- **Frontend Dashboard:** http://localhost:3000
- **Backend API:** http://localhost:8080/metrics
- **AI Predictor:** http://localhost:5000/health

## 🚨 Common Issues

1. **Port already in use**
   - Kill processes using ports 3000, 5000, 8080
   - Use `netstat` or `lsof` to find processes

2. **Services not starting**
   - Check Docker is running
   - Verify all dependencies installed
   - Check logs for errors

3. **Frontend not loading**
   - Ensure backend is running on port 8080
   - Check browser console for errors
   - Verify CORS settings

4. **AI predictions failing**
   - Check predictor service is running
   - Verify model is loaded
   - Check network connectivity

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run `python test_connectivity.py`
3. Check service logs
4. Verify all ports are available

