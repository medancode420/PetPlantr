"""
Background synthetic SLO monitor loop.
Periodically exercises internal endpoints and records last sample in app.state.
"""
import asyncio
import time
import random
from typing import Optional

import httpx

from src.core.settings import Settings


async def _sleep_jittered(base_sec: int, jitter_sec: int) -> None:
    await asyncio.sleep(max(1, base_sec + random.randint(-jitter_sec, jitter_sec)))


async def synthetic_monitor_loop(app, settings: Settings):
    """
    Periodically call health and a tiny breed detect to validate end-to-end.
    Stores the last sample in app.state.synthetic_last.
    """
    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://app", timeout=30)
    try:
        while True:
            if not getattr(settings, "feature_synthetic_monitor", False):
                # Poll flag occasionally without busy loop
                await asyncio.sleep(5)
                continue

            t0 = time.perf_counter()
            health_ok = False
            breed_ok = False
            mesh_ok: Optional[bool] = None

            # Health
            try:
                r = await client.get("/api/v1/health")
                health_ok = r.status_code == 200 and r.json().get("status") in ("healthy", "ready")
            except Exception:
                health_ok = False

            # Breed (send minimal valid file)
            try:
                files = {"file": ("hb.png", b"x", "image/png")}
                r = await client.post("/api/v1/breed/detect", files=files, data={"use_tta": "true", "confidence_threshold": "0.8"}, headers={"X-Client": "ui"})
                breed_ok = r.status_code in (200, 202)
            except Exception:
                breed_ok = False

            # Optional mesh path if enabled and endpoint exists
            if getattr(settings, "synthetic_monitor_enable_mesh", False):
                try:
                    files = {"file": ("hb.png", b"x", "image/png")}
                    r = await client.post("/api/v1/mesh/generate", files=files, headers={"X-Client": "ui"})
                    mesh_ok = r.status_code in (200, 202)
                except Exception:
                    mesh_ok = False

            dt_ms = int((time.perf_counter() - t0) * 1000)
            app.state.synthetic_last = {
                "ts": int(time.time()),
                "latency_ms": dt_ms,
                "health": health_ok,
                "breed": breed_ok,
                "mesh": mesh_ok,
            }

            # Sleep to next interval
            await _sleep_jittered(
                getattr(settings, "synthetic_monitor_interval_sec", 300),
                getattr(settings, "synthetic_monitor_jitter_sec", 20),
            )
    finally:
        await client.aclose()
