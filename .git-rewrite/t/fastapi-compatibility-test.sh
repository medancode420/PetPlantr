#!/bin/bash

# FastAPI Version Compatibility Test Matrix
# Tests against current and pre-release FastAPI versions

echo "🧪 FastAPI Version Compatibility Test Matrix"
echo "============================================="
echo ""

# Create test environment
python3 -m venv test_env
source test_env/bin/activate

# Test matrix
FASTAPI_VERSIONS=(
    "fastapi==0.110.0"  # Current stable
    "fastapi==0.110.3"  # Latest patch
    "fastapi>=0.111.0rc1,<0.112"  # Pre-release
)

for version in "${FASTAPI_VERSIONS[@]}"; do
    echo "📦 Testing with $version"
    echo "------------------------"
    
    # Install specific version
    pip install --quiet "$version" uvicorn[standard] pydantic prometheus-client
    
    # Run basic server test
    echo "Starting server test..."
    timeout 10s python3 -c "
import asyncio
from api_server_minimal import app
from contextlib import asynccontextmanager

# Test lifespan signature compatibility
async def test_lifespan():
    async with app.router.lifespan_context(app) as manager:
        print('✅ Lifespan context manager working')

try:
    asyncio.run(test_lifespan())
    print('✅ FastAPI version compatible')
except Exception as e:
    print(f'❌ Compatibility issue: {e}')
    " || echo "❌ Test failed for $version"
    
    echo ""
done

# Cleanup
deactivate
rm -rf test_env

echo "🎉 Compatibility testing completed!"
echo ""
echo "📋 Add to CI/CD pipeline:"
echo "   - ruff check --fix"
echo "   - mypy api_server_minimal.py"
echo "   - FastAPI version matrix testing"
