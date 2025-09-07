import httpx, respx, pytest
from prometheus_client import REGISTRY


def _metric(name, labels=None):
    return REGISTRY.get_sample_value(name, labels=labels or {})


@pytest.mark.unit
def test_transport_timeout_maps_to_providerbusy(client, monkeypatch, respx_mock):
    monkeypatch.setenv("FEATURE_QUEUE_LADDER", "true")
    # Simulate network timeout on create
    respx_mock.post("https://api.replicate.com/v1/predictions").mock(
        side_effect=httpx.ReadTimeout("boom")
    )
    before = _metric("petplantr_provider_busy_total", {"phase": "transport", "reason": "timeout"}) or 0.0
    r = client.post("/api/v1/mesh/generate", files={"file": ("x.png", b"x", "image/png")})
    assert r.status_code == 202
    assert r.headers.get("X-Queue-Ladder") == "true"
    after = _metric("petplantr_provider_busy_total", {"phase": "transport", "reason": "timeout"}) or 0.0
    assert after >= before + 1
