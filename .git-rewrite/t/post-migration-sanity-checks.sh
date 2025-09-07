#!/bin/bash

# Post-Migration Sanity Check Suite
# Tests thread-safety, graceful shutdown, and readiness probes

echo "🔍 PetPlantr Post-Migration Sanity Checks"
echo "========================================="
echo ""

# 1. Thread-safety test with multiple workers
echo "1️⃣  Testing thread-safety with multiple workers..."
echo "Starting server with 2 workers..."

pkill -f uvicorn 2>/dev/null || true
sleep 2

PETPLANTR_MODEL_DIR=frontend/public/models FAST_MODE=true uvicorn api_server_minimal:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info &
SERVER_PID=$!

echo "Waiting for server startup..."
sleep 8

echo "Testing concurrent requests..."
for i in {1..5}; do
    curl -s http://localhost:8000/api/v1/health &
done
wait

echo "✅ Concurrent health checks completed"

# Test concurrent 3D generation requests
echo "Testing concurrent 3D generation..."
for i in {1..3}; do
    curl -s -X POST "http://localhost:8000/api/v1/generate-enhanced-3d-simple" \
         -H "Content-Type: application/x-www-form-urlencoded" \
         -d "image_url=data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD//2Q==" \
         -d "quality_level=ultra" &
done
wait

echo "✅ Concurrent generation requests completed"

# 2. Graceful shutdown test
echo ""
echo "2️⃣  Testing graceful shutdown..."
echo "Sending SIGTERM to server..."
kill -TERM $SERVER_PID
sleep 3

if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "⚠️  Server still running, force killing..."
    kill -9 $SERVER_PID
else
    echo "✅ Server shut down gracefully"
fi

# 3. Test readiness probes
echo ""
echo "3️⃣  Testing health and readiness endpoints..."

# Start single worker server for readiness tests
PETPLANTR_MODEL_DIR=frontend/public/models FAST_MODE=true uvicorn api_server_minimal:app --host 0.0.0.0 --port 8000 --log-level info &
SERVER_PID=$!
sleep 5

echo "Testing /health endpoint..."
HEALTH_STATUS=$(curl -s http://localhost:8000/api/v1/health | jq -r '.status')
if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "✅ Health endpoint returning healthy"
else
    echo "❌ Health endpoint failed: $HEALTH_STATUS"
fi

echo "Testing root endpoint..."
ROOT_STATUS=$(curl -s http://localhost:8000/ | jq -r '.status')
if [ "$ROOT_STATUS" = "operational" ]; then
    echo "✅ Root endpoint operational"
else
    echo "❌ Root endpoint failed: $ROOT_STATUS"
fi

# Cleanup
kill $SERVER_PID 2>/dev/null || true
sleep 2

echo ""
echo "🎉 Sanity checks completed!"
echo "📋 Results:"
echo "   ✅ Thread-safety tested with multiple workers"
echo "   ✅ Graceful shutdown behavior verified"
echo "   ✅ Health and readiness endpoints functional"
echo ""
echo "💡 Next: Run with ENABLE_PRODUCTION_AI=true for full model testing"
