import asyncio
import pytest
from prometheus_client import REGISTRY

from src.services.hedging import (
    HedgedRequest,
    set_hedging_config,
    cost_tracker,
)


def _metric_value(name: str) -> float:
    v = REGISTRY.get_sample_value(name)
    return 0.0 if v is None else float(v)


@pytest.mark.unit
def test_metrics_increment_on_hedge():
    async def _run():
        # Ensure hedging enabled with a short static delay so hedge will start
        set_hedging_config(
            feature_hedging=True,
            feature_adaptive_hedging=False,
            hedging_delay_ms=50,
            hedging_min_delay_ms=50,
            hedging_max_delay_ms=60,
        )
        cost_tracker.enable_now()

        before_launch = _metric_value("petplantr_hedge_launch_total")
        before_win = _metric_value("petplantr_hedge_win_total")

        async def slow_call():
            # sleeps longer than delay to trigger hedge
            await asyncio.sleep(0.08)
            return {"ok": True}

        h = HedgedRequest("metrics_inc")
        res = await h.race(slow_call, timeout_sec=1.0)
        assert res["ok"] is True

        after_launch = _metric_value("petplantr_hedge_launch_total")
        after_win = _metric_value("petplantr_hedge_win_total")

        assert after_launch >= before_launch + 1
        # secondary may or may not win depending on scheduling
        assert after_win >= before_win

    asyncio.run(_run())


@pytest.mark.unit
def test_parallel_cap_skips_extra_hedges():
    async def _run():
        # Cap parallel hedges at 1 so two concurrent calls cause a skip
        set_hedging_config(
            feature_hedging=True,
            feature_adaptive_hedging=False,
            hedging_delay_ms=50,
            hedging_min_delay_ms=50,
            hedging_max_delay_ms=60,
            hedging_max_parallel_hedges=1,
        )
        cost_tracker.enable_now()

        before_launch = _metric_value("petplantr_hedge_launch_total")
        before_skip_parallel = _metric_value("petplantr_hedge_skip_parallel_total")

        async def slow_call():
            await asyncio.sleep(0.08)
            return {"ok": True}

        async def do_one(name: str):
            h = HedgedRequest(name)
            return await h.race(slow_call, timeout_sec=1.0)

        r1, r2 = await asyncio.gather(do_one("cap1"), do_one("cap2"))
        assert r1["ok"] and r2["ok"]

        after_launch = _metric_value("petplantr_hedge_launch_total")
        after_skip_parallel = _metric_value("petplantr_hedge_skip_parallel_total")

        # Only one secondary should launch, the other should skip due to cap
        assert after_launch >= before_launch + 1
        assert after_skip_parallel >= before_skip_parallel + 1

    asyncio.run(_run())
