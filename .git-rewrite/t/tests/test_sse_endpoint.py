import pytest

@pytest.mark.sprint_c
def test_sse_progress_stream_smoke(monkeypatch):
    # Enable ops endpoints (not required for SSE, but consistent env init)
    monkeypatch.setenv("FEATURE_OPS_ENDPOINTS", "true")

    from api_server_minimal import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    with client.stream("GET", "/api/v1/stream/progress?steps=3&interval_ms=10&job_id=test") as r:
        assert r.status_code == 200
        chunks = []
        for line in r.iter_lines():
            if line:
                chunks.append(line.decode() if isinstance(line, (bytes, bytearray)) else line)
        body = "\n".join(chunks)
        # Check basic SSE markers
        assert "event: start" in body
        assert "event: progress" in body
        assert "event: done" in body
        assert body.index("event: start") < body.index("event: progress") < body.index("event: done")
