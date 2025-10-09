# Production Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying the AI-Enhanced Virtual Memory Manager system in production environments.

## Architecture

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
                    │   Port: 80/443   │
                    └─────────────────┘
```

## Production Deployment Options

### Option 1: Docker Compose (Recommended for Small-Medium Scale)

#### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 2+ CPU cores

#### Deployment Steps
```bash
# 1. Clone repository
git clone <repository-url>
cd virtual-memory-manager

# 2. Deploy with Docker Compose
./deploy.sh  # Linux/macOS
# or
deploy.bat   # Windows

# 3. Verify deployment
python test_connectivity.py
```

#### Environment Variables
Create `.env` file:
```env
# AI Predictor Configuration
PREDICTOR_MODEL_PATH=/app/models
PREDICTOR_HOST=0.0.0.0
PREDICTOR_PORT=5000

# Backend Configuration
VMM_LOG_LEVEL=INFO
VMM_PREDICTOR_ENABLED=true
VMM_PREDICTOR_URL=http://predictor:5000/predict

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8080
REACT_APP_PREDICTOR_URL=http://localhost:5000

# Redis Configuration
REDIS_URL=redis://redis:6379
```

### Option 2: Kubernetes (Recommended for Large Scale)

#### Prerequisites
- Kubernetes cluster 1.20+
- kubectl configured
- Helm 3.0+ (optional)

#### Kubernetes Manifests

**namespace.yaml**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vmm-system
```

**configmap.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vmm-config
  namespace: vmm-system
data:
  PREDICTOR_HOST: "0.0.0.0"
  PREDICTOR_PORT: "5000"
  VMM_LOG_LEVEL: "INFO"
  VMM_PREDICTOR_ENABLED: "true"
```

**predictor-deployment.yaml**
```yaml
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
        - name: PREDICTOR_HOST
          valueFrom:
            configMapKeyRef:
              name: vmm-config
              key: PREDICTOR_HOST
        - name: PREDICTOR_PORT
          valueFrom:
            configMapKeyRef:
              name: vmm-config
              key: PREDICTOR_PORT
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
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

**backend-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: vmm-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: vmm-backend:latest
        ports:
        - containerPort: 8080
        env:
        - name: VMM_LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: vmm-config
              key: VMM_LOG_LEVEL
        - name: VMM_PREDICTOR_ENABLED
          valueFrom:
            configMapKeyRef:
              name: vmm-config
              key: VMM_PREDICTOR_ENABLED
        - name: VMM_PREDICTOR_URL
          value: "http://predictor-service:5000/predict"
        livenessProbe:
          httpGet:
            path: /metrics
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /metrics
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: vmm-system
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

**frontend-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: vmm-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: vmm-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_API_URL
          value: "http://backend-service:8080"
        - name: REACT_APP_PREDICTOR_URL
          value: "http://predictor-service:5000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: vmm-system
spec:
  selector:
    app: frontend
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
```

**ingress.yaml**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vmm-ingress
  namespace: vmm-system
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: vmm.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8080
      - path: /predictor
        pathType: Prefix
        backend:
          service:
            name: predictor-service
            port:
              number: 5000
```

#### Kubernetes Deployment Commands
```bash
# Apply all manifests
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f predictor-deployment.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml

# Check deployment status
kubectl get pods -n vmm-system
kubectl get services -n vmm-system
kubectl get ingress -n vmm-system

# View logs
kubectl logs -f deployment/predictor -n vmm-system
kubectl logs -f deployment/backend -n vmm-system
kubectl logs -f deployment/frontend -n vmm-system
```

### Option 3: Cloud Deployment

#### AWS ECS with Fargate
```yaml
# ecs-task-definition.json
{
  "family": "vmm-system",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "predictor",
      "image": "your-account.dkr.ecr.region.amazonaws.com/vmm-predictor:latest",
      "portMappings": [{"containerPort": 5000}],
      "environment": [
        {"name": "PREDICTOR_HOST", "value": "0.0.0.0"},
        {"name": "PREDICTOR_PORT", "value": "5000"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

#### Google Cloud Run
```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: vmm-system
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        autoscaling.knative.dev/minScale: "1"
    spec:
      containers:
      - image: gcr.io/your-project/vmm-system:latest
        ports:
        - containerPort: 8080
        env:
        - name: VMM_PREDICTOR_URL
          value: "http://predictor-service:5000/predict"
        resources:
          limits:
            cpu: "2000m"
            memory: "4Gi"
```

## Production Configuration

### Environment Variables
```bash
# AI Predictor
PREDICTOR_MODEL_PATH=/app/models
PREDICTOR_HOST=0.0.0.0
PREDICTOR_PORT=5000
PREDICTOR_WORKERS=4

# Backend
VMM_LOG_LEVEL=INFO
VMM_PREDICTOR_ENABLED=true
VMM_PREDICTOR_URL=http://predictor:5000/predict
VMM_TOTAL_FRAMES=1024
VMM_PAGE_SIZE=4096
VMM_TOTAL_PAGES=4096

# Frontend
REACT_APP_API_URL=http://backend:8080
REACT_APP_PREDICTOR_URL=http://predictor:5000
REACT_APP_ENVIRONMENT=production

# Redis
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=your-redis-password

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true
GRAFANA_PORT=3001
```

### Security Considerations

#### 1. Network Security
```yaml
# Network policies for Kubernetes
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vmm-network-policy
  namespace: vmm-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: vmm-system
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: vmm-system
```

#### 2. Secrets Management
```yaml
# Kubernetes secrets
apiVersion: v1
kind: Secret
metadata:
  name: vmm-secrets
  namespace: vmm-system
type: Opaque
data:
  redis-password: <base64-encoded-password>
  api-key: <base64-encoded-api-key>
```

#### 3. SSL/TLS Configuration
```yaml
# TLS certificate
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: vmm-tls
  namespace: vmm-system
spec:
  secretName: vmm-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - vmm.yourdomain.com
```

### Monitoring and Logging

#### 1. Prometheus Configuration
```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
scrape_configs:
- job_name: 'vmm-backend'
  static_configs:
  - targets: ['backend-service:8080']
  metrics_path: '/metrics'
- job_name: 'vmm-predictor'
  static_configs:
  - targets: ['predictor-service:5000']
  metrics_path: '/metrics'
```

#### 2. Grafana Dashboard
```json
{
  "dashboard": {
    "title": "VMM System Metrics",
    "panels": [
      {
        "title": "Page Fault Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(vmm_page_faults_total[5m])",
            "legendFormat": "Page Faults/sec"
          }
        ]
      },
      {
        "title": "AI Prediction Accuracy",
        "type": "stat",
        "targets": [
          {
            "expr": "vmm_ai_hit_rate",
            "legendFormat": "AI Hit Rate"
          }
        ]
      }
    ]
  }
}
```

#### 3. Log Aggregation
```yaml
# Fluentd configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: vmm-system
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*vmm*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
    </source>
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name vmm-logs
    </match>
```

### Scaling Recommendations

#### 1. Horizontal Pod Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: predictor-hpa
  namespace: vmm-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: predictor
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### 2. Vertical Pod Autoscaling
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: backend-vpa
  namespace: vmm-system
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  updatePolicy:
    updateMode: "Auto"
```

### Backup and Disaster Recovery

#### 1. Database Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/vmm"
mkdir -p $BACKUP_DIR

# Backup Redis data
redis-cli --rdb $BACKUP_DIR/redis_$DATE.rdb

# Backup model files
cp -r /app/models $BACKUP_DIR/models_$DATE

# Upload to S3
aws s3 cp $BACKUP_DIR s3://your-backup-bucket/vmm/$DATE/ --recursive
```

#### 2. Disaster Recovery Plan
1. **RTO (Recovery Time Objective)**: 15 minutes
2. **RPO (Recovery Point Objective)**: 5 minutes
3. **Backup Frequency**: Every 6 hours
4. **Retention Period**: 30 days

### Performance Optimization

#### 1. Resource Limits
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

#### 2. Caching Strategy
- **Redis Cache**: 1GB for prediction results
- **CDN**: Static assets (JS, CSS, images)
- **Browser Cache**: 24 hours for API responses

#### 3. Database Optimization
- **Connection Pooling**: 20 connections per service
- **Query Optimization**: Indexed on frequently accessed fields
- **Read Replicas**: 2 read replicas for read-heavy workloads

## Troubleshooting

### Common Issues

#### 1. Service Discovery Issues
```bash
# Check DNS resolution
kubectl exec -it deployment/backend -- nslookup predictor-service

# Check service endpoints
kubectl get endpoints -n vmm-system
```

#### 2. Memory Issues
```bash
# Check memory usage
kubectl top pods -n vmm-system

# Check for memory leaks
kubectl exec -it deployment/backend -- ps aux
```

#### 3. Network Connectivity
```bash
# Test internal connectivity
kubectl exec -it deployment/backend -- curl http://predictor-service:5000/health

# Check network policies
kubectl get networkpolicies -n vmm-system
```

### Health Checks
```bash
# System health check script
#!/bin/bash
echo "Checking VMM System Health..."

# Check predictor
curl -f http://localhost:5000/health || echo "Predictor unhealthy"

# Check backend
curl -f http://localhost:8080/metrics || echo "Backend unhealthy"

# Check frontend
curl -f http://localhost:3000 || echo "Frontend unhealthy"

# Check Redis
redis-cli ping || echo "Redis unhealthy"
```

## Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Update dependencies
2. **Monthly**: Security patches
3. **Quarterly**: Performance review
4. **Annually**: Architecture review

### Monitoring Alerts
- **High CPU Usage**: >80% for 5 minutes
- **High Memory Usage**: >90% for 5 minutes
- **High Error Rate**: >5% for 2 minutes
- **Service Down**: Any service unavailable

This production deployment guide provides a comprehensive framework for deploying the VMM system at scale with proper monitoring, security, and maintenance procedures.

