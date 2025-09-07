import heapq
import pytest

class PriorityQueue:
    def __init__(self):
        self._h = []
        self._i = 0
    def put(self, priority, item):
        # Lower number = higher priority
        heapq.heappush(self._h, (priority, self._i, item))
        self._i += 1
    def get(self):
        return heapq.heappop(self._h)[-1]
    def __len__(self):
        return len(self._h)

@pytest.mark.sprint_c
def test_priority_queue_orders_by_priority_and_fifo_within_priority():
    q = PriorityQueue()
    q.put(10, "low-1")
    q.put(1, "high-1")
    q.put(5, "med-1")
    q.put(1, "high-2")

    assert len(q) == 4
    # High first, FIFO among same priority
    assert q.get() == "high-1"
    assert q.get() == "high-2"
    assert q.get() == "med-1"
    assert q.get() == "low-1"
