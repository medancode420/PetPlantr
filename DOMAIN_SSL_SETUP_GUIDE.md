# PetPlantr Domain Setup & SSL Configuration Guide
## Production Domain Configuration for petplantr.com

### 🎯 **Current Status:** Domain Not Configured
- **Current Access:** http://localhost:8000 (local development)
- **Target:** https://petplantr.com (production)
- **SSL Status:** Self-signed certificates active
- **DNS Status:** Not configured

---

## 🌐 **Phase 1: Domain Acquisition**

### **Step 1: Purchase Domain**
#### **Recommended Registrars:**
1. **GoDaddy** - Popular, reliable, good support
2. **Namecheap** - Affordable, good privacy
3. **Google Domains** - Simple, integrated with Google services
4. **Cloudflare** - Includes CDN and security features

#### **Domain Options:**
- **Primary:** `petplantr.com` ($12-15/year)
- **Backup:** `petplantr.ai` or `petplantr.app`
- **Consider:** `.io` for tech focus ($30-50/year)

### **Step 2: DNS Configuration**
#### **Basic DNS Records Required:**
```
Type: A
Name: @
Value: YOUR_SERVER_IP
TTL: 600

Type: CNAME
Name: www
Value: @
TTL: 600

Type: CNAME
Name: api
Value: @
TTL: 600
```

#### **Advanced DNS Records (Recommended):**
```
Type: MX
Name: @
Value: mail.petplantr.com
Priority: 10

Type: TXT
Name: @
Value: "v=spf1 include:_spf.google.com ~all"

Type: CNAME
Name: mail
Value: ghs.google.com
```

---

## 🔒 **Phase 2: SSL Certificate Setup**

### **Option A: Let's Encrypt (Free, Recommended)**

#### **Step 1: Install Certbot**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python-certbot-nginx

# macOS (for testing)
brew install certbot
```

#### **Step 2: Obtain SSL Certificate**
```bash
# Stop NGINX temporarily
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone -d petplantr.com -d www.petplantr.com

# Or with NGINX plugin
sudo certbot --nginx -d petplantr.com -d www.petplantr.com
```

#### **Step 3: Certificate Auto-Renewal**
```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

### **Option B: Commercial SSL Certificate**

#### **Recommended Providers:**
- **DigiCert** - Enterprise-grade
- **GlobalSign** - Good for business
- **Comodo/Sectigo** - Affordable business SSL

#### **Installation:**
```bash
# Copy certificates to server
sudo cp certificate.crt /etc/ssl/certs/petplantr.crt
sudo cp private.key /etc/ssl/private/petplantr.key
sudo cp intermediate.crt /etc/ssl/certs/petplantr-intermediate.crt
```

---

## 🛠️ **Phase 3: Server Configuration**

### **Step 1: Update NGINX Configuration**
```nginx
# /etc/nginx/sites-available/petplantr.com
server {
    listen 80;
    server_name petplantr.com www.petplantr.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name petplantr.com www.petplantr.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/petplantr.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/petplantr.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # API Proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### **Step 2: Enable Site**
```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/petplantr.com /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload NGINX
sudo systemctl reload nginx
```

### **Step 3: Firewall Configuration**
```bash
# UFW (Ubuntu)
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

---

## 🚀 **Phase 4: Deployment Update**

### **Step 1: Update Production Environment**
```bash
# .env.production
DOMAIN=petplantr.com
SSL_CERT_PATH=/etc/letsencrypt/live/petplantr.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/petplantr.com/privkey.pem
HTTPS_ENABLED=true
```

### **Step 2: Update Docker Compose**
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  api:
    environment:
      - DOMAIN=petplantr.com
      - HTTPS_ENABLED=true
    ports:
      - "8000:8000"
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro

  frontend:
    environment:
      - NEXT_PUBLIC_API_URL=https://petplantr.com/api
    ports:
      - "3000:3000"
```

### **Step 3: Update Deployment Scripts**
```bash
# deploy-production.sh
#!/bin/bash

# Update DNS (if using dynamic DNS)
curl -X PUT "https://api.godaddy.com/v1/domains/petplantr.com/records/A/@" \
  -H "Authorization: sso-key $GODADDY_API_KEY:$GODADDY_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '[{"data": "'$SERVER_IP'", "ttl": 600}]'

# Deploy application
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d

# Reload NGINX
sudo systemctl reload nginx

# Test SSL
curl -I https://petplantr.com
```

---

## 🔍 **Phase 5: Testing & Validation**

### **Step 1: DNS Propagation Test**
```bash
# Check DNS resolution
nslookup petplantr.com
dig petplantr.com

# Test from multiple locations
curl -I https://petplantr.com
```

### **Step 2: SSL Certificate Test**
```bash
# Check certificate
openssl s_client -connect petplantr.com:443 -servername petplantr.com

# SSL Labs test
curl -s "https://www.ssllabs.com/ssltest/analyze.html?d=petplantr.com"

# Certbot certificate info
sudo certbot certificates
```

### **Step 3: Application Testing**
```bash
# Test API endpoints
curl https://petplantr.com/api/v1/health
curl https://petplantr.com/api/v1/breed/detect

# Test frontend
curl -I https://petplantr.com

# Performance test
ab -n 1000 -c 10 https://petplantr.com/
```

---

## 📊 **Phase 6: Monitoring & Maintenance**

### **Step 1: SSL Monitoring**
```bash
# Certificate expiry check
sudo certbot certificates

# Automated monitoring script
#!/bin/bash
CERT_PATH="/etc/letsencrypt/live/petplantr.com/cert.pem"
EXPIRY=$(openssl x509 -enddate -noout -in $CERT_PATH | cut -d= -f2)
EXPIRY_DATE=$(date -d "$EXPIRY" +%s)
CURRENT_DATE=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_DATE - $CURRENT_DATE) / 86400 ))

if [ $DAYS_LEFT -lt 30 ]; then
    echo "SSL Certificate expires in $DAYS_LEFT days" | mail -s "SSL Certificate Alert" admin@petplantr.com
fi
```

### **Step 2: Domain Monitoring**
```bash
# DNS monitoring
#!/bin/bash
DOMAIN="petplantr.com"
EXPECTED_IP="YOUR_SERVER_IP"

CURRENT_IP=$(dig +short $DOMAIN)
if [ "$CURRENT_IP" != "$EXPECTED_IP" ]; then
    echo "DNS mismatch for $DOMAIN: $CURRENT_IP != $EXPECTED_IP" | mail -s "DNS Alert" admin@petplantr.com
fi
```

### **Step 3: Backup SSL Certificates**
```bash
# Certificate backup script
#!/bin/bash
BACKUP_DIR="/opt/ssl-backups"
DATE=$(date +%Y%m%d)

sudo mkdir -p $BACKUP_DIR
sudo tar -czf $BACKUP_DIR/ssl-backup-$DATE.tar.gz /etc/letsencrypt

# Keep only last 7 backups
sudo find $BACKUP_DIR -name "ssl-backup-*.tar.gz" -mtime +7 -delete
```

---

## 🚨 **Troubleshooting Guide**

### **Common Issues:**

#### **SSL Certificate Not Renewing:**
```bash
# Check certbot status
sudo systemctl status certbot

# Manual renewal
sudo certbot renew

# Debug renewal
sudo certbot renew --dry-run -v
```

#### **DNS Not Propagating:**
```bash
# Check DNS records
dig petplantr.com

# Clear DNS cache
sudo systemctl restart systemd-resolved

# Test from different locations
curl -H "Host: petplantr.com" http://YOUR_SERVER_IP
```

#### **Mixed Content Issues:**
```bash
# Find HTTP resources
grep -r "http://" /var/www/petplantr.com/

# Update to HTTPS
sed -i 's|http://petplantr.com|https://petplantr.com|g' /var/www/petplantr.com/index.html
```

#### **Certificate Authority Issues:**
```bash
# Check certificate chain
openssl s_client -connect petplantr.com:443 -servername petplantr.com < /dev/null | openssl x509 -text

# Verify intermediate certificates
curl -I https://petplantr.com
```

---

## 📋 **Implementation Checklist**

### **Pre-Implementation:**
- [ ] Domain purchased and registered
- [ ] Server IP address confirmed
- [ ] DNS registrar API access (optional)
- [ ] SSL certificate provider chosen

### **Domain Setup:**
- [ ] DNS A record configured
- [ ] DNS CNAME records configured
- [ ] DNS propagation verified (24-48 hours)
- [ ] Domain resolving correctly

### **SSL Setup:**
- [ ] Certbot installed
- [ ] SSL certificate obtained
- [ ] Certificate auto-renewal configured
- [ ] SSL test passed (SSL Labs)

### **Server Configuration:**
- [ ] NGINX configured for HTTPS
- [ ] SSL certificates installed
- [ ] Security headers configured
- [ ] Firewall rules updated

### **Application Updates:**
- [ ] Environment variables updated
- [ ] Docker Compose updated
- [ ] Deployment scripts updated
- [ ] Application restarted

### **Testing & Validation:**
- [ ] HTTPS access working
- [ ] SSL certificate valid
- [ ] All endpoints functional
- [ ] Performance tests passed

### **Monitoring & Maintenance:**
- [ ] SSL monitoring configured
- [ ] Domain monitoring configured
- [ ] Certificate backup configured
- [ ] Alerting system configured

---

## 🎯 **Success Criteria**

- ✅ **Domain:** `https://petplantr.com` accessible
- ✅ **SSL:** A+ rating on SSL Labs
- ✅ **Security:** All security headers present
- ✅ **Performance:** < 2s response time
- ✅ **Monitoring:** SSL and domain monitoring active
- ✅ **Backup:** SSL certificates backed up

---

## 🚀 **Next Steps**

### **Immediate Actions:**
1. **Purchase domain** (petplantr.com)
2. **Configure DNS records**
3. **Install Certbot**
4. **Obtain SSL certificate**
5. **Update NGINX configuration**
6. **Test HTTPS access**

### **Short-term Goals:**
1. **Set up monitoring** for SSL and domain
2. **Configure automated backups**
3. **Test failover scenarios**
4. **Performance optimization**

### **Long-term Goals:**
1. **CDN integration** (Cloudflare)
2. **Multi-region deployment**
3. **Advanced security features**
4. **Automated scaling**

---

**🎉 Ready to take PetPlantr from localhost to production with a professional domain and SSL!**

*Last Updated: September 6, 2025*
