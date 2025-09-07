import asyncio
import os
import pytest
import httpx

from src.services.replicate_client import ReplicateClient, settings as rc_settings


@pytest.mark.sprint_c
def test_hedging_triggers_and_idempotency_key_shared(monkeypatch):
    async def _run():
        # Enable hedging with a short delay
        monkeypatch.setenv("FEATURE_HEDGING", "true")
        monkeypatch.setenv("HEDGING_DELAY_MS", "50")
        monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "1")

        # Ensure the hedging module's settings reflect enabled flag and delay
        import src.services.hedging as hedging_mod
        hedging_mod.settings.feature_hedging = True
        hedging_mod.settings.hedging_delay_ms = 50

        client = ReplicateClient()
        await client.startup()

        call_count = 0
        seen_headers = []

        async def fake_request(method, url, **kwargs):
            nonlocal call_count, seen_headers
            call_count += 1
            headers = kwargs.get("headers", {}) or {}
            seen_headers.append(dict(headers))
            # Primary (1st call) slow, Secondary (2nd call) fast
            if call_count == 1:
                await asyncio.sleep(0.20)
                return httpx.Response(200, json={"ok": 1}, request=httpx.Request(method, url))
            else:
                await asyncio.sleep(0.05)
                return httpx.Response(200, json={"ok": 2}, request=httpx.Request(method, url))

        assert client.client is not None
        monkeypatch.setattr(client.client, "request", fake_request)

        resp = await client.request(
            "GET",
            "https://api.replicate.com/v1/test",
            timeout_sec=2.0,
            operation_name="hedge_test",
            use_hedging=True,
        )

        # Secondary should win -> ok == 2
        assert resp.status_code == 200
        assert resp.json().get("ok") == 2
        assert call_count == 2

        # Both legs must share the same idempotency key
        assert len(seen_headers) == 2
        idem_header = rc_settings.idempotency_header
        assert idem_header in seen_headers[0]
        assert idem_header in seen_headers[1]
        assert seen_headers[0][idem_header] == seen_headers[1][idem_header]

        await client.shutdown()

    asyncio.run(_run())


@pytest.mark.sprint_c
def test_hedging_disabled_falls_back_to_single_path(monkeypatch):
    async def _run():
        # Disable hedging and patch module settings directly (import-time object)
        monkeypatch.setenv("FEATURE_HEDGING", "false")
        monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "1")

        # Ensure the hedging module's settings object reflects disabled flag
        import src.services.hedging as hedging_mod
        hedging_mod.settings.feature_hedging = False

        client = ReplicateClient()
        await client.startup()

        call_count = 0

        async def fake_request(method, url, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            return httpx.Response(200, json={"ok": 1}, request=httpx.Request(method, url))

        assert client.client is not None
        monkeypatch.setattr(client.client, "request", fake_request)

        resp = await client.request(
            "GET",
            "https://api.replicate.com/v1/test",
            timeout_sec=1.0,
            operation_name="no_hedge",
            use_hedging=True,  # Even if requested, flag disables
        )

        assert resp.status_code == 200
        assert resp.json().get("ok") == 1
        assert call_count == 1  # Only one underlying call

        await client.shutdown()

    asyncio.run(_run())
