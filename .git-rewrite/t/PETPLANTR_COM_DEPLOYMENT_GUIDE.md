# 🌐 PetPlantr.com Production Deployment Guide

## 🚀 **Domain Setup & Production Deployment**

### **Production URLs**
- **Frontend**: `https://petplantr.com`
- **API**: `https://api.petplantr.com`
- **CDN**: `https://cdn.petplantr.com` (optional)

---

## 📋 **Pre-Deployment Checklist**

### ✅ **1. DNS Configuration**
```bash
# A Records
petplantr.com           → [Frontend Server IP]
www.petplantr.com       → [Frontend Server IP] 
api.petplantr.com       → [API Server IP]

# Optional CDN
cdn.petplantr.com       → [CDN Endpoint]
```

### ✅ **2. SSL Certificates**
```bash
# Using Let's Encrypt or CloudFlare
certbot certonly --nginx -d petplantr.com -d www.petplantr.com
certbot certonly --nginx -d api.petplantr.com
```

### ✅ **3. Environment Configuration**
Production environment files are ready:
- ✅ `frontend/.env.production` - Configured for petplantr.com
- ✅ `api_server_minimal.py` - CORS origins include petplantr.com

---

## 🖥️ **Server Deployment**

### **Frontend Deployment (petplantr.com)**
```bash
# Build production frontend
cd frontend
npm run build
npm run start

# Or using PM2 for production
pm2 start npm --name "petplantr-frontend" -- start
```

### **API Deployment (api.petplantr.com)**
```bash
# Production API with SSL and multiple workers
uvicorn api_server_minimal:app \
  --host 0.0.0.0 \
  --port 443 \
  --ssl-keyfile /etc/ssl/private/api.petplantr.com.key \
  --ssl-certfile /etc/ssl/certs/api.petplantr.com.crt \
  --workers 4 \
  --access-log

# Or using Gunicorn + Nginx reverse proxy
gunicorn api_server_minimal:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

---

## 🐳 **Docker Deployment**

### **Production Docker Compose**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:3000"
      - "443:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=https://api.petplantr.com
      - NEXT_PUBLIC_ENVIRONMENT=production
    volumes:
      - /etc/ssl:/etc/ssl:ro

  api:
    build:
      context: .
      dockerfile: Dockerfile.production
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=production
      - ENABLE_PRODUCTION_AI=true
      - PETPLANTR_MODEL_DIR=/app/models
    volumes:
      - ./models:/app/models
      - /etc/ssl:/etc/ssl:ro

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - /etc/ssl:/etc/ssl:ro
    depends_on:
      - frontend
      - api
```

---

## ☁️ **Cloud Deployment Options**

### **Option 1: Vercel + Railway**
```bash
# Frontend on Vercel
vercel --prod

# API on Railway
railway login
railway deploy
```

### **Option 2: AWS ECS/EKS**
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: petplantr-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: petplantr-api
  template:
    metadata:
      labels:
        app: petplantr-api
    spec:
      containers:
      - name: api
        image: petplantr/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: NODE_ENV
          value: "production"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 5
```

### **Option 3: DigitalOcean App Platform**
```yaml
# .do/app.yaml
name: petplantr
services:
- name: frontend
  source_dir: /frontend
  github:
    repo: your-org/petplantr
    branch: main
  run_command: npm start
  environment_slug: node-js
  instance_count: 2
  instance_size_slug: basic-xxs
  envs:
  - key: NEXT_PUBLIC_API_BASE_URL
    value: https://api.petplantr.com

- name: api
  source_dir: /
  github:
    repo: your-org/petplantr
    branch: main
  run_command: uvicorn api_server_minimal:app --host 0.0.0.0 --port 8080 --workers 2
  environment_slug: python
  instance_count: 2
  instance_size_slug: basic-xxs
  envs:
  - key: NODE_ENV
    value: production
```

---

## 📊 **Production Monitoring**

### **Health Check URLs**
```bash
# Liveness probes
curl https://petplantr.com/api/health
curl https://api.petplantr.com/healthz

# Readiness probes  
curl https://api.petplantr.com/readyz

# Metrics endpoint
curl https://api.petplantr.com/metrics
```

### **Monitoring Stack**
```bash
# Prometheus scraping
scrape_configs:
  - job_name: 'petplantr-api'
    static_configs:
      - targets: ['api.petplantr.com:443']
    metrics_path: '/metrics'
    scheme: https

# Grafana dashboard queries
rate(petplantr_http_requests_total[5m])
histogram_quantile(0.95, petplantr_request_latency_seconds)
petplantr_successful_generations_total
```

---

## 🚦 **Deployment Validation**

```bash
#!/bin/bash
# validate-petplantr-production.sh

echo "🌐 Validating PetPlantr.com Production Deployment"
echo "================================================="

# Check DNS resolution
echo "🔍 DNS Check:"
nslookup petplantr.com
nslookup api.petplantr.com

# Check SSL certificates
echo "🔒 SSL Check:"
openssl s_client -connect petplantr.com:443 -servername petplantr.com < /dev/null
openssl s_client -connect api.petplantr.com:443 -servername api.petplantr.com < /dev/null

# Check service health
echo "🏥 Health Check:"
curl -f https://petplantr.com/api/health
curl -f https://api.petplantr.com/healthz
curl -f https://api.petplantr.com/readyz

# Test end-to-end workflow
echo "🎯 E2E Test:"
curl -X POST "https://api.petplantr.com/api/v1/generate-enhanced-3d-simple" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "image_url=data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD//2Q==" \
  -d "quality_level=ultra"

echo "✅ Production validation complete!"
```

---

## 🎯 **Go-Live Checklist**

- [ ] DNS records configured and propagated
- [ ] SSL certificates installed and valid
- [ ] Environment variables set for production
- [ ] Database migrations completed
- [ ] CDN configured (if using)
- [ ] Monitoring dashboards set up
- [ ] Backup procedures in place
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Performance optimization verified

---

**🚀 PetPlantr is ready for petplantr.com deployment!**

All configuration files, monitoring, and deployment options are prepared for a successful production launch.
