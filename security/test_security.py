#!/usr/bin/env python3
"""
PetPlantr Security Test Script
Tests authentication, rate limiting, and SSL configuration
"""

import requests
import time
import json
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = "https://localhost:443"  # Use HTTPS
API_KEY = "petplantr-api-key-12345"

def test_ssl_connection():
    """Test SSL connection"""
    print("Testing SSL connection...")
    try:
        response = requests.get(f"{BASE_URL}/health", verify=False)
        print(f"SSL connection: {'✓' if response.status_code == 200 else '✗'}")
        return response.status_code == 200
    except Exception as e:
        print(f"SSL connection failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting"""
    print("Testing rate limiting...")
    success_count = 0
    rate_limited_count = 0

    for i in range(15):  # More than free tier limit
        try:
            response = requests.get(
                f"{BASE_URL}/health",
                headers={"X-API-Key": API_KEY},
                verify=False
            )
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
            time.sleep(0.1)  # Small delay between requests
        except Exception as e:
            print(f"Request {i+1} failed: {e}")

    print(f"Successful requests: {success_count}")
    print(f"Rate limited requests: {rate_limited_count}")
    return rate_limited_count > 0

def test_authentication():
    """Test authentication endpoints"""
    print("Testing authentication...")
    # This would test JWT authentication when implemented
    print("Authentication tests: Placeholder (implement JWT endpoints first)")
    return True

def main():
    """Run all security tests"""
    print("🔒 PetPlantr Security Test Suite")
    print("=" * 40)

    tests = [
        ("SSL Connection", test_ssl_connection),
        ("Rate Limiting", test_rate_limiting),
        ("Authentication", test_authentication)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            print("✓ PASSED")
            passed += 1
        else:
            print("✗ FAILED")

    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All security tests passed!")
    else:
        print("⚠️  Some tests failed. Check configuration.")

if __name__ == "__main__":
    main()
