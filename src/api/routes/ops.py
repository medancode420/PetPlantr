from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.core.settings import get_flag
from src.services.synthetic_monitor import ensure_started, is_running, one_shot_sample


router = APIRouter(prefix="/api/v1/ops", tags=["ops"])


@router.get("/synthetic/live")
async def synthetic_live():
    """Liveness endpoint for the synthetic monitor.
    Always registered; behavior is gated dynamically by environment flag.
    """
    enabled = get_flag("ENABLE_SYNTHETIC_MONITOR", True)

    # Start background loop idempotently (non-blocking). If no loop can be started (no running loop),
    # we still respond using a one-shot sample below.
    ensure_started()

    # Take a one-shot sample to avoid startup races
    sample = await one_shot_sample()

    status = {
        "enabled": enabled,
        "running": is_running(),
        "ok": sample.ok,
        "latency_s": round(sample.latency_s, 6),
        "timestamp": sample.timestamp,
    }

    if not enabled:
        # 200 with enabled=false keeps contract stable without 404s
        return status

    # When enabled, enforce ok must be True; otherwise 503
    if not sample.ok:
        raise HTTPException(status_code=503, detail={"status": status})

    return status
