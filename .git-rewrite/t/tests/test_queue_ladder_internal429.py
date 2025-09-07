import pytest

@pytest.mark.sprint_c
def test_internal_own_429_is_not_laddered(monkeypatch):
    # Enable chaos endpoints and ladder feature to ensure logic is exercised
    monkeypatch.setenv("FEATURE_CHAOS_TEST", "true")
    monkeypatch.setenv("FEATURE_QUEUE_LADDER", "true")

    from api_server_minimal import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Hit the internal 429 endpoint; should return 429 and NOT 202
    r = client.get("/api/v1/chaos/own429")
    assert r.status_code == 429
    assert r.headers.get("X-Queue-Ladder") is None
    body = r.json()
    assert body.get("detail") == "internal rate limit"


@pytest.mark.sprint_c
def test_provider_429_is_laddered_to_202(monkeypatch):
    # Ensure laddering is on for provider codes
    monkeypatch.setenv("FEATURE_CHAOS_TEST", "true")
    monkeypatch.setenv("FEATURE_QUEUE_LADDER", "true")

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
