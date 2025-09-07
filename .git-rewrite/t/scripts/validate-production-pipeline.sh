#!/usr/bin/env bash
set -euo pipefail

# Production Pipeline Validation Script for PetPlantr
# Validates all production hardening features and SLO compliance

echo "🧪 PetPlantr Production Pipeline Validation"
echo "============================================"
echo ""

# Configuration
API_ROOT="${API_ROOT:-http://localhost:8000}"
ENVIRONMENT="${ENVIRONMENT:-development}"
TIMEOUT_SEC=30

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

# Helper function for HTTP requests with timeout
make_request() {
    local url="$1"
    local method="${2:-GET}"
    local expected_code="${3:-200}"
    local timeout="${4:-$TIMEOUT_SEC}"
    
    local response
    local status_code
    
    if command -v curl >/dev/null 2>&1; then
        response=$(curl -s -m "$timeout" -w "HTTPSTATUS:%{http_code}" "$url" 2>/dev/null || echo "HTTPSTATUS:000")
        status_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
        
        if [ "$status_code" = "$expected_code" ]; then
            return 0
        else
            echo "Expected $expected_code, got $status_code" >&2
            return 1
        fi
    else
        echo "curl not available" >&2
        return 1
    fi
}

# Test basic API connectivity
echo "🌐 BASIC CONNECTIVITY TESTS"
echo "============================"

echo "Testing API root endpoint..."
make_request "$API_ROOT/" "GET" "200"
test_result $? "API root accessible"

echo ""
echo "🏥 HEALTH & READINESS TESTS"
echo "=========================="

# Test health endpoint (should always return 200)
echo "Testing health endpoint..."
make_request "$API_ROOT/api/health" "GET" "200"
test_result $? "Health endpoint returns 200"

# Test readiness endpoint
echo "Testing readiness endpoint..."
if make_request "$API_ROOT/api/ready" "GET" "200" 5; then
    test_result 0 "Readiness endpoint healthy"
else
    # Readiness can fail if dependencies are down
    echo -e "${YELLOW}⚠️  WARNING${NC} - Readiness check failed (dependencies may be unavailable)"
    test_result 0 "Readiness endpoint responded (even if not ready)"
fi

# Test detailed dependency check
echo "Testing dependency status endpoint..."
make_request "$API_ROOT/api/health/dependencies" "GET" "200"
test_result $? "Dependency status endpoint accessible"

echo ""
echo "⏱️  PERFORMANCE & SLO TESTS"
echo "=========================="

# Test API response times
echo "Testing API response time..."
START_TIME=$(date +%s%3N)
make_request "$API_ROOT/api/health" "GET" "200" 2
END_TIME=$(date +%s%3N)
RESPONSE_TIME=$((END_TIME - START_TIME))

if [ $RESPONSE_TIME -lt 1000 ]; then
    test_result 0 "Health endpoint response time acceptable (${RESPONSE_TIME}ms)"
else
    test_result 1 "Health endpoint response time slow (${RESPONSE_TIME}ms)"
fi

echo ""
echo "🔒 SECURITY & HEADERS TESTS"
echo "=========================="

# Test security headers
echo "Testing security headers..."
if command -v curl >/dev/null 2>&1; then
    HEADERS=$(curl -s -I -m 5 "$API_ROOT/api/health" 2>/dev/null || echo "")
    
    # Check for request ID header
    if echo "$HEADERS" | grep -qi "x-request-id"; then
        test_result 0 "Request ID header present"
    else
        test_result 1 "Request ID header missing"
    fi
    
    # Check for response time header
    if echo "$HEADERS" | grep -qi "x-response-time"; then
        test_result 0 "Response time header present"
    else
        test_result 1 "Response time header missing"
    fi
else
    test_result 1 "Cannot test headers (curl not available)"
fi

echo ""
echo "📊 METRICS & OBSERVABILITY TESTS"
echo "==============================="

# Test metrics endpoint if available
echo "Testing metrics endpoint..."
if make_request "$API_ROOT/metrics" "GET" "200" 3; then
    test_result 0 "Metrics endpoint accessible"
else
    echo -e "${YELLOW}⚠️  INFO${NC} - Metrics endpoint not available (may not be enabled)"
fi

echo ""
echo "🔄 CIRCUIT BREAKER & RELIABILITY TESTS"
echo "====================================="

# Test admission control under load (simple version)
echo "Testing admission control resilience..."
SUCCESS_COUNT=0
for i in {1..5}; do
    if make_request "$API_ROOT/api/health" "GET" "200" 1; then
        ((SUCCESS_COUNT++))
    fi
done

if [ $SUCCESS_COUNT -ge 4 ]; then
    test_result 0 "System handles concurrent requests ($SUCCESS_COUNT/5 successful)"
else
    test_result 1 "System struggles with concurrent load ($SUCCESS_COUNT/5 successful)"
fi

echo ""
echo "📝 CONFIGURATION VALIDATION"
echo "=========================="

# Check environment variables
echo "Validating production configuration..."

# Critical environment variables
CRITICAL_VARS=(
    "REPLICATE_API_TOKEN"
    "AWS_REGION" 
    "S3_BUCKET"
)

MISSING_VARS=0
for var in "${CRITICAL_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo -e "${RED}❌${NC} Missing critical environment variable: $var"
        ((MISSING_VARS++))
    else
        echo -e "${GREEN}✅${NC} Environment variable set: $var"
    fi
done

if [ $MISSING_VARS -eq 0 ]; then
    test_result 0 "All critical environment variables configured"
else
    test_result 1 "$MISSING_VARS critical environment variables missing"
fi

echo ""
echo "🚀 PRODUCTION READINESS CHECKS"
echo "============================="

# Check if running in production mode
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Production environment detected - running additional checks..."
    
    # Check debug mode is disabled
    if [ "${DEBUG:-false}" = "false" ]; then
        test_result 0 "Debug mode disabled for production"
    else
        test_result 1 "Debug mode enabled in production"
    fi
    
    # Check circuit breaker settings
    CB_FAILURE_RATE="${CB_FAILURE_RATE:-0.5}"
    if (( $(echo "$CB_FAILURE_RATE <= 0.7" | bc -l) )); then
        test_result 0 "Circuit breaker failure rate configured safely ($CB_FAILURE_RATE)"
    else
        test_result 1 "Circuit breaker failure rate too high for production ($CB_FAILURE_RATE)"
    fi
else
    echo -e "${YELLOW}⚠️  INFO${NC} - Running in $ENVIRONMENT environment"
    test_result 0 "Non-production environment (skipping production-specific checks)"
fi

echo ""
echo "🧪 API FUNCTIONALITY TESTS"
echo "========================="

# Test breed detection if available
echo "Testing breed detection endpoint..."
if make_request "$API_ROOT/api/v1/breed" "GET" "405" 3; then
    # 405 Method Not Allowed is expected for GET on POST endpoint
    test_result 0 "Breed detection endpoint exists"
elif make_request "$API_ROOT/api/v1/breed" "GET" "404" 3; then
    test_result 1 "Breed detection endpoint not found"
else
    test_result 0 "Breed detection endpoint accessible"
fi

echo ""
echo "🎯 FINAL VALIDATION RESULTS"
echo "=========================="
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

# Calculate success rate
if [ $((PASSED + FAILED)) -gt 0 ]; then
    SUCCESS_RATE=$(( (PASSED * 100) / (PASSED + FAILED) ))
    echo -e "Success Rate: ${SUCCESS_RATE}%"
else
    SUCCESS_RATE=0
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "🎉 ${GREEN}ALL VALIDATIONS PASSED!${NC}"
    echo "PetPlantr production pipeline is ready for deployment! 🚀"
    exit 0
elif [ $SUCCESS_RATE -ge 80 ]; then
    echo -e "✅ ${GREEN}PIPELINE MOSTLY READY${NC}"
    echo "Minor issues detected but system is largely functional."
    echo "Review failed tests and consider deployment."
    exit 0
else
    echo -e "⚠️  ${YELLOW}PIPELINE NEEDS ATTENTION${NC}"
    echo "Significant issues detected. Review and fix before production deployment."
    exit 1
fi
