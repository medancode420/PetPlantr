# PetPlantr Production Deployment Guide

## Overview
This guide covers the complete production deployment of PetPlantr, including infrastructure setup, security configuration, monitoring, and scaling.

## Prerequisites

### System Requirements
- Ubuntu 20.04+ or CentOS 7+
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum, 8GB recommended
- 20GB disk space
- Domain name with DNS access

### Network Requirements
- Ports 80, 443 (HTTP/HTTPS)
- Ports 8000, 8443 (API)
- Port 6379 (Redis - internal)
- Ports 9090, 3000, 9100, 9093 (monitoring - optional)

## Quick Start Deployment

### 1. Clone and Setup
```bash
git clone <repository-url>
cd petplantr
chmod +x deploy-production.sh setup-monitoring.sh
```

### 2. Configure Environment
```bash
# Copy environment templates
cp .env.production.template .env.production
cp .env.security.template .env.security

# Edit with your values
nano .env.production
nano .env.security
```

### 3. Setup SSL Certificates
```bash
# For production SSL (Let's Encrypt)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates to security directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./security/ssl/certs/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./security/ssl/private/
sudo cp /etc/letsencrypt/ssl-dhparams.pem ./security/ssl/

# Set proper permissions
sudo chown -R $USER:$USER ./security/ssl/
chmod 600 ./security/ssl/private/privkey.pem
```

### 4. Deploy Production Stack
```bash
# Run production deployment
./deploy-production.sh --tag v1.0.0

# Optional: Setup monitoring
./setup-monitoring.sh
docker compose -f docker-compose.monitoring.yml up -d
```

### 5. Verify Deployment
```bash
# Check service status
docker compose ps

# Test API endpoints
curl -f https://yourdomain.com/api/v1/health
curl -f https://yourdomain.com/api/docs

# Check monitoring (if enabled)
curl -f http://localhost:3000  # Grafana
curl -f http://localhost:9090  # Prometheus
```

## Detailed Configuration

### Environment Variables

#### Production Environment (.env.production)
```bash
# Application
NODE_ENV=production
ENABLE_PRODUCTION_AI=true

# Security
JWT_SECRET=your-secure-jwt-secret-32-chars-minimum
API_KEY=your-production-api-key

# Database/Cache
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=secure-redis-password

# SSL
SSL_CERT_PATH=/app/security/ssl/certs/fullchain.pem
SSL_KEY_PATH=/app/security/ssl/private/privkey.pem

# Monitoring
LOG_LEVEL=INFO
ENABLE_PROMETHEUS_METRICS=true
```

#### Security Environment (.env.security)
```bash
# JWT Configuration
JWT_SECRET_KEY=your-256-bit-jwt-secret
JWT_ALGORITHM=HS256

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Security Headers
SECURITY_HSTS_MAX_AGE=31536000
```

### SSL/TLS Setup

#### Option 1: Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Setup auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Option 2: Self-Signed (Development/Testing)
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
mv cert.pem ./security/ssl/certs/
mv key.pem ./security/ssl/private/

# Generate DH parameters
openssl dhparam -out ./security/ssl/dhparam.pem 2048
```

### NGINX Configuration

Create `./security/ssl/nginx_ssl.conf`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;
    ssl_dhparam /etc/ssl/dhparam.pem;

    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to PetPlantr API
    location / {
        proxy_pass http://petplantr:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Monitoring Setup

### Prometheus Metrics
The API exposes metrics at `/api/v1/metrics`:
- HTTP request metrics
- Response time histograms
- Error rates
- Custom business metrics

### Grafana Dashboards
Pre-configured dashboards include:
- API Performance Overview
- Error Rate Monitoring
- Resource Usage
- User Activity Analytics

### Alerting Rules
Default alerts for:
- Service downtime
- High response times
- Error rate spikes
- Resource exhaustion

## Scaling Configuration

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
services:
  petplantr:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Load Balancing
```nginx
upstream petplantr_backend {
    server petplantr-1:8000;
    server petplantr-2:8000;
    server petplantr-3:8000;
}

server {
    location / {
        proxy_pass http://petplantr_backend;
    }
}
```

## Backup and Recovery

### Automated Backups
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/petplantr/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database/redis data
docker run --rm -v petplantr_redis_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/redis_$DATE.tar.gz -C /data .

# Backup application data
docker run --rm -v petplantr_uploads:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/uploads_$DATE.tar.gz -C /data .

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

# Setup cron job
crontab -e
# Add: 0 2 * * * /opt/petplantr/backup.sh
```

### Disaster Recovery
1. Stop current deployment: `docker compose down`
2. Restore from backup: `docker run --rm -v backup_volume:/backup -v data_volume:/data alpine tar xzf /backup/latest.tar.gz -C /data`
3. Restart services: `docker compose up -d`

## Security Checklist

### Pre-Deployment
- [ ] Change all default passwords and secrets
- [ ] Configure firewall rules
- [ ] Setup SSL/TLS certificates
- [ ] Review environment variables for sensitive data
- [ ] Enable audit logging

### Post-Deployment
- [ ] Verify SSL configuration with SSL Labs
- [ ] Test security headers
- [ ] Review access logs
- [ ] Setup log monitoring and alerting
- [ ] Configure backup encryption

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker compose logs petplantr

# Check environment variables
docker compose config

# Verify dependencies
docker compose ps
```

#### High Memory Usage
```bash
# Check container resource usage
docker stats

# Adjust Gunicorn workers
# In docker-compose.yml, modify command:
command: ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "--bind", "0.0.0.0:8000", "api_server:app"]
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ./security/ssl/certs/fullchain.pem -text -noout

# Test SSL connection
openssl s_client -connect localhost:8443 -servername yourdomain.com
```

## Performance Optimization

### Application Level
- Enable Gzip compression
- Implement caching headers
- Use connection pooling
- Optimize database queries

### Infrastructure Level
- Use CDN for static assets
- Implement load balancing
- Configure auto-scaling
- Monitor resource usage

## Maintenance

### Regular Tasks
- Update SSL certificates (Let's Encrypt auto-renews)
- Monitor disk space and clean up logs
- Update Docker images monthly
- Review and rotate secrets quarterly
- Backup verification weekly

### Updates
```bash
# Update application
git pull origin main
docker compose build --no-cache
docker compose up -d

# Update monitoring stack
docker compose -f docker-compose.monitoring.yml pull
docker compose -f docker-compose.monitoring.yml up -d
```

## Support

For issues and questions:
1. Check logs: `docker compose logs`
2. Review monitoring dashboards
3. Check GitHub issues
4. Contact development team

---

**Last Updated:** $(date)
**Version:** 1.0.0
