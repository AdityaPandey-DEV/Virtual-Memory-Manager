# Virtual Memory Manager - Deployment Guide

This guide covers different deployment options for the Virtual Memory Manager system.

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** installed
- **Git** for cloning the repository
- At least **4GB RAM** and **2 CPU cores** recommended

### 1. Clone and Setup

```bash
git clone https://github.com/AdityaPandey-DEV/Virtual-Memory-Manager.git
cd Virtual-Memory-Manager
```

### 2. Environment Configuration

Copy the environment template and configure:

```bash
# Linux/macOS
cp env.example .env

# Windows
copy env.example .env
```

Edit `.env` file with your configuration:

```bash
# Backend Configuration
BACKEND_PORT=8080
BACKEND_HOST=0.0.0.0

# AI Predictor Configuration
PREDICTOR_PORT=5000
PREDICTOR_HOST=0.0.0.0

# Frontend Configuration
FRONTEND_PORT=3000
FRONTEND_HOST=localhost

# VMM Configuration
VMM_TOTAL_FRAMES=256
VMM_PAGE_SIZE=4096
VMM_TOTAL_PAGES=1024
VMM_REPLACEMENT_POLICY=CLOCK
VMM_ENABLE_AI=true
```

## Deployment Options

### Option 1: Development Deployment (Recommended for Testing)

**Linux/macOS:**
```bash
./deploy.sh deploy
```

**Windows:**
```cmd
deploy.bat deploy
```

**Manual:**
```bash
docker-compose up --build -d
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- AI Predictor: http://localhost:5000

### Option 2: Production Deployment

**Linux/macOS:**
```bash
./deploy.sh deploy-prod
```

**Windows:**
```cmd
deploy.bat deploy-prod
```

**Manual:**
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

**Access Points:**
- Frontend: http://localhost:80
- Backend API: http://localhost:80/api/
- AI Predictor: http://localhost:80/ai/

### Option 3: Local Development (Without Docker)

#### Start AI Predictor
```bash
cd predictor
pip install -r requirements.txt
python -m uvicorn predictor.service:app --host 0.0.0.0 --port 5000
```

#### Build and Start C++ Backend
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

#### Start React Frontend
```bash
cd frontend
npm install
npm run dev
```

## Management Commands

### Stop Services

**Linux/macOS:**
```bash
./deploy.sh stop
```

**Windows:**
```cmd
deploy.bat stop
```

**Manual:**
```bash
docker-compose down
```

### View Logs

**All services:**
```bash
./deploy.sh logs
# or
docker-compose logs -f
```

**Specific service:**
```bash
./deploy.sh logs backend
# or
docker-compose logs -f backend
```

### Health Checks

```bash
./deploy.sh health
# or
curl http://localhost:8080/metrics
curl http://localhost:5000/health
curl http://localhost:3000
```

### Cleanup

```bash
./deploy.sh cleanup
# or
docker-compose down --volumes --remove-orphans
docker image prune -f
```

## Production Configuration

### Environment Variables

For production deployment, configure these environment variables:

```bash
# Production settings
NODE_ENV=production
DEBUG=false
LOG_LEVEL=WARNING

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Database (if using persistent storage)
DATABASE_URL=postgresql://user:password@localhost:5432/vmm
REDIS_URL=redis://localhost:6379

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/vmm.crt
SSL_KEY_PATH=/etc/ssl/private/vmm.key
```

### SSL/TLS Configuration

1. **Generate SSL certificates:**
```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem
```

2. **Update nginx configuration:**
   - Uncomment the HTTPS server block in `nginx/nginx.conf`
   - Update certificate paths

3. **Deploy with SSL:**
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

### Reverse Proxy Configuration

The production setup includes Nginx as a reverse proxy with:
- **Load balancing** across multiple backend instances
- **SSL termination** for HTTPS
- **Rate limiting** for API protection
- **CORS headers** for cross-origin requests
- **Gzip compression** for better performance
- **Static file caching** for frontend assets

### Scaling

To scale individual services:

```bash
# Scale backend to 3 instances
docker-compose -f docker-compose.prod.yml up --scale backend=3 -d

# Scale AI predictor to 2 instances
docker-compose -f docker-compose.prod.yml up --scale predictor=2 -d
```

## Monitoring and Logging

### Log Files

Logs are stored in the `logs/` directory:
- `logs/backend.log` - Backend application logs
- `logs/predictor.log` - AI predictor logs
- `logs/nginx/access.log` - Nginx access logs
- `logs/nginx/error.log` - Nginx error logs

### Health Monitoring

The system includes health checks for all services:
- **Backend**: `GET /metrics` endpoint
- **AI Predictor**: `GET /health` endpoint
- **Frontend**: HTTP response check
- **Nginx**: `GET /health` endpoint

### Performance Monitoring

Monitor system performance using:
- **Docker stats**: `docker stats`
- **Resource usage**: Check CPU and memory usage
- **API response times**: Monitor `/metrics` endpoint
- **Error rates**: Check logs for error patterns

## Troubleshooting

### Common Issues

1. **Port conflicts:**
   - Check if ports 3000, 5000, 8080 are available
   - Update port configuration in `.env` file

2. **Docker build failures:**
   - Ensure Docker has enough memory (4GB+)
   - Check Docker daemon is running
   - Clear Docker cache: `docker system prune -a`

3. **Service connectivity:**
   - Verify all services are running: `docker-compose ps`
   - Check service logs: `docker-compose logs [service]`
   - Test individual endpoints with curl

4. **Permission issues (Linux/macOS):**
   - Make scripts executable: `chmod +x deploy.sh`
   - Check Docker permissions: `sudo usermod -aG docker $USER`

### Debug Mode

Enable debug logging:

```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Deploy with debug
./deploy.sh deploy
```

### Reset Everything

Complete system reset:

```bash
# Stop and remove everything
docker-compose down --volumes --remove-orphans
docker system prune -a

# Remove all images
docker rmi $(docker images -q)

# Start fresh
./deploy.sh deploy
```

## Security Considerations

### Production Security

1. **Change default passwords** in environment variables
2. **Use HTTPS** in production
3. **Configure firewall** to restrict access
4. **Regular security updates** for base images
5. **Monitor logs** for suspicious activity
6. **Use secrets management** for sensitive data

### Network Security

- Services communicate through Docker network
- External access only through Nginx reverse proxy
- Rate limiting prevents abuse
- CORS headers control cross-origin requests

## Backup and Recovery

### Data Backup

```bash
# Backup volumes
docker run --rm -v vmm_predictor_data:/data -v vmm_backend_data:/data2 \
    -v $(pwd)/backup:/backup alpine \
    tar czf /backup/vmm-backup-$(date +%Y%m%d).tar.gz /data /data2
```

### Recovery

```bash
# Restore from backup
docker run --rm -v vmm_predictor_data:/data -v vmm_backend_data:/data2 \
    -v $(pwd)/backup:/backup alpine \
    tar xzf /backup/vmm-backup-YYYYMMDD.tar.gz -C /
```

## Support

For issues and questions:
- Check the logs: `./deploy.sh logs`
- Run health checks: `./deploy.sh health`
- Review this documentation
- Create an issue on GitHub
