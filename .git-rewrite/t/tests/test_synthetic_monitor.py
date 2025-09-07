import time
import pytest


@pytest.mark.sprint_c
def test_synthetic_monitor_live_sample(monkeypatch):
    # Ensure ops + monitor enabled before app import
    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")
    monkeypatch.setenv("FEATURE_SYNTHETIC_MONITOR", "true")

    from api_server_minimal import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Poll the live endpoint until a sample appears (with small timeout)
    deadline = time.time() + 2.5
    last = None
    enabled = None
    while time.time() < deadline:
        r = client.get("/api/v1/ops/synthetic/live")
        assert r.status_code == 200
        payload = r.json()
        enabled = payload.get("enabled")
        last = payload.get("last")
        if enabled and last:
            break
        time.sleep(0.05)

    assert enabled is True
    assert isinstance(last, dict)
    # Basic shape of the sample
    assert "latency_ms" in last
    assert "health" in last
    assert "breed" in last


@pytest.mark.sprint_c
def test_synthetic_monitor_disabled_flag(monkeypatch):
    # Disable monitor before app import
    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")
    monkeypatch.setenv("FEATURE_SYNTHETIC_MONITOR", "false")

    from importlib import reload
    import src.core.settings as settings_mod
    reload(settings_mod)

    from api_server_minimal import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    r = client.get("/api/v1/ops/synthetic/live")
    assert r.status_code == 200
    data = r.json()
    assert data.get("enabled") is False
    # Last may be None or an old value; only assert key presence
    assert "last" in data
