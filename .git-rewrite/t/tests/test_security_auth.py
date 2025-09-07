"""
Security and Authentication Tests
Critical security validations and authentication flows
"""

import pytest
import jwt
import hashlib
import hmac
import time
from unittest.mock import Mock, patch
from typing import Dict, Any

pytestmark = pytest.mark.security

class TestAuthenticationSecurity:
    """Authentication mechanism security tests"""
    
    def test_jwt_token_validation(self):
        """JWT tokens must be properly validated"""
        
        def create_jwt_token(payload, secret, algorithm="HS256"):
            """Mock JWT token creation"""
            return jwt.encode(payload, secret, algorithm=algorithm)
        
        def validate_jwt_token(token, secret):
            """Mock JWT token validation"""
            try:
                decoded = jwt.decode(token, secret, algorithms=["HS256"])
                
                # Check expiration
                if "exp" in decoded and decoded["exp"] < time.time():
                    return False, "Token expired"
                
                # Check required fields
                required_fields = ["user_id", "iat", "exp"]
                for field in required_fields:
                    if field not in decoded:
                        return False, f"Missing required field: {field}"
                
                return True, decoded
            
            except jwt.InvalidTokenError as e:
                return False, f"Invalid token: {str(e)}"
        
        secret = "test_jwt_secret_key"
        
        # Test valid token
        valid_payload = {
            "user_id": "user_123",
            "iat": int(time.time()),
            "exp": int(time.time() + 3600)  # 1 hour
        }
        
        valid_token = create_jwt_token(valid_payload, secret)
        is_valid, result = validate_jwt_token(valid_token, secret)
        
        assert is_valid, f"Valid token failed validation: {result}"
        assert result["user_id"] == "user_123"
        
        # Test expired token
        expired_payload = {
            "user_id": "user_123",
            "iat": int(time.time() - 7200),  # 2 hours ago
            "exp": int(time.time() - 3600)   # 1 hour ago
        }
        
        expired_token = create_jwt_token(expired_payload, secret)
        is_valid, result = validate_jwt_token(expired_token, secret)
        
        assert not is_valid, "Expired token should be rejected"
        assert "expired" in result.lower()
        
        # Test token with wrong secret
        is_valid, result = validate_jwt_token(valid_token, "wrong_secret")
        assert not is_valid, "Token with wrong secret should be rejected"
    
    def test_password_security_requirements(self):
        """Password validation and hashing security"""
        
        def validate_password_strength(password):
            """Validate password meets security requirements"""
            if len(password) < 8:
                return False, "Password must be at least 8 characters"
            
            if not any(c.isupper() for c in password):
                return False, "Password must contain uppercase letter"
            
            if not any(c.islower() for c in password):
                return False, "Password must contain lowercase letter"
            
            if not any(c.isdigit() for c in password):
                return False, "Password must contain digit"
            
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                return False, "Password must contain special character"
            
            return True, "Password meets requirements"
        
        def hash_password(password, salt=None):
            """Mock secure password hashing"""
            if salt is None:
                salt = "random_salt_123"
            
            # Simulate bcrypt-like hashing
            combined = password + salt
            hashed = hashlib.sha256(combined.encode()).hexdigest()
            return f"$2b$12${salt}${hashed}"
        
        # Test strong password
        strong_password = "SecurePass123!"
        is_valid, message = validate_password_strength(strong_password)
        assert is_valid, f"Strong password failed validation: {message}"
        
        # Test weak passwords
        weak_passwords = [
            ("short", "at least 8 characters"),
            ("nouppercase123!", "uppercase letter"),
            ("NOLOWERCASE123!", "lowercase letter"),
            ("NoNumbers!", "digit"),
            ("NoSpecialChars123", "special character")
        ]
        
        for weak_pass, expected_error in weak_passwords:
            is_valid, message = validate_password_strength(weak_pass)
            assert not is_valid, f"Weak password '{weak_pass}' should be rejected"
            assert expected_error.lower() in message.lower()
        
        # Test password hashing
        password = "SecurePass123!"
        hashed = hash_password(password)
        
        assert hashed != password, "Password should be hashed"
        assert "$2b$12$" in hashed, "Hash should include bcrypt-like format"
    
    def test_session_management(self):
        """Session security and lifecycle management"""
        
        class SessionManager:
            def __init__(self):
                self.sessions = {}
                self.max_age = 3600  # 1 hour
            
            def create_session(self, user_id):
                session_id = f"sess_{hash(user_id + str(time.time()))}"
                self.sessions[session_id] = {
                    "user_id": user_id,
                    "created_at": time.time(),
                    "last_activity": time.time()
                }
                return session_id
            
            def validate_session(self, session_id):
                if session_id not in self.sessions:
                    return False, "Session not found"
                
                session = self.sessions[session_id]
                
                # Check expiration
                if time.time() - session["created_at"] > self.max_age:
                    del self.sessions[session_id]
                    return False, "Session expired"
                
                # Update last activity
                session["last_activity"] = time.time()
                return True, session
            
            def invalidate_session(self, session_id):
                if session_id in self.sessions:
                    del self.sessions[session_id]
                    return True
                return False
        
        manager = SessionManager()
        
        # Test session creation
        session_id = manager.create_session("user_123")
        assert session_id.startswith("sess_")
        
        # Test session validation
        is_valid, session_data = manager.validate_session(session_id)
        assert is_valid, "Valid session should pass validation"
        assert session_data["user_id"] == "user_123"
        
        # Test session invalidation
        assert manager.invalidate_session(session_id)
        is_valid, _ = manager.validate_session(session_id)
        assert not is_valid, "Invalidated session should be rejected"


class TestInputValidationSecurity:
    """Input validation and sanitization tests"""
    
    def test_sql_injection_prevention(self):
        """Prevent SQL injection attacks"""
        
        def safe_database_query(user_id, order_status=None):
            """Mock parameterized query function"""
            # Simulate safe parameterized queries
            allowed_statuses = ["pending", "processing", "completed", "cancelled"]
            
            if order_status and order_status not in allowed_statuses:
                raise ValueError(f"Invalid order status: {order_status}")
            
            # Check for SQL injection patterns
            dangerous_patterns = ["'", "--", ";", "DROP", "DELETE", "UPDATE", "INSERT"]
            user_id_str = str(user_id)
            
            for pattern in dangerous_patterns:
                if pattern.lower() in user_id_str.lower():
                    raise ValueError("Potentially dangerous input detected")
            
            # Mock query result
            return {"user_id": user_id, "orders": []}
        
        # Test safe inputs
        result = safe_database_query("user_123", "pending")
        assert result["user_id"] == "user_123"
        
        # Test SQL injection attempts
        malicious_inputs = [
            "user_123'; DROP TABLE users; --",
            "user_123' OR 1=1",
            "user_123; DELETE FROM orders",
            "user_123' UNION SELECT * FROM passwords"
        ]
        
        for malicious_input in malicious_inputs:
            with pytest.raises(ValueError, match="dangerous input"):
                safe_database_query(malicious_input)
    
    def test_xss_prevention(self):
        """Prevent Cross-Site Scripting (XSS) attacks"""
        
        def sanitize_user_input(input_text):
            """Mock XSS sanitization"""
            if not isinstance(input_text, str):
                return ""
            
            # Check for dangerous patterns
            dangerous_patterns = [
                "<script>", "</script>", "javascript:", "onload=", "onerror=",
                "<iframe>", "<object>", "<embed>", "eval(", "alert("
            ]
            
            sanitized = input_text
            for pattern in dangerous_patterns:
                if pattern.lower() in sanitized.lower():
                    raise ValueError("Potentially malicious script detected")
            
            # HTML entity encoding for safe characters
            sanitized = sanitized.replace("&", "&amp;")
            sanitized = sanitized.replace("<", "&lt;")
            sanitized = sanitized.replace(">", "&gt;")
            sanitized = sanitized.replace('"', "&quot;")
            sanitized = sanitized.replace("'", "&#x27;")
            
            return sanitized
        
        # Test safe input
        safe_input = "My dog's name is Buddy & he's great!"
        sanitized = sanitize_user_input(safe_input)
        assert "&amp;" in sanitized
        assert "&#x27;" in sanitized
        
        # Test XSS attempts
        malicious_scripts = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]
        
        for script in malicious_scripts:
            with pytest.raises(ValueError, match="malicious script"):
                sanitize_user_input(script)
    
    def test_file_upload_security(self):
        """File upload security validation"""
        
        def validate_file_upload(filename, file_content, max_size=10*1024*1024):
            """Mock secure file upload validation"""
            # Check file size
            if len(file_content) > max_size:
                return False, "File too large"
            
            # Check filename for path traversal
            if ".." in filename or "/" in filename or "\\" in filename:
                return False, "Invalid filename"
            
            # Check file extension
            allowed_extensions = [".jpg", ".jpeg", ".png", ".gif"]
            if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
                return False, "Invalid file type"
            
            # Check file signature (magic bytes)
            image_signatures = {
                b'\xff\xd8\xff': 'jpeg',
                b'\x89PNG\r\n\x1a\n': 'png',
                b'GIF87a': 'gif',
                b'GIF89a': 'gif'
            }
            
            file_type = None
            for signature, ftype in image_signatures.items():
                if file_content.startswith(signature):
                    file_type = ftype
                    break
            
            if not file_type:
                return False, "Invalid file format"
            
            return True, f"Valid {file_type} file"
        
        # Test valid file
        valid_jpeg = b'\xff\xd8\xff\xe0' + b'fake_jpeg_data'
        is_valid, message = validate_file_upload("photo.jpg", valid_jpeg)
        assert is_valid, f"Valid JPEG should pass: {message}"
        
        # Test path traversal attempt
        is_valid, message = validate_file_upload("../../../etc/passwd", valid_jpeg)
        assert not is_valid, "Path traversal should be blocked"
        
        # Test invalid extension
        is_valid, message = validate_file_upload("malware.exe", b"fake_exe_data")
        assert not is_valid, "Executable files should be blocked"
        
        # Test file too large
        large_file = b"x" * (20 * 1024 * 1024)  # 20MB
        is_valid, message = validate_file_upload("large.jpg", large_file)
        assert not is_valid, "Large files should be rejected"


class TestAPIKeySecurity:
    """API key and webhook security tests"""
    
    def test_api_key_validation(self):
        """API key format and validation"""
        
        def generate_api_key(user_id):
            """Mock API key generation"""
            import secrets
            prefix = "pk_live_" if "prod" in user_id else "pk_test_"
            random_part = secrets.token_urlsafe(32)
            return prefix + random_part
        
        def validate_api_key(api_key):
            """Mock API key validation"""
            if not api_key:
                return False, "Missing API key"
            
            if not (api_key.startswith("pk_live_") or api_key.startswith("pk_test_")):
                return False, "Invalid API key format"
            
            if len(api_key) < 50:
                return False, "API key too short"
            
            # Check for valid characters (base64url)
            import re
            pattern = r'^pk_(live|test)_[A-Za-z0-9_-]+$'
            if not re.match(pattern, api_key):
                return False, "Invalid API key characters"
            
            return True, "Valid API key"
        
        # Test API key generation
        test_key = generate_api_key("test_user")
        live_key = generate_api_key("prod_user")
        
        assert test_key.startswith("pk_test_")
        assert live_key.startswith("pk_live_")
        
        # Test validation
        is_valid, message = validate_api_key(test_key)
        assert is_valid, f"Generated test key should be valid: {message}"
        
        is_valid, message = validate_api_key(live_key)
        assert is_valid, f"Generated live key should be valid: {message}"
        
        # Test invalid keys
        invalid_keys = [
            "",
            "invalid_key",
            "pk_invalid_format",
            "pk_test_",  # Too short
            "pk_test_invalid@characters!"
        ]
        
        for invalid_key in invalid_keys:
            is_valid, message = validate_api_key(invalid_key)
            assert not is_valid, f"Invalid key '{invalid_key}' should be rejected"
    
    def test_webhook_signature_verification(self):
        """Webhook signature security validation"""
        
        def generate_webhook_signature(payload, secret):
            """Generate HMAC signature for webhook"""
            signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            return f"sha256={signature}"
        
        def verify_webhook_signature(payload, signature, secret):
            """Verify webhook HMAC signature"""
            if not signature or not signature.startswith("sha256="):
                return False, "Invalid signature format"
            
            expected_signature = generate_webhook_signature(payload, secret)
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(signature, expected_signature), "Signature verified"
        
        webhook_secret = "webhook_secret_key_123"
        payload = '{"order_id": "order_123", "status": "completed"}'
        
        # Generate valid signature
        valid_signature = generate_webhook_signature(payload, webhook_secret)
        
        # Test signature verification
        is_valid, message = verify_webhook_signature(payload, valid_signature, webhook_secret)
        assert is_valid, f"Valid signature should verify: {message}"
        
        # Test invalid signatures
        invalid_signatures = [
            "",
            "invalid_format",
            "sha256=wrong_signature",
            "md5=wrong_algorithm"
        ]
        
        for invalid_sig in invalid_signatures:
            is_valid, message = verify_webhook_signature(payload, invalid_sig, webhook_secret)
            assert not is_valid, f"Invalid signature '{invalid_sig}' should be rejected"
        
        # Test signature with wrong secret
        wrong_secret_sig = generate_webhook_signature(payload, "wrong_secret")
        is_valid, message = verify_webhook_signature(payload, wrong_secret_sig, webhook_secret)
        assert not is_valid, "Signature with wrong secret should be rejected"


class TestRateLimitingSecurity:
    """Rate limiting and abuse prevention tests"""
    
    def test_api_rate_limiting(self):
        """API rate limiting implementation"""
        
        class RateLimiter:
            def __init__(self, max_requests=100, time_window=3600):
                self.max_requests = max_requests
                self.time_window = time_window
                self.requests = {}
            
            def is_allowed(self, client_id):
                now = time.time()
                
                # Clean old entries
                if client_id in self.requests:
                    self.requests[client_id] = [
                        req_time for req_time in self.requests[client_id]
                        if now - req_time < self.time_window
                    ]
                else:
                    self.requests[client_id] = []
                
                # Check limit
                if len(self.requests[client_id]) >= self.max_requests:
                    return False, "Rate limit exceeded"
                
                # Record request
                self.requests[client_id].append(now)
                return True, "Request allowed"
        
        limiter = RateLimiter(max_requests=5, time_window=60)  # 5 requests per minute
        
        client_id = "client_123"
        
        # Test normal usage
        for i in range(5):
            is_allowed, message = limiter.is_allowed(client_id)
            assert is_allowed, f"Request {i+1} should be allowed"
        
        # Test rate limit exceeded
        is_allowed, message = limiter.is_allowed(client_id)
        assert not is_allowed, "6th request should be rate limited"
        assert "rate limit" in message.lower()
    
    def test_brute_force_protection(self):
        """Brute force attack protection"""
        
        class BruteForceProtection:
            def __init__(self, max_attempts=5, lockout_time=900):  # 15 minutes
                self.max_attempts = max_attempts
                self.lockout_time = lockout_time
                self.failed_attempts = {}
                self.locked_accounts = {}
            
            def record_failed_login(self, email):
                now = time.time()
                
                if email not in self.failed_attempts:
                    self.failed_attempts[email] = []
                
                self.failed_attempts[email].append(now)
                
                # Clean old attempts
                self.failed_attempts[email] = [
                    attempt_time for attempt_time in self.failed_attempts[email]
                    if now - attempt_time < self.lockout_time
                ]
                
                # Check if account should be locked
                if len(self.failed_attempts[email]) >= self.max_attempts:
                    self.locked_accounts[email] = now
                    return True  # Account locked
                
                return False  # Not locked yet
            
            def is_account_locked(self, email):
                if email not in self.locked_accounts:
                    return False, "Account not locked"
                
                lock_time = self.locked_accounts[email]
                if time.time() - lock_time > self.lockout_time:
                    # Lockout expired
                    del self.locked_accounts[email]
                    if email in self.failed_attempts:
                        del self.failed_attempts[email]
                    return False, "Lockout expired"
                
                return True, f"Account locked for {self.lockout_time} seconds"
            
            def record_successful_login(self, email):
                # Clear failed attempts on successful login
                if email in self.failed_attempts:
                    del self.failed_attempts[email]
                if email in self.locked_accounts:
                    del self.locked_accounts[email]
        
        protection = BruteForceProtection(max_attempts=3, lockout_time=60)
        
        email = "test@example.com"
        
        # Test failed login attempts
        assert not protection.record_failed_login(email)  # 1st attempt
        assert not protection.record_failed_login(email)  # 2nd attempt
        assert protection.record_failed_login(email)      # 3rd attempt - locks account
        
        # Test account lockout
        is_locked, message = protection.is_account_locked(email)
        assert is_locked, f"Account should be locked: {message}"
        
        # Test successful login clears lockout
        protection.record_successful_login(email)
        is_locked, message = protection.is_account_locked(email)
        assert not is_locked, f"Successful login should clear lockout: {message}"


class TestAdvancedCryptographicSecurity:
    """Advanced cryptographic security tests"""
    
    def test_encryption_key_rotation(self):
        """Test encryption key rotation security"""
        import hashlib
        import time
        
        class KeyManager:
            def __init__(self):
                self.keys = {}
                self.current_key_id = 1
                self.rotation_interval = 86400  # 24 hours
            
            def generate_key(self):
                # Simulate key generation
                key_data = hashlib.sha256(f"key_{self.current_key_id}_{time.time()}".encode()).hexdigest()
                self.keys[self.current_key_id] = {
                    'key': key_data,
                    'created_at': time.time(),
                    'active': True
                }
                return self.current_key_id
            
            def rotate_keys(self):
                # Mark current key as deprecated
                if self.current_key_id in self.keys:
                    self.keys[self.current_key_id]['active'] = False
                
                # Generate new key
                self.current_key_id += 1
                return self.generate_key()
            
            def encrypt_data(self, data, key_id=None):
                if key_id is None:
                    key_id = self.current_key_id
                
                if key_id not in self.keys:
                    raise ValueError("Invalid key ID")
                
                key = self.keys[key_id]['key']
                # Simulate encryption (simplified)
                encrypted = hashlib.sha256(f"{data}_{key}".encode()).hexdigest()
                return {'encrypted_data': encrypted, 'key_id': key_id}
            
            def decrypt_data(self, encrypted_data, key_id):
                if key_id not in self.keys:
                    raise ValueError("Key not found for decryption")
                
                # Simulate successful decryption check
                return f"decrypted_data_with_key_{key_id}"
        
        km = KeyManager()
        
        # Generate initial key
        key1 = km.generate_key()
        assert key1 == 1
        
        # Encrypt data with first key
        encrypted1 = km.encrypt_data("sensitive_data")
        assert encrypted1['key_id'] == 1
        
        # Rotate keys
        key2 = km.rotate_keys()
        assert key2 == 2
        assert not km.keys[1]['active']  # Old key deprecated
        assert km.keys[2]['active']      # New key active
        
        # Should still be able to decrypt old data
        decrypted = km.decrypt_data(encrypted1['encrypted_data'], encrypted1['key_id'])
        assert "key_1" in decrypted
        
        # New encryption should use new key
        encrypted2 = km.encrypt_data("new_data")
        assert encrypted2['key_id'] == 2
    
    def test_secure_random_generation(self):
        """Test cryptographically secure random generation"""
        import secrets
        import re
        
        def generate_secure_token(length=32):
            return secrets.token_urlsafe(length)
        
        def generate_secure_api_key():
            # Generate API key with specific format
            prefix = "pk_live_" if secrets.choice([True, False]) else "pk_test_"
            random_part = secrets.token_urlsafe(32)
            return prefix + random_part

        def validate_entropy(token, min_entropy=4.0):
            # Simple entropy calculation
            from collections import Counter
            import math
            char_counts = Counter(token)
            length = len(token)

            entropy = -sum((count / length) * math.log2(count / length)
                          for count in char_counts.values())

            return entropy >= min_entropy
        
        # Test token generation
        tokens = [generate_secure_token() for _ in range(10)]
        
        # All tokens should be unique
        assert len(set(tokens)) == 10, "All tokens should be unique"
        
        # All tokens should have sufficient entropy
        for token in tokens:
            assert validate_entropy(token), f"Token has insufficient entropy: {token}"
        
        # Test API key format
        api_keys = [generate_secure_api_key() for _ in range(5)]
        for key in api_keys:
            assert key.startswith(('pk_live_', 'pk_test_')), f"Invalid API key format: {key}"
            assert len(key) > 40, f"API key too short: {key}"
    
    def test_timing_attack_resistance(self):
        """Test resistance to timing attacks"""
        import time
        import hmac
        import hashlib
        
        def constant_time_compare(a, b):
            """Constant-time string comparison to prevent timing attacks"""
            if len(a) != len(b):
                return False
            
            result = 0
            for x, y in zip(a, b):
                result |= ord(x) ^ ord(y)
            
            return result == 0
        
        def authenticate_user(provided_password, stored_hash, stored_salt):
            # Use constant-time comparison
            computed_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), 
                                              stored_salt.encode(), 100000)
            computed_hash_hex = computed_hash.hex()
            
            return constant_time_compare(computed_hash_hex, stored_hash)
        
        # Setup test data
        correct_password = "secure_password_123"
        stored_salt = "random_salt_456"
        stored_hash = hashlib.pbkdf2_hmac('sha256', correct_password.encode(), 
                                        stored_salt.encode(), 100000).hex()
        
        # Test correct password
        assert authenticate_user(correct_password, stored_hash, stored_salt)
        
        # Test incorrect passwords of various lengths
        wrong_passwords = [
            "wrong",
            "wrong_password",
            "secure_password_124",  # Close but wrong
            "completely_different_password_that_is_much_longer"
        ]
        
        for wrong_password in wrong_passwords:
            assert not authenticate_user(wrong_password, stored_hash, stored_salt)
        
        # Timing test (simplified - in practice would need many iterations)
        start_time = time.time()
        authenticate_user("wrong", stored_hash, stored_salt)
        short_time = time.time() - start_time
        
        start_time = time.time()
        authenticate_user("wrong_password_that_is_much_longer", stored_hash, stored_salt)
        long_time = time.time() - start_time
        
        # Times should be relatively similar (allowing for some variance)
        time_ratio = max(short_time, long_time) / min(short_time, long_time)
        assert time_ratio < 2.0, "Timing difference suggests vulnerability to timing attacks"


class TestAdvancedAccessControl:
    """Advanced access control and authorization tests"""
    
    def test_role_based_access_control(self):
        """Test sophisticated role-based access control"""
        class RBACSystem:
            def __init__(self):
                self.roles = {
                    'admin': {
                        'permissions': ['read', 'write', 'delete', 'manage_users', 'system_config'],
                        'resources': ['*']
                    },
                    'manager': {
                        'permissions': ['read', 'write', 'manage_orders'],
                        'resources': ['orders', 'customers', 'reports']
                    },
                    'employee': {
                        'permissions': ['read', 'write'],
                        'resources': ['orders', 'customers']
                    },
                    'customer': {
                        'permissions': ['read'],
                        'resources': ['own_orders', 'public_info']
                    }
                }
                
                self.users = {}
            
            def assign_role(self, user_id, role, resource_context=None):
                if role not in self.roles:
                    return False
                
                self.users[user_id] = {
                    'role': role,
                    'context': resource_context or {}
                }
                return True
            
            def check_permission(self, user_id, permission, resource):
                if user_id not in self.users:
                    return False
                
                user = self.users[user_id]
                role_info = self.roles[user['role']]
                
                # Check permission
                if permission not in role_info['permissions']:
                    return False
                
                # Check resource access
                allowed_resources = role_info['resources']
                if '*' in allowed_resources:
                    return True
                
                if resource in allowed_resources:
                    return True
                
                # Check contextual access (e.g., own_orders)
                if resource.startswith('own_') and user['context'].get('owns_resource'):
                    return True
                
                return False
        
        rbac = RBACSystem()
        
        # Assign roles
        rbac.assign_role('admin_1', 'admin')
        rbac.assign_role('manager_1', 'manager')
        rbac.assign_role('employee_1', 'employee')
        rbac.assign_role('customer_1', 'customer', {'owns_resource': True})
        
        # Test admin access (should have access to everything)
        assert rbac.check_permission('admin_1', 'delete', 'orders')
        assert rbac.check_permission('admin_1', 'system_config', 'database')
        
        # Test manager access
        assert rbac.check_permission('manager_1', 'write', 'orders')
        assert rbac.check_permission('manager_1', 'manage_orders', 'orders')
        assert not rbac.check_permission('manager_1', 'delete', 'users')  # No delete permission
        
        # Test employee access
        assert rbac.check_permission('employee_1', 'read', 'customers')
        assert not rbac.check_permission('employee_1', 'manage_orders', 'orders')  # No management permission
        
        # Test customer access
        assert rbac.check_permission('customer_1', 'read', 'own_orders')
        assert not rbac.check_permission('customer_1', 'write', 'orders')  # No write permission
    
    def test_attribute_based_access_control(self):
        """Test attribute-based access control (ABAC)"""
        class ABACSystem:
            def __init__(self):
                self.policies = []
            
            def add_policy(self, name, condition_func, effect='allow'):
                self.policies.append({
                    'name': name,
                    'condition': condition_func,
                    'effect': effect
                })
            
            def evaluate_access(self, subject_attrs, resource_attrs, action, environment_attrs):
                # Default deny
                decision = 'deny'
                
                for policy in self.policies:
                    try:
                        if policy['condition'](subject_attrs, resource_attrs, action, environment_attrs):
                            decision = policy['effect']
                            if decision == 'deny':  # Explicit deny overrides allow
                                break
                    except Exception:
                        continue  # Skip malformed policies
                
                return decision
        
        abac = ABACSystem()
        
        # Policy 1: Users can access their own data
        def own_data_policy(subject, resource, action, env):
            return (subject.get('user_id') == resource.get('owner_id') and 
                   action in ['read', 'update'])
        
        # Policy 2: Admins can access everything during business hours
        def admin_business_hours_policy(subject, resource, action, env):
            return (subject.get('role') == 'admin' and 
                   9 <= env.get('hour', 0) <= 17)
        
        # Policy 3: Deny access from suspicious locations
        def location_security_policy(subject, resource, action, env):
            suspicious_countries = ['BadCountry1', 'BadCountry2']
            return env.get('country') in suspicious_countries  # This will deny if true
        
        abac.add_policy('own_data', own_data_policy, 'allow')
        abac.add_policy('admin_hours', admin_business_hours_policy, 'allow')
        abac.add_policy('geo_security', location_security_policy, 'deny')
        
        # Test scenarios
        # User accessing own data during business hours from safe location
        decision = abac.evaluate_access(
            {'user_id': 'user123', 'role': 'customer'},
            {'owner_id': 'user123', 'type': 'order'},
            'read',
            {'hour': 14, 'country': 'US'}
        )
        assert decision == 'allow'
        
        # Admin accessing data during business hours
        decision = abac.evaluate_access(
            {'user_id': 'admin1', 'role': 'admin'},
            {'owner_id': 'user456', 'type': 'order'},
            'delete',
            {'hour': 10, 'country': 'US'}
        )
        assert decision == 'allow'
        
        # Access from suspicious location (should be denied)
        decision = abac.evaluate_access(
            {'user_id': 'user123', 'role': 'customer'},
            {'owner_id': 'user123', 'type': 'order'},
            'read',
            {'hour': 14, 'country': 'BadCountry1'}
        )
        assert decision == 'deny'
    
    def test_multi_factor_authentication(self):
        """Test multi-factor authentication implementation"""
        import random
        import time
        
        class MFASystem:
            def __init__(self):
                self.user_secrets = {}
                self.pending_authentications = {}
                self.backup_codes = {}
            
            def setup_mfa(self, user_id):
                # Generate TOTP secret (simplified)
                secret = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567', k=32))
                
                # Generate backup codes
                backup_codes = [''.join(random.choices('0123456789', k=8)) for _ in range(10)]
                
                self.user_secrets[user_id] = secret
                self.backup_codes[user_id] = backup_codes
                
                return {'secret': secret, 'backup_codes': backup_codes}
            
            def generate_totp(self, secret, timestamp=None):
                # Simplified TOTP generation
                if timestamp is None:
                    timestamp = int(time.time())
                
                time_step = timestamp // 30  # 30-second window
                # Simplified: use hash of secret + time_step
                import hashlib
                token = hashlib.md5(f"{secret}{time_step}".encode()).hexdigest()[:6]
                return token.upper()
            
            def verify_mfa(self, user_id, token, is_backup_code=False):
                if user_id not in self.user_secrets:
                    return False
                
                if is_backup_code:
                    # Check backup codes
                    if (user_id in self.backup_codes and 
                        token in self.backup_codes[user_id]):
                        # Remove used backup code
                        self.backup_codes[user_id].remove(token)
                        return True
                    return False
                
                # Check TOTP
                secret = self.user_secrets[user_id]
                current_time = int(time.time())
                
                # Check current and previous time windows (60 seconds total)
                for time_offset in [0, -30]:
                    expected_token = self.generate_totp(secret, current_time + time_offset)
                    if token == expected_token:
                        return True
                
                return False
            
            def require_mfa_step_up(self, user_id, sensitive_action):
                # For sensitive actions, require fresh MFA
                if user_id not in self.pending_authentications:
                    self.pending_authentications[user_id] = {}
                
                self.pending_authentications[user_id][sensitive_action] = {
                    'required': True,
                    'timestamp': time.time()
                }
                return True
            
            def complete_step_up_auth(self, user_id, action, token):
                if (user_id not in self.pending_authentications or 
                    action not in self.pending_authentications[user_id]):
                    return False
                
                # Check if MFA verification is recent (within 5 minutes)
                auth_time = self.pending_authentications[user_id][action]['timestamp']
                if time.time() - auth_time > 300:  # 5 minutes
                    return False
                
                if self.verify_mfa(user_id, token):
                    del self.pending_authentications[user_id][action]
                    return True
                
                return False
        
        mfa = MFASystem()
        
        # Setup MFA for user
        user_id = 'test_user_123'
        mfa_setup = mfa.setup_mfa(user_id)
        
        assert 'secret' in mfa_setup
        assert len(mfa_setup['backup_codes']) == 10
        
        # Test TOTP verification
        secret = mfa_setup['secret']
        current_token = mfa.generate_totp(secret)
        assert mfa.verify_mfa(user_id, current_token)
        
        # Test invalid token
        assert not mfa.verify_mfa(user_id, 'INVALID')
        
        # Test backup code
        backup_code = mfa_setup['backup_codes'][0]
        assert mfa.verify_mfa(user_id, backup_code, is_backup_code=True)
        
        # Backup code should be consumed
        assert not mfa.verify_mfa(user_id, backup_code, is_backup_code=True)
        
        # Test step-up authentication
        assert mfa.require_mfa_step_up(user_id, 'delete_account')
        
        # Complete step-up with valid token
        new_token = mfa.generate_totp(secret)
        assert mfa.complete_step_up_auth(user_id, 'delete_account', new_token)


class TestSecurityEdgeCases:
    """Test security edge cases and attack scenarios"""
    
    def test_input_sanitization_edge_cases(self):
        """Test edge cases in input sanitization"""
        import re
        import html
        
        def sanitize_input(user_input, max_length=1000):
            if not isinstance(user_input, str):
                return ""
            
            # Length check
            if len(user_input) > max_length:
                user_input = user_input[:max_length]
            
            # HTML escape
            sanitized = html.escape(user_input)
            
            # Remove potentially dangerous patterns
            dangerous_patterns = [
                r'<script.*?</script>',
                r'javascript:',
                r'vbscript:',
                r'on\w+\s*=',
                r'<iframe.*?</iframe>'
            ]
            
            for pattern in dangerous_patterns:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            
            return sanitized.strip()
        
        # Test various malicious inputs
        malicious_inputs = [
            '<script>alert("xss")</script>',
            'javascript:alert("xss")',
            '<img src="x" onerror="alert(1)">',
            '<iframe src="javascript:alert(1)"></iframe>',
            'x' * 2000,  # Oversized input
            None,  # Non-string input
            123,   # Number input
        ]
        
        for malicious_input in malicious_inputs:
            result = sanitize_input(malicious_input)
            assert '<script>' not in result.lower()
            assert 'javascript:' not in result.lower()
            assert 'onerror=' not in result.lower()
            assert len(result) <= 1000

    def test_token_security_edge_cases(self):
        """Test token security edge cases"""
        import secrets
        import hashlib
        import time
        
        class SecureTokenManager:
            def __init__(self):
                self.tokens = {}
                self.max_tokens_per_user = 5
                self.token_expiry = 3600  # 1 hour
            
            def generate_token(self, user_id):
                # Clean expired tokens first
                self._cleanup_expired_tokens(user_id)
                
                # Check token limit per user
                user_tokens = [t for t in self.tokens.values() if t['user_id'] == user_id]
                if len(user_tokens) >= self.max_tokens_per_user:
                    # Remove oldest token (find by token_hash, not token value)
                    oldest_token = min(user_tokens, key=lambda x: x['created_at'])
                    # Find the hash key for this token
                    token_hash_to_remove = None
                    for hash_key, token_data in self.tokens.items():
                        if token_data == oldest_token:
                            token_hash_to_remove = hash_key
                            break
                    if token_hash_to_remove:
                        del self.tokens[token_hash_to_remove]
                
                # Generate new token
                token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                
                self.tokens[token_hash] = {
                    'token': token,
                    'user_id': user_id,
                    'created_at': time.time(),
                    'last_used': time.time()
                }
                
                return token
            
            def validate_token(self, token):
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                
                if token_hash not in self.tokens:
                    return False
                
                token_data = self.tokens[token_hash]
                
                # Check expiry
                if time.time() - token_data['created_at'] > self.token_expiry:
                    del self.tokens[token_hash]
                    return False
                
                # Update last used
                token_data['last_used'] = time.time()
                return True
            
            def _cleanup_expired_tokens(self, user_id=None):
                now = time.time()
                expired_tokens = [
                    token_hash for token_hash, data in self.tokens.items()
                    if now - data['created_at'] > self.token_expiry
                    and (user_id is None or data['user_id'] == user_id)
                ]
                
                for token_hash in expired_tokens:
                    del self.tokens[token_hash]
        
        # Test token manager
        manager = SecureTokenManager()
        
        # Test normal token operations
        token1 = manager.generate_token("user1")
        assert manager.validate_token(token1) is True
        assert manager.validate_token("invalid_token") is False
        
        # Test token limit per user
        tokens = []
        for i in range(7):  # Generate more than max_tokens_per_user
            token = manager.generate_token("user2")
            tokens.append(token)
        
        # Only the last 5 should be valid (max_tokens_per_user)
        valid_count = sum(1 for token in tokens if manager.validate_token(token))
        assert valid_count <= manager.max_tokens_per_user

    def test_encryption_edge_cases(self):
        """Test encryption edge cases"""
        import base64
        
        def simple_encrypt(data, key):
            """Simple XOR encryption for testing"""
            if not isinstance(data, bytes):
                data = data.encode('utf-8')
            if not isinstance(key, bytes):
                key = key.encode('utf-8')
            
            # Extend key to match data length
            extended_key = (key * (len(data) // len(key) + 1))[:len(data)]
            
            encrypted = bytes(a ^ b for a, b in zip(data, extended_key))
            return base64.b64encode(encrypted).decode('utf-8')
        
        def simple_decrypt(encrypted_data, key):
            """Simple XOR decryption for testing"""
            try:
                data = base64.b64decode(encrypted_data.encode('utf-8'))
                if not isinstance(key, bytes):
                    key = key.encode('utf-8')
                
                # Extend key to match data length
                extended_key = (key * (len(data) // len(key) + 1))[:len(data)]
                
                decrypted = bytes(a ^ b for a, b in zip(data, extended_key))
                return decrypted.decode('utf-8')
            except Exception:
                return None
        
        # Test normal encryption/decryption
        original_data = "sensitive information"
        key = "encryption_key"
        
        encrypted = simple_encrypt(original_data, key)
        decrypted = simple_decrypt(encrypted, key)
        
        assert decrypted == original_data
        
        # Test edge cases
        assert simple_decrypt("invalid_base64", key) is None
        assert simple_decrypt(encrypted, "wrong_key") != original_data
        
        # Test empty data
        empty_encrypted = simple_encrypt("", key)
        empty_decrypted = simple_decrypt(empty_encrypted, key)
        assert empty_decrypted == ""
    

if __name__ == "__main__":
    # Run security tests
    pytest.main([__file__, "-v", "-m", "security"])
