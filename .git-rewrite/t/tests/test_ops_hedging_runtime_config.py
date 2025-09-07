import pytest


def test_runtime_update_hedging_parallel_cap_via_ops(monkeypatch):
    # Enable ops endpoints and auth before import
    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")
    monkeypatch.setenv("OPS_TOKEN", "secret")

    from importlib import reload
    import api_server_minimal as mod
    reload(mod)
    from fastapi.testclient import TestClient

    client = TestClient(mod.app)

    # Update the cap to 1 via ops endpoint
    r = client.post(
        "/api/v1/ops/hedging/config",
        headers={"X-Ops-Token": "secret"},
        json={"hedging_max_parallel_hedges": 1},
    )
    assert r.status_code == 200, r.text

    # Verify via GET
    r2 = client.get("/api/v1/ops/hedging/config", headers={"X-Ops-Token": "secret"})
    assert r2.status_code == 200
    d = r2.json()
    assert d.get("max_parallel_hedges") == 1

    # Also confirm the hedging module reflects it
    import src.services.hedging as hedging_mod
    assert getattr(hedging_mod.settings, 'hedging_max_parallel_hedges', None) == 1
