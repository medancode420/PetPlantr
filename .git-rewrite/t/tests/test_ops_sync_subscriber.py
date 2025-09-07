import asyncio
import json
import time
import pytest

try:
    import fakeredis.aioredis as fredis
except Exception:  # pragma: no cover
    fredis = None


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.sprint_c
async def test_ops_subscriber_applies_update(monkeypatch):
    if fredis is None:
        pytest.skip("fakeredis not installed")

    # Feature + auth gates
    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")
    monkeypatch.setenv("OPS_TOKEN", "secret")

    # Shared FakeRedis for both instances
    r = fredis.FakeRedis()

    # Spin two app instances that share Redis; your code likely sets up ops_sync on app.state
    import importlib
    from fastapi.testclient import TestClient
    import api_server_minimal as mod1

    app1 = mod1.app
    mod2 = importlib.reload(importlib.import_module("api_server_minimal"))
    app2 = mod2.app

    if not hasattr(app1.state, "ops_sync") or not hasattr(app2.state, "ops_sync"):
        pytest.skip("OpsConfigSync not configured on app.state")

    # Wire the same Redis and start subscribers if needed
    app1.state.ops_sync.redis = r
    app2.state.ops_sync.redis = r
    if hasattr(app1.state.ops_sync, "start"):
        await app1.state.ops_sync.start()
        await app2.state.ops_sync.start()

    c2 = TestClient(app2)
    try:
        # Helper to poll until condition or timeout (avoids flakiness)
        async def wait_until(pred, timeout=2.0, step=0.05):
            start = time.monotonic()
            while time.monotonic() - start < timeout:
                if pred():
                    return True
                await asyncio.sleep(step)
            return False

        # Publish a change WITHOUT using the HTTP route (simulate another instance)
        published = False
        for fname in ("publish", "broadcast", "publish_dict", "publish_cap"):
            fn = getattr(app1.state.ops_sync, fname, None)
            if fn:
                maybe_coro = fn({"hedging_max_parallel_hedges": 3})
                if asyncio.iscoroutine(maybe_coro):
                    await maybe_coro
                published = True
                break

        if not published:
            # Fallback: publish raw JSON to the configured channel
            chan = getattr(app1.state.ops_sync, "channel", None) \
                   or getattr(app1.state.ops_sync, "CHANNEL", None) \
                   or "petplantr:ops:hedging:pubsub"
            await r.publish(chan, json.dumps({"key": "hedging_max_parallel_hedges", "value": 3}))

        # Wait for instance B to reflect the change via its subscriber
        def _b_has_value():
            resp = c2.get("/api/v1/ops/hedging/config", headers={"X-Ops-Token": "secret"})
            if resp.status_code != 200:
                return False
            cfg = resp.json()
            val = cfg.get("hedging_max_parallel_hedges") or cfg.get("HEDGING_MAX_PARALLEL_HEDGES")
            try:
                return int(val) == 3
            except Exception:
                return False

        assert await wait_until(_b_has_value), "instance B did not apply fan-out update in time"
    finally:
        if hasattr(app1.state, "ops_sync"):
            await app1.state.ops_sync.stop()
        if hasattr(app2.state, "ops_sync"):
            await app2.state.ops_sync.stop()
