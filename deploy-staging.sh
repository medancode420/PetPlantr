#!/bin/bash
# Deploy to staging environment

echo "🚀 Deploying to PetPlantr Staging..."

# Pull latest images
docker pull ghcr.io/medancode420/petplantr:latest

# Stop existing containers
docker compose -f docker-compose.staging.yml down

# Start new containers
docker compose -f docker-compose.staging.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Run health checks
echo "🔍 Running health checks..."
curl -f http://localhost:8000/api/v1/health

if [ $? -eq 0 ]; then
    echo "✅ Staging deployment successful!"
    echo "🌐 Staging URL: http://staging.petplantr.com"
else
    echo "❌ Staging deployment failed!"
    exit 1
fi
