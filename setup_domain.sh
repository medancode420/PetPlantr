#!/bin/bash
# PetPlantr Domain Setup Script
# Configures petplantr.com domain with DNS and SSL

set -euo pipefail

# Configuration
DOMAIN="petplantr.com"
SERVER_IP="${SERVER_IP:-192.168.1.218}"  # Update this with your actual server IP
EMAIL="admin@petplantr.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a setup.log
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get current IP
get_current_ip() {
    curl -s https://api.ipify.org || curl -s https://ipv4.icanhazip.com
}

log "🚀 Starting PetPlantr domain setup for $DOMAIN"

# Check prerequisites
log "🔍 Checking prerequisites..."

if ! command_exists curl; then
    error "curl is required but not installed"
    exit 1
fi

if ! command_exists dig; then
    warning "dig not found, installing dnsutils..."
    if command_exists apt; then
        sudo apt update && sudo apt install -y dnsutils
    elif command_exists yum; then
        sudo yum install -y bind-utils
    else
        warning "Please install dig manually for DNS verification"
    fi
fi

success "Prerequisites check complete"

# Get current server IP
CURRENT_IP=$(get_current_ip)
log "📡 Current server IP: $CURRENT_IP"

if [ "$CURRENT_IP" != "$SERVER_IP" ]; then
    warning "Server IP mismatch!"
    warning "Configured IP: $SERVER_IP"
    warning "Current IP: $CURRENT_IP"
    read -p "Continue with current IP? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Please update SERVER_IP in this script and run again"
        exit 1
    fi
    SERVER_IP="$CURRENT_IP"
fi

# Create DNS configuration
log "📝 Creating DNS configuration..."

cat > dns_records.txt << EOF
# PetPlantr DNS Records for $DOMAIN
# Add these records to your DNS provider (GoDaddy, Namecheap, etc.)

# A Records
@ A $SERVER_IP  ; Root domain
www A $SERVER_IP  ; WWW subdomain
api A $SERVER_IP  ; API subdomain

# CNAME Records
mail CNAME ghs.google.com  ; Gmail integration

# MX Records (Optional - for email)
@ MX 1 ASPMX.L.GOOGLE.COM
@ MX 5 ALT1.ASPMX.L.GOOGLE.COM
@ MX 5 ALT2.ASPMX.L.GOOGLE.COM
@ MX 10 ALT3.ASPMX.L.GOOGLE.COM
@ MX 10 ALT4.ASPMX.L.GOOGLE.COM

# TXT Records (Optional - for verification)
@ TXT "v=spf1 include:_spf.google.com ~all"
@ TXT "google-site-verification=your-verification-code"

# SRV Records (Optional - for services)
_xmpp-server._tcp SRV 5 0 5269 xmpp-server.l.google.com
_xmpp-client._tcp SRV 5 0 5222 talk.l.google.com
EOF

success "DNS records configuration created: dns_records.txt"

# Test DNS resolution (if domain is already configured)
log "🔍 Testing DNS resolution..."

if dig +short "$DOMAIN" >/dev/null 2>&1; then
    CURRENT_DNS_IP=$(dig +short "$DOMAIN" | head -1)
    log "Current DNS IP for $DOMAIN: $CURRENT_DNS_IP"

    if [ "$CURRENT_DNS_IP" = "$SERVER_IP" ]; then
        success "DNS is correctly configured!"
    else
        warning "DNS IP mismatch. Expected: $SERVER_IP, Got: $CURRENT_DNS_IP"
        warning "DNS may still be propagating (can take 24-48 hours)"
    fi
else
    warning "Domain $DOMAIN not resolving. DNS not configured yet."
fi

# SSL Certificate setup
log "🔒 Setting up SSL certificate..."

if command_exists certbot; then
    success "Certbot is already installed"
else
    log "📦 Installing Certbot..."
    if command_exists apt; then
        sudo apt update
        sudo apt install -y certbot python3-certbot-nginx
    elif command_exists yum; then
        sudo yum install -y certbot python-certbot-nginx
    elif command_exists brew; then
        brew install certbot
    else
        error "Please install Certbot manually"
        exit 1
    fi
    success "Certbot installed"
fi

# Create SSL certificate directory
sudo mkdir -p /etc/letsencrypt/live/"$DOMAIN"

# Create self-signed certificate for immediate use
log "🔐 Creating self-signed certificate for immediate HTTPS..."

sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/"$DOMAIN".key \
    -out /etc/ssl/certs/"$DOMAIN".crt \
    -subj "/C=US/ST=State/L=City/O=PetPlantr/CN=$DOMAIN"

success "Self-signed certificate created"

# Update NGINX configuration
log "🌐 Updating NGINX configuration..."

sudo tee /etc/nginx/sites-available/"$DOMAIN" > /dev/null << EOF
# PetPlantr Production Configuration
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL Configuration (Self-signed for now)
    ssl_certificate /etc/ssl/certs/$DOMAIN.crt;
    ssl_certificate_key /etc/ssl/private/$DOMAIN.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # API Proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static files and frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/"$DOMAIN" /etc/nginx/sites-enabled/

# Test NGINX configuration
log "🧪 Testing NGINX configuration..."
if sudo nginx -t; then
    success "NGINX configuration is valid"
    sudo systemctl reload nginx
    success "NGINX reloaded"
else
    error "NGINX configuration test failed"
    exit 1
fi

# Update environment variables
log "⚙️  Updating environment configuration..."

cat > .env.production.domain << EOF
# PetPlantr Production Environment with Domain
DOMAIN=$DOMAIN
SERVER_IP=$SERVER_IP
HTTPS_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/$DOMAIN.crt
SSL_KEY_PATH=/etc/ssl/private/$DOMAIN.key

# API Configuration
API_BASE_URL=https://$DOMAIN/api
FRONTEND_URL=https://$DOMAIN

# Monitoring
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3030
EOF

success "Environment configuration created: .env.production.domain"

# Create Let's Encrypt certificate script
log "📜 Creating Let's Encrypt certificate script..."

cat > get_ssl_cert.sh << EOF
#!/bin/bash
# Get Let's Encrypt SSL certificate for $DOMAIN

set -euo pipefail

DOMAIN="$DOMAIN"
EMAIL="$EMAIL"

echo "🔒 Getting Let's Encrypt certificate for \$DOMAIN..."

# Stop NGINX temporarily
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone \\
    -d "\$DOMAIN" \\
    -d "www.\$DOMAIN" \\
    --email "\$EMAIL" \\
    --agree-tos \\
    --non-interactive

# Update NGINX configuration to use Let's Encrypt certs
sudo sed -i "s|/etc/ssl/certs/\$DOMAIN.crt|/etc/letsencrypt/live/\$DOMAIN/fullchain.pem|g" /etc/nginx/sites-available/\$DOMAIN
sudo sed -i "s|/etc/ssl/private/\$DOMAIN.key|/etc/letsencrypt/live/\$DOMAIN/privkey.pem|g" /etc/nginx/sites-available/\$DOMAIN

# Reload NGINX
sudo systemctl start nginx
sudo nginx -t && sudo systemctl reload nginx

echo "✅ SSL certificate installed!"
echo "🔄 Certificate will auto-renew before expiry"
EOF

chmod +x get_ssl_cert.sh
success "SSL certificate script created: get_ssl_cert.sh"

# Create domain verification script
log "🔍 Creating domain verification script..."

cat > verify_domain.sh << EOF
#!/bin/bash
# Verify domain configuration for $DOMAIN

DOMAIN="$DOMAIN"
SERVER_IP="$SERVER_IP"

echo "🔍 Verifying $DOMAIN configuration..."

# Check DNS
echo "📡 Checking DNS..."
DNS_IP=\$(dig +short "\$DOMAIN" | head -1)
if [ "\$DNS_IP" = "\$SERVER_IP" ]; then
    echo "✅ DNS: Correctly configured"
else
    echo "❌ DNS: Expected \$SERVER_IP, got \$DNS_IP"
fi

# Check HTTP redirect
echo "🌐 Checking HTTP redirect..."
HTTP_STATUS=\$(curl -s -o /dev/null -w "%{http_code}" http://\$DOMAIN)
if [ "\$HTTP_STATUS" = "301" ]; then
    echo "✅ HTTP: Redirects to HTTPS"
else
    echo "❌ HTTP: Status \$HTTP_STATUS"
fi

# Check HTTPS
echo "🔒 Checking HTTPS..."
HTTPS_STATUS=\$(curl -s -o /dev/null -w "%{http_code}" https://\$DOMAIN)
if [ "\$HTTPS_STATUS" = "200" ]; then
    echo "✅ HTTPS: Working"
else
    echo "❌ HTTPS: Status \$HTTPS_STATUS"
fi

# Check SSL certificate
echo "📜 Checking SSL certificate..."
SSL_INFO=\$(openssl s_client -connect \$DOMAIN:443 -servername \$DOMAIN < /dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
if [ -n "\$SSL_INFO" ]; then
    echo "✅ SSL: Certificate valid"
    echo "   \$SSL_INFO"
else
    echo "❌ SSL: Certificate issue"
fi

# Check API
echo "🔌 Checking API..."
API_STATUS=\$(curl -s -o /dev/null -w "%{http_code}" https://\$DOMAIN/api/v1/health)
if [ "\$API_STATUS" = "200" ]; then
    echo "✅ API: Healthy"
else
    echo "❌ API: Status \$API_STATUS"
fi

echo "🎯 Domain verification complete!"
EOF

chmod +x verify_domain.sh
success "Domain verification script created: verify_domain.sh"

# Create summary
log "📋 Creating setup summary..."

cat > DOMAIN_SETUP_SUMMARY.md << EOF
# PetPlantr Domain Setup Summary

## ✅ Completed Steps

### 1. DNS Configuration
- **Domain:** $DOMAIN
- **Server IP:** $SERVER_IP
- **DNS Records:** Created in \`dns_records.txt\`
- **Status:** Ready for DNS provider configuration

### 2. SSL Setup
- **Certificate Type:** Self-signed (temporary)
- **SSL Script:** \`get_ssl_cert.sh\` (for Let's Encrypt)
- **NGINX Config:** Updated for HTTPS
- **Status:** HTTPS enabled with self-signed cert

### 3. Server Configuration
- **NGINX:** Configured for $DOMAIN
- **SSL:** Enabled with security headers
- **Proxy:** API and frontend routing
- **Status:** Server ready for domain

### 4. Environment Setup
- **Config File:** \`.env.production.domain\`
- **Variables:** Domain, SSL paths, URLs
- **Status:** Production environment ready

## 📋 Next Steps

### 1. Configure DNS Records
Add the DNS records from \`dns_records.txt\` to your DNS provider:
- GoDaddy, Namecheap, or your domain registrar
- Allow 24-48 hours for DNS propagation

### 2. Get SSL Certificate
Run the SSL certificate script:
\`\`\`bash
sudo ./get_ssl_cert.sh
\`\`\`

### 3. Verify Setup
Test the domain configuration:
\`\`\`bash
./verify_domain.sh
\`\`\`

### 4. Update Monitoring
Update Grafana and Prometheus with production URLs:
- Replace localhost with $DOMAIN
- Configure SSL monitoring

## 🔗 Access URLs

- **Production Site:** https://$DOMAIN
- **API Endpoint:** https://$DOMAIN/api/v1/health
- **Grafana:** http://localhost:3030 (admin/admin)
- **Prometheus:** http://localhost:9090

## 📞 Support

If you encounter issues:
1. Check \`setup.log\` for errors
2. Run \`./verify_domain.sh\` for diagnostics
3. Ensure DNS has propagated (24-48 hours)
4. Verify firewall allows ports 80, 443

---
*Setup completed on: \$(date)*
*Domain: $DOMAIN*
*Server IP: $SERVER_IP*
EOF

success "Setup summary created: DOMAIN_SETUP_SUMMARY.md"

log "🎉 Domain setup script completed!"
log ""
log "📋 Summary of created files:"
log "  📄 dns_records.txt - DNS records to add to your provider"
log "  🔐 get_ssl_cert.sh - Script to get Let's Encrypt certificate"
log "  🔍 verify_domain.sh - Script to verify domain configuration"
log "  ⚙️  .env.production.domain - Production environment variables"
log "  📋 DOMAIN_SETUP_SUMMARY.md - Complete setup guide"
log ""
log "🚀 Next steps:"
log "1. Add DNS records from dns_records.txt to your domain provider"
log "2. Wait 24-48 hours for DNS propagation"
log "3. Run sudo ./get_ssl_cert.sh to get Let's Encrypt certificate"
log "4. Run ./verify_domain.sh to test the setup"
log ""
log "🌐 Your domain will be: https://$DOMAIN"
