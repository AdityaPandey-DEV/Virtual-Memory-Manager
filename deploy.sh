#!/bin/bash

# Virtual Memory Manager Deployment Script
# This script handles deployment of the VMM system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="vmm"
COMPOSE_FILE="docker-compose.yml"
PROD_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Docker and Docker Compose are installed"
}

# Check if environment file exists
check_env() {
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment file $ENV_FILE not found"
        if [ -f "env.example" ]; then
            log_info "Copying env.example to $ENV_FILE"
            cp env.example $ENV_FILE
            log_warning "Please edit $ENV_FILE with your configuration before continuing"
        else
            log_error "No environment file found. Please create $ENV_FILE"
            exit 1
        fi
    else
        log_success "Environment file found"
    fi
}

# Build and start services
deploy_dev() {
    log_info "Deploying in development mode..."
    
    # Stop existing containers
    docker-compose -f $COMPOSE_FILE down 2>/dev/null || true
    
    # Build and start services
    docker-compose -f $COMPOSE_FILE up --build -d
    
    log_success "Development deployment completed"
    log_info "Services available at:"
    log_info "  Frontend: http://localhost:3000"
    log_info "  Backend: http://localhost:8080"
    log_info "  AI Predictor: http://localhost:5000"
}

# Deploy production
deploy_prod() {
    log_info "Deploying in production mode..."
    
    # Stop existing containers
    docker-compose -f $PROD_COMPOSE_FILE down 2>/dev/null || true
    
    # Create necessary directories
    mkdir -p logs nginx/ssl
    
    # Build and start services
    docker-compose -f $PROD_COMPOSE_FILE up --build -d
    
    log_success "Production deployment completed"
    log_info "Services available at:"
    log_info "  Frontend: http://localhost:80"
    log_info "  Backend API: http://localhost:80/api/"
    log_info "  AI Predictor: http://localhost:80/ai/"
}

# Stop services
stop_services() {
    log_info "Stopping all services..."
    
    # Stop development services
    docker-compose -f $COMPOSE_FILE down 2>/dev/null || true
    
    # Stop production services
    docker-compose -f $PROD_COMPOSE_FILE down 2>/dev/null || true
    
    log_success "All services stopped"
}

# Show logs
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        log_info "Showing logs for all services..."
        docker-compose -f $COMPOSE_FILE logs -f
    else
        log_info "Showing logs for $service..."
        docker-compose -f $COMPOSE_FILE logs -f $service
    fi
}

# Health check
health_check() {
    log_info "Performing health checks..."
    
    # Check if services are running
    if docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        log_success "Services are running"
        
        # Check individual services
        if curl -s http://localhost:8080/metrics > /dev/null; then
            log_success "Backend is healthy"
        else
            log_warning "Backend health check failed"
        fi
        
        if curl -s http://localhost:5000/health > /dev/null; then
            log_success "AI Predictor is healthy"
        else
            log_warning "AI Predictor health check failed"
        fi
        
        if curl -s http://localhost:3000 > /dev/null; then
            log_success "Frontend is healthy"
        else
            log_warning "Frontend health check failed"
        fi
    else
        log_error "No services are running"
    fi
}

# Clean up
cleanup() {
    log_info "Cleaning up..."
    
    # Remove containers
    docker-compose -f $COMPOSE_FILE down --volumes --remove-orphans 2>/dev/null || true
    docker-compose -f $PROD_COMPOSE_FILE down --volumes --remove-orphans 2>/dev/null || true
    
    # Remove images
    docker image prune -f
    
    log_success "Cleanup completed"
}

# Main script
case "${1:-deploy}" in
    "deploy")
        check_docker
        check_env
        deploy_dev
        ;;
    "deploy-prod")
        check_docker
        check_env
        deploy_prod
        ;;
    "stop")
        stop_services
        ;;
    "logs")
        show_logs $2
        ;;
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy      Deploy in development mode (default)"
        echo "  deploy-prod Deploy in production mode"
        echo "  stop        Stop all services"
        echo "  logs [service] Show logs (optionally for specific service)"
        echo "  health      Perform health checks"
        echo "  cleanup     Clean up containers and images"
        echo "  help        Show this help message"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac