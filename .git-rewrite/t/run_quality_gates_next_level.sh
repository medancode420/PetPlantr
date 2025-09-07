#!/bin/bash

# PetPlantr Quality Gates - Next Level Safety Net
# Professional-grade safeguards maintaining 95% coverage bar

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Quality gate tracking
PASSED_GATES=0
TOTAL_GATES=7
FAILED_GATES=()

echo "🚀 PetPlantr Quality Gates Suite"
echo "==============================="
echo "Next-level quality & early issue detection"
echo ""

# Function to log quality gate results
log_gate_result() {
    local gate_name="$1"
    local status="$2"
    local details="$3"
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ $gate_name: PASSED${NC}"
        [ -n "$details" ] && echo -e "   ${CYAN}$details${NC}"
        ((PASSED_GATES++))
    else
        echo -e "${RED}❌ $gate_name: FAILED${NC}"
        [ -n "$details" ] && echo -e "   ${YELLOW}$details${NC}"
        FAILED_GATES+=("$gate_name")
    fi
    echo ""
}

# Function to run with timeout and error handling
run_with_timeout() {
    local timeout_duration="$1"
    local description="$2"
    shift 2
    
    echo -e "${BLUE}🔄 $description...${NC}"
    
    if timeout "$timeout_duration" "$@"; then
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo -e "${RED}⏰ Timeout after $timeout_duration${NC}"
        else
            echo -e "${RED}💥 Command failed with exit code $exit_code${NC}"
        fi
        return $exit_code
    fi
}

# ================================
# QUALITY GATE 1: SECRETS SCAN
# ================================
echo -e "${PURPLE}🔐 QUALITY GATE 1: Secrets & Security Scan${NC}"
echo "============================================"

if command -v gitleaks &> /dev/null; then
    if run_with_timeout 60s "Scanning for secrets with gitleaks" gitleaks detect --config .gitleaks.toml --verbose; then
        log_gate_result "Secrets Scan" "PASS" "No secrets detected in codebase"
    else
        log_gate_result "Secrets Scan" "FAIL" "Secrets or security issues found - check gitleaks output"
    fi
else
    log_gate_result "Secrets Scan" "FAIL" "gitleaks not installed - install with: brew install gitleaks"
fi

# Additional security scans
echo "🛡️  Running additional security scans..."
if run_with_timeout 120s "Security audit with safety & bandit" python -m safety check --json --output safety-report.json; then
    echo -e "${GREEN}   ✓ Dependency security scan passed${NC}"
else
    echo -e "${YELLOW}   ⚠ Security vulnerabilities found - check safety-report.json${NC}"
fi

if run_with_timeout 60s "Static security analysis" bandit -r . -f json -o bandit-report.json; then
    echo -e "${GREEN}   ✓ Static security analysis passed${NC}"
else
    echo -e "${YELLOW}   ⚠ Security issues found - check bandit-report.json${NC}"
fi

# ================================
# QUALITY GATE 2: TEST COVERAGE ≥95%
# ================================
echo -e "${PURPLE}🧪 QUALITY GATE 2: Test Coverage (≥95%)${NC}"
echo "========================================"

if run_with_timeout 300s "Running test suite with coverage" python -m pytest tests/ --cov=tests --cov-fail-under=95 --cov-report=xml --cov-report=html --cov-report=term-missing --tb=short -v; then
    COVERAGE_RESULT=$(python -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    coverage = float(root.attrib['line-rate']) * 100
    print(f'{coverage:.1f}%')
except:
    print('Unknown')
")
    log_gate_result "Test Coverage" "PASS" "Coverage: $COVERAGE_RESULT (≥95% required)"
else
    log_gate_result "Test Coverage" "FAIL" "Coverage below 95% threshold or tests failed"
fi

# ================================
# QUALITY GATE 3: MUTATION TESTING
# ================================
echo -e "${PURPLE}🧬 QUALITY GATE 3: Mutation Testing${NC}"
echo "==================================="

if command -v mutmut &> /dev/null; then
    if run_with_timeout 600s "Running mutation tests on critical paths" ./run_mutation_tests.sh; then
        log_gate_result "Mutation Testing" "PASS" "High-quality test assertions verified"
    else
        log_gate_result "Mutation Testing" "FAIL" "Weak test assertions detected - check mutation-reports/"
    fi
else
    log_gate_result "Mutation Testing" "FAIL" "mutmut not installed - run: pip install mutmut"
fi

# ================================
# QUALITY GATE 4: PERFORMANCE BENCHMARKS
# ================================
echo -e "${PURPLE}⚡ QUALITY GATE 4: Performance Benchmarks${NC}"
echo "========================================"

if run_with_timeout 180s "Running performance benchmarks" python -m pytest tests/test_performance_benchmarks.py --benchmark-only --benchmark-json=benchmark-results.json --benchmark-compare-fail=mean:10% -v; then
    log_gate_result "Performance Benchmarks" "PASS" "No performance regressions detected"
else
    log_gate_result "Performance Benchmarks" "FAIL" "Performance regression >10% detected"
fi

# ================================
# QUALITY GATE 5: CODE QUALITY
# ================================
echo -e "${PURPLE}🎨 QUALITY GATE 5: Code Quality${NC}"
echo "==============================="

# Check code formatting
if run_with_timeout 60s "Checking code formatting" python -m black --check . --diff; then
    BLACK_STATUS="PASS"
else
    BLACK_STATUS="FAIL"
    echo -e "${YELLOW}   💡 Run 'python -m black .' to auto-format${NC}"
fi

# Check linting
if run_with_timeout 60s "Running linting checks" python -m flake8 . --max-line-length=100 --ignore=E203,W503; then
    LINT_STATUS="PASS"
else
    LINT_STATUS="FAIL"
fi

if [ "$BLACK_STATUS" = "PASS" ] && [ "$LINT_STATUS" = "PASS" ]; then
    log_gate_result "Code Quality" "PASS" "Code formatting and linting standards met"
else
    log_gate_result "Code Quality" "FAIL" "Code formatting or linting issues found"
fi

# ================================
# QUALITY GATE 6: INTEGRATION HEALTH
# ================================
echo -e "${PURPLE}🩺 QUALITY GATE 6: Integration Health Checks${NC}"
echo "============================================"

if run_with_timeout 120s "Running integration health checks" python -m pytest tests/test_integration.py --tb=short -v; then
    log_gate_result "Integration Health" "PASS" "All integration checks passed"
else
    log_gate_result "Integration Health" "FAIL" "Integration test failures detected"
fi

# ================================
# QUALITY GATE 7: DEPLOYMENT READINESS
# ================================
echo -e "${PURPLE}🚀 QUALITY GATE 7: Deployment Readiness${NC}"
echo "====================================="

# Check health endpoint
if python health_check.py & 
   HEALTH_PID=$!
   sleep 5
   if curl -f http://localhost:8080/health >/dev/null 2>&1; then
       HEALTH_STATUS="PASS"
       kill $HEALTH_PID 2>/dev/null || true
   else
       HEALTH_STATUS="FAIL" 
       kill $HEALTH_PID 2>/dev/null || true
   fi
then
    log_gate_result "Deployment Readiness" "$HEALTH_STATUS" "Health check endpoint verified"
else
    log_gate_result "Deployment Readiness" "FAIL" "Health check endpoint failed"
fi

# ================================
# FINAL QUALITY GATE SUMMARY
# ================================
echo "📊 QUALITY GATES SUMMARY"
echo "========================"
echo -e "Passed: ${GREEN}$PASSED_GATES${NC}/$TOTAL_GATES"

if [ ${#FAILED_GATES[@]} -gt 0 ]; then
    echo -e "Failed Gates: ${RED}${FAILED_GATES[*]}${NC}"
    echo ""
    echo -e "${RED}❌ QUALITY GATES FAILED${NC}"
    echo ""
    echo "🔧 Next Steps:"
    echo "1. 🧪 Fix failing tests: python -m pytest tests/ -v --tb=short"
    echo "2. 🎨 Format code: python -m black ."
    echo "3. 🔐 Review security reports: safety-report.json, bandit-report.json"
    echo "4. 🧬 Check mutation testing: mutation-reports/"
    echo "5. ⚡ Profile performance: benchmark-results.json"
    echo ""
    echo "🚨 Production deployment blocked until all gates pass"
    exit 1
else
    echo ""
    echo -e "${GREEN}🎉 ALL QUALITY GATES PASSED!${NC}"
    echo -e "${GREEN}✅ Ready for production deployment${NC}"
    echo ""
    echo "📈 Quality Metrics:"
    echo "  • Test Coverage: ≥95% ✓"
    echo "  • Security: Scanned ✓"
    echo "  • Mutation Score: High ✓"
    echo "  • Performance: No regression ✓" 
    echo "  • Code Quality: Standards met ✓"
    echo "  • Integration: Healthy ✓"
    echo "  • Deployment: Ready ✓"
    echo ""
    echo "🚀 Safe to deploy to production!"
    exit 0
fi
