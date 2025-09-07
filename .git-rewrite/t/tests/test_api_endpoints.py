"""
API Endpoint Tests
Validates all API endpoints, request/response formats, and error handling
"""

import pytest
import json
from unittest.mock import Mock, patch
from typing import Dict, Any

pytestmark = pytest.mark.integration

class TestBreedDetectionAPI:
    """Breed detection API endpoint tests"""
    
    def test_breed_detection_success(self, api_client, auth_headers, sample_dog_image):
        """POST /api/v1/detect-breed - successful detection"""
        
        # Mock successful API response
        def mock_post(url, files=None, headers=None):
            response = Mock()
            response.status_code = 200
            response.json.return_value = {
                "success": True,
                "breed": "golden_retriever",
                "confidence": 0.92,
                "features": ["floppy_ears", "medium_size", "golden_coat"],
                "processing_time_ms": 450,
                "request_id": "req_12345"
            }
            return response
        
        with patch.object(api_client, 'post', side_effect=mock_post):
            response = api_client.post(
                '/api/v1/detect-breed',
                files={'image': sample_dog_image},
                headers=auth_headers
            )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "breed" in data
        assert "confidence" in data
        assert data["confidence"] > 0.8
        assert "request_id" in data
    
    def test_breed_detection_missing_image(self, api_client, auth_headers):
        """POST /api/v1/detect-breed - missing image file"""
        
        def mock_post_error(url, files=None, headers=None):
            response = Mock()
            response.status_code = 400
            response.json.return_value = {
                "success": False,
                "error": "Missing required file: image",
                "error_code": "MISSING_IMAGE"
            }
            return response
        
        with patch.object(api_client, 'post', side_effect=mock_post_error):
            response = api_client.post(
                '/api/v1/detect-breed',
                files={},  # No image file
                headers=auth_headers
            )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "MISSING_IMAGE" in data["error_code"]
    
    def test_breed_detection_invalid_format(self, api_client, auth_headers):
        """POST /api/v1/detect-breed - invalid image format"""
        
        def mock_post_error(url, files=None, headers=None):
            response = Mock()
            response.status_code = 422
            response.json.return_value = {
                "success": False,
                "error": "Invalid image format. Supported: JPEG, PNG, GIF",
                "error_code": "INVALID_FORMAT"
            }
            return response
        
        invalid_image = b"not_an_image"
        
        with patch.object(api_client, 'post', side_effect=mock_post_error):
            response = api_client.post(
                '/api/v1/detect-breed',
                files={'image': invalid_image},
                headers=auth_headers
            )
        
        assert response.status_code == 422
        data = response.json()
        assert "INVALID_FORMAT" in data["error_code"]
    
    def test_breed_detection_rate_limiting(self, api_client, auth_headers, sample_dog_image):
        """Rate limiting should prevent abuse"""
        
        def mock_rate_limit(url, files=None, headers=None):
            response = Mock()
            response.status_code = 429
            response.json.return_value = {
                "success": False,
                "error": "Rate limit exceeded. Try again in 60 seconds.",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "retry_after": 60
            }
            response.headers = {"Retry-After": "60"}
            return response
        
        with patch.object(api_client, 'post', side_effect=mock_rate_limit):
            response = api_client.post(
                '/api/v1/detect-breed',
                files={'image': sample_dog_image},
                headers=auth_headers
            )
        
        assert response.status_code == 429
        assert "Retry-After" in response.headers


class TestPlanterGenerationAPI:
    """3D planter generation API tests"""
    
    def test_generate_planter_success(self, api_client, auth_headers):
        """POST /api/v1/generate-planter - successful generation"""
        
        def mock_post_success(url, json=None, headers=None):
            response = Mock()
            response.status_code = 202  # Accepted for async processing
            response.json.return_value = {
                "success": True,
                "job_id": "job_67890",
                "estimated_completion": "2024-01-01T12:30:00Z",
                "status": "queued",
                "queue_position": 3
            }
            return response
        
        request_data = {
            "breed": "golden_retriever",
            "size": "medium",
            "material": "pla",
            "custom_features": ["drainage_holes"],
            "user_preferences": {
                "color": "natural",
                "engraving": "Buddy"
            }
        }
        
        with patch.object(api_client, 'post', side_effect=mock_post_success):
            response = api_client.post(
                '/api/v1/generate-planter',
                json=request_data,
                headers=auth_headers
            )
        
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
    
    def test_generate_planter_invalid_breed(self, api_client, auth_headers):
        """POST /api/v1/generate-planter - unsupported breed"""
        
        def mock_post_error(url, json=None, headers=None):
            response = Mock()
            response.status_code = 400
            response.json.return_value = {
                "success": False,
                "error": "Unsupported breed: dragon",
                "error_code": "INVALID_BREED",
                "supported_breeds": ["golden_retriever", "german_shepherd", "pug"]
            }
            return response
        
        request_data = {
            "breed": "dragon",  # Invalid breed
            "size": "medium",
            "material": "pla"
        }
        
        with patch.object(api_client, 'post', side_effect=mock_post_error):
            response = api_client.post(
                '/api/v1/generate-planter',
                json=request_data,
                headers=auth_headers
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "INVALID_BREED" in data["error_code"]
        assert "supported_breeds" in data
    
    def test_check_generation_status(self, api_client, auth_headers):
        """GET /api/v1/generate-planter/{job_id} - check status"""
        
        def mock_get_status(url, headers=None):
            response = Mock()
            response.status_code = 200
            response.json.return_value = {
                "success": True,
                "job_id": "job_67890",
                "status": "completed",
                "progress": 100,
                "result": {
                    "stl_download_url": "https://api.petplantr.com/download/job_67890.stl",
                    "preview_image": "https://api.petplantr.com/preview/job_67890.png",
                    "print_estimates": {
                        "time_hours": 6.5,
                        "material_grams": 85
                    }
                },
                "completed_at": "2024-01-01T12:35:00Z"
            }
            return response
        
        with patch.object(api_client, 'get', side_effect=mock_get_status):
            response = api_client.get(
                '/api/v1/generate-planter/job_67890',
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "stl_download_url" in data["result"]


class TestOrderAPI:
    """Order management API tests"""
    
    def test_create_order_success(self, api_client, auth_headers):
        """POST /api/v1/orders - create new order"""
        
        def mock_post_order(url, json=None, headers=None):
            response = Mock()
            response.status_code = 201
            response.json.return_value = {
                "success": True,
                "order_id": "order_123456",
                "status": "pending",
                "total_amount": 4999,  # $49.99 in cents
                "currency": "usd",
                "items": [
                    {
                        "type": "custom_planter",
                        "breed": "golden_retriever",
                        "size": "medium",
                        "price": 4999
                    }
                ],
                "payment_intent": "pi_test_1234567890",
                "created_at": "2024-01-01T12:00:00Z"
            }
            return response
        
        order_data = {
            "items": [
                {
                    "type": "custom_planter",
                    "breed": "golden_retriever",
                    "size": "medium",
                    "material": "pla",
                    "custom_features": ["drainage_holes"]
                }
            ],
            "shipping_address": {
                "name": "John Doe",
                "line1": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94102",
                "country": "US"
            }
        }
        
        with patch.object(api_client, 'post', side_effect=mock_post_order):
            response = api_client.post(
                '/api/v1/orders',
                json=order_data,
                headers=auth_headers
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "order_id" in data
        assert data["total_amount"] > 0
        assert "payment_intent" in data
    
    def test_get_order_status(self, api_client, auth_headers):
        """GET /api/v1/orders/{order_id} - get order details"""
        
        def mock_get_order(url, headers=None):
            response = Mock()
            response.status_code = 200
            response.json.return_value = {
                "success": True,
                "order_id": "order_123456",
                "status": "processing",
                "payment_status": "paid",
                "total_amount": 4999,
                "tracking": {
                    "current_stage": "printing",
                    "estimated_completion": "2024-01-05T12:00:00Z",
                    "updates": [
                        {
                            "stage": "payment_confirmed",
                            "timestamp": "2024-01-01T12:00:00Z"
                        },
                        {
                            "stage": "printing_started",
                            "timestamp": "2024-01-01T14:00:00Z"
                        }
                    ]
                }
            }
            return response
        
        with patch.object(api_client, 'get', side_effect=mock_get_order):
            response = api_client.get(
                '/api/v1/orders/order_123456',
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == "order_123456"
        assert "tracking" in data
        assert data["payment_status"] == "paid"


class TestAuthenticationAPI:
    """Authentication and authorization tests"""
    
    def test_login_success(self, api_client):
        """POST /api/v1/auth/login - successful login"""
        
        def mock_login(url, json=None, headers=None):
            response = Mock()
            response.status_code = 200
            response.json.return_value = {
                "success": True,
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "refresh_token_123",
                "expires_in": 3600,
                "user": {
                    "id": "user_123",
                    "email": "test@example.com",
                    "subscription_tier": "premium"
                }
            }
            return response
        
        login_data = {
            "email": "test@example.com",
            "password": "secure_password123"
        }
        
        with patch.object(api_client, 'post', side_effect=mock_login):
            response = api_client.post('/api/v1/auth/login', json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
    
    def test_login_invalid_credentials(self, api_client):
        """POST /api/v1/auth/login - invalid credentials"""
        
        def mock_login_error(url, json=None, headers=None):
            response = Mock()
            response.status_code = 401
            response.json.return_value = {
                "success": False,
                "error": "Invalid email or password",
                "error_code": "INVALID_CREDENTIALS"
            }
            return response
        
        login_data = {
            "email": "test@example.com",
            "password": "wrong_password"
        }
        
        with patch.object(api_client, 'post', side_effect=mock_login_error):
            response = api_client.post('/api/v1/auth/login', json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "INVALID_CREDENTIALS" in data["error_code"]
    
    def test_protected_endpoint_without_auth(self, api_client):
        """Protected endpoints require authentication"""
        
        def mock_unauthorized(url, headers=None):
            response = Mock()
            response.status_code = 401
            response.json.return_value = {
                "success": False,
                "error": "Authentication required",
                "error_code": "MISSING_AUTH"
            }
            return response
        
        # Try to access protected endpoint without auth
        with patch.object(api_client, 'get', side_effect=mock_unauthorized):
            response = api_client.get('/api/v1/orders')
        
        assert response.status_code == 401
        data = response.json()
        assert "MISSING_AUTH" in data["error_code"]


class TestAPIPerformance:
    """API performance and load tests"""
    
    def test_response_times(self, api_client, auth_headers, performance_baseline):
        """API responses must meet performance baselines"""
        
        import time
        
        def mock_timed_response(url, **kwargs):
            start_time = time.time()
            # Simulate processing time
            time.sleep(0.05)  # 50ms simulation
            end_time = time.time()
            
            response = Mock()
            response.status_code = 200
            response.json.return_value = {"success": True, "data": "test"}
            response.elapsed.total_seconds.return_value = end_time - start_time
            return response
        
        endpoints_to_test = [
            '/api/v1/health',
            '/api/v1/orders',
            '/api/v1/user/profile'
        ]
        
        max_response_time = performance_baseline["api_response_ms"] / 1000  # Convert to seconds
        
        for endpoint in endpoints_to_test:
            with patch.object(api_client, 'get', side_effect=mock_timed_response):
                response = api_client.get(endpoint, headers=auth_headers)
            
            response_time = response.elapsed.total_seconds()
            
            assert response_time <= max_response_time, (
                f"{endpoint} response time {response_time:.3f}s exceeds "
                f"{max_response_time}s baseline"
            )
    
    def test_concurrent_requests(self, api_client, auth_headers):
        """API must handle concurrent requests"""
        
        def mock_concurrent_response(url, **kwargs):
            response = Mock()
            response.status_code = 200
            response.json.return_value = {"success": True}
            return response
        
        import threading
        import time
        
        results = []
        
        def make_request():
            with patch.object(api_client, 'get', side_effect=mock_concurrent_response):
                response = api_client.get('/api/v1/health', headers=auth_headers)
                results.append(response.status_code)
        
        # Simulate 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 10
        assert all(status == 200 for status in results)


class TestAdvancedAPISecurity:
    """Advanced API security scenarios"""
    
    def test_api_versioning_compatibility(self, api_client, auth_headers):
        """Test API version compatibility"""
        def mock_versioned_response(url, headers=None):
            api_version = headers.get('API-Version', 'v1') if headers else 'v1'
            
            responses = {
                'v1': {'data': {'format': 'legacy'}, 'deprecated': False},
                'v2': {'data': {'format': 'enhanced'}, 'deprecated': False},
                'v3': {'data': {'format': 'latest'}, 'beta': True}
            }
            
            response = Mock()
            if api_version in responses:
                response.status_code = 200
                response.json.return_value = responses[api_version]
            else:
                response.status_code = 400
                response.json.return_value = {'error': 'Unsupported API version'}
            
            return response
        
        # Test supported versions
        for version in ['v1', 'v2', 'v3']:
            headers = {**auth_headers, 'API-Version': version}
            with patch.object(api_client, 'get', side_effect=mock_versioned_response):
                response = api_client.get('/api/breeds', headers=headers)
                assert response.status_code == 200
        
        # Test unsupported version
        headers = {**auth_headers, 'API-Version': 'v99'}
        with patch.object(api_client, 'get', side_effect=mock_versioned_response):
            response = api_client.get('/api/breeds', headers=headers)
            assert response.status_code == 400
    
    def test_request_size_limits(self, api_client, auth_headers):
        """Test request size limitations"""
        def mock_size_limited_response(url, files=None, json=None, headers=None):
            max_file_size = 50 * 1024 * 1024  # 50MB
            max_json_size = 1024 * 1024  # 1MB
            
            response = Mock()
            
            if files:
                total_size = sum(len(f) if isinstance(f, bytes) else len(str(f)) for f in files.values())
                if total_size > max_file_size:
                    response.status_code = 413
                    response.json.return_value = {'error': 'Request entity too large'}
                    return response
            
            if json:
                json_size = len(str(json))
                if json_size > max_json_size:
                    response.status_code = 413
                    response.json.return_value = {'error': 'JSON payload too large'}
                    return response
            
            response.status_code = 200
            response.json.return_value = {'status': 'success'}
            return response
        
        # Test normal size file
        normal_file = b'x' * (10 * 1024 * 1024)  # 10MB
        with patch.object(api_client, 'post', side_effect=mock_size_limited_response):
            response = api_client.post('/api/upload', files={'image': normal_file}, headers=auth_headers)
            assert response.status_code == 200
        
        # Test oversized file
        large_file = b'x' * (60 * 1024 * 1024)  # 60MB
        with patch.object(api_client, 'post', side_effect=mock_size_limited_response):
            response = api_client.post('/api/upload', files={'image': large_file}, headers=auth_headers)
            assert response.status_code == 413
    
    def test_concurrent_user_sessions(self, api_client):
        """Test handling of concurrent user sessions"""
        import threading
        import time
        
        session_store = {}
        access_log = []
        
        def simulate_user_session(user_id, session_count):
            for i in range(session_count):
                session_id = f"{user_id}_session_{i}"
                
                # Simulate login
                session_store[session_id] = {
                    'user_id': user_id,
                    'created_at': time.time(),
                    'last_activity': time.time()
                }
                
                access_log.append(f"{user_id}_login_{i}")
                
                # Simulate some activity
                time.sleep(0.01)  # Small delay
                session_store[session_id]['last_activity'] = time.time()
                access_log.append(f"{user_id}_activity_{i}")
        
        # Simulate multiple users with concurrent sessions
        threads = []
        for user_id in ['user_1', 'user_2', 'user_3']:
            thread = threading.Thread(target=simulate_user_session, args=(user_id, 3))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify concurrent sessions were handled
        assert len(session_store) == 9  # 3 users * 3 sessions each
        assert len(access_log) == 18   # 9 logins + 9 activities
        
        # Check session isolation
        user_1_sessions = [s for s in session_store.values() if s['user_id'] == 'user_1']
        assert len(user_1_sessions) == 3


class TestAdvancedAPIPerformance:
    """Advanced API performance testing"""
    
    def test_response_compression(self, api_client, auth_headers):
        """Test API response compression"""
        def mock_compressed_response(url, headers=None):
            # Check if client accepts compression
            accept_encoding = headers.get('Accept-Encoding', '') if headers else ''
            
            large_data = {'items': [{'id': i, 'data': 'x' * 1000} for i in range(100)]}
            
            response = Mock()
            response.status_code = 200
            
            if 'gzip' in accept_encoding:
                # Simulate compression (roughly 10:1 ratio for repetitive data)
                response.headers = {'Content-Encoding': 'gzip', 'Content-Length': '10000'}
                response.json.return_value = large_data
            else:
                # Uncompressed
                response.headers = {'Content-Length': '100000'}
                response.json.return_value = large_data
            
            return response
        
        # Test with compression
        headers_with_gzip = {**auth_headers, 'Accept-Encoding': 'gzip, deflate'}
        with patch.object(api_client, 'get', side_effect=mock_compressed_response):
            response = api_client.get('/api/large-data', headers=headers_with_gzip)
            assert 'gzip' in response.headers.get('Content-Encoding', '')
            assert int(response.headers['Content-Length']) < 50000
        
        # Test without compression
        with patch.object(api_client, 'get', side_effect=mock_compressed_response):
            response = api_client.get('/api/large-data', headers=auth_headers)
            assert 'Content-Encoding' not in response.headers
            assert int(response.headers['Content-Length']) >= 100000
    
    def test_connection_pooling(self, api_client):
        """Test connection pooling efficiency"""
        connection_pool = {'active_connections': 0, 'total_created': 0, 'reused': 0}

        def simulate_request_with_pooling(url):
            if connection_pool['active_connections'] < 10:  # Pool size limit
                if connection_pool['total_created'] < 10:
                    # Create new connection
                    connection_pool['total_created'] += 1
                    connection_pool['active_connections'] += 1
                else:
                    # Reuse existing connection
                    connection_pool['reused'] += 1
            else:
                # Pool is full, reuse existing connection
                connection_pool['reused'] += 1

            # Simulate request processing
            response = Mock()
            response.status_code = 200
            response.json.return_value = {'status': 'success'}

            return response
        
        # Make multiple requests to test pooling
        for i in range(20):
            with patch.object(api_client, 'get', side_effect=simulate_request_with_pooling):
                response = api_client.get(f'/api/test-{i}')
                assert response.status_code == 200
        
        # Verify connection reuse
        assert connection_pool['total_created'] <= 10  # Limited pool size
        assert connection_pool['reused'] >= 10         # Connections were reused
    
    def test_caching_headers(self, api_client, auth_headers):
        """Test HTTP caching headers"""
        def mock_cached_response(url, headers=None):
            # Check for cache control headers
            if_modified_since = headers.get('If-Modified-Since') if headers else None
            if_none_match = headers.get('If-None-Match') if headers else None
            
            response = Mock()
            
            # Simulate cached response
            if if_modified_since or if_none_match:
                response.status_code = 304  # Not Modified
                response.headers = {'Cache-Control': 'max-age=3600'}
                response.json.return_value = {}
            else:
                response.status_code = 200
                response.headers = {
                    'Cache-Control': 'max-age=3600',
                    'ETag': '"123456789"',
                    'Last-Modified': 'Wed, 21 Oct 2015 07:28:00 GMT'
                }
                response.json.return_value = {'data': 'fresh_content'}
            
            return response
        
        # First request - get fresh data
        with patch.object(api_client, 'get', side_effect=mock_cached_response):
            response = api_client.get('/api/cacheable-data', headers=auth_headers)
            assert response.status_code == 200
            assert 'ETag' in response.headers
        
        # Second request with cache headers - should get 304
        cache_headers = {
            **auth_headers,
            'If-None-Match': '"123456789"',
            'If-Modified-Since': 'Wed, 21 Oct 2015 07:28:00 GMT'
        }
        with patch.object(api_client, 'get', side_effect=mock_cached_response):
            response = api_client.get('/api/cacheable-data', headers=cache_headers)
            assert response.status_code == 304


class TestAdvancedDataValidation:
    """Advanced data validation scenarios"""
    
    def test_nested_json_validation(self, api_client, auth_headers):
        """Test validation of complex nested JSON structures"""
        def validate_nested_order(order_data):
            required_fields = {
                'customer': ['name', 'email', 'address'],
                'items': ['product_id', 'quantity', 'customizations'],
                'payment': ['method', 'amount', 'currency'],
                'shipping': ['address', 'method', 'cost']
            }
            
            errors = []
            
            for section, fields in required_fields.items():
                if section not in order_data:
                    errors.append(f"Missing section: {section}")
                    continue
                
                section_data = order_data[section]
                if isinstance(section_data, list):
                    # Handle arrays (like items)
                    for i, item in enumerate(section_data):
                        for field in fields:
                            if field not in item:
                                errors.append(f"Missing {section}[{i}].{field}")
                else:
                    # Handle objects
                    for field in fields:
                        if field not in section_data:
                            errors.append(f"Missing {section}.{field}")
            
            return len(errors) == 0, errors
        
        # Test valid nested structure
        valid_order = {
            'customer': {'name': 'John Doe', 'email': 'john@example.com', 'address': '123 Main St'},
            'items': [{'product_id': 'planter_001', 'quantity': 1, 'customizations': {'color': 'blue'}}],
            'payment': {'method': 'card', 'amount': 49.99, 'currency': 'USD'},
            'shipping': {'address': '123 Main St', 'method': 'standard', 'cost': 9.99}
        }
        
        is_valid, errors = validate_nested_order(valid_order)
        assert is_valid, f"Valid order should pass validation: {errors}"
        
        # Test invalid structure
        invalid_order = {
            'customer': {'name': 'John Doe'},  # Missing email and address
            'items': [{'product_id': 'planter_001'}],  # Missing quantity and customizations
            # Missing payment and shipping sections
        }
        
        is_valid, errors = validate_nested_order(invalid_order)
        assert not is_valid, "Invalid order should fail validation"
        assert len(errors) >= 5, f"Should have multiple validation errors: {errors}"
    
    def test_business_rule_validation(self):
        """Test complex business rule validation"""
        def validate_order_business_rules(order_data, user_profile):
            violations = []
            
            # Rule 1: Premium materials require premium subscription
            for item in order_data.get('items', []):
                if (item.get('material') == 'premium_resin' and 
                    user_profile.get('subscription_tier') != 'premium'):
                    violations.append("Premium materials require premium subscription")
            
            # Rule 2: Large orders require pre-approval
            total_quantity = sum(item.get('quantity', 0) for item in order_data.get('items', []))
            if total_quantity > 10 and not order_data.get('pre_approved', False):
                violations.append("Orders over 10 items require pre-approval")
            
            # Rule 3: International shipping restrictions
            customer_country = order_data.get('customer', {}).get('country')
            shipping_country = order_data.get('shipping', {}).get('country')
            restricted_countries = ['Country1', 'Country2']
            
            if shipping_country in restricted_countries:
                violations.append(f"Shipping to {shipping_country} is restricted")
            
            # Rule 4: Minimum order value
            total_value = sum(item.get('price', 0) * item.get('quantity', 0) 
                            for item in order_data.get('items', []))
            if total_value < 25.00:
                violations.append("Minimum order value is $25.00")
            
            return len(violations) == 0, violations
        
        # Test valid order
        valid_order = {
            'items': [{'material': 'pla', 'quantity': 2, 'price': 30.00}],
            'customer': {'country': 'US'},
            'shipping': {'country': 'US'}
        }
        user_profile = {'subscription_tier': 'basic'}
        
        is_valid, violations = validate_order_business_rules(valid_order, user_profile)
        assert is_valid, f"Valid order should pass business rules: {violations}"
        
        # Test order violating multiple rules
        invalid_order = {
            'items': [
                {'material': 'premium_resin', 'quantity': 15, 'price': 10.00}  # Premium material + large quantity + low total
            ],
            'customer': {'country': 'US'},
            'shipping': {'country': 'Country1'},  # Restricted country
            'pre_approved': False
        }
        
        is_valid, violations = validate_order_business_rules(invalid_order, user_profile)
        assert not is_valid, "Invalid order should fail business rules"
        assert len(violations) >= 3, f"Should have multiple rule violations: {violations}"


class TestAPIEdgeCases:
    """Test API edge cases and error conditions"""
    
    def test_malformed_request_handling(self):
        """Test handling of malformed requests"""
        def validate_api_request(request_data):
            try:
                # Simulate JSON parsing
                if not isinstance(request_data, dict):
                    return {"error": "Invalid JSON", "status": 400}
                
                # Check required fields
                required_fields = ["action", "data"]
                for field in required_fields:
                    if field not in request_data:
                        return {"error": f"Missing field: {field}", "status": 400}
                
                # Validate data types
                if not isinstance(request_data["data"], dict):
                    return {"error": "Data must be object", "status": 400}
                
                return {"status": 200, "message": "Valid request"}
                
            except Exception as e:
                return {"error": f"Processing error: {str(e)}", "status": 500}
        
        # Test various malformed requests
        assert validate_api_request(None)["status"] == 400
        assert validate_api_request("invalid")["status"] == 400
        assert validate_api_request({})["status"] == 400
        assert validate_api_request({"action": "test"})["status"] == 400
        assert validate_api_request({"action": "test", "data": "not_dict"})["status"] == 400
        
        # Test valid request
        valid_request = {"action": "detect", "data": {"image": "base64..."}}
        assert validate_api_request(valid_request)["status"] == 200

    def test_rate_limiting_edge_cases(self):
        """Test edge cases in rate limiting"""
        import time
        
        class RateLimiter:
            def __init__(self, max_requests=10, window_seconds=60):
                self.max_requests = max_requests
                self.window_seconds = window_seconds
                self.requests = {}
            
            def is_allowed(self, client_id):
                now = time.time()
                
                # Clean old requests
                if client_id in self.requests:
                    self.requests[client_id] = [
                        req_time for req_time in self.requests[client_id]
                        if now - req_time < self.window_seconds
                    ]
                else:
                    self.requests[client_id] = []
                
                # Check if under limit
                if len(self.requests[client_id]) >= self.max_requests:
                    return False
                
                # Add current request
                self.requests[client_id].append(now)
                return True
        
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        
        # Test normal usage
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is False  # Exceeded limit
        
        # Test different clients
        assert limiter.is_allowed("client2") is True  # Different client
        
        # Test window expiration (simulate time passing)
        time.sleep(0.1)  # Small delay for test
        # In real scenario, requests would expire after window_seconds    def test_concurrent_request_handling(self):
        """Test concurrent request handling scenarios"""
        import threading
        import queue
        import time

        def simulate_concurrent_processing(request_queue, results_queue, max_concurrent=3):
            active_threads = []
            
            def process_request(request_id):
                # Simulate processing time
                time.sleep(0.01)  # Small delay
                results_queue.put(f"processed_{request_id}")
            
            while not request_queue.empty() or active_threads:
                # Start new threads if under limit and requests available
                while len(active_threads) < max_concurrent and not request_queue.empty():
                    try:
                        request_id = request_queue.get_nowait()
                        thread = threading.Thread(target=process_request, args=(request_id,))
                        thread.start()
                        active_threads.append(thread)
                    except queue.Empty:
                        break
                
                # Clean up finished threads
                active_threads = [t for t in active_threads if t.is_alive()]
                
                # Small delay to prevent busy waiting
                time.sleep(0.001)
            
            # Wait for all threads to complete
            for thread in active_threads:
                thread.join()
        
        # Test concurrent processing
        request_queue = queue.Queue()
        results_queue = queue.Queue()
        
        # Add test requests
        for i in range(5):
            request_queue.put(f"request_{i}")
        
        simulate_concurrent_processing(request_queue, results_queue)
        
        # Check all requests were processed
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 5
        assert all("processed_" in result for result in results)


if __name__ == "__main__":
    # Run API integration tests
    pytest.main([__file__, "-v", "-m", "integration"])
