#!/bin/bash
# Deploy PetPlantr frontend

echo "🚀 Deploying PetPlantr Frontend..."

# Create web server configuration
cat > nginx-frontend.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /var/www/petplantr/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
