# src/ops_config_sync.py
import asyncio
import json
import os
from typing import Optional, Any

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # Fallback to None when not installed in tests
    redis = None  # type: ignore

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
PUBSUB_CHANNEL = os.getenv("OPS_PUBSUB_CHANNEL", "petplantr:ops:hedging:pubsub")
CAP_KEY = os.getenv("OPS_CAP_KEY", "petplantr:ops:hedging_max_parallel_hedges")


class OpsConfigSync:
    def __init__(self, app: Any):
        self.app = app
        self.redis: Any = None
        self.sub_task: Optional[asyncio.Task] = None
        # Expose channel for tests/ops tooling
        self.channel = PUBSUB_CHANNEL

    async def start(self):
        """Initialize Redis (if not injected) and start the subscriber task."""
        if self.redis is None:
            if redis is None:
                # Library not available; nothing to do in this environment
                return
            # Create an async client
            self.redis = await redis.from_url(  # type: ignore
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
        # Load persisted cap if present
        try:
            val = await self.redis.get(CAP_KEY)  # type: ignore[attr-defined]
        except Exception:
            val = None
        if val is not None:
            try:
                iv = int(val)
                hedger = getattr(self.app.state, "hedger", None)
                if hedger:
                    lock = getattr(hedger, "_lock", None)
                    if lock is None:
                        lock = asyncio.Lock()
                    async with lock:
                        setattr(hedger.s, "hedging_max_parallel_hedges", iv)
            except Exception:
                pass
        # Start subscriber
        if self.sub_task is None or self.sub_task.done():
            self.sub_task = asyncio.create_task(self._subscriber())
        # Allow brief time for subscription to attach
        await asyncio.sleep(0.05)

    async def stop(self):
        if self.sub_task:
            self.sub_task.cancel()
            try:
                await self.sub_task
            except Exception:
                pass
        if self.redis:
            try:
                await self.redis.aclose()  # type: ignore[union-attr]
            except Exception:
                pass

    async def _subscriber(self):
        if not self.redis:
            return
        # Local clamps aligned with API server bounds
        CLAMPS = {
            "hedging_max_parallel_hedges": (0, 32),
            "hedging_min_delay_ms": (50, 10_000),
            "hedging_budget_per_min": (0, 120),
        }
        try:
            pubsub = self.redis.pubsub()  # type: ignore[union-attr]
            await pubsub.subscribe(self.channel)
            # Use async generator when available (fakeredis.aioredis supports this)
            async for msg in pubsub.listen():
                try:
                    if msg.get("type") != "message":
                        continue
                    data = msg.get("data", "{}")
                    if isinstance(data, (bytes, bytearray)):
                        try:
                            data = data.decode()
                        except Exception:
                            continue
                    try:
                        payload = json.loads(data)
                    except Exception:
                        continue
                    # Support either {"key": "...", "value": X} or a flat dict of updates
                    if isinstance(payload, dict) and "key" in payload and "value" in payload:
                        items = [(payload.get("key"), payload.get("value"))]
                    elif isinstance(payload, dict):
                        items = list(payload.items())
                    else:
                        continue
                    hedger = getattr(self.app.state, "hedger", None)
                    if not hedger:
                        continue
                    lock = getattr(hedger, "_lock", None)
                    if lock is None:
                        lock = asyncio.Lock()
                    async with lock:
                        for k, raw in items:
                            if k not in CLAMPS:
                                # Unknown key: ignore
                                continue
                            lo, hi = CLAMPS[k]
                            try:
                                if raw is None:
                                    continue
                                v = int(raw)
                            except Exception:
                                continue
                            v = max(lo, min(hi, v))
                            try:
                                setattr(hedger.s, k, v)
                            except Exception:
                                # Best effort only
                                pass
                except asyncio.CancelledError:
                    return
                except Exception:
                    # Soft backoff on unexpected message issues
                    await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            return
        except Exception:
            # Never crash process; silent backoff
            await asyncio.sleep(0.2)

    async def publish_cap(self, val: int):
        if not self.redis:
            return
        try:
            await self.redis.set(CAP_KEY, val)  # type: ignore[union-attr]
            await self.redis.publish(
                self.channel, json.dumps({"key": "hedging_max_parallel_hedges", "value": val})
            )  # type: ignore[union-attr]
        except Exception:
            pass

    async def publish(self, payload: Any):
        """Publish a dict of updates to the pubsub channel. Test helper friendly."""
        if not self.redis:
            return
        try:
            data = payload
            # If caller passed a simple value, wrap it
            if not isinstance(data, dict):
                data = {"hedging_max_parallel_hedges": int(data)}
            await self.redis.publish(self.channel, json.dumps(data))  # type: ignore[union-attr]
        except Exception:
            pass

    # Alias used by some tests
    publish_dict = publish
    broadcast = publish
