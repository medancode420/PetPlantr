"""Minimal metrics facade used in tests and local runs.
If prometheus_client is available, expose real metrics; otherwise, provide no-op shims.
"""

from __future__ import annotations

try:
	from prometheus_client import Counter, Gauge
except Exception:  # pragma: no cover - fallback when lib not installed
	class _Noop:
		def __init__(self, *_, **__):
			pass

		def labels(self, *_, **__):
			return self

		def inc(self, *_):
			return None

		def set(self, *_):
			return None

	Counter = _Noop  # type: ignore
	Gauge = _Noop  # type: ignore


synthetic_checks_total = Counter(
	"synthetic_checks_total",
	"Total number of synthetic checks performed",
)

synthetic_last_latency_seconds = Gauge(
	"synthetic_last_latency_seconds",
	"Latency of the last synthetic check in seconds",
)
