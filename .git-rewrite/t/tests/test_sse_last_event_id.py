import pytest

@pytest.mark.integration
def test_sse_accepts_last_event_id(monkeypatch):
    # Ensure app uses default SSE
    from importlib import reload
    import api_server_minimal as mod
    reload(mod)
    from fastapi.testclient import TestClient

    client = TestClient(mod.app)

    r1 = client.get("/api/v1/mesh/stream/demo")
    assert r1.status_code == 200
    assert "text/event-stream" in r1.headers.get("content-type", "")

    last_id = None
    for line in r1.text.splitlines():
        if line.startswith("id:"):
            try:
                last_id = int(line.split(":", 1)[1].strip())
            except Exception:
                pass

    headers = {}
    if last_id is not None:
        headers["Last-Event-ID"] = str(last_id)

    r2 = client.get("/api/v1/mesh/stream/demo", headers=headers)
    assert r2.status_code == 200
    assert "text/event-stream" in r2.headers.get("content-type", "")
