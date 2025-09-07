"""
Unit tests for API enhancements
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json

def test_batch_prediction_endpoint(client):
    """Test batch prediction endpoint"""
    test_data = {
        "images": ["base64_test_image_1", "base64_test_image_2"],
        "options": {"model": "clip-dpt"}
    }

    response = client.post("/api/v2/predict/batch", json=test_data)
    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert "total_processed" in data
    assert data["total_processed"] == 2
    assert len(data["results"]) == 2

def test_analytics_endpoint(client):
    """Test analytics endpoint"""
    response = client.get("/api/v2/analytics?days=7")
    assert response.status_code == 200

    data = response.json()
    assert "total_predictions" in data
    assert "average_confidence" in data
    assert "top_breeds" in data
    assert "performance_metrics" in data

def test_detailed_health_endpoint(client):
    """Test detailed health endpoint"""
    response = client.get("/api/v2/health/detailed")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "uptime" in data
    assert "memory_usage" in data
    assert "cpu_usage" in data

def test_feedback_endpoint(client):
    """Test feedback submission"""
    feedback_data = {
        "rating": 5,
        "comment": "Great prediction!",
        "breed": "Golden Retriever",
        "actual_breed": "Golden Retriever"
    }

    response = client.post("/api/v2/feedback", json=feedback_data)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"

def test_model_info_endpoint(client):
    """Test model information endpoint"""
    response = client.get("/api/v2/models/info")
    assert response.status_code == 200

    data = response.json()
    assert "models" in data
    assert "status" in data
    assert len(data["models"]) > 0
