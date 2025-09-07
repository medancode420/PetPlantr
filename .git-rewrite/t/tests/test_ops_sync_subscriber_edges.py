import asyncio, json, pytest
try:
    import fakeredis.aioredis as fredis
except Exception:
    fredis = None


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.sprint_c
async def test_unknown_key_is_ignored(monkeypatch):
    if fredis is None:
        pytest.skip("fakeredis not installed")

    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")
    monkeypatch.setenv("OPS_TOKEN", "secret")

    import api_server_minimal as mod
    app = mod.app
    if not hasattr(app.state, "ops_sync"):
        pytest.skip("OpsConfigSync not configured on app.state")

    r = fredis.FakeRedis()
    app.state.ops_sync.redis = r
    if hasattr(app.state.ops_sync, "start"):
        await app.state.ops_sync.start()

    # Publish bogus key; expect no exception and no crash
    chan = getattr(app.state.ops_sync, "channel", None) or getattr(app.state.ops_sync, "CHANNEL", None) or "petplantr:ops:hedging:pubsub"
    await r.publish(chan, json.dumps({"not_a_real_key": 123}))
    await asyncio.sleep(0.1)  # allow subscriber to no-op
    # cleanup
    if hasattr(app.state, "ops_sync"):
        await app.state.ops_sync.stop()


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.sprint_c
async def test_min_delay_is_clamped(monkeypatch):
    if fredis is None:
        pytest.skip("fakeredis not installed")

    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")
    monkeypatch.setenv("OPS_TOKEN", "secret")

    from fastapi.testclient import TestClient
    import api_server_minimal as mod
    app = mod.app
    if not hasattr(app.state, "ops_sync"):
        pytest.skip("OpsConfigSync not configured on app.state")

    r = fredis.FakeRedis()
    app.state.ops_sync.redis = r
    if hasattr(app.state.ops_sync, "start"):
        await app.state.ops_sync.start()

    # Publish a too-low min delay; expect clamped to >=50 (per clamps in ops_config_sync)
    chan = getattr(app.state.ops_sync, "channel", None) or getattr(app.state.ops_sync, "CHANNEL", None) or "petplantr:ops:hedging:pubsub"
    await r.publish(chan, json.dumps({"hedging_min_delay_ms": 1}))
    await asyncio.sleep(0.15)

    c = TestClient(app)
    cfg = c.get("/api/v1/ops/hedging/config", headers={"X-Ops-Token":"secret"}).json()
    val = int(cfg.get("hedging_min_delay_ms") or cfg.get("HEDGING_MIN_DELAY_MS"))
    assert val >= 50
    # cleanup
    if hasattr(app.state, "ops_sync"):
        await app.state.ops_sync.stop()
