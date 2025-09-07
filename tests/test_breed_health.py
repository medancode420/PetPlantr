"""
Breed API health and gating tests.
These tests verify the ENABLE_BREED_API flag and model loaded gating without requiring torch/CLIP.
"""

import importlib
from fastapi import FastAPI
from fastapi.testclient import TestClient


def make_app():
    # Import router fresh each time to avoid globals leaking
    breed = importlib.import_module("src.api.routes.breed")
    app = FastAPI()
    app.include_router(breed.router, prefix="/api/v1")
    return app


import pytest


@pytest.mark.sprint_c
def test_health_503_when_api_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_BREED_API", "false")
    app = make_app()
    client = TestClient(app)
    r = client.get("/api/v1/breed/health")
    assert r.status_code == 503


@pytest.mark.sprint_c
def test_health_503_when_model_not_loaded(monkeypatch):
    monkeypatch.setenv("ENABLE_BREED_API", "true")
    # Monkeypatch service model info
    svc = importlib.import_module("src.services.breed_detection")
    monkeypatch.setattr(svc, "get_model_info", lambda: {"loaded": False})
    app = make_app()
    client = TestClient(app)
    r = client.get("/api/v1/breed/health")
    assert r.status_code == 503


@pytest.mark.sprint_c
def test_health_200_when_model_loaded(monkeypatch):
    monkeypatch.setenv("ENABLE_BREED_API", "true")
    svc = importlib.import_module("src.services.breed_detection")
    monkeypatch.setattr(svc, "get_model_info", lambda: {"loaded": True, "model_version": "test", "device": "cpu", "num_breeds": 5})
    app = make_app()
    client = TestClient(app)
    r = client.get("/api/v1/breed/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["model_loaded"] is True
