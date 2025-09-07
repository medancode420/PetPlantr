import asyncio
import pytest

class WeightedSemaphore:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.available = capacity
        self._cond = asyncio.Condition()
    async def acquire(self, weight: int = 1):
        async with self._cond:
            await self._cond.wait_for(lambda: self.available >= weight)
            self.available -= weight
    async def release(self, weight: int = 1):
        async with self._cond:
            self.available += weight
            self._cond.notify_all()

@pytest.mark.asyncio
@pytest.mark.sprint_c
async def test_weighted_semaphore_respects_capacity_and_progress():
    sem = WeightedSemaphore(capacity=3)
    order = []

    async def task(name, w):
        await sem.acquire(w)
        order.append(f"acq-{name}")
        await asyncio.sleep(0.01)
        await sem.release(w)
        order.append(f"rel-{name}")

    t1 = asyncio.create_task(task("A", 2))
    t2 = asyncio.create_task(task("B", 2))
    t3 = asyncio.create_task(task("C", 1))

    await asyncio.gather(t1, t2, t3)

    # All acquire once
    assert order.count("acq-A") == 1
    assert order.count("acq-B") == 1
    assert order.count("acq-C") == 1

    # Heavier task B must wait until capacity frees up
    assert order.index("acq-B") > min(order.index("rel-A"), order.index("rel-C"))
