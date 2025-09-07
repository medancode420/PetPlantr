import asyncio
import pytest

from src.services.hedging import (
    adaptive_delay,
    HedgedRequest,
    set_hedging_config,
    cost_tracker,
    enable_kill_switch,
    disable_kill_switch,
    settings as hedging_settings,
)


@pytest.mark.unit
def test_delay_respects_min_max_and_updates_ema(monkeypatch):
    # Enable adaptive hedging and configure bounds/alpha
    set_hedging_config(
        feature_adaptive_hedging=True,
        hedging_min_delay_ms=100,
        hedging_max_delay_ms=800,
        adaptive_ema_alpha=0.5,
        hedging_delay_ms=500,
    )

    # Seed EMA down then up and ensure clamping within [min,max]
    adaptive_delay.observe_primary_seconds(0.060)  # 60ms
    d1 = adaptive_delay.suggest_delay_ms()
    assert 100 <= d1 <= 800, d1

    adaptive_delay.observe_primary_seconds(1.200)  # 1200ms
    d2 = adaptive_delay.suggest_delay_ms()
    assert 100 <= d2 <= 800, d2
    assert d2 >= d1


@pytest.mark.unit
def test_hedge_triggers_after_delay_when_allowed(monkeypatch):
    async def _run():
        # Turn on hedging and adaptive mode with short bounds so hedge will start
        set_hedging_config(
            feature_hedging=True,
            feature_adaptive_hedging=True,
            hedging_min_delay_ms=100,
            hedging_max_delay_ms=150,
            adaptive_ema_alpha=0.5,
            hedging_delay_ms=150,
        )

        # Ensure cost tracker allows hedging
        disable_kill_switch()
        cost_tracker.enable_now()

        calls = {"n": 0}

        async def slow_call():
            calls["n"] += 1
            # Exceed delay (~0.1-0.15s) so secondary should start
            await asyncio.sleep(0.20)
            return {"ok": True, "leg": calls["n"]}

        hedger = HedgedRequest("adaptive_delay_test")
        res = await hedger.race(slow_call, timeout_sec=2.0)

        assert res["ok"] is True
        assert calls["n"] == 2  # primary + hedged
        assert hedger.secondary_task is not None

    asyncio.run(_run())


@pytest.mark.unit
def test_hedge_skipped_if_kill_switch_enabled(monkeypatch):
    async def _run():
        # Enable feature but turn on kill switch to block hedging
        set_hedging_config(feature_hedging=True, feature_adaptive_hedging=True, hedging_delay_ms=50)
        enable_kill_switch()  # disables hedging via cost tracker window

        calls = {"n": 0}

        async def slow_call():
            calls["n"] += 1
            await asyncio.sleep(0.15)
            return {"ok": True}

        hedger = HedgedRequest("kill_switch_test")
        res = await hedger.race(slow_call, timeout_sec=1.0)

        # Hedge should be skipped -> only one invocation
        assert res["ok"] is True
        assert calls["n"] == 1

        # Clean up kill switch for any later tests
        disable_kill_switch()

    asyncio.run(_run())


@pytest.mark.unit
def test_budget_limit_zero_blocks_hedge(monkeypatch):
    async def _run():
        # Set budget to zero so cost gate prevents starting secondary
        set_hedging_config(feature_hedging=True, feature_adaptive_hedging=False, hedging_delay_ms=50)
        hedging_settings.hedging_cost_limit_per_hour = 0.0

        calls = {"n": 0}

        async def slow_call():
            calls["n"] += 1
            await asyncio.sleep(0.20)
            return {"ok": True}

        hedger = HedgedRequest("budget_zero_test")
        res = await hedger.race(slow_call, timeout_sec=1.0)

        assert res["ok"] is True
        assert calls["n"] == 1  # no hedged second leg due to budget gate

        # Restore a sane budget for any subsequent tests
        hedging_settings.hedging_cost_limit_per_hour = 50.0

    asyncio.run(_run())


@pytest.mark.unit
def test_concurrency_budget_gate_allows_single_secondary(monkeypatch):
    async def _run():
        # Static delay for determinism
        set_hedging_config(feature_hedging=True, feature_adaptive_hedging=False, hedging_delay_ms=50)
        # Reset tracker state and allow only one hedged launch within the hour
        cost_tracker.enable_now()
        cost_tracker.hourly_costs = {}
        hedging_settings.hedging_cost_limit_per_hour = 0.001  # equals single hedge cost

        calls = {"n": 0}

        async def slow_call():
            calls["n"] += 1
            await asyncio.sleep(0.20)
            return {"ok": True}

        async def run_one(i):
            hedger = HedgedRequest(f"conc_test_{i}")
            return await hedger.race(slow_call, timeout_sec=1.0)

        # Run several hedged requests concurrently
        N = 5
        results = await asyncio.gather(*(run_one(i) for i in range(N)))
        assert all(r["ok"] is True for r in results)

        # Total calls = N primaries + at most 1 secondary due to budget gate
        assert calls["n"] == N + 1

        # Restore budget for other tests
        hedging_settings.hedging_cost_limit_per_hour = 50.0
        cost_tracker.hourly_costs = {}

    asyncio.run(_run())


@pytest.mark.unit
def test_concurrency_allows_multiple_secondaries_with_sufficient_budget(monkeypatch):
    async def _run():
        set_hedging_config(feature_hedging=True, feature_adaptive_hedging=False, hedging_delay_ms=40, hedging_max_parallel_hedges=100)
        cost_tracker.enable_now()
        cost_tracker.hourly_costs = {}
        hedging_settings.hedging_cost_limit_per_hour = 1.0  # ample budget

        calls = {"n": 0}

        async def slow_call():
            calls["n"] += 1
            await asyncio.sleep(0.20)
            return {"ok": True}

        async def run_one(i):
            hedger = HedgedRequest(f"conc_ok_{i}")
            return await hedger.race(slow_call, timeout_sec=1.0)

        N = 4
        results = await asyncio.gather(*(run_one(i) for i in range(N)))
        assert all(r["ok"] is True for r in results)

        # Expect each to hedge once: total calls ≈ 2N
        assert calls["n"] == 2 * N

        hedging_settings.hedging_cost_limit_per_hour = 50.0
        cost_tracker.hourly_costs = {}

    asyncio.run(_run())


@pytest.mark.unit
def test_no_hedge_when_primary_finishes_before_delay(monkeypatch):
    async def _run():
        # Large delay so primary returns first
        set_hedging_config(feature_hedging=True, feature_adaptive_hedging=False, hedging_delay_ms=300)
        cost_tracker.enable_now()

        calls = {"n": 0}

        async def fast_call():
            calls["n"] += 1
            await asyncio.sleep(0.05)
            return {"ok": True}

        hedger = HedgedRequest("no_hedge_fast_primary")
        res = await hedger.race(fast_call, timeout_sec=1.0)
        assert res["ok"] is True
        assert calls["n"] == 1  # no hedged call

    asyncio.run(_run())
