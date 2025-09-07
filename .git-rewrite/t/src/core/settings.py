"""
Production Settings Configuration for PetPlantr
Comprehensive environment configuration with sensible defaults
"""
import os
from typing import Optional

class Settings:
    """Production settings with comprehensive environment configuration."""
    
    # Core API Configuration
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Upstream/Replicate Configuration
    replicate_api_token: str = os.getenv("REPLICATE_API_TOKEN", "")
    replicate_timeout_sec_breed: float = float(os.getenv("REPLICATE_TIMEOUT_SEC_BREED", "8.0"))
    replicate_timeout_sec_mesh: float = float(os.getenv("REPLICATE_TIMEOUT_SEC_MESH", "60.0"))
    upstream_connect_timeout_ms: int = int(os.getenv("UPSTREAM_CONNECT_TIMEOUT_MS", "800"))
    retry_max_attempts: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "2"))
    retry_max_jitter_ms: int = int(os.getenv("RETRY_MAX_JITTER_MS", "300"))
    
    # Circuit Breaker Configuration
    cb_failure_rate: float = float(os.getenv("CB_FAILURE_RATE", "0.5"))  # 50% failure rate triggers open
    cb_min_requests: int = int(os.getenv("CB_MIN_REQUESTS", "20"))       # Minimum requests before evaluation
    cb_open_sec: int = int(os.getenv("CB_OPEN_SEC", "30"))               # How long to stay open
    cb_halfopen_max: int = int(os.getenv("CB_HALFOPEN_MAX_INFLIGHT", "3"))  # Max concurrent in half-open
    
    # Request Hedging Configuration (Sprint B)
    feature_hedging: bool = os.getenv("FEATURE_HEDGING", "false").lower() == "true"
    hedging_delay_ms: int = int(os.getenv("HEDGING_DELAY_MS", "180"))      # Launch hedged request after this delay
    hedging_max_extra: int = int(os.getenv("HEDGING_MAX_EXTRA", "1"))      # Number of hedged duplicates
    idempotency_header: str = os.getenv("IDEMPOTENCY_HEADER", "Idempotency-Key")
    hedging_cost_limit_per_hour: float = float(os.getenv("HEDGING_COST_LIMIT_PER_HOUR", "50.0"))  # Auto-disable if exceeded
    hedging_max_parallel_hedges: int = int(os.getenv("HEDGING_MAX_PARALLEL_HEDGES", "8"))  # Cap concurrent hedged requests (raised default)

    # Sprint C: Adaptive Hedging Controls
    feature_adaptive_hedging: bool = os.getenv("FEATURE_ADAPTIVE_HEDGING", "false").lower() == "true"
    hedging_min_delay_ms: int = int(os.getenv("HEDGING_MIN_DELAY_MS", "60"))
    hedging_max_delay_ms: int = int(os.getenv("HEDGING_MAX_DELAY_MS", "600"))
    adaptive_ema_alpha: float = float(os.getenv("ADAPTIVE_EMA_ALPHA", "0.2"))
    # Per-minute hedge launch budget (ops-tunable)
    hedging_budget_per_min: int = int(os.getenv("HEDGING_BUDGET_PER_MIN", "3"))
    
    # Mesh Fidelity Governor Configuration (Sprint B)
    feature_mesh_governor: bool = os.getenv("FEATURE_MESH_GOVERNOR", "true").lower() == "true"
    governor_qdepth_warn: int = int(os.getenv("GOVERNOR_QDEPTH_WARN", "80"))
    governor_qdepth_drop: int = int(os.getenv("GOVERNOR_QDEPTH_DROP", "120"))
    governor_tokens_warn: int = int(os.getenv("GOVERNOR_TOKENS_WARN", "5"))
    governor_tokens_drop: int = int(os.getenv("GOVERNOR_TOKENS_DROP", "8"))
    
    # Admission Control & Queue Limits
    max_queue_depth_breed: int = int(os.getenv("MAX_QUEUE_DEPTH_BREED", "50"))
    max_queue_depth_mesh: int = int(os.getenv("MAX_QUEUE_DEPTH_MESH", "100"))
    max_tokens_in_use: int = int(os.getenv("MAX_TOKENS_IN_USE", "6"))
    
    # Performance Targets & SLO Thresholds
    breed_p95_target_ms: int = int(os.getenv("BREED_P95_TARGET_MS", "300"))
    mesh_p95_target_min: int = int(os.getenv("MESH_P95_TARGET_MIN", "5"))
    error_rate_max: float = float(os.getenv("ERROR_RATE_MAX", "0.01"))  # 1% max error rate
    alert_queue_threshold: int = int(os.getenv("ALERT_QUEUE_THRESHOLD", "75"))
    
    # AWS & S3 Configuration
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    s3_bucket: str = os.getenv("S3_BUCKET", "petplantr-models")
    s3_prefix: str = os.getenv("S3_PREFIX", "artifacts/")
    
    # Observability & Monitoring
    metrics_exporter: str = os.getenv("METRICS_EXPORTER", "prometheus")  # prometheus|otlp
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN")
    otel_exporter_otlp_endpoint: Optional[str] = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    # Sprint C: Synthetic monitor & ops endpoints
    feature_synthetic_monitor: bool = os.getenv("FEATURE_SYNTHETIC_MONITOR", "true").lower() == "true"
    feature_ops_endpoints: bool = os.getenv("FEATURE_OPS_ENDPOINTS", "true").lower() == "true"
    # Synthetic monitor tunables
    synthetic_monitor_interval_sec: int = int(os.getenv("SYNTHETIC_MONITOR_INTERVAL_SEC", "300"))
    synthetic_monitor_enable_mesh: bool = os.getenv("SYNTHETIC_MONITOR_ENABLE_MESH", "false").lower() == "true"
    synthetic_monitor_jitter_sec: int = int(os.getenv("SYNTHETIC_MONITOR_JITTER_SEC", "20"))
    
    # Rate Limiting & Abuse Protection
    rate_limit_rps_per_ip: int = int(os.getenv("RATE_LIMIT_RPS_PER_IP", "10"))
    rate_limit_burst_per_ip: int = int(os.getenv("RATE_LIMIT_BURST_PER_IP", "20"))
    
    # Feature Flags
    feature_point_e_fallback: bool = os.getenv("FEATURE_POINT_E_FALLBACK", "true").lower() == "true"
    feature_mesh_fidelity_governor: bool = os.getenv("FEATURE_MESH_FIDELITY_GOVERNOR", "true").lower() == "true"
    
    # GPT-5 Preview Feature (Sprint C)
    gpt5_preview_enabled: bool = os.getenv("ENABLE_GPT5_PREVIEW", "false").lower() == "true"
    gpt5_model_name: str = os.getenv("GPT5_MODEL_NAME", "gpt-5-preview")
    next_public_enable_gpt5_preview: bool = os.getenv("NEXT_PUBLIC_ENABLE_GPT5_PREVIEW", "false").lower() == "true"

    # File Upload & Processing Limits
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "3"))
    max_image_resolution: int = int(os.getenv("MAX_IMAGE_RESOLUTION", "512"))

    def __init__(self):
        """Load dynamic flags from environment on each instance for testability."""
        # Minimal dynamic overrides used in tests and runtime
        self.feature_mesh_governor = os.getenv("FEATURE_MESH_GOVERNOR", "true").lower() == "true"
        self.feature_mesh_fidelity_governor = os.getenv("FEATURE_MESH_FIDELITY_GOVERNOR", "true").lower() == "true"
        # Keep related Sprint C toggles dynamic as well
        self.feature_hedging = os.getenv("FEATURE_HEDGING", "false").lower() == "true"
        self.feature_adaptive_hedging = os.getenv("FEATURE_ADAPTIVE_HEDGING", "false").lower() == "true"
        self.gpt5_preview_enabled = os.getenv("ENABLE_GPT5_PREVIEW", "false").lower() == "true"
        self.next_public_enable_gpt5_preview = os.getenv("NEXT_PUBLIC_ENABLE_GPT5_PREVIEW", "false").lower() == "true"
        # Synthetic monitor flag may toggle at runtime in tests
        self.feature_synthetic_monitor = os.getenv("FEATURE_SYNTHETIC_MONITOR", "true").lower() == "true"
        # Ops endpoints flag should also be dynamic to avoid stale values across tests
        self.feature_ops_endpoints = os.getenv("FEATURE_OPS_ENDPOINTS", "true").lower() == "true"

# Global settings instance
settings = Settings()

# Environment validation
def validate_production_config():
    """Validate critical production configuration."""
    errors = []
    
    if not settings.replicate_api_token or len(settings.replicate_api_token) < 10:
        errors.append("REPLICATE_API_TOKEN must be set and valid")
    
    if not settings.aws_access_key_id:
        errors.append("AWS_ACCESS_KEY_ID must be set")
    
    if not settings.aws_secret_access_key:
        errors.append("AWS_SECRET_ACCESS_KEY must be set")
    
    if settings.environment == "production":
        if settings.debug:
            errors.append("DEBUG should be False in production")
        
        if settings.cb_failure_rate > 0.8:
            errors.append("CB_FAILURE_RATE too high for production")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    return True
