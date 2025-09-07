#!/bin/bash
# Quick test runner for PetPlantr development

set -e

echo "🧪 PetPlantr Test Runner"
echo "======================="

# Activate virtual environment if available
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Set test environment
export ENVIRONMENT=test
export PYTHONPATH="$(pwd):${PYTHONPATH}"
# Disable noisy third-party pytest plugin autoload and explicitly enable only what we need
export PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
PLUGS_BASE="-p pytest_asyncio -p respx"
PLUGS_COV="-p pytest_cov ${PLUGS_BASE}"

case "${1:-all}" in
    "critical")
        echo "🔥 Running CRITICAL tests only..."
        python -m pytest tests/test_critical_business_logic.py -v --tb=short -m critical ${PLUGS_BASE}
        ;;
    "fast")
        echo "⚡ Running FAST tests only..."
        python -m pytest tests/ -v --tb=short -m "not slow" --maxfail=3 ${PLUGS_BASE}
        ;;
    "ai")
        echo "🤖 Running AI/ML tests..."
        python -m pytest tests/test_ai_model_quality.py -v --tb=short -m ai ${PLUGS_BASE}
        ;;
    "security")
        echo "🔒 Running SECURITY tests..."
        python -m pytest tests/test_security_auth.py -v --tb=short -m security ${PLUGS_BASE}
        echo "🛡️ Running security scan..."
        bandit -r . -f json --severity-level medium || true
        ;;
    "api")
        echo "🌐 Running API tests..."
        python -m pytest tests/test_api_endpoints.py -v --tb=short -m integration ${PLUGS_BASE}
        ;;
    "coverage")
        echo "📊 Running tests with coverage..."
        python -m pytest tests/ -v ${PLUGS_COV} --cov=src --cov-report=term-missing --cov-report=xml:coverage.xml
        echo "📄 Coverage report: file://$(pwd)/htmlcov/index.html"
        ;;
    "benchmark")
        echo "🏃‍♀️ Running performance benchmarks..."
        python -m pytest tests/ -v --benchmark-only --benchmark-sort=mean ${PLUGS_BASE}
        ;;
    "smoke")
        echo "💨 Running smoke tests..."
        python -m pytest tests/test_critical_business_logic.py::TestSTLMathValidation::test_stl_triangle_count_accuracy -v ${PLUGS_BASE}
        python -m pytest tests/test_critical_business_logic.py::TestPricingLogic::test_pricing_accuracy -v ${PLUGS_BASE}
        ;;
    *)
        echo "🎯 Running ALL tests..."
        python -m pytest tests/ -v --tb=short --maxfail=5 ${PLUGS_COV} --cov=src --cov-report=term-missing --cov-report=xml:coverage.xml
        ;;
esac

echo ""
echo "✅ Test run complete!"
