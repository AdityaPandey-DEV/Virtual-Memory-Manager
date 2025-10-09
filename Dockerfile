# Multi-stage build for Virtual Memory Manager
FROM node:18-alpine AS frontend-builder

# Build frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Python AI Predictor stage
FROM python:3.11-slim AS predictor

WORKDIR /app/predictor
COPY predictor/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY predictor/ ./

# C++ Backend stage
FROM ubuntu:22.04 AS backend-builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY backend/ ./
RUN mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    cmake --build . --config Release

# Final production stage
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    nodejs \
    npm \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy built applications
COPY --from=frontend-builder /app/frontend/dist /var/www/html
COPY --from=predictor /app/predictor /app/predictor
COPY --from=backend-builder /app/backend/build/bin/Release/vmm_simulator /app/backend/vmm_simulator

# Install Python dependencies
WORKDIR /app/predictor
RUN pip3 install --no-cache-dir -r requirements.txt

# Create startup script
RUN echo '#!/bin/bash\n\
# Start AI Predictor\n\
cd /app/predictor && python3 -m uvicorn predictor.service:app --host 0.0.0.0 --port 5000 &\n\
\n\
# Start C++ Backend\n\
cd /app/backend && ./vmm_simulator &\n\
\n\
# Start Nginx\n\
nginx -g "daemon off;"' > /app/start.sh && chmod +x /app/start.sh

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Expose ports
EXPOSE 80 8080 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Start all services
CMD ["/app/start.sh"]
