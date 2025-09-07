# src/hedging_autotune.py
import asyncio
from typing import Any

class HedgingAutoTuner:
    def __init__(self, app: Any, min_cap: int = 0, max_cap: int = 8, step: int = 1, interval_sec: int = 45):
        self.app = app
        self.min_cap = max(0, int(min_cap))
        self.max_cap = max(self.min_cap, int(max_cap))
        self.step = max(1, int(step))
        self.interval_sec = max(15, int(interval_sec))
        self.task: asyncio.Task | None = None

    def _snapshot(self):
        try:
            from src.services.hedging import stats, settings  # type: ignore
        except Exception:
            return None
        h = getattr(self.app.state, 'hedger', None)
        if not h:
            return None
        ema = float(getattr(stats, 'ema_start_ms', 500.0))
        started = int(getattr(stats, 'hedges_started', 0))
        won = int(getattr(stats, 'hedges_won', 0))
        win_rate = (won / started) if started else 0.0
        queue_depth = int(getattr(self.app.state, 'queue_depth', 0))
        tokens_total = int(getattr(h, 'capacity_tokens', 1) or 1)
        tokens_avail = int(h.tokens_available()) if hasattr(h, 'tokens_available') else tokens_total
        used_ratio = (tokens_total - tokens_avail) / max(tokens_total, 1)
        cap = int(getattr(settings, 'hedging_max_parallel_hedges', 2))
        return {
            'ema': ema,
            'win_rate': win_rate,
            'queue_depth': queue_depth,
            'used_ratio': used_ratio,
            'cap': cap,
        }

    async def start(self):
        self.task = asyncio.create_task(self.loop())

    async def stop(self):
        if self.task:
            self.task.cancel()

    async def loop(self):
        while True:
            try:
                await asyncio.sleep(self.interval_sec)
                snap = self._snapshot()
                if not snap:
                    continue
                h = getattr(self.app.state, 'hedger', None)
                if not h:
                    continue
                cap = snap['cap']
                new_cap = cap
                # Simple policy
                if snap['ema'] > 900 or snap['queue_depth'] > 50 or snap['used_ratio'] > 0.8:
                    new_cap = min(self.max_cap, cap + self.step)
                elif snap['win_rate'] < 0.15 or snap['ema'] < 400:
                    new_cap = max(self.min_cap, cap - self.step)
                if new_cap != cap:
                    # Update under lock if available
                    lock = getattr(h, '_lock', None)
                    if lock is None:
                        try:
                            from src.services.hedging import _budget_gate_lock as lock  # type: ignore
                        except Exception:
                            lock = asyncio.Lock()
                    async with lock:
                        from src.services.hedging import settings as hedge_settings, set_hedging_config  # type: ignore
                        set_hedging_config(hedging_max_parallel_hedges=int(new_cap))
                    sync = getattr(self.app.state, 'ops_sync', None)
                    if sync and hasattr(sync, 'publish_cap'):
                        try:
                            await sync.publish_cap(int(new_cap))
                        except Exception:
                            pass
            except asyncio.CancelledError:
                break
            except Exception:
                # don't crash
                continue
