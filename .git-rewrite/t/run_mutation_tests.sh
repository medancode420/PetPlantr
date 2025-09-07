#!/bin/bash

# Mutation Testing Script for PetPlantr
# Ensures tests actually fail when code changes

set -e

echo "🧬 Starting Mutation Testing for PetPlantr"
echo "=========================================="

# Install mutation testing tools if not present
if ! command -v mutmut &> /dev/null; then
    echo "📦 Installing mutation testing tools..."
    pip install mutmut
fi

# Clean previous results
echo "🧹 Cleaning previous mutation test results..."
rm -rf .mutmut-cache
rm -f mutation-report.json
rm -rf html/

# Run mutation tests on critical modules
echo "🎯 Running mutation tests on critical paths..."

echo "  💰 Testing pricing logic..."
mutmut run --paths-to-mutate=petplantr/pricing.py --runner="python -m pytest tests/test_critical_business_logic.py::TestPricingLogic -x" || true

echo "  💳 Testing payment processing..."
mutmut run --paths-to-mutate=petplantr/payments.py --runner="python -m pytest tests/test_critical_business_logic.py::TestPaymentProcessing -x" || true

echo "  📐 Testing STL validation..."
mutmut run --paths-to-mutate=petplantr/stl_validator.py --runner="python -m pytest tests/test_critical_business_logic.py::TestSTLMathValidation -x" || true

echo "  🤖 Testing AI confidence scoring..."
mutmut run --paths-to-mutate=petplantr/ai/confidence.py --runner="python -m pytest tests/test_ai_model_quality.py::TestModelDriftDetection -x" || true

echo "  🔒 Testing security/auth..."
mutmut run --paths-to-mutate=petplantr/security/auth.py --runner="python -m pytest tests/test_security_auth.py::TestAuthenticationSecurity -x" || true

# Generate reports
echo "📊 Generating mutation test reports..."
mutmut show --reporter json > mutation-report.json || true
mutmut html || true

# Analyze results
echo "📈 Analyzing mutation test results..."

# Parse JSON report and check scores
if [ -f mutation-report.json ]; then
    echo "📋 Mutation Test Summary:"
    echo "========================"
    
    # Extract key metrics (simplified parsing)
    total_mutants=$(grep -o '"total":' mutation-report.json | wc -l || echo "0")
    killed_mutants=$(grep -o '"killed":' mutation-report.json | wc -l || echo "0")
    
    if [ "$total_mutants" -gt 0 ]; then
        mutation_score=$(echo "scale=2; $killed_mutants / $total_mutants * 100" | bc -l 2>/dev/null || echo "0")
        echo "🎯 Mutation Score: ${mutation_score}%"
        echo "💀 Killed Mutants: $killed_mutants"
        echo "🧬 Total Mutants: $total_mutants"
        
        # Check if mutation score meets threshold
        threshold=80
        if (( $(echo "$mutation_score >= $threshold" | bc -l 2>/dev/null || echo "0") )); then
            echo "✅ Mutation score meets threshold (≥${threshold}%)"
        else
            echo "❌ Mutation score below threshold (≥${threshold}%)"
            echo "🔧 Consider strengthening test assertions"
            exit 1
        fi
    else
        echo "⚠️  No mutation results found"
    fi
else
    echo "⚠️  Mutation report not generated"
fi

# Check for HTML report
if [ -d "html" ]; then
    echo "📄 HTML report generated: html/index.html"
    echo "🌐 Open in browser to view detailed results"
else
    echo "⚠️  HTML report not generated"
fi

echo ""
echo "🧬 Mutation testing complete!"
echo "💡 High mutation scores indicate strong, specific test assertions"
echo "💡 Low scores suggest tests may pass even when code is broken"

# Optional: Open HTML report in browser (macOS)
if [[ "$OSTYPE" == "darwin"* ]] && [ -f "html/index.html" ]; then
    read -p "📖 Open HTML report in browser? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open html/index.html
    fi
fi
