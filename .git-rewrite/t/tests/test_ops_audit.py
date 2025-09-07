import pytest

@pytest.mark.unit
def test_audit_logs_success_and_denied(monkeypatch):
    # Enable ops and set token before import
    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")
    monkeypatch.setenv("OPS_TOKEN", "secret")

    from importlib import reload
    import api_server_minimal as mod
    reload(mod)
    from fastapi.testclient import TestClient

    client = TestClient(mod.app)

    # 1) Denied attempt (wrong token)
    r1 = client.post(
        "/api/v1/ops/hedging/config",
        headers={"X-Ops-Token": "wrong"},
        json={"hedging_min_delay_ms": 80},
    )
    assert r1.status_code == 401

    # 2) Success update
    r2 = client.post(
        "/api/v1/ops/hedging/config",
        headers={"X-Ops-Token": "secret"},
        json={"hedging_min_delay_ms": 80, "hedging_budget_per_min": 5},
    )
    assert r2.status_code == 200

    # 3) Audit recent (requires token)
    r3 = client.get("/api/v1/ops/audit/recent?n=10", headers={"X-Ops-Token": "secret"})
    assert r3.status_code == 200
    items = r3.json().get("items", [])
    assert len(items) >= 2

    last = items[-1]
    assert last.get("action") == "hedging.update"
    assert last.get("status") == "ok"
    assert last.get("changes", {}).get("hedging_min_delay_ms") == 80

    any_denied = any(e.get("action") == "ops.auth" and e.get("status") == "denied" for e in items)
    assert any_denied
