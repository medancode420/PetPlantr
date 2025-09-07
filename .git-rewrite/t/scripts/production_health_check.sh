#!/bin/bash

# Production Health Check for PetPlantr
# Validates all production services and APIs

set -e

PRODUCTION_URL="${1:-https://petplantr.vercel.app}"
TIMEOUT=30

echo "🏥 PetPlantr Production Health Check"
echo "===================================="
echo "🌐 Testing: $PRODUCTION_URL"
echo "⏱️  Timeout: ${TIMEOUT}s"
echo ""

# Function to test endpoint
test_endpoint() {
    local url="$1"
    local description="$2"
    local expected_status="${3:-200}"
    
    echo -n "🔍 Testing $description... "
    
    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" || echo "000")
    
    if [ "$status" = "$expected_status" ]; then
        echo "✅ OK ($status)"
        return 0
    else
        echo "❌ FAIL ($status)"
        return 1
    fi
}

# Function to test JSON API
test_api() {
    local url="$1"
    local description="$2"
    local expected_field="$3"
    
    echo -n "🔍 Testing $description... "
    
    response=$(curl -s --max-time $TIMEOUT "$url" || echo "{}")
    
    if echo "$response" | jq -e "$expected_field" > /dev/null 2>&1; then
        echo "✅ OK"
        return 0
    else
        echo "❌ FAIL"
        echo "  Response: $response"
        return 1
    fi
}

failed_tests=0

# 1. Basic connectivity
test_endpoint "$PRODUCTION_URL" "Main site" || ((failed_tests++))

# 2. Upload page
test_endpoint "$PRODUCTION_URL/upload" "Upload page" || ((failed_tests++))

# 3. Health check API
test_api "$PRODUCTION_URL/api/health" "Health check API" ".status" || ((failed_tests++))

# 4. Demo model file
test_endpoint "$PRODUCTION_URL/demo/sample-planter.glb" "Demo GLB model" || ((failed_tests++))

# 5. AI API (basic structure test)
echo -n "🔍 Testing AI API structure... "
ai_response=$(curl -s --max-time $TIMEOUT -X POST "$PRODUCTION_URL/api/replicate" \
  -H "Content-Type: application/json" \
  -d '{"test": true}' || echo "{}")

if echo "$ai_response" | jq -e '.error' > /dev/null 2>&1; then
    echo "✅ OK (returns error structure as expected)"
else
    echo "❌ FAIL"
    echo "  Response: $ai_response"
    ((failed_tests++))
fi

# 6. Upload API structure
echo -n "🔍 Testing Upload API structure... "
upload_response=$(curl -s --max-time $TIMEOUT -X POST "$PRODUCTION_URL/api/upload" \
  -H "Content-Type: application/json" \
  -d '{"test": true}' || echo "{}")

if echo "$upload_response" | jq -e '.error' > /dev/null 2>&1; then
    echo "✅ OK (returns error structure as expected)"
else
    echo "❌ FAIL"
    echo "  Response: $upload_response"
    ((failed_tests++))
fi

echo ""
echo "📊 Health Check Summary"
echo "======================"

if [ $failed_tests -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED!"
    echo "✅ Production deployment is healthy"
    echo "🚀 Ready for users!"
    exit 0
else
    echo "❌ $failed_tests tests failed"
    echo "⚠️  Production deployment needs attention"
    echo "🔧 Check the failed endpoints and try again"
    exit 1
fi
