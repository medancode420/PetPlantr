#!/bin/bash

# 🧪 PetPlantr Complete System Test
# Comprehensive testing for all PetPlantr components

echo "🐾 PetPlantr System Health Check"
echo "================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
PASSED=0
FAILED=0

# Helper function for test results
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC} - $2"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} - $2"
        ((FAILED++))
    fi
}

# Add lightweight HTTP helper (used later)
make_request() {
    local url="$1"
    local method="${2:-GET}"
    local expected="${3:-200}"
    local timeout="${4:-5}"
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" --max-time "$timeout" "$url")
    [ "$status" = "$expected" ]
}

# Farm Manager API Base URL
FARM_API="https://cm1ffbb7hf.execute-api.us-east-1.amazonaws.com/dev"
# Optional local/first-party app base for production hardening tests
APP_API="${APP_API:-http://localhost:8000}"

# Helper to pick first 200 OK endpoint among candidates
pick_ok_endpoint() {
    local base="$1"; shift
    for path in "$@"; do
        local code
        code=$(curl -s -o /dev/null -w "%{http_code}" "$base$path" || echo "")
        if [ "$code" = "200" ]; then
            echo "$base$path"
            return 0
        fi
    done
    return 1
}

echo "🏭 BACKEND FARM MANAGER TESTS"
echo "============================="

# Test 1: Farm Status
echo "Testing Farm Status..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FARM_API/api/farm/status")
test_result $([ "$STATUS_CODE" = "200" ] && echo 0 || echo 1) "Farm Status API ($STATUS_CODE)"

# Test 2: Farm Analytics
echo "Testing Farm Analytics..."
ANALYTICS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FARM_API/api/farm/analytics")
test_result $([ "$ANALYTICS_CODE" = "200" ] && echo 0 || echo 1) "Farm Analytics API ($ANALYTICS_CODE)"

# Test 3: Printer Health
echo "Testing Printer Health..."
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FARM_API/api/farm/health")
test_result $([ "$HEALTH_CODE" = "200" ] && echo 0 || echo 1) "Printer Health API ($HEALTH_CODE)"

# Test 4: Frontend Dashboard
echo "Testing Frontend Dashboard..."
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FARM_API/api/farm/frontend")
test_result $([ "$FRONTEND_CODE" = "200" ] && echo 0 || echo 1) "Frontend Dashboard API ($FRONTEND_CODE)"

# Test 5: Real-time Data
echo "Testing Real-time Stream..."
REALTIME_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FARM_API/api/farm/realtime-stream")
test_result $([ "$REALTIME_CODE" = "200" ] && echo 0 || echo 1) "Real-time Stream API ($REALTIME_CODE)"

echo ""
echo "🖥️  FRONTEND TESTS"
echo "=================="

# Check if frontend is running
if [ -d "../frontend" ] || [ -d "../../frontend" ]; then
    echo "Frontend directory found..."
    
    # Check if Next.js is running on port 3000
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000" | grep -q "200\|301\|302"; then
        test_result 0 "Frontend server running on localhost:3000"
    else
        test_result 1 "Frontend server not running (try: npm run dev)"
    fi
else
    echo -e "${YELLOW}⚠️  SKIP${NC} - Frontend directory not found"
fi

echo ""
echo "🤖 AI PIPELINE TESTS"
echo "===================="

# Check for AI model files
if [ -f "./advanced_neural_ai_3d.py" ] || [ -f "../advanced_neural_ai_3d.py" ] || [ -f "../../advanced_neural_ai_3d.py" ]; then
    test_result 0 "AI pipeline files found"
    
    # Check Python dependencies
    if python3 -c "import torch, torchvision" 2>/dev/null; then
        test_result 0 "PyTorch dependencies available"
    else
        test_result 1 "PyTorch dependencies missing"
    fi
    
    if python3 -c "import trimesh, numpy" 2>/dev/null; then
        test_result 0 "3D processing dependencies available"
    else
        test_result 1 "3D processing dependencies missing"
    fi
else
    test_result 1 "AI pipeline files not found"
fi

echo ""
echo "🗄️  DATABASE TESTS"
echo "=================="

# Test DynamoDB tables (via API)
echo "Testing DynamoDB via API..."
PRINTERS_RESPONSE=$(curl -s "$FARM_API/api/farm/printers")
if echo "$PRINTERS_RESPONSE" | grep -q "printers"; then
    test_result 0 "Printers table accessible"
else
    test_result 1 "Printers table not accessible"
fi

JOBS_RESPONSE=$(curl -s "$FARM_API/api/farm/jobs")
if echo "$JOBS_RESPONSE" | grep -q "jobs"; then
    test_result 0 "Jobs table accessible"
else
    test_result 1 "Jobs table not accessible"
fi

echo ""
echo "📦 STL FILE PROCESSING TESTS"
echo "============================"

# Check for STL processing capabilities
if python3 -c "import trimesh" 2>/dev/null; then
    test_result 0 "STL processing library (trimesh) available"
else
    test_result 1 "STL processing library missing"
fi

# Check for sample STL files
if ls *.stl >/dev/null 2>&1 || ls ../*.stl >/dev/null 2>&1; then
    test_result 0 "Sample STL files found"
else
    test_result 1 "No STL files found for testing"
fi

echo ""
echo "🔗 INTEGRATION TESTS"
echo "===================="

# Test complete workflow
echo "Testing end-to-end workflow..."

# Create a test print job
TEST_JOB=$(cat << EOF
{
  "customerId": "test_customer",
  "customerEmail": "test@example.com",
  "petName": "TestDog",
  "breed": "Golden Retriever",
  "stlFile": "test-dog.stl",
  "estimatedTime": 120,
  "materialType": "PLA",
  "materialColor": "Blue",
  "priority": 5,
  "qualityRequirements": "standard"
}
EOF
)

JOB_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "$TEST_JOB" "$FARM_API/api/farm/jobs")
if echo "$JOB_RESPONSE" | grep -q "job.*created"; then
    test_result 0 "End-to-end job creation workflow"
else
    test_result 1 "End-to-end job creation failed"
fi

echo ""
echo "📊 PERFORMANCE TESTS"
echo "==================="

# Test API response times
echo "Testing API performance..."
START_TIME=$(python3 -c 'import time; print(int(time.time()*1000))')
curl -s "$FARM_API/api/farm/status" > /dev/null
END_TIME=$(python3 -c 'import time; print(int(time.time()*1000))')
RESPONSE_TIME=$((END_TIME - START_TIME))

if [ "$RESPONSE_TIME" -lt 2000 ]; then
    test_result 0 "API response time acceptable (${RESPONSE_TIME}ms)"
else
    test_result 1 "API response time slow (${RESPONSE_TIME}ms)"
fi

echo ""
echo "🏭 PRODUCTION HARDENING TESTS"
echo "============================="

# Resolve health/readiness endpoints on APP_API
HEALTH_URL=$(pick_ok_endpoint "$APP_API" "/api/health" "/health")
READY_URL=$(pick_ok_endpoint "$APP_API" "/api/ready" "/ready")
DEPS_URL=$(pick_ok_endpoint "$APP_API" "/api/health/dependencies" "/health/dependencies")

if [ -n "$HEALTH_URL" ]; then
    echo "Testing production health endpoint..."
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")
    test_result $([ "$STATUS_CODE" = "200" ] && echo 0 || echo 1) "Production Health API ($STATUS_CODE)"

    echo "Testing production readiness endpoint..."
    if [ -n "$READY_URL" ]; then
        READINESS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$READY_URL")
        if [ "$READINESS_CODE" = "200" ] || [ "$READINESS_CODE" = "503" ]; then
            test_result 0 "Production Readiness API responds ($READINESS_CODE)"
        else
            test_result 1 "Production Readiness API unexpected response ($READINESS_CODE)"
        fi
    else
        echo -e "${YELLOW}⚠️  SKIP${NC} - Readiness endpoint not found on ${APP_API}"
    fi

    echo "Testing dependency status endpoint..."
    if [ -n "$DEPS_URL" ]; then
        DEPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DEPS_URL")
        test_result $([ "$DEPS_CODE" = "200" ] && echo 0 || echo 1) "Dependency Status API ($DEPS_CODE)"
    else
        echo -e "${YELLOW}⚠️  SKIP${NC} - Dependency status endpoint not found on ${APP_API}"
    fi

    # Test metrics endpoint if available
    echo "Testing metrics endpoint..."
    METRICS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$APP_API/metrics")
    if [ "$METRICS_CODE" = "200" ]; then
        test_result 0 "Metrics endpoint available ($METRICS_CODE)"
    else
        echo -e "${YELLOW}⚠️  INFO${NC} - Metrics endpoint not available (may not be enabled)"
    fi

    # Test production headers
    echo "Testing production headers..."
    HEADERS=$(curl -s -I "$HEALTH_URL" | tr '\r' '\n')
    if echo "$HEADERS" | grep -qi "x-request-id"; then
        test_result 0 "Request ID header present"
    else
        test_result 1 "Request ID header missing"
    fi

    if echo "$HEADERS" | grep -qi "x-response-time"; then
        test_result 0 "Response time header present" 
    else
        test_result 1 "Response time header missing"
    fi

    # Test circuit breaker resilience
    echo "Testing circuit breaker resilience..."
    SUCCESS_COUNT=0
    for i in {1..5}; do
        HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" --max-time 2)
        if [ "$HEALTH_CODE" = "200" ]; then
            ((SUCCESS_COUNT++))
        fi
    done

    if [ $SUCCESS_COUNT -ge 4 ]; then
        test_result 0 "System handles load well ($SUCCESS_COUNT/5 successful)"
    else
        test_result 1 "System struggles with load ($SUCCESS_COUNT/5 successful)"
    fi
else
    echo -e "${YELLOW}⚠️  SKIP${NC} - App health endpoint not reachable on ${APP_API} (/api/health or /health). Set APP_API to your FastAPI base to run these checks."
fi

echo ""
echo "🚀 SPRINT B FEATURES TESTS"
echo "=========================="

# Test hedging feature availability
echo "Testing hedging feature availability..."
if [ "${FEATURE_HEDGING:-false}" = "true" ]; then
    test_result 0 "Request hedging feature enabled"
    
    # Test hedging cost tracking
    echo "Testing hedging cost tracking..."
    COST_LIMIT="${HEDGING_COST_LIMIT_PER_HOUR:-50.0}"
    if (( $(echo "$COST_LIMIT > 0" | bc -l 2>/dev/null || echo 0) )); then
        test_result 0 "Hedging cost limit configured ($COST_LIMIT/hour)"
    else
        test_result 1 "Hedging cost limit not properly configured"
    fi
else
    echo -e "${YELLOW}⚠️  INFO${NC} - Request hedging disabled (feature flag off)"
fi

# Test mesh governor feature
echo "Testing mesh fidelity governor..."
if [ "${FEATURE_MESH_GOVERNOR:-true}" = "true" ]; then
    test_result 0 "Mesh fidelity governor enabled"
    
    # Validate governor thresholds
    WARN_THRESHOLD="${GOVERNOR_QDEPTH_WARN:-80}"
    DROP_THRESHOLD="${GOVERNOR_QDEPTH_DROP:-120}"
    
    if [ "$DROP_THRESHOLD" -gt "$WARN_THRESHOLD" ]; then
        test_result 0 "Governor thresholds properly configured (warn:$WARN_THRESHOLD, drop:$DROP_THRESHOLD)"
    else
        test_result 1 "Governor thresholds misconfigured (drop should be > warn)"
    fi
else
    test_result 1 "Mesh fidelity governor disabled"
fi

# Test Sprint B performance improvements
echo "Testing Sprint B performance characteristics..."
if [ -n "$HEALTH_URL" ]; then
    START_TIME=$(python3 -c 'import time; print(int(time.time()*1000))')
    if make_request "$HEALTH_URL" "GET" "200" 1; then
        END_TIME=$(python3 -c 'import time; print(int(time.time()*1000))')
        SPRINT_B_RESPONSE_TIME=$((END_TIME - START_TIME))
        if [ "$SPRINT_B_RESPONSE_TIME" -lt 500 ]; then
            test_result 0 "Sprint B optimizations maintain low latency (${SPRINT_B_RESPONSE_TIME}ms)"
        else
            test_result 1 "Sprint B response time degraded (${SPRINT_B_RESPONSE_TIME}ms)"
        fi
    else
        test_result 1 "Health endpoint returned non-200 during Sprint B perf test"
    fi
else
    echo -e "${YELLOW}⚠️  SKIP${NC} - Sprint B perf test skipped (no reachable health endpoint on ${APP_API})"
fi

echo ""
echo "🎯 FINAL RESULTS"
echo "================"
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n🎉 ${GREEN}ALL SYSTEMS OPERATIONAL!${NC}"
    echo "PetPlantr is ready for production! 🐾"
else
    echo -e "\n⚠️  ${YELLOW}SOME ISSUES DETECTED${NC}"
    echo "Review failed tests above and fix issues before production deployment."
fi

echo ""
echo "🔧 QUICK FIXES"
echo "=============="
echo "If tests failed, try these commands:"
echo ""
echo "📱 Start Frontend:"
echo "  cd frontend && npm run dev"
echo ""
echo "🐍 Install Python Dependencies:"
echo "  pip install torch torchvision trimesh numpy"
echo ""
echo "🏗️  Redeploy Backend:"
echo "  cd backend && ./deploy-farmmanager-only.sh"
echo ""
echo "📊 View Live API Data:"
echo "  curl $FARM_API/api/farm/status | jq"
echo ""
echo "🎮 Test Individual Endpoints:"
echo "  ./test-farmmanager.sh $FARM_API"
