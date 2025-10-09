# Deploy Virtual Memory Manager to Render

## Overview

This guide shows how to deploy your Virtual Memory Manager to Render's free tier. Render provides:
- **Free tier**: 750 hours/month, sleeps after 15min inactivity
- **Automatic deployments** from GitHub
- **Custom domains** (free)
- **SSL certificates** (automatic)

## Prerequisites

1. **GitHub repository** with your code
2. **Render account** (free)
3. **Environment variables** configured

## Deployment Steps

### 1. Prepare Your Repository

Make sure your repository has:
- ✅ Environment variables fixed (already done)
- ✅ `render.yaml` configuration file
- ✅ `backend/Dockerfile` for C++ backend
- ✅ All source code committed

### 2. Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Connect your GitHub account

### 3. Deploy Services

#### Option A: Using render.yaml (Recommended)

1. **Go to Render Dashboard**
   - Click "New +"
   - Select "Blueprint"

2. **Connect Repository**
   - Select your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Deploy**
   - Click "Apply"
   - Render will create all 3 services automatically

#### Option B: Manual Deployment

Deploy each service individually:

#### 3.1 Deploy AI Predictor (Python)

1. **Create Web Service**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**
   ```
   Name: vmm-predictor
   Environment: Python
   Build Command: pip install -r predictor/requirements.txt
   Start Command: cd predictor && python -m uvicorn predictor.service:app --host 0.0.0.0 --port $PORT
   ```

3. **Environment Variables**
   ```
   PREDICTOR_HOST=0.0.0.0
   PREDICTOR_PORT=5000
   LOG_LEVEL=INFO
   MODEL_PATH=model.pkl
   AI_MODEL_TYPE=xgboost
   AI_PREDICTION_THRESHOLD=0.7
   ```

#### 3.2 Deploy C++ Backend

1. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**
   ```
   Name: vmm-backend
   Environment: Docker
   Dockerfile Path: ./backend/Dockerfile
   ```

3. **Environment Variables**
   ```
   BACKEND_PORT=8080
   BACKEND_HOST=0.0.0.0
   PREDICTOR_URL=https://vmm-predictor.onrender.com
   VMM_TOTAL_FRAMES=256
   VMM_PAGE_SIZE=4096
   VMM_TOTAL_PAGES=1024
   VMM_REPLACEMENT_POLICY=CLOCK
   VMM_ENABLE_AI=true
   LOG_LEVEL=INFO
   ```

#### 3.3 Deploy React Frontend

1. **Create Static Site**
   - Click "New +" → "Static Site"
   - Connect your GitHub repository

2. **Configure Build**
   ```
   Build Command: cd frontend && npm install && npm run build
   Publish Directory: frontend/dist
   ```

3. **Environment Variables**
   ```
   NODE_ENV=production
   VITE_BACKEND_URL=https://vmm-backend.onrender.com
   ```

## Environment Variables Reference

### Frontend (React)
```bash
NODE_ENV=production
VITE_BACKEND_URL=https://your-backend-url.onrender.com
VITE_FRONTEND_PORT=3000
```

### Backend (C++)
```bash
BACKEND_PORT=8080
BACKEND_HOST=0.0.0.0
PREDICTOR_URL=https://your-predictor-url.onrender.com
VMM_TOTAL_FRAMES=256
VMM_PAGE_SIZE=4096
VMM_TOTAL_PAGES=1024
VMM_REPLACEMENT_POLICY=CLOCK
VMM_ENABLE_AI=true
LOG_LEVEL=INFO
```

### AI Predictor (Python)
```bash
PREDICTOR_HOST=0.0.0.0
PREDICTOR_PORT=5000
LOG_LEVEL=INFO
MODEL_PATH=model.pkl
AI_MODEL_TYPE=xgboost
AI_PREDICTION_THRESHOLD=0.7
```

## Service URLs

After deployment, you'll get URLs like:
- **Frontend**: `https://vmm-frontend.onrender.com`
- **Backend**: `https://vmm-backend.onrender.com`
- **AI Predictor**: `https://vmm-predictor.onrender.com`

## Custom Domain (Optional)

1. **Add Custom Domain**
   - Go to your service settings
   - Click "Custom Domains"
   - Add your domain (e.g., `vmm.yourdomain.com`)

2. **Configure DNS**
   - Add CNAME record pointing to your Render URL
   - Render will automatically provision SSL

## Monitoring and Logs

### View Logs
1. Go to your service dashboard
2. Click "Logs" tab
3. View real-time logs

### Health Checks
- **Backend**: `GET /metrics`
- **AI Predictor**: `GET /health`
- **Frontend**: Static file serving

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check build logs in Render dashboard
   - Ensure all dependencies are in requirements.txt/package.json
   - Verify Dockerfile syntax

2. **Service Not Starting**
   - Check start command
   - Verify environment variables
   - Check service logs

3. **Connection Issues**
   - Ensure services are using correct URLs
   - Check CORS settings
   - Verify environment variables are set

### Debug Commands

```bash
# Check service status
curl https://your-backend-url.onrender.com/metrics

# Check AI predictor
curl https://your-predictor-url.onrender.com/health

# Check frontend
curl https://your-frontend-url.onrender.com
```

## Cost Optimization

### Free Tier Limits
- **750 hours/month** per service
- **Sleeps after 15 minutes** of inactivity
- **Cold starts** when waking up

### Tips to Stay Free
1. **Combine services** where possible
2. **Use static site** for frontend (no cold starts)
3. **Optimize build times**
4. **Monitor usage** in dashboard

## Scaling

### Upgrade to Paid Plans
- **Starter**: $7/month per service
- **Standard**: $25/month per service
- **Pro**: $85/month per service

### Benefits of Paid Plans
- **No sleep** (always running)
- **More resources** (CPU, RAM)
- **Faster builds**
- **Priority support**

## Security

### Environment Variables
- **Never commit** `.env` files
- **Use Render's** environment variable system
- **Rotate secrets** regularly

### HTTPS
- **Automatic SSL** certificates
- **Force HTTPS** redirects
- **Secure headers** configured

## Backup and Recovery

### Database (if added)
- **Automatic backups** on paid plans
- **Manual exports** available
- **Point-in-time recovery**

### Code
- **GitHub integration** for version control
- **Automatic deployments** on push
- **Rollback** to previous versions

## Support

- **Documentation**: [render.com/docs](https://render.com/docs)
- **Community**: [render.com/community](https://render.com/community)
- **Support**: Available on paid plans

## Next Steps

1. ✅ **Deploy to Render** using this guide
2. ✅ **Test all services** are working
3. ✅ **Configure custom domain** (optional)
4. ✅ **Set up monitoring** and alerts
5. ✅ **Optimize performance** for production
