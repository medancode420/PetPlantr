import pytest

@pytest.mark.sprint_c
def test_queue_ladder_transforms_429_to_202(monkeypatch):
    # Enable queue ladder and chaos test endpoint before app import
    monkeypatch.setenv("FEATURE_QUEUE_LADDER", "true")
    monkeypatch.setenv("FEATURE_CHAOS_TEST", "true")

    from api_server_minimal import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    r = client.get("/api/v1/chaos/force_status?code=429")
    assert r.status_code == 202
    assert r.headers.get("X-Queue-Ladder") == "true"
    body = r.json()
    assert body.get("status") == "queued"
    assert body.get("original_status") == 429
    assert isinstance(body.get("id"), str)
    assert body.get("next_check", "").startswith("/api/status/")


@pytest.mark.sprint_c
def test_queue_ladder_disabled_returns_original_status(monkeypatch):
    # Disable queue ladder, enable chaos so endpoint exists
    monkeypatch.setenv("FEATURE_QUEUE_LADDER", "false")
    monkeypatch.setenv("FEATURE_CHAOS_TEST", "true")

    # Import fresh app
    from api_server_minimal import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    r = client.get("/api/v1/chaos/force_status?code=503")
    assert r.status_code == 503
    data = r.json()
    assert data.get("detail") == "forced 503"
