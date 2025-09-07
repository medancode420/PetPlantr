import asyncio
import os
import pytest
import httpx
import respx
from prometheus_client import REGISTRY

from src.services.replicate_client import ReplicateClient


def _metric(name, labels=None):
    return REGISTRY.get_sample_value(name, labels=labels or {})


@pytest.mark.sprint_c
def test_providerbusy_ladders_to_202_via_global_handler(monkeypatch):
    """
    Simulate Replicate upstream returning 429 on final attempt.
    Expect the Replicate client to raise ProviderBusy, which the FastAPI app
    globally converts to 202 (when FEATURE_QUEUE_LADDER=true).
    """
    # Enable global laddering and chaos so app boot is consistent with tests
    monkeypatch.setenv("FEATURE_QUEUE_LADDER", "true")
    monkeypatch.setenv("FEATURE_CHAOS_TEST", "true")

    # Import app to register the global ProviderBusy handler
    from api_server_minimal import app  # noqa: F401

    async def _run():
        client = ReplicateClient()
        await client.startup()

        # Patch the underlying http client to always return 429
        call_count = 0

        async def fake_request(method, url, **kwargs):
            nonlocal call_count
            call_count += 1
            # Return a 429 response object
            return httpx.Response(429, json={"detail": "rate limited"}, request=httpx.Request(method, url))

        assert client.client is not None
        monkeypatch.setattr(client.client, "request", fake_request)

        # Now call client.request and expect ProviderBusy to bubble
        error = None
        try:
            await client.request(
                "GET",
                "https://api.replicate.com/v1/predictions",
                timeout_sec=0.5,
                operation_name="providerbusy_test",
                use_hedging=False,
            )
        except Exception as e:  # Don't import ProviderBusy directly; just assert type name
            error = e

        # We should have gotten a ProviderBusy from the wrapper
        assert error is not None
        assert error.__class__.__name__ == "ProviderBusy"

        # Sanity: at least one attempt
        assert call_count >= 1

        await client.shutdown()

    asyncio.run(_run())


@pytest.mark.unit
def test_mesh_create_429_ladder_and_metric(client, monkeypatch, respx_mock):
    monkeypatch.setenv("FEATURE_QUEUE_LADDER", "true")
    # Upstream create returns 429 with Retry-After
    respx_mock.post("https://api.replicate.com/v1/predictions").mock(
        return_value=httpx.Response(429, json={"detail": "rate"}, headers={"Retry-After": "7"})
    )

    before = _metric("petplantr_provider_busy_total", {"phase": "create", "reason": "http429"}) or 0.0
    r = client.post("/api/v1/mesh/generate", files={"file": ("x.png", b"x", "image/png")})
    assert r.status_code == 202
    assert r.headers.get("X-Queue-Ladder") == "true"
    # Handler should propagate Retry-After from upstream if present (or fallback)
    assert r.headers.get("Retry-After") in ("7", "10")
    after = _metric("petplantr_provider_busy_total", {"phase": "create", "reason": "http429"}) or 0.0
    assert after >= before + 1


@pytest.mark.unit
def test_mesh_poll_503_ladder_and_metric(client, monkeypatch, respx_mock):
    monkeypatch.setenv("FEATURE_QUEUE_LADDER", "true")
    # Create ok -> returns id
    respx_mock.post("https://api.replicate.com/v1/predictions").mock(
        return_value=httpx.Response(201, json={"id": "p1", "status": "starting"})
    )
    # Poll returns 503
    respx_mock.get("https://api.replicate.com/v1/predictions/p1").mock(
        return_value=httpx.Response(503, json={"detail": "busy"})
    )

    before = _metric("petplantr_provider_busy_total", {"phase": "poll", "reason": "http503"}) or 0.0
    r = client.post("/api/v1/mesh/generate", files={"file": ("x.png", b"x", "image/png")})
    assert r.status_code == 202
    assert r.headers.get("X-Queue-Ladder") == "true"
    after = _metric("petplantr_provider_busy_total", {"phase": "poll", "reason": "http503"}) or 0.0
    assert after >= before + 1
