#!/bin/bash
# Rollback production deployment

echo "🔄 Rolling back PetPlantr Production..."

# Stop current containers
docker compose -f docker-compose.production.yml down

# Restore from backup
echo "💾 Restoring from backup..."
./restore-backup.sh

# Start previous version
docker compose -f docker-compose.production.yml up -d

# Verify rollback
echo "🔍 Verifying rollback..."
sleep 30
curl -f http://localhost:8000/api/v1/health

if [ $? -eq 0 ]; then
    echo "✅ Rollback successful!"
else
    echo "❌ Rollback failed!"
    exit 1
fi
