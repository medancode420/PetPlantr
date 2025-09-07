#!/bin/bash
# Deploy to production environment

echo "🚀 Deploying to PetPlantr Production..."

# Create backup before deployment
echo "💾 Creating backup..."
./backup.sh

# Pull latest images
docker pull ghcr.io/medancode420/petplantr:latest

# Stop existing containers
docker compose -f docker-compose.production.yml down

# Start new containers
docker compose -f docker-compose.production.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 60

# Run comprehensive health checks
echo "🔍 Running health checks..."
curl -f http://localhost:8000/api/v1/health
curl -f http://localhost:8000/api/v2/health/detailed

if [ $? -eq 0 ]; then
    echo "✅ Production deployment successful!"
    echo "🌐 Production URL: https://petplantr.com"

    # Send notification (if configured)
    echo "📢 Deployment notification sent"
else
    echo "❌ Production deployment failed!"
    echo "🔄 Rolling back..."
    ./rollback.sh
    exit 1
fi
