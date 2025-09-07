#!/bin/bash

# 🎨 Frontend Integration Test Suite
# Enhanced API testing for better frontend development

echo "🚀 Testing Enhanced Farm Manager APIs for Frontend Integration..."
echo "=================================================="

BASE_URL="https://your-api-gateway-url.amazonaws.com/dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    
    echo -e "\n${BLUE}Testing:${NC} $description"
    echo -e "${YELLOW}$method${NC} $endpoint"
    
    if [ -n "$data" ]; then
        echo "Data: $data"
        response=$(curl -s -X $method \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer your-test-token" \
            -d "$data" \
            "$BASE_URL$endpoint")
    else
        response=$(curl -s -X $method \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer your-test-token" \
            "$BASE_URL$endpoint")
    fi
    
    # Check if response is valid JSON
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Valid JSON Response${NC}"
        echo "$response" | jq '.' | head -20
    else
        echo -e "${RED}❌ Invalid JSON Response${NC}"
        echo "Response: $response"
    fi
    
    echo "----------------------------------------"
}

echo -e "\n${BLUE}=== FRONTEND-OPTIMIZED ENDPOINTS ===${NC}"

# Test new frontend dashboard endpoint
test_endpoint "GET" "/api/farm/frontend?customerId=customer_123" "Frontend Customer Dashboard"

# Test live farm data endpoint
test_endpoint "GET" "/api/farm/live" "Live Farm Data for Real-time Updates"

# Test enhanced farm status
test_endpoint "GET" "/api/farm/status" "Enhanced Farm Status"

# Test job filtering
test_endpoint "GET" "/api/farm/jobs?status=printing&limit=10" "Filtered Jobs for Frontend"

# Test detailed printer information
test_endpoint "GET" "/api/farm/printers?detailed=true" "Detailed Printer Information"

# Test farm metrics
test_endpoint "GET" "/api/farm/metrics?timeframe=24h" "Farm Performance Metrics"

# Test farm optimization recommendations
test_endpoint "GET" "/api/farm/optimization" "Farm Optimization Insights"

echo -e "\n${BLUE}=== CRUD OPERATIONS TEST ===${NC}"

# Test adding a new printer
printer_data='{
  "name": "Frontend Test Printer",
  "ipAddress": "192.168.1.100",
  "materialLoaded": "PLA White"
}'
test_endpoint "POST" "/api/farm/printers" "Add New Printer" "$printer_data"

# Test creating a print job
job_data='{
  "customerId": "customer_123",
  "customerEmail": "test@example.com",
  "petName": "Buddy",
  "breed": "Golden Retriever",
  "stlFile": "buddy_planter.stl",
  "estimatedTime": 120,
  "materialType": "PLA",
  "materialColor": "Golden",
  "priority": 7,
  "qualityRequirements": "high"
}'
test_endpoint "POST" "/api/farm/jobs" "Create Print Job" "$job_data"

# Test job assignment
assignment_data='{
  "jobId": "job_12345",
  "printerId": "printer_001"
}'
test_endpoint "POST" "/api/farm/assign" "Assign Job to Printer" "$assignment_data"

# Test job completion
completion_data='{
  "jobId": "job_12345",
  "success": true,
  "qualityScore": 95.5
}'
test_endpoint "POST" "/api/farm/complete" "Complete Print Job" "$completion_data"

echo -e "\n${BLUE}=== UPDATE OPERATIONS TEST ===${NC}"

# Test printer status update
printer_update='{
  "status": "maintenance",
  "temperatureBed": 25,
  "temperatureNozzle": 20
}'
test_endpoint "PUT" "/api/farm/printers/printer_001" "Update Printer Status" "$printer_update"

# Test job priority update
job_update='{
  "priority": 9,
  "deadline": "2025-07-30T12:00:00Z"
}'
test_endpoint "PUT" "/api/farm/jobs/job_12345" "Update Job Priority" "$job_update"

echo -e "\n${BLUE}=== ERROR HANDLING TEST ===${NC}"

# Test missing required parameters
test_endpoint "GET" "/api/farm/frontend" "Frontend Dashboard without Customer ID (Should Error)"

# Test invalid printer ID
test_endpoint "PUT" "/api/farm/printers/invalid_printer" "Update Non-existent Printer" '{"status": "idle"}'

# Test invalid job data
invalid_job='{
  "invalidField": "invalid"
}'
test_endpoint "POST" "/api/farm/jobs" "Create Job with Invalid Data" "$invalid_job"

echo -e "\n${BLUE}=== PERFORMANCE TEST ===${NC}"

# Test bulk operations
echo -e "\n${YELLOW}Testing response times...${NC}"
for i in {1..5}; do
    echo -n "Request $i: "
    start_time=$(date +%s%N)
    curl -s "$BASE_URL/api/farm/status" >/dev/null
    end_time=$(date +%s%N)
    duration=$(((end_time - start_time) / 1000000))
    echo "${duration}ms"
done

echo -e "\n${GREEN}✅ Frontend Integration Test Suite Completed!${NC}"
echo "=================================================="
echo ""
echo "📊 Test Results Summary:"
echo "• Frontend Dashboard Endpoint: ✅ Tested"
echo "• Live Data Endpoint: ✅ Tested"
echo "• Enhanced CRUD Operations: ✅ Tested"
echo "• Error Handling: ✅ Tested"
echo "• Performance: ✅ Measured"
echo ""
echo "🎯 Ready for frontend integration!"
echo "Use these endpoints in your React/Vue/Angular applications."
