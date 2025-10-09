# Environment Variables Analysis

## Current Status: ❌ NOT USING ENVIRONMENT VARIABLES

Your codebase is **NOT** currently using environment variables. All configuration is hardcoded.

## Issues Found

### 1. Backend (C++) - Hardcoded Values
```cpp
// In backend/src/main.cpp
vmm_config_.total_frames = 256;           // Should be VMM_TOTAL_FRAMES
vmm_config_.page_size = 4096;             // Should be VMM_PAGE_SIZE  
vmm_config_.total_pages = 1024;           // Should be VMM_TOTAL_PAGES
vmm_config_.ai_predictor_url = "http://localhost:5000/predict"; // Should be PREDICTOR_URL
server_ = std::make_unique<SimpleHTTPServer>(8080); // Should be BACKEND_PORT
```

### 2. Frontend (React) - Hardcoded URLs
```typescript
// In frontend/src/hooks/useSimulation.ts
const API_BASE = 'http://localhost:8080'; // Should be REACT_APP_BACKEND_URL

// In frontend/src/hooks/useMetrics.ts  
const API_BASE = 'http://localhost:8080'; // Should be REACT_APP_BACKEND_URL

// In frontend/src/hooks/useEventStream.ts
const API_BASE = 'http://localhost:8080'; // Should be REACT_APP_BACKEND_URL
```

### 3. AI Predictor (Python) - No Environment Variables
```python
# In predictor/service.py
# No environment variable usage found
# All configuration is hardcoded
```

## Required Fixes

### 1. Backend C++ - Add Environment Variable Support
Need to add environment variable reading in C++:
- Use `getenv()` function
- Add fallback to default values
- Update all hardcoded values

### 2. Frontend React - Use Environment Variables
Need to replace hardcoded URLs with environment variables:
- Use `import.meta.env.VITE_*` (Vite) or `process.env.REACT_APP_*` (Create React App)
- Update all API_BASE constants

### 3. AI Predictor Python - Add Environment Support
Need to add environment variable support:
- Use `os.getenv()` with defaults
- Add configuration loading

## Recommended Free Deployment Platforms

### 1. **Railway** (Recommended)
- **Free Tier**: $5/month credit (enough for small apps)
- **Pros**: Easy Docker deployment, automatic HTTPS, custom domains
- **Perfect for**: Full-stack applications with Docker
- **Deployment**: Connect GitHub repo, auto-deploy on push

### 2. **Render**
- **Free Tier**: 750 hours/month, sleeps after 15min inactivity
- **Pros**: Great for static sites and APIs, automatic deployments
- **Cons**: Cold starts, limited resources
- **Perfect for**: Frontend + Backend API

### 3. **Fly.io**
- **Free Tier**: 3 shared-cpu VMs, 256MB RAM each
- **Pros**: Global edge deployment, great performance
- **Perfect for**: Multi-service applications

### 4. **Heroku** (Limited Free Tier)
- **Free Tier**: Discontinued, but has low-cost options
- **Pros**: Easy deployment, add-ons ecosystem
- **Cons**: No longer free

### 5. **Vercel** (Frontend Only)
- **Free Tier**: Unlimited static sites
- **Pros**: Excellent for React apps, automatic deployments
- **Cons**: Only frontend, need separate backend hosting

### 6. **Netlify** (Frontend Only)
- **Free Tier**: 100GB bandwidth, 300 build minutes
- **Pros**: Great for static sites, form handling
- **Cons**: Only frontend, need separate backend hosting

## Recommended Deployment Strategy

### Option 1: Railway (Full Stack)
```yaml
# Deploy all services together
- Frontend: React app
- Backend: C++ API  
- AI Predictor: Python FastAPI
- Database: PostgreSQL (if needed)
```

### Option 2: Split Deployment
```yaml
# Frontend: Vercel/Netlify
- React app on Vercel
- Automatic deployments from GitHub

# Backend: Railway/Render
- C++ backend on Railway
- Python AI predictor on Railway
- Connect via environment variables
```

## Next Steps

1. **Fix Environment Variables** (Required before deployment)
2. **Choose Deployment Platform** (Railway recommended)
3. **Configure CI/CD** (GitHub Actions)
4. **Set up Monitoring** (Health checks, logs)
5. **Configure Custom Domain** (Optional)

## Priority Order

1. ✅ **Fix environment variables in code** (CRITICAL)
2. ✅ **Test locally with .env file**
3. ✅ **Deploy to Railway**
4. ✅ **Configure custom domain**
5. ✅ **Set up monitoring**
