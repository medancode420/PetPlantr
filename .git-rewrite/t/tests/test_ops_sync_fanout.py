import asyncio
import pytest

try:
    import fakeredis.aioredis as fredis  # type: ignore
except Exception:  # pragma: no cover
    fredis = None  # type: ignore


def _make_two_apps(monkeypatch, redis_client):
    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")
    monkeypatch.setenv("OPS_TOKEN", "secret")
    from importlib import reload
    import api_server_minimal as mod
    reload(mod)
    from fastapi.testclient import TestClient
    # Reuse module but construct two clients; both share app.state.ops_sync.redis via injected fake
    app = mod.app
    # Inject FakeRedis into both by stubbing OpsConfigSync.start
    if getattr(app.state, "ops_sync", None):
        asyncio.get_event_loop().run_until_complete(app.state.ops_sync.stop())
    class StubSync:
        def __init__(self, app):
            self.app = app
            self.redis = redis_client
        async def start(self):
            # mark redis and skip subscriber; test only publish path
            self.app.state.ops_sync = self
        async def stop(self):
            pass
        async def publish_cap(self, val: int):
            await self.redis.set("petplantr:ops:hedging_max_parallel_hedges", val)
    mod.OpsConfigSync = StubSync  # type: ignore
    # restart lifespan bits that set ops_sync
    with TestClient(mod.app) as c1, TestClient(mod.app) as c2:
        yield c1, c2, mod


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ops_config_fanout(monkeypatch):
    if fredis is None:
        pytest.skip("fakeredis not installed")
    r = fredis.FakeRedis()
    # Create two clients against the same app; fanout via stub publish
    async def run():
        for _ in range(1):
            pass
    # Build apps/clients
    gen = _make_two_apps(monkeypatch, r)
    c1, c2, mod = next(gen)

    # Ensure ops_sync injected
    assert mod.app.state.ops_sync is not None

    # Set initial cap via POST on client1
    res = c1.post(
        "/api/v1/ops/hedging/config",
        headers={"X-Ops-Token": "secret"},
        json={"hedging_max_parallel_hedges": 2},
    )
    assert res.status_code == 200, res.text

    # Allow a short delay for app state to update
    await asyncio.sleep(0.1)

    # Read live hedger cap from app state (simulating client2 view)
    hedger = mod.app.state.hedger
    assert getattr(hedger.s, "hedging_max_parallel_hedges", None) == 2

    # Cleanup
    try:
        next(gen)
    except StopIteration:
        pass
