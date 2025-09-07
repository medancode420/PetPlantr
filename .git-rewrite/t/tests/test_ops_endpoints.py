import pytest
import os

@pytest.mark.sprint_c
def test_ops_hedging_config_and_kill_switch(monkeypatch):
    # Ensure ops endpoints are enabled before app import
    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")

    from api_server_minimal import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # If OPS_TOKEN is set in the environment, include it in all requests
    headers = {}
    ops_token = os.environ.get("OPS_TOKEN")
    if ops_token:
        headers["X-Ops-Token"] = ops_token

    # GET current hedging config
    r = client.get("/api/v1/ops/hedging/config", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "feature_enabled" in data

    # POST update to enable adaptive hedging and adjust bounds
    r2 = client.post(
        "/api/v1/ops/hedging/config",
        json={
            "feature_adaptive_hedging": True,
            "hedging_min_delay_ms": 80,
            "hedging_max_delay_ms": 500,
            "adaptive_ema_alpha": 0.25,
        },
        headers=headers,
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("feature_adaptive") is True
    assert d2.get("min_delay_ms") == 80
    assert d2.get("max_delay_ms") == 500

    # Enable kill switch -> hedging_allowed should be False
    r3 = client.post("/api/v1/ops/kill-switch", json={"action": "enable"}, headers=headers)
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3.get("hedging_allowed") is False

    # Disable kill switch -> hedging_allowed should be True
    r4 = client.post("/api/v1/ops/kill-switch", json={"action": "disable"}, headers=headers)
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4.get("hedging_allowed") is True
