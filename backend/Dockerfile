# C++ Backend Dockerfile for Render
FROM ubuntu:22.04

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy source code
COPY . .

# Build the application
RUN mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    cmake --build . --config Release

# Create startup script
RUN echo '#!/bin/bash\n\
# Start the VMM simulator\n\
cd /app/build/bin/Release && ./vmm_simulator' > /app/start.sh && \
    chmod +x /app/start.sh

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/metrics || exit 1

# Start the application
CMD ["/app/start.sh"]