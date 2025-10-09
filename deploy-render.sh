#!/bin/bash

# Virtual Memory Manager - Render Deployment Script
# This script helps prepare your project for Render deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in the right directory
check_project_structure() {
    log_info "Checking project structure..."
    
    if [ ! -f "render.yaml" ]; then
        log_error "render.yaml not found. Make sure you're in the project root."
        exit 1
    fi
    
    if [ ! -d "frontend" ]; then
        log_error "frontend directory not found."
        exit 1
    fi
    
    if [ ! -d "backend" ]; then
        log_error "backend directory not found."
        exit 1
    fi
    
    if [ ! -d "predictor" ]; then
        log_error "predictor directory not found."
        exit 1
    fi
    
    log_success "Project structure looks good!"
}

# Check if environment variables are configured
check_env_vars() {
    log_info "Checking environment variable usage..."
    
    # Check frontend files
    if grep -q "import.meta.env.VITE_BACKEND_URL" frontend/src/hooks/useSimulation.ts; then
        log_success "Frontend using environment variables"
    else
        log_warning "Frontend may not be using environment variables properly"
    fi
    
    # Check predictor files
    if grep -q "os.getenv" predictor/service.py; then
        log_success "AI Predictor using environment variables"
    else
        log_warning "AI Predictor may not be using environment variables properly"
    fi
    
    log_info "Environment variable check completed"
}

# Test local build
test_local_build() {
    log_info "Testing local build..."
    
    # Test frontend build
    log_info "Building frontend..."
    cd frontend
    if npm install && npm run build; then
        log_success "Frontend build successful"
    else
        log_error "Frontend build failed"
        exit 1
    fi
    cd ..
    
    # Test backend build (if possible)
    if command -v cmake &> /dev/null; then
        log_info "Testing backend build..."
        cd backend
        if mkdir -p build && cd build && cmake .. && make; then
            log_success "Backend build successful"
        else
            log_warning "Backend build failed (this is expected on some systems)"
        fi
        cd ../..
    else
        log_warning "CMake not available, skipping backend build test"
    fi
    
    # Test Python dependencies
    log_info "Testing Python dependencies..."
    cd predictor
    if pip install -r requirements.txt; then
        log_success "Python dependencies installed successfully"
    else
        log_error "Python dependencies installation failed"
        exit 1
    fi
    cd ..
}

# Create deployment checklist
create_checklist() {
    log_info "Creating deployment checklist..."
    
    cat > DEPLOYMENT_CHECKLIST.md << EOF
# Render Deployment Checklist

## Pre-Deployment Checklist

### ✅ Code Preparation
- [ ] All code committed to GitHub
- [ ] Environment variables configured
- [ ] Frontend build tested locally
- [ ] Backend Dockerfile created
- [ ] Python dependencies working

### ✅ Render Account Setup
- [ ] Render account created
- [ ] GitHub connected to Render
- [ ] Repository access granted

### ✅ Service Configuration
- [ ] render.yaml file configured
- [ ] Environment variables documented
- [ ] Service URLs planned

## Deployment Steps

### 1. Deploy AI Predictor
- [ ] Create Web Service in Render
- [ ] Set environment: Python
- [ ] Configure build command: \`pip install -r predictor/requirements.txt\`
- [ ] Configure start command: \`cd predictor && python -m uvicorn predictor.service:app --host 0.0.0.0 --port \$PORT\`
- [ ] Set environment variables
- [ ] Deploy and test

### 2. Deploy C++ Backend
- [ ] Create Web Service in Render
- [ ] Set environment: Docker
- [ ] Configure Dockerfile path: \`./backend/Dockerfile\`
- [ ] Set environment variables (including predictor URL)
- [ ] Deploy and test

### 3. Deploy React Frontend
- [ ] Create Static Site in Render
- [ ] Configure build command: \`cd frontend && npm install && npm run build\`
- [ ] Configure publish directory: \`frontend/dist\`
- [ ] Set environment variables (including backend URL)
- [ ] Deploy and test

## Post-Deployment Testing

### Health Checks
- [ ] Frontend loads: \`https://your-frontend.onrender.com\`
- [ ] Backend API: \`https://your-backend.onrender.com/metrics\`
- [ ] AI Predictor: \`https://your-predictor.onrender.com/health\`

### Integration Testing
- [ ] Frontend can connect to backend
- [ ] Backend can connect to AI predictor
- [ ] All services respond correctly
- [ ] Real-time features working (SSE)

## Environment Variables Reference

### Frontend
\`\`\`bash
NODE_ENV=production
VITE_BACKEND_URL=https://your-backend.onrender.com
\`\`\`

### Backend
\`\`\`bash
BACKEND_PORT=8080
BACKEND_HOST=0.0.0.0
PREDICTOR_URL=https://your-predictor.onrender.com
VMM_TOTAL_FRAMES=256
VMM_PAGE_SIZE=4096
VMM_TOTAL_PAGES=1024
VMM_REPLACEMENT_POLICY=CLOCK
VMM_ENABLE_AI=true
LOG_LEVEL=INFO
\`\`\`

### AI Predictor
\`\`\`bash
PREDICTOR_HOST=0.0.0.0
PREDICTOR_PORT=5000
LOG_LEVEL=INFO
MODEL_PATH=model.pkl
AI_MODEL_TYPE=xgboost
AI_PREDICTION_THRESHOLD=0.7
\`\`\`

## Troubleshooting

### Common Issues
1. **Build Failures**: Check build logs in Render dashboard
2. **Connection Issues**: Verify environment variables and URLs
3. **Service Not Starting**: Check start commands and dependencies
4. **Cold Starts**: Services sleep after 15min inactivity (free tier)

### Debug Commands
\`\`\`bash
# Test backend
curl https://your-backend.onrender.com/metrics

# Test AI predictor
curl https://your-predictor.onrender.com/health

# Test frontend
curl https://your-frontend.onrender.com
\`\`\`

## Support Resources
- [Render Documentation](https://render.com/docs)
- [Render Community](https://render.com/community)
- [GitHub Issues](https://github.com/AdityaPandey-DEV/Virtual-Memory-Manager/issues)
EOF

    log_success "Deployment checklist created: DEPLOYMENT_CHECKLIST.md"
}

# Main execution
main() {
    log_info "🚀 Preparing Virtual Memory Manager for Render deployment..."
    
    check_project_structure
    check_env_vars
    test_local_build
    create_checklist
    
    log_success "✅ Project is ready for Render deployment!"
    log_info "📋 Next steps:"
    log_info "1. Review DEPLOYMENT_CHECKLIST.md"
    log_info "2. Go to https://render.com"
    log_info "3. Create new Web Service"
    log_info "4. Connect your GitHub repository"
    log_info "5. Follow the deployment checklist"
    
    log_info "📖 For detailed instructions, see RENDER_DEPLOYMENT.md"
}

# Run main function
main "$@"
