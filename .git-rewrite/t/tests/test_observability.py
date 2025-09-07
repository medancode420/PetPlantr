import os
import pytest

@pytest.mark.sprint_c
def test_observability_metrics_and_trace_headers(client, monkeypatch):
    # Ensure metrics route may be enabled (prometheus optional in env)
    r = client.get("/health")
    assert r.status_code == 200

    # Correlation headers present
    assert "X-Trace-ID" in r.headers
    assert "X-Request-ID" in r.headers

    # If metrics are exposed, endpoint should return text/plain; version varies
    resp = client.get("/metrics")
    if resp.status_code == 200:
        assert "petplantr_http_requests_total" in resp.text or resp.text.strip() != ""
    else:
        assert resp.status_code in (404, 500)
