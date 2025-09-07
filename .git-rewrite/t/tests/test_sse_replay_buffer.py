import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_sse_replay_after_last_event_id(monkeypatch):
    from importlib import reload
    import api_server_minimal as mod
    reload(mod)

    client = TestClient(mod.app)

    # First request to get some events
    r1 = client.get("/api/v1/mesh/stream/demo?steps=5&interval_ms=1")
    assert r1.status_code == 200
    ids = [int(l.split(":", 1)[1]) for l in r1.text.splitlines() if l.startswith("id:")]
    assert ids, "no ids found"
    last_id = ids[-2]  # pick a mid id to test replay of last frame(s)

    # Second request with Last-Event-ID should only return ids > last_id
    r2 = client.get(
        "/api/v1/mesh/stream/demo?steps=3&interval_ms=1",
        headers={"Last-Event-ID": str(last_id)},
    )
    assert r2.status_code == 200
    ids2 = [int(l.split(":", 1)[1]) for l in r2.text.splitlines() if l.startswith("id:")]
    assert ids2 and all(i > last_id for i in ids2)
