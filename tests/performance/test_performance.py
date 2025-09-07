"""
Performance tests for PetPlantr
"""

import pytest
import time
from fastapi.testclient import TestClient

def test_api_response_time(client):
    """Test API response time"""
    start_time = time.time()
    response = client.get("/api/v1/health")
    end_time = time.time()

    assert response.status_code == 200
    response_time = end_time - start_time
    assert response_time < 1.0  # Should respond within 1 second

def test_batch_processing_performance(client):
    """Test batch processing performance"""
    test_data = {
        "images": ["base64_test_image"] * 5,
        "options": {"model": "clip-dpt"}
    }

    start_time = time.time()
    response = client.post("/api/v2/predict/batch", json=test_data)
    end_time = time.time()

    assert response.status_code == 200
    processing_time = end_time - start_time
    assert processing_time < 5.0  # Should process within 5 seconds

def test_memory_usage(client):
    """Test memory usage under load"""
    import psutil
    import os

    # Get initial memory
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Make multiple requests
    for _ in range(10):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    # Check memory hasn't grown excessively
    final_memory = process.memory_info().rss
    memory_growth = final_memory - initial_memory
    max_growth = 50 * 1024 * 1024  # 50MB max growth
    assert memory_growth < max_growth

def test_concurrent_performance(client):
    """Test performance under concurrent load"""
    import threading
    import queue

    results = queue.Queue()
    errors = []

    def make_request():
        try:
            start_time = time.time()
            response = client.get("/api/v1/health")
            end_time = time.time()

            if response.status_code == 200:
                response_time = end_time - start_time
                results.put(response_time)
            else:
                errors.append(f"Status: {response.status_code}")
        except Exception as e:
            errors.append(str(e))

    # Start concurrent requests
    threads = []
    for _ in range(20):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Check results
    response_times = []
    while not results.empty():
        response_times.append(results.get())

    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(response_times) == 20

    # Check average response time
    avg_response_time = sum(response_times) / len(response_times)
    assert avg_response_time < 2.0  # Average should be under 2 seconds

    # Check no response took too long
    max_response_time = max(response_times)
    assert max_response_time < 5.0  # Max should be under 5 seconds
