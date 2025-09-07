#!/bin/bash

# PetPlantr Test-on-Save Script
# Provides instant feedback for developers

echo "🧪 PetPlantr Test-on-Save - Starting Watch Mode"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to show usage
show_usage() {
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  full        - Watch all files, run full test suite (default)"
    echo "  quick       - Watch critical files only, run quick tests"
    echo "  critical    - Watch business logic, run critical tests only"
    echo "  performance - Watch for performance regressions"
    echo ""
    echo "Examples:"
    echo "  $0              # Full watch mode"
    echo "  $0 quick        # Quick test mode"
    echo "  $0 critical     # Critical business logic only"
    echo "  $0 performance  # Performance benchmarks only"
}

# Parse command line arguments
MODE=${1:-full}

case $MODE in
    full)
        echo -e "${GREEN}🔍 Full Watch Mode - All tests on any Python file change${NC}"
        ptw --runner="python -m pytest tests/ --tb=short -v --maxfail=5" \
            --ignore=".venv" \
            --ignore="htmlcov" \
            --ignore=".pytest_cache" \
            --ignore="__pycache__" \
            --patterns="*.py"
        ;;
    
    quick)
        echo -e "${YELLOW}⚡ Quick Test Mode - Critical tests only${NC}"
        ptw --runner="python -m pytest tests/test_critical_business_logic.py -v --tb=short --maxfail=3" \
            --ignore=".venv" \
            --ignore="htmlcov" \
            --patterns="**/pricing.py,**/payments.py,**/stl_validator.py,tests/test_critical_*.py"
        ;;
    
    critical)
        echo -e "${RED}🎯 Critical Path Mode - Business logic only${NC}"
        ptw --runner="python -m pytest tests/test_critical_business_logic.py tests/test_security_auth.py -v --tb=short" \
            --ignore=".venv" \
            --patterns="**/pricing.py,**/payments.py,**/auth.py,**/stl_validator.py"
        ;;
    
    performance)
        echo -e "${YELLOW}⚡ Performance Mode - Benchmark tests only${NC}"
        ptw --runner="python -m pytest tests/test_performance_benchmarks.py --benchmark-only --benchmark-compare-fail=mean:10% -v" \
            --ignore=".venv" \
            --patterns="**/performance*.py,**/benchmark*.py,tests/test_performance_*.py"
        ;;
    
    help|--help|-h)
        show_usage
        exit 0
        ;;
    
    *)
        echo -e "${RED}❌ Unknown mode: $MODE${NC}"
        show_usage
        exit 1
        ;;
esac
