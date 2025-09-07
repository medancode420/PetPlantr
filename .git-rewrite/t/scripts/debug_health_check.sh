#!/bin/bash

# Debug Health Check for PetPlantr
# Focuses on the specific failures

set +e  # Continue on errors

PRODUCTION_URL="https://petplantr.vercel.app"
echo "🔧 Debugging PetPlantr Health Check Issues"
echo "=========================================="
echo ""

# 1. Test Demo GLB file
echo "1️⃣ Testing Demo GLB File..."
echo "Expected: 200 OK"
echo "Actual:"
curl -s -I "$PRODUCTION_URL/demo/sample-planter.glb" | head -3
echo ""

# 2. Test API endpoints with minimal timeout
echo "2️⃣ Testing API Endpoints (5s timeout)..."

echo "🔍 Replicate API (no params - should error):"
response=$(timeout 5 curl -s -X POST "$PRODUCTION_URL/api/replicate" \
  -H "Content-Type: application/json" \
  -d '{}' 2>/dev/null || echo "TIMEOUT")
echo "Response: $response"
echo ""

echo "🔍 Upload API (no file - should error):"
response=$(timeout 5 curl -s -X POST "$PRODUCTION_URL/api/upload" \
  -H "Content-Type: application/json" \
  -d '{}' 2>/dev/null || echo "TIMEOUT")
echo "Response: $response"
echo ""

# 3. Test what happens with valid-looking requests
echo "3️⃣ Testing with Valid Parameters..."

echo "🔍 Replicate API (with prompt):"
response=$(timeout 10 curl -s -X POST "$PRODUCTION_URL/api/replicate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}' 2>/dev/null || echo "TIMEOUT")
echo "Response: $response"
echo ""

# 4. Check if it's an environment issue
echo "4️⃣ Environment Check..."
echo "🔍 Trying to detect if APIs have environment issues:"
response=$(timeout 3 curl -s -X POST "$PRODUCTION_URL/api/replicate" \
  -H "Content-Type: application/json" \
  -d '{"imageUrl": "test", "prompt": "test"}' 2>/dev/null || echo "TIMEOUT")
  
if [[ "$response" == *"REPLICATE_API_TOKEN"* ]]; then
    echo "❌ REPLICATE_API_TOKEN not set in production"
elif [[ "$response" == "TIMEOUT" ]]; then
    echo "⏰ API timeout (cold start or hanging)"
elif [[ "$response" == "" ]]; then
    echo "📭 Empty response (possible server error)"
else
    echo "📝 Got response: $response"
fi

echo ""
echo "🎯 Summary of Issues:"
echo "1. Demo GLB file: Missing from production (404)"
echo "2. API endpoints: Timeout/hanging (cold start or env issues)"
echo "3. Likely causes:"
echo "   • Missing demo file in deployment"
echo "   • Environment variables not set in production"
echo "   • Cold start delays on serverless functions"
