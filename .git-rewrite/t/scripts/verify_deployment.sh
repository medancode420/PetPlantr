#!/bin/bash

# Quick verification script for deployment
echo "🔍 PetPlantr Deployment Verification"
echo "===================================="

echo "1️⃣ Testing demo GLB file..."
curl -s -I "https://petplantr.vercel.app/demo/sample-planter.glb" | head -1

echo "2️⃣ Testing API responsiveness..."
timeout 5 curl -s -X POST "https://petplantr.vercel.app/api/replicate" \
  -H "Content-Type: application/json" -d '{}' | head -50

echo "3️⃣ Running full health check in 30 seconds..."
sleep 30
./scripts/production_health_check.sh

echo "✅ Verification complete!"
echo "📋 If all tests pass, the fixes are deployed successfully!"
