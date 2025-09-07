"""
PetPlantr Security Monitoring and Threat Detection
"""

import time
import hashlib
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
import re

class SecurityMonitor:
    def __init__(self):
        self.threats = {
            'suspicious_requests': deque(maxlen=1000),
            'failed_authentications': deque(maxlen=500),
            'rate_limit_hits': deque(maxlen=200),
            'sql_injection_attempts': deque(maxlen=100),
            'xss_attempts': deque(maxlen=100)
        }
        self.ip_tracking = defaultdict(lambda: {'requests': 0, 'last_request': None})
        self.blocked_ips = set()

    def log_request(self, ip, user_agent, request_data):
        """Log and analyze incoming request"""
        timestamp = datetime.now()

        # Update IP tracking
        self.ip_tracking[ip]['requests'] += 1
        self.ip_tracking[ip]['last_request'] = timestamp

        # Check for suspicious patterns
        if self._is_suspicious_request(ip, user_agent, request_data):
            self.threats['suspicious_requests'].append({
                'ip': ip,
                'timestamp': timestamp,
                'user_agent': user_agent,
                'data': request_data
            })

        # Check rate limiting
        if self._check_rate_limit(ip):
            self.threats['rate_limit_hits'].append({
                'ip': ip,
                'timestamp': timestamp
            })

        # Check for SQL injection
        if self._detect_sql_injection(request_data):
            self.threats['sql_injection_attempts'].append({
                'ip': ip,
                'timestamp': timestamp,
                'data': request_data
            })

        # Check for XSS
        if self._detect_xss(request_data):
            self.threats['xss_attempts'].append({
                'ip': ip,
                'timestamp': timestamp,
                'data': request_data
            })

    def _is_suspicious_request(self, ip, user_agent, request_data):
        """Check if request appears suspicious"""
        suspicious_patterns = [
            r'(?i)(union|select|insert|update|delete|drop|create|alter)\s',
            r'(?i)(script|javascript|vbscript|onload|onerror)',
            r'(?i)(eval|exec|system|shell_exec)',
            r'\.\./',  # Directory traversal
            r'<script',  # Script tags
        ]

        combined_data = f"{user_agent} {json.dumps(request_data)}"

        for pattern in suspicious_patterns:
            if re.search(pattern, combined_data):
                return True

        return False

    def _check_rate_limit(self, ip):
        """Check if IP has exceeded rate limit"""
        # Simple rate limiting: max 100 requests per minute
        recent_requests = [
            req for req in self.ip_tracking[ip]
            if req['timestamp'] > datetime.now() - timedelta(minutes=1)
        ]

        return len(recent_requests) > 100

    def _detect_sql_injection(self, data):
        """Detect potential SQL injection attempts"""
        sql_patterns = [
            r'(\'|").*?(union|select|insert|update|delete|drop).*?(\'|")',
            r'(\'|").*?(\d+\s*=\s*\d+).*?(\'|")',
            r'(\'|").*?(or|and).*?(\d+\s*=\s*\d+).*?(\'|")',
        ]

        data_str = json.dumps(data) if isinstance(data, dict) else str(data)

        for pattern in sql_patterns:
            if re.search(pattern, data_str, re.IGNORECASE):
                return True

        return False

    def _detect_xss(self, data):
        """Detect potential XSS attempts"""
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
        ]

        data_str = json.dumps(data) if isinstance(data, dict) else str(data)

        for pattern in xss_patterns:
            if re.search(pattern, data_str, re.IGNORECASE):
                return True

        return False

    def block_ip(self, ip):
        """Block an IP address"""
        self.blocked_ips.add(ip)

    def unblock_ip(self, ip):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip)

    def is_blocked(self, ip):
        """Check if IP is blocked"""
        return ip in self.blocked_ips

    def get_security_report(self):
        """Generate security report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'threats': {},
            'blocked_ips': list(self.blocked_ips),
            'active_ips': len(self.ip_tracking)
        }

        for threat_type, threats in self.threats.items():
            report['threats'][threat_type] = len(threats)

        return report

    def get_recent_threats(self, hours=24):
        """Get recent threats"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_threats = {}

        for threat_type, threats in self.threats.items():
            recent = [t for t in threats if t['timestamp'] > cutoff]
            recent_threats[threat_type] = recent

        return recent_threats

# Global security monitor
security_monitor = SecurityMonitor()

def log_security_event(ip, user_agent, request_data):
    """Log security event"""
    security_monitor.log_request(ip, user_agent, request_data)

def is_ip_blocked(ip):
    """Check if IP is blocked"""
    return security_monitor.is_blocked(ip)

def get_security_report():
    """Get security report"""
    return security_monitor.get_security_report()

if __name__ == "__main__":
    # Example usage
    security_monitor.log_request(
        '192.168.1.100',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        {'query': 'SELECT * FROM users'}
    )

    report = security_monitor.get_security_report()
    print(json.dumps(report, indent=2))
