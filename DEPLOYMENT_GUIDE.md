# PetPlantr Deployment Guide

## Overview
Complete guide for deploying PetPlantr in production environments.

## Prerequisites
- Ubuntu 20.04+ or CentOS 7+
- Python 3.8+
- Docker & Docker Compose
- 4GB RAM minimum
- 10GB disk space

## Quick Deployment

### Automated Deployment
```bash
# Clone repository
git clone https://github.com/medancode420/PetPlantr.git
cd PetPlantr

# Run automated deployment
./production-iteration.sh --domain yourdomain.com --ssl-type letsencrypt

# Verify deployment
./health-monitor.sh
```

### Manual Deployment Steps

#### 1. System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip nginx certbot docker.io docker-compose

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2. Application Setup
```bash
# Clone and setup
git clone https://github.com/medancode420/PetPlantr.git
cd PetPlantr

# Install Python dependencies
pip install -r requirements.txt

# Setup SSL certificates
./setup-ssl.sh --type letsencrypt --domain yourdomain.com --email admin@yourdomain.com
```

#### 3. Monitoring Setup
```bash
# Enable monitoring stack
./enable-monitoring.sh

# Start monitoring services
cd monitoring
docker compose -f docker-compose.monitoring.yml up -d
cd ..
```

#### 4. Web Server Configuration
```bash
# Copy nginx configuration
sudo cp nginx.production.conf /etc/nginx/sites-available/petplantr
sudo ln -s /etc/nginx/sites-available/petplantr /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

#### 5. Application Deployment
```bash
# Start application
docker compose up -d

# Verify deployment
curl https://yourdomain.com/api/v1/health
```

## Configuration

### Environment Variables
```bash
# Production environment
cp .env.example .env.production
nano .env.production
```

### SSL Configuration
```bash
# Let's Encrypt (recommended for production)
./setup-ssl.sh --type letsencrypt --domain yourdomain.com

# Self-signed (development only)
./setup-ssl.sh --type self-signed --domain localhost
```

### Monitoring Configuration
```bash
# Enable full monitoring stack
./enable-monitoring.sh

# Access monitoring
# Grafana: http://yourdomain.com:3000
# Prometheus: http://yourdomain.com:9090
```

## Security

### SSL/TLS Setup
```bash
# Generate SSL certificates
./setup-ssl.sh --type letsencrypt --domain yourdomain.com --email admin@yourdomain.com

# Security hardening
./harden-security.sh
```

### Firewall Configuration
```bash
# UFW configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw --force enable
```

## Monitoring

### Health Monitoring
```bash
# Real-time health monitoring
./health-monitor.sh

# Performance monitoring
python3 performance-monitor.py
```

### System Monitoring
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

## Backup & Recovery

### Automated Backups
```bash
# Configure automated backups
./backup.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * cd /path/to/PetPlantr && ./backup.sh
```

### Recovery Procedures
```bash
# Emergency rollback
git checkout <previous-tag>
docker compose down
docker compose up -d --build

# Data recovery
# Restore from backups/backups/daily/
tar -xzf latest-backup.tar.gz
```

## Troubleshooting

### Common Issues

#### API Not Responding
```bash
# Check service status
docker compose ps

# View logs
docker compose logs api

# Restart service
docker compose restart api
```

#### SSL Certificate Issues
```bash
# Renew certificates
./setup-ssl.sh --force

# Check certificate validity
openssl x509 -in security/ssl/certs/selfsigned.crt -text -noout
```

#### Performance Issues
```bash
# Run performance optimization
./optimize-performance.sh

# Monitor system resources
./health-monitor.sh
```

## Scaling

### Horizontal Scaling
```bash
# Add more API instances
docker compose up -d --scale api=3

# Load balancer configuration
# Update nginx configuration for multiple backends
```

### Vertical Scaling
```bash
# Increase resource limits
# Edit docker-compose.yml
# Increase memory and CPU limits
```

## Maintenance

### Regular Tasks
- Monitor system health daily
- Review logs weekly
- Update dependencies monthly
- Backup verification weekly
- Security updates as needed

### Update Procedures
```bash
# Update application
git pull origin main
docker compose down
docker compose up -d --build

# Update SSL certificates
./setup-ssl.sh --force

# Update monitoring
cd monitoring
docker compose pull
docker compose up -d
```

## Support

### Monitoring & Alerts
- Set up alerts for critical metrics
- Monitor error rates and response times
- Regular health check reviews

### Documentation
- Keep deployment documentation updated
- Document custom configurations
- Maintain runbooks for common issues
