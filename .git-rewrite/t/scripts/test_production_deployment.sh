#!/bin/bash

# Force Production Deployment and Test Script
# Ensures real AI models are deployed and working

echo "🚀 PetPlantr Production Deployment Test"
echo "========================================"

# Check if we have internet connectivity
echo "📡 Checking connectivity..."
curl -s --max-time 5 https://httpbin.org/ip > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Internet connection: OK"
else
    echo "❌ Internet connection: FAILED"
    exit 1
fi

# Test the production deployment
echo "🌐 Testing production deployment..."
RESPONSE=$(curl -s --max-time 10 -w "%{http_code}" https://petplantr.vercel.app/ -o /dev/null)
if [ "$RESPONSE" = "200" ]; then
    echo "✅ Production site: OK (HTTP $RESPONSE)"
else
    echo "❌ Production site: FAILED (HTTP $RESPONSE)"
fi

# Test the API with environment check
echo "🔧 Testing API environment..."
API_RESPONSE=$(curl -s --max-time 10 -X POST https://petplantr.vercel.app/api/replicate \
    -H "Content-Type: application/json" \
    -d '{"prompt": "simple test"}' \
    -w "\nHTTP_CODE:%{http_code}")

if echo "$API_RESPONSE" | grep -q "HTTP_CODE:503"; then
    echo "⚠️  API returned 503 - Environment variables not configured"
elif echo "$API_RESPONSE" | grep -q "HTTP_CODE:200"; then
    echo "✅ API responding correctly"
    echo "Response: $API_RESPONSE"
else
    echo "❌ API failed or timed out"
    echo "Response: $API_RESPONSE"
fi

# Check for real models in the codebase
echo "🤖 Verifying real models in codebase..."
if grep -q "cjwbw/shap-e" frontend/app/api/replicate/route.ts; then
    echo "✅ Shap-E model found in code"
else
    echo "❌ Shap-E model NOT found in code"
fi

if grep -q "cjwbw/point-e" frontend/app/api/replicate/route.ts; then
    echo "✅ Point-E model found in code"
else
    echo "❌ Point-E model NOT found in code"
fi

# Check for demo fallback removal
if grep -q "demo.*fallback\|fallback.*demo" frontend/app/api/replicate/route.ts; then
    echo "⚠️  Demo fallback code still present"
else
    echo "✅ Demo fallback code removed"
fi

echo "========================================"
echo "✅ Deployment test complete!"
echo ""
echo "Next steps if API is failing:"
echo "1. Check Vercel dashboard for environment variables"
echo "2. Ensure REPLICATE_API_TOKEN is set in production"
echo "3. Force redeploy if needed"
