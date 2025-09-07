"""
Metrics endpoint test with stubbed service metrics.
"""
import importlib
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def make_app():
    breed = importlib.import_module("src.api.routes.breed")
    app = FastAPI()
    app.include_router(breed.router, prefix="/api/v1")
    return app


@pytest.mark.sprint_c
def test_metrics_ok(monkeypatch):
    monkeypatch.setenv("ENABLE_BREED_API", "true")
    svc = importlib.import_module("src.services.breed_detection")

    monkeypatch.setattr(svc, "get_model_info", lambda: {"loaded": True})
    monkeypatch.setattr(
        svc,
        "get_performance_metrics",
        lambda: {"loaded": True, "requests_total": 3, "in_flight": 0, "avg_duration_ms": 12.3},
    )

    app = make_app()
    client = TestClient(app)
    r = client.get("/api/v1/breed/metrics")
    assert r.status_code == 200
    body = r.json()
    assert body["loaded"] is True
    assert "requests_total" in body
