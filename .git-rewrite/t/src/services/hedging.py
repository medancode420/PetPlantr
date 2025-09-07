"""
Request Hedging Implementation for PetPlantr
Reduces p95 tail latency by racing duplicate requests under feature flag
"""
import asyncio
import time
import uuid
import logging
from typing import Callable, Awaitable, Optional, Any, Dict
from contextlib import asynccontextmanager
import weakref

logger = logging.getLogger(__name__)

# Import with fallback for development
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.settings import settings
    from services.metrics import hedged_attempts_total, hedged_wins_total, hedging_cost_per_hour
    SETTINGS_AVAILABLE = True
    METRICS_AVAILABLE = True
except ImportError:
    logger.warning("Settings or metrics not available for hedging")
    SETTINGS_AVAILABLE = False
    METRICS_AVAILABLE = False
    # Mock settings for development
    class MockSettings:
        feature_hedging = False
        hedging_delay_ms = 180
        hedging_max_extra = 1
        hedging_cost_limit_per_hour = 50.0
        # Sprint C defaults
        feature_adaptive_hedging = False
        hedging_min_delay_ms = 60
        hedging_max_delay_ms = 600
        adaptive_ema_alpha = 0.2
        hedging_max_parallel_hedges = 2
    settings = MockSettings()
    hedged_attempts_total = None
    hedged_wins_total = None
    hedging_cost_per_hour = None

# Optional Prometheus metrics (first-class hedging telemetry)
try:
    from prometheus_client import Counter, Gauge, Histogram
    HEDGE_LAUNCH = Counter("petplantr_hedge_launch_total", "Number of secondary legs started")
    HEDGE_WIN = Counter("petplantr_hedge_win_total", "Number of times the secondary leg won the race")
    HEDGE_SKIP_BUDGET = Counter("petplantr_hedge_skip_budget_total", "Hedges skipped due to budget window or kill-switch")
    HEDGE_SKIP_CAPACITY = Counter("petplantr_hedge_skip_capacity_total", "Hedges skipped due to token/capacity constraints")
    HEDGE_SKIP_PARALLEL = Counter("petplantr_hedge_skip_parallel_total", "Hedges skipped due to parallel hedge cap")
    HEDGE_SKIP_DISABLED = Counter("petplantr_hedge_skip_disabled_total", "Hedges skipped because feature disabled")
    HEDGE_DELAY_MS = Histogram(
        "petplantr_hedge_delay_ms",
        "Applied hedge delay (ms)",
        buckets=[50, 100, 200, 300, 500, 800, 1200, 2000, 5000, 10000]
    )
    HEDGE_PARALLEL = Gauge("petplantr_hedge_parallel", "Current number of parallel hedges")
except Exception:
    class _N:
        def inc(self, *_, **__):
            pass
        def observe(self, *_, **__):
            pass
        def set(self, *_, **__):
            pass
    HEDGE_LAUNCH = HEDGE_WIN = HEDGE_SKIP_BUDGET = HEDGE_SKIP_CAPACITY = HEDGE_SKIP_PARALLEL = HEDGE_SKIP_DISABLED = _N()
    HEDGE_DELAY_MS = _N()
    HEDGE_PARALLEL = _N()

# Global lock to ensure budget/launch gate is concurrency-safe
# NOTE: Resolve lock per running event loop to avoid cross-loop errors in tests
_locks_by_loop = weakref.WeakKeyDictionary()

def _get_budget_gate_lock() -> asyncio.Lock:
    loop = asyncio.get_running_loop()
    lock = _locks_by_loop.get(loop)
    if lock is None:
        lock = asyncio.Lock()
        _locks_by_loop[loop] = lock
    return lock

# Keep a module attribute for compatibility with other modules expecting it
_budget_gate_lock = asyncio.Lock()
# Global counter of current parallel hedges
_current_parallel_hedges = 0

class CostTracker:
    """Track hedging costs and enforce budgets."""
    
    def __init__(self):
        self.hourly_costs = {}  # timestamp_hour -> cost
        self.breed_cost_estimate = 0.001  # $0.001 per breed request estimate
        self.hedging_disabled_until = 0  # Unix timestamp
        
    def record_hedged_request(self, request_type: str = "breed"):
        """Record cost for a hedged request."""
        current_hour = int(time.time() // 3600)
        
        if current_hour not in self.hourly_costs:
            self.hourly_costs[current_hour] = 0
            
        if request_type == "breed":
            self.hourly_costs[current_hour] += self.breed_cost_estimate
            
        # Clean old hours (keep last 24)
        cutoff_hour = current_hour - 24
        self.hourly_costs = {h: cost for h, cost in self.hourly_costs.items() if h > cutoff_hour}
        
        # Update metrics
        if METRICS_AVAILABLE and hedging_cost_per_hour:
            current_cost = self.hourly_costs.get(current_hour, 0)
            hedging_cost_per_hour.set(current_cost)
            
        return self.get_current_hourly_cost()
    
    def get_current_hourly_cost(self) -> float:
        """Get current hour's hedging cost."""
        current_hour = int(time.time() // 3600)
        return self.hourly_costs.get(current_hour, 0)
    
    def should_allow_hedging(self) -> bool:
        """Check if hedging should be allowed based on cost budget."""
        now = time.time()
        
        # Check if hedging is temporarily disabled
        if now < self.hedging_disabled_until:
            return False
            
        current_cost = self.get_current_hourly_cost()
        if current_cost >= settings.hedging_cost_limit_per_hour:
            # Disable hedging for 1 hour
            self.hedging_disabled_until = now + 3600
            logger.warning(f"Hedging disabled due to cost limit: ${current_cost:.2f}/hour >= ${settings.hedging_cost_limit_per_hour}")
            return False
            
        return True
    
    def disable_for_seconds(self, seconds: int = 3600):
        self.hedging_disabled_until = time.time() + max(0, seconds)
    
    def enable_now(self):
        self.hedging_disabled_until = 0

# Global cost tracker
cost_tracker = CostTracker()

class AdaptiveDelay:
    """Adaptive hedging delay estimator using EMA of observed primary latencies."""
    
    def __init__(self, initial_ms: int, alpha: float, min_ms: int, max_ms: int):
        self.ema_ms = float(initial_ms)
        self.alpha = max(0.01, min(0.99, float(alpha)))
        self.min_ms = int(min_ms)
        self.max_ms = int(max_ms)
        # Ratio of EMA at which to trigger hedge; tuned conservatively
        self.ratio = 0.6
    
    def observe_primary_seconds(self, duration_sec: float):
        ms = max(1.0, duration_sec * 1000.0)
        self.ema_ms = self.alpha * ms + (1.0 - self.alpha) * self.ema_ms
        return self.ema_ms
    
    def suggest_delay_ms(self) -> int:
        raw = int(self.ema_ms * self.ratio)
        return max(self.min_ms, min(self.max_ms, raw))

# Global adaptive delay estimator
adaptive_delay = AdaptiveDelay(
    initial_ms=getattr(settings, 'hedging_delay_ms', 180),
    alpha=getattr(settings, 'adaptive_ema_alpha', 0.2),
    min_ms=getattr(settings, 'hedging_min_delay_ms', 60),
    max_ms=getattr(settings, 'hedging_max_delay_ms', 600),
)

class _HedgingStats:
    """Lightweight local stats for auto-tuning.
    Tracks counts and exposes EMA via adaptive_delay.
    """
    def __init__(self):
        self.hedges_started = 0
        self.hedges_won = 0

    @property
    def ema_start_ms(self) -> float:
        return float(getattr(adaptive_delay, 'ema_ms', 0.0))

stats = _HedgingStats()

class HedgedRequest:
    """Manages a hedged request race between primary and secondary calls."""
    
    def __init__(self, request_name: str = "hedged_request"):
        self.request_name = request_name
        self.start_time = time.time()
        self.primary_task: Optional[asyncio.Task] = None
        self.secondary_task: Optional[asyncio.Task] = None
        self.idem_key = f"{request_name}-{uuid.uuid4()}"
        self._launched_secondary = False
        
    async def race(
        self,
        request_func: Callable[[], Awaitable[Any]],
        timeout_sec: float,
        delay_ms: Optional[int] = None
    ) -> Any:
        """
        Execute hedged request race.
        
        Args:
            request_func: Function that makes the actual request
            timeout_sec: Timeout for each individual request
            delay_ms: Delay before launching secondary (uses setting if None)
        """
        global _current_parallel_hedges
        # Fast path: feature flag disabled
        if not settings.feature_hedging:
            HEDGE_SKIP_DISABLED.inc()
            return await request_func()
        
        # Choose delay: adaptive or static
        if getattr(settings, 'feature_adaptive_hedging', False):
            chosen_delay_ms = adaptive_delay.suggest_delay_ms()
        else:
            chosen_delay_ms = (delay_ms or settings.hedging_delay_ms)
        delay_sec = chosen_delay_ms / 1000.0
        HEDGE_DELAY_MS.observe(chosen_delay_ms)
        
        # Start primary request immediately
        self.primary_task = asyncio.create_task(
            self._wrap_request(request_func(), "primary")
        )
        
        try:
            # Wait for either primary completion or hedging delay
            done, pending = await asyncio.wait(
                {self.primary_task},
                timeout=delay_sec,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            if done:
                # Primary completed within delay window
                result = await self.primary_task
                logger.debug(f"[{self.request_name}] Primary completed fast ({time.time() - self.start_time:.3f}s)")
                return result
            
            # Primary didn't complete - attempt to start secondary (hedged request)
            # Concurrency-safe budget/kill-switch and parallel cap gate
            async with _get_budget_gate_lock():
                if not cost_tracker.should_allow_hedging():
                    logger.info(f"[{self.request_name}] Hedging skipped by budget/kill-switch at launch gate")
                    HEDGE_SKIP_BUDGET.inc()
                    result = await self.primary_task
                    return result
                
                # Parallel hedges cap
                # global _current_parallel_hedges  # removed redundant global
                if _current_parallel_hedges >= getattr(settings, 'hedging_max_parallel_hedges', 2):
                    HEDGE_SKIP_PARALLEL.inc()
                    result = await self.primary_task
                    return result
                
                # Record hedging attempt and cost under the same lock, increment parallel
                if METRICS_AVAILABLE and hedged_attempts_total:
                    hedged_attempts_total.inc()
                stats.hedges_started += 1
                cost_tracker.record_hedged_request()
                _current_parallel_hedges += 1
                self._launched_secondary = True
                HEDGE_PARALLEL.set(_current_parallel_hedges)
                HEDGE_LAUNCH.inc()
        
            logger.info(f"[{self.request_name}] Starting hedged request after {delay_sec:.3f}s delay (chosen={chosen_delay_ms}ms)")
            
            # Start secondary request
            self.secondary_task = asyncio.create_task(
                self._wrap_request(request_func(), "secondary")
            )
            
            # Race primary vs secondary
            done, pending = await asyncio.wait(
                {self.primary_task, self.secondary_task},
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Get winner
            winner_task = next(iter(done))
            winner_result = await winner_task
            
            # Cancel loser
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Track which request won
            if winner_task == self.secondary_task:
                logger.info(f"[{self.request_name}] Hedged request won the race!")
                if METRICS_AVAILABLE and hedged_wins_total:
                    hedged_wins_total.inc()
                stats.hedges_won += 1
                HEDGE_WIN.inc()
            else:
                logger.debug(f"[{self.request_name}] Primary request won")
            
            duration = time.time() - self.start_time
            logger.info(f"[{self.request_name}] Hedged race completed in {duration:.3f}s")
            
            return winner_result
            
        except Exception as e:
            # Cancel any pending tasks
            for task in [self.primary_task, self.secondary_task]:
                if task and not task.done():
                    task.cancel()
            
            logger.error(f"[{self.request_name}] Hedged request failed: {e}")
            raise
        finally:
            # Release global parallel counter if we incremented it
            if self._launched_secondary:
                async with _get_budget_gate_lock():
                    _current_parallel_hedges = max(0, _current_parallel_hedges - 1)
                    HEDGE_PARALLEL.set(_current_parallel_hedges)

    async def _wrap_request(self, coro: Awaitable[Any], request_type: str) -> Any:
        """Wrap request with logging and error handling."""
        try:
            start = time.time()
            result = await coro
            duration = time.time() - start
            # Observe only primary completions for adaptive delay
            if request_type == "primary" and getattr(settings, 'feature_adaptive_hedging', False):
                new_ema = adaptive_delay.observe_primary_seconds(duration)
                logger.debug(f"[{self.request_name}] Adaptive EMA updated to {new_ema:.1f}ms")
            logger.debug(f"[{self.request_name}] {request_type} completed in {duration:.3f}s")
            return result
        except Exception as e:
            logger.warning(f"[{self.request_name}] {request_type} failed: {e}")
            raise

@asynccontextmanager
async def hedged_request(request_name: str = "hedged_request"):
    """
    Context manager for hedged requests.
    
    Usage:
        async with hedged_request("breed_detection") as hedger:
            result = await hedger.race(request_func, timeout_sec=8.0)
    """
    hedger = HedgedRequest(request_name)
    try:
        yield hedger
    finally:
        # Cleanup any pending tasks
        for task in [hedger.primary_task, hedger.secondary_task]:
            if task and not task.done():
                task.cancel()

def get_hedging_stats() -> Dict[str, Any]:
    """Get current hedging statistics."""
    return {
        "feature_enabled": settings.feature_hedging,
        "feature_adaptive": getattr(settings, 'feature_adaptive_hedging', False),
        "cost_budget_per_hour": settings.hedging_cost_limit_per_hour,
        "current_hourly_cost": cost_tracker.get_current_hourly_cost(),
        "hedging_allowed": cost_tracker.should_allow_hedging(),
        "disabled_until": cost_tracker.hedging_disabled_until,
        "delay_ms": settings.hedging_delay_ms,
        "min_delay_ms": getattr(settings, 'hedging_min_delay_ms', None),
        "max_delay_ms": getattr(settings, 'hedging_max_delay_ms', None),
        "ema_ms": getattr(adaptive_delay, 'ema_ms', None),
        "max_extra": settings.hedging_max_extra,
        "max_parallel_hedges": getattr(settings, 'hedging_max_parallel_hedges', 2),
        # Local stats for tuner/ops
        "hedges_started": getattr(stats, 'hedges_started', 0),
        "hedges_won": getattr(stats, 'hedges_won', 0),
    }

# Runtime configuration helpers (ops endpoints)

def set_hedging_config(**kwargs) -> Dict[str, Any]:
    """Set hedging configuration at runtime. Returns updated stats."""
    for k, v in kwargs.items():
        if hasattr(settings, k):
            setattr(settings, k, v)
    # Update adaptive estimator bounds/alpha if provided
    if 'hedging_min_delay_ms' in kwargs:
        adaptive_delay.min_ms = int(kwargs['hedging_min_delay_ms'])
    if 'hedging_max_delay_ms' in kwargs:
        adaptive_delay.max_ms = int(kwargs['hedging_max_delay_ms'])
    if 'adaptive_ema_alpha' in kwargs:
        adaptive_delay.alpha = max(0.01, min(0.99, float(kwargs['adaptive_ema_alpha'])))
    if 'hedging_delay_ms' in kwargs:
        adaptive_delay.ema_ms = float(kwargs['hedging_delay_ms'])
    return get_hedging_stats()

def enable_kill_switch():
    cost_tracker.disable_for_seconds(3600)
    return get_hedging_stats()

def disable_kill_switch():
    cost_tracker.enable_now()
    return get_hedging_stats()

# Export the main interface
__all__ = [
    "hedged_request",
    "HedgedRequest", 
    "cost_tracker",
    "get_hedging_stats",
    "set_hedging_config",
    "enable_kill_switch",
    "disable_kill_switch",
    # Expose internals useful for ops sync/tuner
    "adaptive_delay",
    "_budget_gate_lock",
    "settings",
    "stats",
]
