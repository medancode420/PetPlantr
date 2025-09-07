"""
PetPlantr Test Configuration & Fixtures
Central test setup, data factories, and shared fixtures
"""

import pytest
import tempfile
import os
import json
import struct
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch
import numpy as np
from PIL import Image
import io
import base64
from io import BytesIO
import httpx
import respx
from fastapi.testclient import TestClient

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)

# ================================
# SPRINT C FIXTURES
# ================================

@pytest.fixture(autouse=True)
def _safe_env(monkeypatch):
    """Never use real tokens in tests"""
    monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token")
    monkeypatch.setenv("S3_BUCKET", "test-bucket") 
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("FEATURE_HEDGING", "true")
    monkeypatch.setenv("FEATURE_MESH_GOVERNOR", "true")
    monkeypatch.setenv("HEDGING_COST_LIMIT_PER_HOUR", "50.0")
    monkeypatch.setenv("GOVERNOR_QDEPTH_WARN", "80")
    monkeypatch.setenv("GOVERNOR_QDEPTH_DROP", "120")
    yield

@pytest.fixture
def client():
    """FastAPI test client"""
    try:
        # Import your main FastAPI app - adjust path as needed
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        from api_server_minimal import app
    except Exception as e:
        raise RuntimeError(f"Import app failed: {e}")
    return TestClient(app)

@pytest.fixture
def respx_mock():
    """Mock Replicate API calls"""
    with respx.mock(base_url="https://api.replicate.com") as mock:
        yield mock

def _png_data_url(w=64, h=64, color=(0,0,0)):
    """Generate a test PNG data URL"""
    im = Image.new("RGB", (w, h), color)
    b = BytesIO()
    im.save(b, "PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()

@pytest.fixture
def test_image_data():
    """Test image data for upload tests"""
    return _png_data_url()

@pytest.fixture
def test_image_bytes():
    """Test image as raw bytes"""
    im = Image.new("RGB", (64, 64), (0,0,0))
    b = BytesIO()
    im.save(b, "PNG")
    return b.getvalue()

# ================================
# GOLDEN DATASET FIXTURES
# ================================

@pytest.fixture
def golden_breed_dataset():
    """Golden dataset for AI model validation"""
    return {
        "golden_retriever": {
            "confidence_threshold": 0.85,
            "expected_features": ["floppy_ears", "medium_size", "golden_coat"],
            "test_images": ["golden_1.jpg", "golden_2.jpg"],
            "planter_params": {"ear_droop": 0.7, "size_scale": 1.0}
        },
        "german_shepherd": {
            "confidence_threshold": 0.90,
            "expected_features": ["pointed_ears", "large_size", "dark_coat"],
            "test_images": ["shepherd_1.jpg", "shepherd_2.jpg"],
            "planter_params": {"ear_droop": 0.1, "size_scale": 1.2}
        },
        "pug": {
            "confidence_threshold": 0.88,
            "expected_features": ["flat_face", "small_size", "wrinkled"],
            "test_images": ["pug_1.jpg", "pug_2.jpg"],
            "planter_params": {"face_compression": 0.8, "size_scale": 0.7}
        }
    }

@pytest.fixture
def sample_dog_image():
    """Generate a sample dog image for testing"""
    # Create a simple test image
    img = Image.new('RGB', (224, 224), color='brown')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

@pytest.fixture
def valid_stl_data():
    """Sample valid STL data for testing"""
    # Create STL header with PetPlantr signature
    header = b'PetPlantr STL v1.0' + b'\x00' * (80 - 18)  # 80-byte header with signature
    triangle_count = (100).to_bytes(4, 'little')  # 100 triangles to meet quality threshold
    
    # Create 100 triangles (each triangle = 50 bytes)
    triangles = b''
    for i in range(100):
        triangle = (
            # Normal vector (3 floats)
            struct.pack('<f', 0.0) +  # nx
            struct.pack('<f', 0.0) +  # ny
            struct.pack('<f', 1.0) +  # nz
            # Vertices (9 floats)
            struct.pack('<f', float(i)) + struct.pack('<f', 0.0) + struct.pack('<f', 0.0) +  # v1
            struct.pack('<f', float(i+1)) + struct.pack('<f', 0.0) + struct.pack('<f', 0.0) +  # v2
            struct.pack('<f', float(i)) + struct.pack('<f', 1.0) + struct.pack('<f', 0.0) +  # v3
            # Attribute byte count
            (0).to_bytes(2, 'little')
        )
        triangles += triangle
    
    return header + triangle_count + triangles

# ================================
# API & PAYMENT FIXTURES
# ================================

@pytest.fixture
def mock_stripe_payment():
    """Mock successful Stripe payment"""
    return {
        "id": "pi_test_1234567890",
        "amount": 4999,  # $49.99
        "currency": "usd",
        "status": "succeeded",
        "metadata": {
            "order_id": "order_test_123",
            "product_type": "custom_planter"
        }
    }

@pytest.fixture
def api_client():
    """Test API client"""
    # This would be your actual Flask/FastAPI test client
    # from your_app import create_app
    # app = create_app(testing=True)
    # return app.test_client()
    
    # Mock for now
    return Mock()

@pytest.fixture
def auth_headers():
    """Valid authentication headers"""
    return {
        "Authorization": "Bearer test_token_123",
        "Content-Type": "application/json"
    }

# ================================
# PRICING & BUSINESS LOGIC FIXTURES
# ================================

@pytest.fixture
def pricing_test_cases():
    """Comprehensive pricing test scenarios"""
    return {
        "basic_small": {
            "size": "small",
            "complexity": "basic",
            "material": "pla",
            "expected_price": 29.99,
            "print_time_hours": 4
        },
        "premium_large": {
            "size": "large", 
            "complexity": "high",
            "material": "premium_resin",
            "expected_price": 134.98,  # Fixed: 89.99 * 1.5 = 134.985 -> rounds to 134.98
            "print_time_hours": 12
        },
        "custom_features": {
            "size": "medium",
            "complexity": "medium",
            "material": "pla",
            "custom_features": ["drainage_holes", "name_engraving"],
            "expected_price": 64.99,  # Fixed: 49.99 + 5.00 + 10.00 = 64.99
            "print_time_hours": 7
        }
    }

# ================================
# ENVIRONMENT & SETUP FIXTURES
# ================================

@pytest.fixture
def temp_workspace():
    """Temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_env_vars():
    """Mock environment variables"""
    env_vars = {
        "STRIPE_SECRET_KEY": "sk_test_mock",
        "OPENAI_API_KEY": "mock_openai_key",
        "DATABASE_URL": "sqlite:///:memory:",
        "JWT_SECRET": "test_jwt_secret"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture(autouse=True)
def reset_singleton_state():
    """Reset any singleton/global state between tests"""
    # Add any global state resets here
    yield
    # Cleanup after test

# ================================
# PERFORMANCE & LOAD FIXTURES
# ================================

@pytest.fixture
def performance_baseline():
    """Performance baselines for critical operations"""
    return {
        "breed_detection_ms": 500,  # Max 500ms for breed detection
        "stl_generation_seconds": 30,  # Max 30s for STL generation
        "api_response_ms": 200,  # Max 200ms for API responses
        "image_processing_ms": 1000  # Max 1s for image processing
    }

# ================================
# PERFORMANCE BASELINE TESTING
# ================================

@pytest.fixture
def performance_thresholds():
    """Performance thresholds that fail build if exceeded"""
    return {
        "stl_math_ms": 100,        # STL calculations must be < 100ms
        "ai_inference_ms": 500,    # AI inference must be < 500ms  
        "api_response_ms": 200,    # API responses must be < 200ms
        "image_processing_ms": 1000, # Image processing must be < 1s
        "database_query_ms": 50,   # DB queries must be < 50ms
        "regression_tolerance": 0.10  # Max 10% performance regression
    }

@pytest.fixture
def benchmark_baseline():
    """Baseline performance metrics for regression detection"""
    return {
        "stl_volume_calculation": {"mean_ms": 45, "std_ms": 5},
        "breed_detection_inference": {"mean_ms": 250, "std_ms": 25},
        "planter_generation": {"mean_ms": 800, "std_ms": 50},
        "api_auth_validation": {"mean_ms": 15, "std_ms": 3},
        "price_calculation": {"mean_ms": 5, "std_ms": 1}
    }

# ================================ 
# MUTATION TESTING HELPERS
# ================================

@pytest.fixture
def mutation_test_targets():
    """Critical code paths that must have strong mutation test scores"""
    return {
        "pricing_logic": {
            "path": "petplantr/pricing.py",
            "min_mutation_score": 0.85  # 85% mutations must be killed
        },
        "stl_validation": {
            "path": "petplantr/stl_validator.py", 
            "min_mutation_score": 0.90  # 90% mutations must be killed
        },
        "ai_confidence": {
            "path": "petplantr/ai/confidence.py",
            "min_mutation_score": 0.80  # 80% mutations must be killed
        },
        "payment_processing": {
            "path": "petplantr/payments.py",
            "min_mutation_score": 0.95  # 95% mutations must be killed (critical!)
        }
    }

# ================================
# SECURITY & SECRETS TESTING
# ================================

@pytest.fixture
def security_test_patterns():
    """Patterns to detect in security testing"""
    return {
        "potential_secrets": [
            r"sk_live_[a-zA-Z0-9]{24}",  # Stripe live keys
            r"sk_test_[a-zA-Z0-9]{24}",  # Stripe test keys
            r"AKIA[0-9A-Z]{16}",         # AWS access keys
            r"-----BEGIN.*PRIVATE.*KEY-----",  # Private keys
            r"postgres://.*:.*@",        # DB connection strings
        ],
        "xss_vectors": [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "';DROP TABLE users;--",
        ],
        "injection_vectors": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'/*",
            "' UNION SELECT * FROM users --",
        ]
    }

@pytest.fixture 
def health_check_endpoints():
    """Health check endpoints that must return 200 in CI"""
    return {
        "basic_health": "/health",
        "detailed_health": "/health/detailed", 
        "database_health": "/health/db",
        "ai_model_health": "/health/ai",
        "storage_health": "/health/storage",
        "payment_health": "/health/payments"
    }

# ================================
# CI/CD TESTING FIXTURES  
# ================================

@pytest.fixture
def deployment_checklist():
    """Checklist items that must pass before deployment"""
    return {
        "test_coverage": {"threshold": 95, "current": None},
        "mutation_score": {"threshold": 80, "current": None}, 
        "performance_regression": {"threshold": 10, "current": None},
        "security_scan": {"max_high_vulns": 0, "max_medium_vulns": 2},
        "dependency_audit": {"max_critical": 0, "max_high": 1},
        "docker_image_size": {"max_mb": 500, "current": None},
        "startup_time": {"max_seconds": 30, "current": None}
    }

@pytest.fixture
def release_metadata():
    """Metadata for semantic release automation"""
    return {
        "version_pattern": r"^v\d+\.\d+\.\d+$",
        "changelog_sections": [
            "🚀 Features",
            "🐛 Bug Fixes", 
            "⚡️ Performance",
            "🔒 Security",
            "📚 Documentation",
            "🧪 Testing"
        ],
        "docker_tags": ["latest", "stable"],
        "environments": ["staging", "production"]
    }

# ================================
# ADVANCED TEST DATA FACTORIES
# ================================

def create_performance_test_data(size: str = "medium") -> Dict[str, Any]:
    """Factory for performance test data of varying sizes"""
    sizes = {
        "small": {"triangles": 100, "image_size": (224, 224), "batch_size": 10},
        "medium": {"triangles": 1000, "image_size": (512, 512), "batch_size": 50}, 
        "large": {"triangles": 10000, "image_size": (1024, 1024), "batch_size": 100},
        "xlarge": {"triangles": 50000, "image_size": (2048, 2048), "batch_size": 200}
    }
    
    config = sizes.get(size, sizes["medium"])
    
    return {
        "stl_data": _generate_stl_with_triangles(config["triangles"]),
        "test_images": _generate_test_images(config["image_size"], config["batch_size"]),
        "expected_processing_time": _estimate_processing_time(config),
        "memory_limit_mb": config["triangles"] * 0.1  # Rough estimate
    }

def _generate_stl_with_triangles(triangle_count: int) -> bytes:
    """Generate STL data with specified triangle count for performance testing"""
    header = b'PetPlantr Perf Test' + b'\x00' * (80 - 19)
    triangle_count_bytes = triangle_count.to_bytes(4, 'little')
    
    triangles = b''
    for i in range(triangle_count):
        triangle = (
            struct.pack('<f', 0.0) + struct.pack('<f', 0.0) + struct.pack('<f', 1.0) +  # Normal
            struct.pack('<f', float(i)) + struct.pack('<f', 0.0) + struct.pack('<f', 0.0) +  # V1
            struct.pack('<f', float(i+1)) + struct.pack('<f', 0.0) + struct.pack('<f', 0.0) +  # V2  
            struct.pack('<f', float(i)) + struct.pack('<f', 1.0) + struct.pack('<f', 0.0) +  # V3
            (0).to_bytes(2, 'little')  # Attribute
        )
        triangles += triangle
    
    return header + triangle_count_bytes + triangles

def _generate_test_images(size: tuple, count: int) -> list:
    """Generate test images for batch processing performance tests"""
    images = []
    for i in range(count):
        img = Image.new('RGB', size, color=(i % 255, (i*2) % 255, (i*3) % 255))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        images.append(img_bytes.getvalue())
    return images

def _estimate_processing_time(config: Dict) -> Dict[str, float]:
    """Estimate expected processing times for performance validation"""
    return {
        "stl_processing_ms": config["triangles"] * 0.01,  # ~0.01ms per triangle
        "image_processing_ms": (config["image_size"][0] * config["image_size"][1]) / 1000,
        "batch_processing_ms": config["batch_size"] * 10  # ~10ms per item in batch
    }

# ================================
# QUALITY GATE VALIDATORS
# ================================

def validate_coverage_threshold(coverage_pct: float, threshold: float = 95.0) -> bool:
    """Validate test coverage meets minimum threshold"""
    return coverage_pct >= threshold

def validate_mutation_score(killed_mutants: int, total_mutants: int, threshold: float = 0.80) -> bool:
    """Validate mutation testing score meets minimum threshold"""
    if total_mutants == 0:
        return True
    score = killed_mutants / total_mutants
    return score >= threshold

def validate_performance_regression(current_time: float, baseline_time: float, tolerance: float = 0.10) -> bool:
    """Validate performance hasn't regressed beyond tolerance"""
    if baseline_time == 0:
        return True
    regression = (current_time - baseline_time) / baseline_time
    return regression <= tolerance

def validate_security_scan_results(scan_results: Dict) -> bool:
    """Validate security scan results meet requirements"""
    return (
        scan_results.get("critical_vulns", 0) == 0 and
        scan_results.get("high_vulns", 0) == 0 and
        scan_results.get("secrets_found", 0) == 0
    )

def _has_ml():
    try:
        import torch  # type: ignore
        import transformers  # type: ignore
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    if _has_ml():
        return
    skip_ml = pytest.mark.skip(reason="ML deps not installed")
    for it in items:
        if "ml" in getattr(it, "keywords", {}):
            it.add_marker(skip_ml)
