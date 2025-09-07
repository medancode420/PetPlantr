#!/bin/bash
# Run PetPlantr test suite

echo "🧪 Running PetPlantr Test Suite..."

# Install test dependencies if needed
pip install pytest pytest-cov pytest-asyncio aiohttp psutil

# Run unit tests
echo "📋 Running Unit Tests..."
pytest tests/unit/ -v --cov=api_enhancements --cov-report=html

# Run integration tests
echo "🔗 Running Integration Tests..."
pytest tests/integration/ -v

# Run performance tests
echo "⚡ Running Performance Tests..."
pytest tests/performance/ -v --durations=10

# Generate coverage report
echo "📊 Generating Coverage Report..."
coverage html
coverage report

echo "✅ Test suite completed!"
echo "📈 Coverage report: htmlcov/index.html"
