#!/bin/bash

echo "🧪 Farm Manager Quick Test Suite"
echo "================================"
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to local testing
BASE_URL=${1:-"http://localhost:3000"}

echo "Testing Farm Manager endpoints at: $BASE_URL"
echo

# Function to test an endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=${4:-200}
    
    echo -n "Testing $description... "
    
    response=$(curl -s -w "\n%{http_code}" "$method" "$BASE_URL$endpoint" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
        echo "   Response: $(echo "$body" | jq -r '.status // .message // .farmStats.totalPrinters // "OK"' 2>/dev/null || echo "OK")"
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
        echo "   Expected: $expected_status, Got: $http_code"
    fi
    echo
}

# Function to test POST endpoint
test_post_endpoint() {
    local endpoint=$1
    local data=$2
    local description=$3
    local expected_status=${4:-200}
    
    echo -n "Testing $description... "
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$data" \
        "$BASE_URL$endpoint" 2>/dev/null)
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
        echo "   Response: $(echo "$body" | jq -r '.message // .jobId // .printerId // "OK"' 2>/dev/null || echo "OK")"
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
        echo "   Expected: $expected_status, Got: $http_code"
    fi
    echo
}

echo "🏭 CORE FARM MANAGEMENT TESTS"
echo "=============================="

# Core GET endpoints
test_endpoint "-X GET" "/api/farm/status" "Farm Status"
test_endpoint "-X GET" "/api/farm/printers" "List Printers"
test_endpoint "-X GET" "/api/farm/jobs" "List Jobs"
test_endpoint "-X GET" "/api/farm/metrics" "Farm Metrics"

echo "📊 ANALYTICS & INSIGHTS TESTS"
echo "=============================="

# Analytics endpoints
test_endpoint "-X GET" "/api/farm/analytics" "Farm Analytics"
test_endpoint "-X GET" "/api/farm/health" "Printer Health"
test_endpoint "-X GET" "/api/farm/insights" "Customer Insights"
test_endpoint "-X GET" "/api/farm/predictions" "Predictive Analytics"

echo "🎨 FRONTEND INTEGRATION TESTS"
echo "=============================="

# Frontend endpoints
test_endpoint "-X GET" "/api/farm/frontend" "Frontend Dashboard"
test_endpoint "-X GET" "/api/farm/live" "Live Farm Data"
test_endpoint "-X GET" "/api/farm/optimization" "Farm Optimization"

echo "⚡ REAL-TIME & STREAMING TESTS"
echo "=============================="

# Real-time endpoints
test_endpoint "-X GET" "/api/farm/realtime-stream" "Real-time Stream"

echo "✍️  CREATE OPERATIONS TESTS"
echo "============================"

# Test creating a printer
printer_data='{
  "name": "Test Printer 1",
  "ipAddress": "192.168.1.100",
  "materialLoaded": "PLA"
}'

test_post_endpoint "/api/farm/printers" "$printer_data" "Add Printer" 201

# Test creating a job
job_data='{
  "customerId": "test_customer_123",
  "customerEmail": "test@example.com",
  "petName": "Buddy",
  "breed": "Golden Retriever",
  "stlFile": "golden_retriever.stl",
  "estimatedTime": 120,
  "materialType": "PLA",
  "materialColor": "Brown",
  "priority": 5,
  "qualityRequirements": "high"
}'

test_post_endpoint "/api/farm/jobs" "$job_data" "Create Print Job" 201

echo "🏁 TEST SUMMARY"
echo "==============="
echo -e "${YELLOW}Local testing completed!${NC}"
echo
echo "To test with a deployed API:"
echo "1. Deploy: npx serverless deploy --stage dev"
echo "2. Get URL: npx serverless info --stage dev | grep ServiceEndpoint"
echo "3. Run: ./test-farmmanager.sh [YOUR_API_URL]"
echo
echo "For comprehensive testing, use:"
echo "./test-advanced-backend.sh [API_URL]"
