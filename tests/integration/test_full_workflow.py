"""
Integration tests for full PetPlantr workflow
"""

import pytest
import time
from fastapi.testclient import TestClient

def test_full_prediction_workflow(client):
    """Test complete prediction workflow"""
    # This would test the full pipeline from image upload to result
    # For now, we'll test the API endpoints integration

    # Test health check
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    # Test analytics
    response = client.get("/api/v2/analytics")
    assert response.status_code == 200

    # Test model info
    response = client.get("/api/v2/models/info")
    assert response.status_code == 200

def test_concurrent_requests(client):
    """Test handling of concurrent requests"""
    import asyncio
    import aiohttp

    async def make_request(session, url):
        async with session.get(url) as response:
            return response.status

    async def test_concurrency():
        urls = ["http://localhost:8000/api/v1/health"] * 10
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return results

    # Run concurrency test
    results = asyncio.run(test_concurrency())
    assert all(status == 200 for status in results)

def test_error_handling(client):
    """Test error handling across endpoints"""
    # Test invalid batch prediction
    response = client.post("/api/v2/predict/batch", json={"images": []})
    assert response.status_code in [400, 422]  # Bad request or validation error

    # Test invalid analytics request
    response = client.get("/api/v2/analytics?days=-1")
    assert response.status_code in [400, 422]
