"""
SLO Metrics and Observability for PetPlantr
Prometheus metrics for monitoring service health and performance
"""
import time
import logging
from typing import Dict, Any, Optional
from enum import Enum
import os

logger = logging.getLogger(__name__)

# Mock Prometheus metrics for development
# In production, use: from prometheus_client import Counter, Histogram, Gauge, Info
class MockMetric:
    def __init__(self, name: str, description: str, labelnames=None, **kwargs):
        self.name = name
        self.description = description
        self.labelnames = labelnames or []
        self._value = 0
        self._labels = {}
    
    def inc(self, amount: float = 1):
        self._value += amount
        logger.debug(f"Metric {self.name} incremented to {self._value}")
    
    def observe(self, amount: float):
        self._value = amount
        logger.debug(f"Metric {self.name} observed: {amount}")
    
    def set(self, amount: float):
        self._value = amount
        logger.debug(f"Metric {self.name} set to: {amount}")
    
    def labels(self, **kwargs):
        new_metric = MockMetric(self.name, self.description)
        new_metric._labels = kwargs
        return new_metric
    
    def info(self, data: Dict[str, str]):
        logger.info(f"Metric {self.name} info: {data}")

# Production metrics registry
METRICS_ENABLED = os.getenv("METRICS_EXPORTER", "mock") != "mock"

if METRICS_ENABLED:
    try:
        from prometheus_client import Counter, Histogram, Gauge, Info
        logger.info("Using Prometheus metrics")
    except ImportError:
        logger.warning("Prometheus client not available, using mock metrics")
        Counter = Histogram = Gauge = Info = MockMetric
else:
    Counter = Histogram = Gauge = Info = MockMetric
    logger.info("Using mock metrics (development mode)")

# Core SLO Metrics
http_requests_total = Counter(
    'petplantr_http_requests_total',
    'Total HTTP requests by route and status',
    ['route', 'method', 'status_code']
)

http_request_duration_seconds = Histogram(
    'petplantr_http_request_duration_seconds',
    'HTTP request duration by route',
    ['route', 'method'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

# Replicate API Metrics
replicate_requests_total = Counter(
    'petplantr_replicate_requests_total',
    'Total Replicate API requests by operation and status',
    ['operation', 'status']
)

replicate_request_duration_seconds = Histogram(
    'petplantr_replicate_request_duration_seconds',
    'Replicate API request duration by operation',
    ['operation'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

# Circuit Breaker Metrics
circuit_breaker_state = Gauge(
    'petplantr_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half-open, 2=open)',
    ['service']
)

circuit_breaker_failures_total = Counter(
    'petplantr_circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['service']
)

# Queue & Admission Control Metrics
queue_depth_current = Gauge(
    'petplantr_queue_depth_current',
    'Current queue depth by operation',
    ['operation']
)

admission_control_rejections_total = Counter(
    'petplantr_admission_control_rejections_total',
    'Total requests rejected by admission control',
    ['operation', 'reason']
)

# SLO Violation Metrics
slo_violations_total = Counter(
    'petplantr_slo_violations_total',
    'Total SLO violations by metric and severity',
    ['metric', 'severity']
)

# Resource Usage Metrics
active_connections_current = Gauge(
    'petplantr_active_connections_current',
    'Current active connections',
    ['pool']
)

memory_usage_bytes = Gauge(
    'petplantr_memory_usage_bytes',
    'Memory usage in bytes',
    ['component']
)

# Business Metrics
generations_total = Counter(
    'petplantr_generations_total',
    'Total 3D model generations by status',
    ['status', 'quality']
)

generation_duration_seconds = Histogram(
    'petplantr_generation_duration_seconds',
    'Model generation duration',
    ['quality'],
    buckets=[5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0]
)

# Sprint B: Hedging Metrics
hedged_attempts_total = Counter(
    'petplantr_hedged_attempts_total',
    'Total hedged breed requests fired'
)

hedged_wins_total = Counter(
    'petplantr_hedged_wins_total', 
    'Hedged duplicates that won the race'
)

hedging_cost_per_hour = Gauge(
    'petplantr_hedging_cost_per_hour',
    'Estimated hedging cost per hour in USD'
)

# Sprint B: Mesh Governor Metrics
governor_transitions_total = Counter(
    'petplantr_mesh_governor_transitions_total',
    'Times governor switched presets',
    ['from_preset', 'to_preset']
)

mesh_preset_active = Gauge(
    'petplantr_mesh_preset_active',
    'Current active mesh preset (0=baseline, 1=warn, 2=drop)',
    []
)

mesh_fidelity_degraded_total = Counter(
    'petplantr_mesh_fidelity_degraded_total',
    'Requests where mesh fidelity was degraded',
    ['reason']
)

# System Health Metrics
system_health_score = Gauge(
    'petplantr_system_health_score',
    'Overall system health score (0-1)',
    []
)

dependency_health = Gauge(
    'petplantr_dependency_health',
    'Dependency health status (0=down, 1=up)',
    ['dependency']
)

# Application Info
app_info = Info(
    'petplantr_app_info',
    'Application information'
)

class MetricsCollector:
    """Central metrics collection and SLO monitoring."""
    
    def __init__(self):
        self.start_time = time.time()
        self.slo_thresholds = {
            'breed_detection_p95_ms': float(os.getenv('BREED_P95_TARGET_MS', '300')),
            'mesh_generation_p95_min': float(os.getenv('MESH_P95_TARGET_MIN', '5')),
            'error_rate_max': float(os.getenv('ERROR_RATE_MAX', '0.01')),
            'queue_depth_alert': int(os.getenv('ALERT_QUEUE_THRESHOLD', '75'))
        }
        
        # Initialize app info
        if hasattr(app_info, 'info'):
            app_info.info({
                'version': os.getenv('APP_VERSION', '1.0.0'),
                'environment': os.getenv('ENVIRONMENT', 'development'),
                'build_date': os.getenv('BUILD_DATE', str(int(time.time()))),
                'git_commit': os.getenv('GIT_COMMIT', 'unknown')
            })
    
    def record_http_request(self, route: str, method: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        http_requests_total.labels(
            route=route,
            method=method,
            status_code=str(status_code)
        ).inc()
        
        http_request_duration_seconds.labels(
            route=route,
            method=method
        ).observe(duration)
        
        # Check SLO violations
        if route == '/api/v1/breed/detect' and duration > self.slo_thresholds['breed_detection_p95_ms'] / 1000:
            slo_violations_total.labels(
                metric='breed_detection_latency',
                severity='warning'
            ).inc()
    
    def record_replicate_request(self, operation: str, status: str, duration: float):
        """Record Replicate API request metrics."""
        replicate_requests_total.labels(
            operation=operation,
            status=status
        ).inc()
        
        replicate_request_duration_seconds.labels(
            operation=operation
        ).observe(duration)
    
    def update_circuit_breaker_state(self, service: str, state: str, failure_count: int = 0):
        """Update circuit breaker metrics."""
        state_map = {'closed': 0, 'half_open': 1, 'open': 2}
        circuit_breaker_state.labels(service=service).set(state_map.get(state, 0))
        
        if failure_count > 0:
            circuit_breaker_failures_total.labels(service=service).inc(failure_count)
    
    def update_queue_depth(self, operation: str, depth: int):
        """Update queue depth metrics."""
        queue_depth_current.labels(operation=operation).set(depth)
        
        # Check for queue alerts
        if depth >= self.slo_thresholds['queue_depth_alert']:
            slo_violations_total.labels(
                metric='queue_depth',
                severity='critical'
            ).inc()
    
    def record_admission_rejection(self, operation: str, reason: str):
        """Record admission control rejection."""
        admission_control_rejections_total.labels(
            operation=operation,
            reason=reason
        ).inc()
    
    def record_generation(self, status: str, quality: str, duration: Optional[float] = None):
        """Record model generation metrics."""
        generations_total.labels(
            status=status,
            quality=quality
        ).inc()
        
        if duration is not None:
            generation_duration_seconds.labels(quality=quality).observe(duration)
    
    def update_dependency_health(self, dependency: str, is_healthy: bool):
        """Update dependency health status."""
        dependency_health.labels(dependency=dependency).set(1 if is_healthy else 0)
    
    def calculate_health_score(self) -> float:
        """Calculate overall system health score."""
        # Simplified health calculation
        # In production, this would consider multiple factors
        uptime = time.time() - self.start_time
        base_score = min(uptime / 3600, 1.0)  # Ramp up over first hour
        
        # Adjust based on recent errors, queue depth, etc.
        # This is a placeholder - implement based on your SLOs
        health_score = base_score * 0.95  # Conservative estimate
        
        system_health_score.set(health_score)
        return health_score
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        return {
            'health_score': self.calculate_health_score(),
            'uptime_seconds': time.time() - self.start_time,
            'slo_thresholds': self.slo_thresholds,
            'metrics_enabled': METRICS_ENABLED
        }

# Global metrics collector
metrics = MetricsCollector()

# Context managers for easy metric collection
class MetricsTimer:
    """Context manager for timing operations."""
    
    def __init__(self, metric, **labels):
        self.metric = metric
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            if self.labels:
                self.metric.labels(**self.labels).observe(duration)
            else:
                self.metric.observe(duration)

def time_http_request(route: str, method: str):
    """Decorator/context manager for timing HTTP requests."""
    return MetricsTimer(http_request_duration_seconds, route=route, method=method)

def time_replicate_request(operation: str):
    """Decorator/context manager for timing Replicate requests."""
    return MetricsTimer(replicate_request_duration_seconds, operation=operation)
