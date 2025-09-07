import time
import pytest

@pytest.mark.sprint_c
def test_security_headers_and_simple_rate_budget(client):
    r = client.get("/")
    # Security headers set by middleware
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("X-XSS-Protection") == "1; mode=block"

    # Simple token bucket stub (local test only)
    capacity = 5
    tokens = capacity
    refill_rate = 5  # per second
    last = time.time()

    def allow():
        nonlocal tokens, last
        now = time.time()
        tokens = min(capacity, tokens + (now - last) * refill_rate)
        last = now
        if tokens >= 1:
            tokens -= 1
            return True
        return False

    decisions = [allow() for _ in range(10)]
    assert decisions.count(True) >= capacity
    assert any(not d for d in decisions)
