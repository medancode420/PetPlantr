from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from src.core.settings import get_flag, get_int
from src.services.metrics import synthetic_checks_total, synthetic_last_latency_seconds


_loop_task: Optional[asyncio.Task] = None
_loop_started = False


@dataclass
class SyntheticSample:
	ok: bool
	latency_s: float
	timestamp: float


async def _do_check() -> SyntheticSample:
	# Simulate a lightweight check (e.g., HEAD to own /api/v1/health)
	t0 = time.perf_counter()
	await asyncio.sleep(0.01)
	latency = time.perf_counter() - t0
	try:
		synthetic_checks_total.inc()  # type: ignore[attr-defined]
		synthetic_last_latency_seconds.set(latency)  # type: ignore[attr-defined]
	except Exception:
		# metrics may be no-ops in local
		pass
	return SyntheticSample(ok=True, latency_s=latency, timestamp=time.time())


async def _loop(period_s: float) -> None:
	global _loop_started
	_loop_started = True
	try:
		while True:
			# Read enable flag dynamically so tests can flip it at runtime
			if get_flag("ENABLE_SYNTHETIC_MONITOR", True):
				await _do_check()
			await asyncio.sleep(period_s)
	finally:
		_loop_started = False


def ensure_started() -> None:
	"""Idempotently start the background loop if enabled.
	Non-blocking: creates an asyncio task; safe to call multiple times.
	"""
	global _loop_task
	if _loop_task and not _loop_task.done():
		return

	# Only start if enabled at this moment; the loop itself re-checks the flag
	if get_flag("ENABLE_SYNTHETIC_MONITOR", True):
		period = float(get_int("SYNTHETIC_MONITOR_PERIOD_MS", 5000)) / 1000.0
		try:
			_loop_task = asyncio.create_task(_loop(period))
		except RuntimeError:
			# Not in an event loop (e.g., module imported in sync context). It's fine;
			# the endpoint will perform a one-shot check as a fallback.
			_loop_task = None


async def one_shot_sample() -> SyntheticSample:
	"""Perform a one-off synthetic sample immediately."""
	return await _do_check()


def is_running() -> bool:
	return bool(_loop_task and not _loop_task.done()) or _loop_started
