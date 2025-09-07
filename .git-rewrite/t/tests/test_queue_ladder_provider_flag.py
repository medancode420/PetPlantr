import pytest

@pytest.mark.unit
def test_provider_flag_ladders_via_global_handler(monkeypatch):
    monkeypatch.setenv("FEATURE_CHAOS_TEST", "true")
    monkeypatch.setenv("FEATURE_QUEUE_LADDER", "true")

    from api_server_minimal import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    r = client.get("/api/v1/chaos/force_status?code=429&provider=true")
    assert r.status_code == 202
    assert r.headers.get("X-Queue-Ladder") == "true"
    body = r.json()
    assert body.get("state") == "in_progress"
    assert isinstance(body.get("id"), str)
    assert body.get("next", "").startswith("/api/status/")
