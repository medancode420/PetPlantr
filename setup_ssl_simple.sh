#!/bin/bash
# Simple SSL setup for PetPlantr on macOS

DOMAIN="petplantr.com"
SSL_DIR="./ssl"

# Create SSL directory
mkdir -p "$SSL_DIR"

echo "🔐 Creating self-signed SSL certificate for $DOMAIN..."

# Create self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/$DOMAIN.key" \
    -out "$SSL_DIR/$DOMAIN.crt" \
    -subj "/C=US/ST=State/L=City/O=PetPlantr/CN=$DOMAIN"

echo "✅ SSL certificate created in $SSL_DIR/"
echo "📄 Certificate: $SSL_DIR/$DOMAIN.crt"
echo "🔑 Private Key: $SSL_DIR/$DOMAIN.key"

# Create NGINX configuration for local HTTPS
cat > nginx.petplantr.conf << EOF
# PetPlantr Local HTTPS Configuration
server {
    listen 443 ssl;
    server_name localhost $DOMAIN;

    ssl_certificate $PWD/ssl/$DOMAIN.crt;
    ssl_certificate_key $PWD/ssl/$DOMAIN.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 80;
    server_name localhost $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}
EOF

echo "✅ NGINX configuration created: nginx.petplantr.conf"
echo ""
echo "🚀 To use HTTPS locally:"
echo "1. Copy nginx.petplantr.conf to /usr/local/etc/nginx/servers/"
echo "2. Reload NGINX: sudo brew services restart nginx"
echo "3. Access: https://localhost (accept self-signed certificate)"
echo ""
echo "🌐 For production domain setup:"
echo "1. Add DNS records from dns_records.txt to your domain provider"
echo "2. Wait 24-48 hours for DNS propagation"
echo "3. Run: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
