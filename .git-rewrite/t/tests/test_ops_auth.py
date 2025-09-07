import pytest

@pytest.mark.sprint_c
def test_ops_endpoints_require_token_when_set(monkeypatch):
    # Enable ops endpoints and set ops token before import
    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")
    monkeypatch.setenv("OPS_TOKEN", "secret123")

    from importlib import reload
    import api_server_minimal as mod
    reload(mod)
    from fastapi.testclient import TestClient

    client = TestClient(mod.app)

    # Missing token -> 401
    r1 = client.get("/api/v1/ops/hedging/config")
    assert r1.status_code == 401

    # Wrong token -> 401
    r2 = client.get("/api/v1/ops/hedging/config", headers={"X-Ops-Token": "wrong"})
    assert r2.status_code == 401

    # Correct token -> 200
    r3 = client.get("/api/v1/ops/hedging/config", headers={"X-Ops-Token": "secret123"})
    assert r3.status_code == 200
