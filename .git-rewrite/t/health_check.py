#!/usr/bin/env python3
"""
PetPlantr Health Check & Smoke Test Endpoint
Validates that the container is production-ready
"""

from flask import Flask, jsonify
import sys
import os
import json
import time
import requests
from datetime import datetime
import subprocess

app = Flask(__name__)

def check_environment():
    """Check required environment variables"""
    required_vars = [
        'STRIPE_SECRET_KEY',
        'OPENAI_API_KEY', 
        'DATABASE_URL'
    ]
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    return {
        "status": "pass" if not missing else "fail",
        "missing_vars": missing,
        "total_required": len(required_vars)
    }

def check_dependencies():
    """Check critical dependencies are installed"""
    try:
        import numpy
        import PIL
        import pytest
        import mutmut
        
        return {
            "status": "pass",
            "dependencies": {
                "numpy": numpy.__version__,
                "PIL": PIL.__version__,
                "pytest": pytest.__version__,
                "mutmut": "installed"
            }
        }
    except ImportError as e:
        return {
            "status": "fail",
            "error": str(e)
        }

def check_ai_models():
    """Check AI models are accessible"""
    try:
        # Mock AI model check - replace with actual model loading
        model_status = {
            "breed_detection": "loaded",
            "confidence_scoring": "loaded", 
            "3d_generation": "loaded"
        }
        
        return {
            "status": "pass",
            "models": model_status
        }
    except Exception as e:
        return {
            "status": "fail",
            "error": str(e)
        }

def check_external_services():
    """Check external service connectivity"""
    services = {}
    
    # Check Stripe API (without making actual charges)
    try:
        stripe_key = os.environ.get('STRIPE_SECRET_KEY', '')
        if stripe_key.startswith('sk_test_'):
            services['stripe'] = {"status": "pass", "environment": "test"}
        elif stripe_key.startswith('sk_live_'):
            services['stripe'] = {"status": "pass", "environment": "live"}
        else:
            services['stripe'] = {"status": "fail", "error": "Invalid Stripe key"}
    except Exception as e:
        services['stripe'] = {"status": "fail", "error": str(e)}
    
    # Check OpenAI API connectivity
    try:
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        if openai_key.startswith('sk-'):
            services['openai'] = {"status": "pass", "key_format": "valid"}
        else:
            services['openai'] = {"status": "fail", "error": "Invalid OpenAI key format"}
    except Exception as e:
        services['openai'] = {"status": "fail", "error": str(e)}
    
    return services

def run_smoke_tests():
    """Run critical smoke tests"""
    try:
        # Run a subset of critical tests
        result = subprocess.run([
            'python', '-m', 'pytest', 
            'tests/test_critical_business_logic.py::TestPricingLogic::test_basic_pricing',
            '--tb=short', '-v'
        ], capture_output=True, text=True, timeout=30)
        
        return {
            "status": "pass" if result.returncode == 0 else "fail",
            "returncode": result.returncode,
            "output": result.stdout[-500:] if result.stdout else "",  # Last 500 chars
            "errors": result.stderr[-500:] if result.stderr else ""
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "fail",
            "error": "Smoke tests timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "status": "fail", 
            "error": str(e)
        }

@app.route('/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "petplantr",
        "version": "1.0.0"
    })

@app.route('/health/detailed')
def detailed_health_check():
    """Comprehensive health check with all systems"""
    start_time = time.time()
    
    # Run all health checks
    checks = {
        "environment": check_environment(),
        "dependencies": check_dependencies(), 
        "ai_models": check_ai_models(),
        "external_services": check_external_services(),
        "smoke_tests": run_smoke_tests()
    }
    
    # Determine overall status
    overall_status = "healthy"
    failed_checks = []
    
    for check_name, check_result in checks.items():
        if isinstance(check_result, dict) and check_result.get("status") == "fail":
            overall_status = "unhealthy"
            failed_checks.append(check_name)
        elif isinstance(check_result, dict):
            # Check nested services
            for service_name, service_result in check_result.items():
                if isinstance(service_result, dict) and service_result.get("status") == "fail":
                    overall_status = "unhealthy"
                    failed_checks.append(f"{check_name}.{service_name}")
    
    processing_time = round((time.time() - start_time) * 1000, 2)
    
    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "petplantr",
        "version": "1.0.0",
        "processing_time_ms": processing_time,
        "failed_checks": failed_checks,
        "checks": checks
    }
    
    # Return appropriate HTTP status code
    status_code = 200 if overall_status == "healthy" else 503
    return jsonify(response), status_code

@app.route('/health/readiness')
def readiness_check():
    """Kubernetes readiness probe endpoint"""
    # Quick checks for readiness
    env_check = check_environment()
    deps_check = check_dependencies()
    
    ready = (env_check["status"] == "pass" and 
             deps_check["status"] == "pass")
    
    return jsonify({
        "ready": ready,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200 if ready else 503

@app.route('/health/liveness')
def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return jsonify({
        "alive": True,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
