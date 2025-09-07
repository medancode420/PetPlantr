"""
Production-ready Replicate Client with Circuit Breaker
Implements timeout budgets, retries, and reliability patterns
"""
import time
import asyncio
import random
import logging
from typing import Callable, Awaitable, Optional, Dict, Any
from enum import Enum
import httpx

import os
import uuid

# Import ProviderBusy to signal upstream busy/rate-limit conditions
try:
    from replicate_client import ProviderBusy  # type: ignore
except Exception:  # Fallback shim if minimal class not present
    class ProviderBusy(Exception):  # type: ignore
        def __init__(self, status: int, message: str = "provider busy", retry_after: Optional[str] = None):
            super().__init__(message)
            self.status = int(status)
            self.retry_after = retry_after

# Labeled metric for upstream busy/timeout classification (default registry)
try:
    from prometheus_client import Counter as _PromCounter  # type: ignore

    PROVIDER_BUSY = _PromCounter(
        "petplantr_provider_busy_total",
        "Upstream busy/timeout events from provider",
        ["phase", "reason"],  # phase: create|poll|transport|other ; reason: http429|http503|timeout|connect
    )
except Exception:  # prometheus not installed in some test envs
    class _N:  # type: ignore
        def labels(self, *_, **__):
            return self
        def inc(self, *_, **__):
            return None
    PROVIDER_BUSY = _N()  # type: ignore

# Settings configuration - TODO: Import from settings.py
class Config:
    replicate_api_token = os.getenv("REPLICATE_API_TOKEN", "")
    replicate_timeout_sec_breed = float(os.getenv("REPLICATE_TIMEOUT_SEC_BREED", "8.0"))
    replicate_timeout_sec_mesh = float(os.getenv("REPLICATE_TIMEOUT_SEC_MESH", "60.0"))
    upstream_connect_timeout_ms = int(os.getenv("UPSTREAM_CONNECT_TIMEOUT_MS", "800"))
    retry_max_attempts = int(os.getenv("RETRY_MAX_ATTEMPTS", "2"))
    retry_max_jitter_ms = int(os.getenv("RETRY_MAX_JITTER_MS", "300"))
    cb_failure_rate = float(os.getenv("CB_FAILURE_RATE", "0.5"))
    cb_min_requests = int(os.getenv("CB_MIN_REQUESTS", "20"))
    cb_open_sec = int(os.getenv("CB_OPEN_SEC", "30"))
    cb_halfopen_max = int(os.getenv("CB_HALFOPEN_MAX_INFLIGHT", "3"))
    idempotency_header = os.getenv("IDEMPOTENCY_HEADER", "X-Idempotency-Key")

settings = Config()

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """
    Lightweight circuit breaker for upstream service protection.
    
    Features:
    - Failure rate based triggering
    - Half-open probing for recovery
    - Configurable thresholds and timeouts
    """
    
    def __init__(self):
        self.state = CircuitBreakerState.CLOSED
        self.failures = 0
        self.successes = 0
        self.open_until = 0.0
        self.half_open_inflight = 0
        self.last_failure_time = 0.0
        
        # Sliding window for failure rate calculation
        self.request_window = []
        self.window_size_sec = 60  # 1 minute window
        
    def _clean_window(self):
        """Remove old entries from the sliding window."""
        now = time.time()
        cutoff = now - self.window_size_sec
        self.request_window = [entry for entry in self.request_window if entry['timestamp'] > cutoff]
    
    def _get_failure_rate(self) -> float:
        """Calculate current failure rate in the time window."""
        self._clean_window()
        
        if len(self.request_window) < settings.cb_min_requests:
            return 0.0
        
        failures = sum(1 for entry in self.request_window if not entry['success'])
        return failures / len(self.request_window)
    
    def _record_request(self, success: bool):
        """Record a request outcome in the sliding window."""
        self.request_window.append({
            'timestamp': time.time(),
            'success': success
        })
        
        # Keep window size manageable
        if len(self.request_window) > settings.cb_min_requests * 3:
            self._clean_window()
    
    def allow_request(self) -> bool:
        """Check if a request should be allowed through the circuit breaker."""
        now = time.time()
        
        if self.state == CircuitBreakerState.OPEN:
            if now >= self.open_until:
                logger.info("Circuit breaker transitioning from OPEN to HALF_OPEN")
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_inflight = 0
            else:
                return False
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_inflight >= settings.cb_halfopen_max:
                return False
        
        return True
    
    def record_success(self):
        """Record a successful request."""
        self._record_request(True)
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info("Circuit breaker transitioning from HALF_OPEN to CLOSED")
            self.state = CircuitBreakerState.CLOSED
            self.failures = 0
            self.successes = 0
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_inflight = max(0, self.half_open_inflight - 1)
    
    def record_failure(self):
        """Record a failed request."""
        self._record_request(False)
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.warning("Circuit breaker transitioning from HALF_OPEN to OPEN (failure during probe)")
            self.state = CircuitBreakerState.OPEN
            self.open_until = time.time() + settings.cb_open_sec
        elif self.state == CircuitBreakerState.CLOSED:
            failure_rate = self._get_failure_rate()
            if failure_rate >= settings.cb_failure_rate:
                logger.error(f"Circuit breaker OPENING due to high failure rate: {failure_rate:.2%}")
                self.state = CircuitBreakerState.OPEN
                self.open_until = time.time() + settings.cb_open_sec
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_inflight = max(0, self.half_open_inflight - 1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics."""
        return {
            'state': self.state.value,
            'failure_rate': self._get_failure_rate(),
            'requests_in_window': len(self.request_window),
            'half_open_inflight': self.half_open_inflight,
            'open_until': self.open_until if self.state == CircuitBreakerState.OPEN else None,
            'last_failure_time': self.last_failure_time
        }

# Global circuit breaker instance
circuit_breaker = CircuitBreaker()

# Optional hedging import (feature-flagged)
try:
    from src.services.hedging import hedged_request as hedged_request_ctx  # type: ignore
    from src.services.hedging import settings as hedging_settings  # type: ignore
    HEDGING_ENABLED_IMPORT = True
except Exception:
    hedged_request_ctx = None  # type: ignore
    hedging_settings = None  # type: ignore
    HEDGING_ENABLED_IMPORT = False


def _phase_from_operation(operation_name: str) -> str:
    op = (operation_name or "").lower()
    if "create" in op:
        return "create"
    if "poll" in op:
        return "poll"
    return "other"

class ReplicateClient:
    """
    Production-ready Replicate API client with reliability features.
    
    Features:
    - HTTP/2 connection pooling
    - Configurable timeouts per operation
    - Exponential backoff with jitter
    - Circuit breaker integration
    - Comprehensive error handling
    - Optional request hedging (feature-flagged)
    - ProviderBusy signalling for upstream 429/503
    """
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self._request_count = 0
        self._error_count = 0
    
    async def startup(self):
        """Initialize the HTTP client with optimal settings."""
        self.client = httpx.AsyncClient(
            http2=True,
            timeout=None,  # We handle timeouts per request
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0
            ),
            headers={
                "Authorization": f"Token {settings.replicate_api_token}",
                "User-Agent": "PetPlantr/1.0",
                "Content-Type": "application/json"
            }
        )
        logger.info("Replicate client initialized with HTTP/2 and connection pooling")
    
    async def shutdown(self):
        """Clean shutdown of the HTTP client."""
        if self.client:
            await self.client.aclose()
            logger.info("Replicate client shutdown complete")

    async def request(
        self,
        method: str,
        url: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_sec: float,
        idempotent: bool = True,
        operation_name: str = "replicate_call",
        use_hedging: bool = True,
    ) -> httpx.Response:
        """
        Perform an HTTP request to Replicate with retries, circuit breaker, and optional hedging.
        """
        if self.client is None:
            raise ReplicateClientError("Client not initialized")

        # Compose per-request timeout
        per_req_timeout = httpx.Timeout(
            connect=settings.upstream_connect_timeout_ms / 1000.0,
            read=timeout_sec,
            write=10.0,
            pool=5.0,
        )

        # Build headers with a stable idempotency key for both hedge legs
        base_headers = dict(self.client.headers)
        if headers:
            base_headers.update(headers)
        idem_key = f"{operation_name}-{uuid.uuid4()}"
        base_headers[settings.idempotency_header] = idem_key

        async def do_http() -> httpx.Response:
            assert self.client is not None
            return await self.client.request(
                method,
                url,
                json=json,
                data=data,
                headers=base_headers,
                timeout=per_req_timeout,
            )

        # Helper to run the request with our retry/circuit-breaker wrapper
        async def run_once() -> httpx.Response:
            return await self.call_with_retries(
                request_func=do_http,
                timeout_sec=timeout_sec,
                idempotent=idempotent,
                operation_name=operation_name,
                idempotency_key=idem_key,
            )

        # Hedging gate: feature flag and import availability
        should_hedge = (
            use_hedging and HEDGING_ENABLED_IMPORT and hasattr(hedging_settings, 'feature_hedging')
            and getattr(hedging_settings, 'feature_hedging', False)
        )

        if should_hedge and hedged_request_ctx is not None:
            # Race duplicate requests using the same idempotency key
            try:
                async with hedged_request_ctx(operation_name) as hedger:
                    return await hedger.race(run_once, timeout_sec=timeout_sec)
            except Exception:
                # Fallback to single-path on any hedging error
                logger.warning("Hedged path failed, falling back to single request", exc_info=True)
                return await run_once()
        else:
            return await run_once()
    
    async def call_with_retries(
        self,
        request_func: Callable[[], Awaitable[httpx.Response]],
        timeout_sec: float,
        idempotent: bool = True,
        operation_name: str = "replicate_call",
        idempotency_key: Optional[str] = None
    ) -> httpx.Response:
        """
        Execute a Replicate API call with retries and circuit breaker protection.
        
        Args:
            request_func: Function that returns the HTTP request
            timeout_sec: Total timeout for the operation
            idempotent: Whether the operation can be safely retried
            operation_name: Name for logging and metrics
        """
        # Check circuit breaker
        if not circuit_breaker.allow_request():
            self._error_count += 1
            raise ReplicateUnavailableError("Circuit breaker is OPEN - upstream unavailable")
        
        # Track half-open inflight requests
        if circuit_breaker.state == CircuitBreakerState.HALF_OPEN:
            circuit_breaker.half_open_inflight += 1
        
        attempts = settings.retry_max_attempts if idempotent else 1
        last_exception: Optional[Exception] = None
        
        for attempt in range(attempts):
            try:
                self._request_count += 1
                start_time = time.time()
                
                logger.debug(f"[{operation_name}] Attempt {attempt + 1}/{attempts}")
                
                # Execute request - idempotency handled at higher level
                response = await request_func()

                # Classify provider busy (upstream 429/503) early and carry Retry-After
                if response.status_code in (429, 503):
                    circuit_breaker.record_failure()
                    retry_after = response.headers.get("Retry-After") or response.headers.get("retry-after")
                    reason = "http429" if response.status_code == 429 else "http503"
                    PROVIDER_BUSY.labels(phase=_phase_from_operation(operation_name), reason=reason).inc()
                    logger.warning(f"[{operation_name}] Upstream busy {response.status_code}, attempt {attempt + 1}; retry_after={retry_after}")
                    if attempt < attempts - 1:
                        await self._jittered_sleep(attempt)
                        continue
                    else:
                        self._error_count += 1
                        raise ProviderBusy(int(response.status_code), "provider busy", retry_after=retry_after)

                # Success path
                if 200 <= response.status_code < 300:
                    duration = time.time() - start_time
                    logger.info(f"[{operation_name}] Success in {duration:.2f}s (attempt {attempt + 1})")
                    circuit_breaker.record_success()
                    return response

                # Handle client errors (other 4xx) - don't retry
                if 400 <= response.status_code < 500:
                    circuit_breaker.record_failure()
                    self._error_count += 1
                    raise ReplicateClientError(f"Client error {response.status_code}: {response.text}")

                # Handle server errors (other 5xx)
                logger.warning(f"[{operation_name}] Server error {response.status_code}, attempt {attempt + 1}")
                circuit_breaker.record_failure()
                if attempt < attempts - 1:
                    await self._jittered_sleep(attempt)
                    continue
                else:
                    self._error_count += 1
                    raise ReplicateServerError(f"Server error {response.status_code}: {response.text}")

            except asyncio.TimeoutError as e:
                logger.warning(f"[{operation_name}] Timeout on attempt {attempt + 1}")
                circuit_breaker.record_failure()
                last_exception = e
                
                if attempt < attempts - 1:
                    await self._jittered_sleep(attempt)
                    continue
                else:
                    self._error_count += 1
                    raise ReplicateTimeoutError(f"Operation timed out after {timeout_sec}s")
            
            except httpx.ReadTimeout as e:
                # Treat upstream read timeouts as provider unavailable -> bubble as ProviderBusy for laddering
                logger.warning(f"[{operation_name}] Upstream read timeout: {e}")
                circuit_breaker.record_failure()
                self._error_count += 1
                PROVIDER_BUSY.labels(phase="transport", reason="timeout").inc()
                raise ProviderBusy(503, "provider timeout/unavailable") from e
            except httpx.ConnectTimeout as e:
                logger.warning(f"[{operation_name}] Upstream connect timeout: {e}")
                circuit_breaker.record_failure()
                self._error_count += 1
                PROVIDER_BUSY.labels(phase="transport", reason="timeout").inc()
                raise ProviderBusy(503, "provider timeout/unavailable") from e
            except httpx.PoolTimeout as e:
                logger.warning(f"[{operation_name}] Upstream pool timeout: {e}")
                circuit_breaker.record_failure()
                self._error_count += 1
                PROVIDER_BUSY.labels(phase="transport", reason="timeout").inc()
                raise ProviderBusy(503, "provider timeout/unavailable") from e
            except httpx.ConnectError as e:
                logger.warning(f"[{operation_name}] Upstream connect error: {e}")
                circuit_breaker.record_failure()
                self._error_count += 1
                PROVIDER_BUSY.labels(phase="transport", reason="connect").inc()
                raise ProviderBusy(503, "provider timeout/unavailable") from e
            except httpx.RequestError as e:
                # Preserve existing mapping for other request errors
                logger.warning(f"[{operation_name}] Network error on attempt {attempt + 1}: {e}")
                circuit_breaker.record_failure()
                last_exception = e
                if attempt < attempts - 1:
                    await self._jittered_sleep(attempt)
                    continue
                else:
                    self._error_count += 1
                    raise ReplicateNetworkError(f"Network error: {e}")
            except ProviderBusy:
                # Bubble immediately
                raise
            except Exception as e:
                logger.error(f"[{operation_name}] Unexpected error on attempt {attempt + 1}: {e}")
                circuit_breaker.record_failure()
                last_exception = e
                if attempt < attempts - 1:
                    await self._jittered_sleep(attempt)
                    continue
                else:
                    self._error_count += 1
                    raise ReplicateUnknownError(f"Unexpected error: {e}")
        
        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
        raise ReplicateUnknownError("Unknown error in retry loop")
    
    async def _jittered_sleep(self, attempt: int):
        """Sleep with exponential backoff and jitter."""
        base_delay = 0.2 * (2 ** attempt)
        jitter = random.uniform(0, settings.retry_max_jitter_ms / 1000.0)
        delay = min(base_delay + jitter, 2.0)  # Cap at 2 seconds
        
        logger.debug(f"Retrying in {delay:.2f}s")
        await asyncio.sleep(delay)

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            'total_requests': self._request_count,
            'total_errors': self._error_count,
            'error_rate': self._error_count / max(self._request_count, 1),
            'circuit_breaker': circuit_breaker.get_stats()
        }

# Custom exceptions for better error handling
class ReplicateError(Exception):
    """Base exception for Replicate API errors."""
    pass

class ReplicateUnavailableError(ReplicateError):
    """Raised when circuit breaker is open."""
    pass

class ReplicateClientError(ReplicateError):
    """Raised for 4xx client errors."""
    pass

class ReplicateServerError(ReplicateError):
    """Raised for 5xx server errors."""
    pass

class ReplicateTimeoutError(ReplicateError):
    """Raised when requests timeout."""
    pass

class ReplicateNetworkError(ReplicateError):
    """Raised for network connectivity issues."""
    pass

class ReplicateUnknownError(ReplicateError):
    """Raised for unexpected errors."""
    pass

# Global client instance
replicate_client = ReplicateClient()
