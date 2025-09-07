import asyncio
import pytest


def _make_client(monkeypatch):
    # Ensure ops endpoints and token are set before import
    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")
    monkeypatch.setenv("OPS_TOKEN", "secret")
    from importlib import reload
    import api_server_minimal as mod
    reload(mod)
    from fastapi.testclient import TestClient
    return TestClient(mod.app), mod


@pytest.mark.unit
def test_ops_can_update_min_delay_and_budget(monkeypatch):
    client, mod = _make_client(monkeypatch)

    # Enable adaptive hedging and set initial values
    monkeypatch.setenv("FEATURE_ADAPTIVE_HEDGING", "true")
    monkeypatch.setenv("HEDGING_MIN_DELAY_MS", "200")
    monkeypatch.setenv("HEDGING_BUDGET_PER_MIN", "2")

    # Apply via POST
    r = client.post(
        "/api/v1/ops/hedging/config",
        headers={"X-Ops-Token": "secret"},
        json={"hedging_min_delay_ms": 80, "hedging_budget_per_min": 5},
    )
    assert r.status_code == 200, r.text
    js = r.json()
    assert js.get("updated", {}).get("hedging_min_delay_ms") == 80
    assert js.get("updated", {}).get("hedging_budget_per_min") == 5

    # Confirm via GET
    g = client.get("/api/v1/ops/hedging/config", headers={"X-Ops-Token": "secret"})
    assert g.status_code == 200
    cfg = g.json()
    assert cfg["HEDGING_MIN_DELAY_MS"] == 80
    assert cfg["HEDGING_BUDGET_PER_MIN"] == 5

    # Confirm live hedger reflects changes
    hedger = mod.app.state.hedger
    assert getattr(hedger.s, "hedging_min_delay_ms", None) == 80
    assert getattr(hedger.s, "hedging_budget_per_min", None) == 5


@pytest.mark.unit
def test_clamps_and_runtime_effect_on_hedging(monkeypatch):
    client, mod = _make_client(monkeypatch)

    # Start with small delay so hedging would occur
    r = client.post(
        "/api/v1/ops/hedging/config",
        headers={"X-Ops-Token": "secret"},
        json={"hedging_min_delay_ms": 50, "hedging_budget_per_min": 10},
    )
    assert r.status_code == 200

    hedger = mod.app.state.hedger

    calls = {"n": 0}

    async def slow():
        calls["n"] += 1
        await asyncio.sleep(0.08)  # 80ms > 50ms -> hedge can start
        return {"ok": True, "leg": calls["n"]}

    async def _run_once():
        # Should hedge (two legs)
        res = await hedger.run(slow, lambda: None, True, tokens_free=6, required_tokens_for_mesh=3)
        assert res["ok"] is True
        assert calls["n"] == 2

        # Now raise delay high so hedge does NOT start
        r2 = client.post(
            "/api/v1/ops/hedging/config",
            headers={"X-Ops-Token": "secret"},
            json={"hedging_min_delay_ms": 1000},
        )
        assert r2.status_code == 200

        calls["n"] = 0
        res2 = await hedger.run(slow, lambda: None, True, tokens_free=6, required_tokens_for_mesh=3)
        assert res2["ok"] is True
        # 80ms < 1000ms -> hedge should not start -> only one call
        assert calls["n"] == 1

    asyncio.run(_run_once())


@pytest.mark.unit
def test_invalid_values_are_clamped_and_validated(monkeypatch):
    client, mod = _make_client(monkeypatch)

    # Negative -> clamp to 50; too big budget -> clamp to 120
    r = client.post(
        "/api/v1/ops/hedging/config",
        headers={"X-Ops-Token": "secret"},
        json={"hedging_min_delay_ms": -10, "hedging_budget_per_min": 9999},
    )
    assert r.status_code == 200
    cfg = client.get("/api/v1/ops/hedging/config", headers={"X-Ops-Token": "secret"}).json()
    assert cfg["HEDGING_MIN_DELAY_MS"] == 50
    assert cfg["HEDGING_BUDGET_PER_MIN"] == 120
