#!/usr/bin/env python3
"""
Advanced Performance & Load Testing Suite
Comprehensive testing of API performance, scalability, and reliability
"""

import requests
import json
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
import sys
import random
import hashlib

# Configuration
BASE_URL = "http://localhost:3000"
API_ENDPOINT = f"{BASE_URL}/api/generate-enhanced-3d-simple"

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class PerformanceMetrics:
    def __init__(self):
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.rate_limited_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.quality_scores = []
        self.throughput_data = deque(maxlen=100)
        self.error_details = defaultdict(int)
        self.start_time = 0.0
        self.end_time = 0.0
        self.lock = threading.Lock()

    def add_response(self, duration, success, cached=False, qa_score=None, error_code=None):
        with self.lock:
            self.response_times.append(duration)
            if success:
                self.success_count += 1
                if cached:
                    self.cache_hits += 1
                else:
                    self.cache_misses += 1
                if qa_score is not None:
                    self.quality_scores.append(qa_score)
            else:
                self.error_count += 1
                if error_code == 429:
                    self.rate_limited_count += 1
                if error_code:
                    self.error_details[error_code] += 1

    def get_summary(self):
        total_requests = self.success_count + self.error_count
        if not self.response_times:
            return {"error": "No response data collected"}
        
        duration = (self.end_time - self.start_time) if self.start_time > 0 and self.end_time > 0 else 0
        
        return {
            "total_requests": total_requests,
            "successful_requests": self.success_count,
            "error_rate": (self.error_count / total_requests * 100) if total_requests > 0 else 0,
            "rate_limited": self.rate_limited_count,
            "cache_hit_rate": (self.cache_hits / (self.cache_hits + self.cache_misses) * 100) if (self.cache_hits + self.cache_misses) > 0 else 0,
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "p95_response_time": self.percentile(self.response_times, 95),
            "p99_response_time": self.percentile(self.response_times, 99),
            "throughput_rps": total_requests / duration if duration > 0 else 0,
            "avg_quality_score": statistics.mean(self.quality_scores) if self.quality_scores else 0,
            "error_breakdown": dict(self.error_details),
            "test_duration": duration
        }

    @staticmethod
    def percentile(data, percentile):
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")

def print_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
    print(f"{message}")
    print(f"{'='*60}{Colors.ENDC}")

class LoadTestRunner:
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.test_images = [
            "https://picsum.photos/400/300.jpg",
            "https://picsum.photos/350/250.jpg", 
            "https://picsum.photos/500/400.jpg",
            "https://example.com/test-image.jpg",
            "https://httpbin.org/image/jpeg",
        ]
        self.qualities = ["draft", "standard", "high"]

    def make_request(self, payload, timeout=30):
        """Make a single API request and record metrics"""
        start_time = time.time()
        try:
            response = requests.post(API_ENDPOINT, json=payload, timeout=timeout)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                cached = data.get('fromCache', False)
                qa_score = data.get('qualityAssurance', {}).get('score')
                self.metrics.add_response(duration, True, cached, qa_score)
                return {"success": True, "cached": cached, "qa_score": qa_score}
            else:
                self.metrics.add_response(duration, False, error_code=response.status_code)
                return {"success": False, "status_code": response.status_code}
                
        except Exception as e:
            duration = time.time() - start_time
            self.metrics.add_response(duration, False, error_code=0)
            return {"success": False, "error": str(e)}

    def test_baseline_performance(self):
        """Test baseline single-request performance"""
        print_header("BASELINE PERFORMANCE TEST")
        
        payload = {
            "imageUrl": self.test_images[0],
            "quality": "draft",
            "breed": "Baseline Test"
        }
        
        print_info("Testing baseline performance with single request...")
        result = self.make_request(payload)
        
        if result.get('success'):
            print_success(f"Baseline test successful - QA Score: {result.get('qa_score', 'N/A')}%")
        else:
            print_warning(f"Baseline test failed: {result}")
        
        return result.get('success', False)

    def test_cache_performance(self):
        """Test cache effectiveness and performance"""
        print_header("CACHE PERFORMANCE TEST")
        
        payload = {
            "imageUrl": self.test_images[1],
            "quality": "standard",
            "breed": "Cache Performance Test"
        }
        
        print_info("Testing cache miss (first request)...")
        result1 = self.make_request(payload)
        
        if not result1.get('success'):
            print_warning("First cache request failed")
            return False
        
        time.sleep(1)  # Brief pause
        
        print_info("Testing cache hit (duplicate request)...")
        result2 = self.make_request(payload)
        
        if result2.get('success') and result2.get('cached'):
            print_success("Cache is working effectively")
            return True
        else:
            print_warning("Cache performance suboptimal")
            return False

    def test_concurrent_load(self, num_workers=5, requests_per_worker=3):
        """Test concurrent request handling"""
        print_header(f"CONCURRENT LOAD TEST ({num_workers} workers, {requests_per_worker} requests each)")
        
        self.metrics.start_time = time.time()
        
        def worker_task(worker_id):
            results = []
            for i in range(requests_per_worker):
                payload = {
                    "imageUrl": f"{self.test_images[worker_id % len(self.test_images)]}?worker={worker_id}&req={i}",
                    "quality": random.choice(["draft", "standard"]),
                    "breed": f"Worker {worker_id} Request {i}"
                }
                result = self.make_request(payload, timeout=45)
                results.append(result)
                time.sleep(random.uniform(0.5, 1.5))  # Randomized delay
            return results
        
        print_info(f"Starting {num_workers} concurrent workers...")
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_workers)]
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                print_info(f"Worker completed ({completed}/{num_workers})")
                try:
                    future.result()
                except Exception as e:
                    print_error(f"Worker failed: {e}")
        
        self.metrics.end_time = time.time()
        return True

    def test_quality_level_performance(self):
        """Test performance across different quality levels"""
        print_header("QUALITY LEVEL PERFORMANCE TEST")
        
        quality_results = {}
        
        for quality in ["draft", "standard"]:  # Limit to avoid rate limits
            print_info(f"Testing {quality} quality level...")
            
            payload = {
                "imageUrl": f"{self.test_images[2]}?quality={quality}",
                "quality": quality,
                "breed": f"Quality Test {quality.title()}"
            }
            
            result = self.make_request(payload)
            quality_results[quality] = result
            
            if result.get('success'):
                print_success(f"{quality} quality completed successfully")
            else:
                print_warning(f"{quality} quality failed: {result}")
            
            time.sleep(2)  # Pause between quality tests
        
        return quality_results

    def test_error_handling_performance(self):
        """Test how quickly the API handles various error conditions"""
        print_header("ERROR HANDLING PERFORMANCE TEST")
        
        error_tests = [
            {
                "name": "Invalid Image URL",
                "payload": {"imageUrl": "not-a-url", "quality": "draft", "breed": "Error Test"}
            },
            {
                "name": "Invalid Quality",
                "payload": {"imageUrl": self.test_images[0], "quality": "invalid", "breed": "Error Test"}
            },
            {
                "name": "Missing Fields",
                "payload": {"imageUrl": self.test_images[0]}
            }
        ]
        
        error_results = {}
        
        for test in error_tests:
            print_info(f"Testing: {test['name']}")
            start_time = time.time()
            
            try:
                response = requests.post(API_ENDPOINT, json=test['payload'], timeout=10)
                duration = time.time() - start_time
                
                # For error tests, we expect 4xx status codes and fast responses
                if 400 <= response.status_code < 500 and duration < 2.0:
                    print_success(f"{test['name']}: Fast error response ({response.status_code}, {duration:.2f}s)")
                    error_results[test['name']] = {"success": True, "duration": duration}
                else:
                    print_warning(f"{test['name']}: Slow or unexpected response ({response.status_code}, {duration:.2f}s)")
                    error_results[test['name']] = {"success": False, "duration": duration}
                    
            except Exception as e:
                duration = time.time() - start_time
                print_error(f"{test['name']}: Exception ({duration:.2f}s): {e}")
                error_results[test['name']] = {"success": False, "error": str(e)}
            
            time.sleep(1)
        
        return error_results

    def test_security_endpoints(self):
        """Test security-related endpoints and features"""
        print_header("SECURITY & MONITORING TEST")
        
        security_results = {}
        
        # Test health endpoint
        try:
            response = requests.get(f"{API_ENDPOINT}?health=true", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print_success(f"Health endpoint: {health_data.get('status', 'unknown')}")
                security_results['health'] = {"success": True, "status": health_data.get('status')}
            else:
                print_warning(f"Health endpoint returned {response.status_code}")
                security_results['health'] = {"success": False, "status_code": response.status_code}
        except Exception as e:
            print_error(f"Health endpoint error: {e}")
            security_results['health'] = {"success": False, "error": str(e)}
        
        time.sleep(1)
        
        # Test analytics endpoint
        try:
            response = requests.get(f"{API_ENDPOINT}?analytics=true", timeout=10)
            if response.status_code == 200:
                analytics = response.json()
                total_requests = analytics.get('rateLimitStats', {}).get('totalRequests', 0)
                print_success(f"Analytics endpoint: {total_requests} total requests tracked")
                security_results['analytics'] = {"success": True, "total_requests": total_requests}
            else:
                print_warning(f"Analytics endpoint returned {response.status_code}")
                security_results['analytics'] = {"success": False, "status_code": response.status_code}
        except Exception as e:
            print_error(f"Analytics endpoint error: {e}")
            security_results['analytics'] = {"success": False, "error": str(e)}
        
        return security_results

    def generate_performance_report(self):
        """Generate a comprehensive performance report"""
        print_header("PERFORMANCE ANALYSIS REPORT")
        
        summary = self.metrics.get_summary()
        
        if "error" in summary:
            print_error("No performance data to analyze")
            return
        
        # Overall Performance
        print(f"{Colors.BOLD}Overall Performance:{Colors.ENDC}")
        print(f"  Total Requests: {summary['total_requests']}")
        success_rate = 100 - float(summary['error_rate']) if summary['error_rate'] is not None else 100
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Error Rate: {summary['error_rate']:.1f}%")
        print(f"  Rate Limited: {summary['rate_limited']} requests")
        print(f"  Test Duration: {summary['test_duration']:.1f}s")
        print(f"  Throughput: {summary['throughput_rps']:.2f} requests/second")
        
        # Response Time Analysis
        print(f"\n{Colors.BOLD}Response Time Analysis:{Colors.ENDC}")
        print(f"  Average: {summary['avg_response_time']:.2f}s")
        print(f"  Median: {summary['median_response_time']:.2f}s")
        print(f"  Min: {summary['min_response_time']:.2f}s")
        print(f"  Max: {summary['max_response_time']:.2f}s")
        print(f"  95th Percentile: {summary['p95_response_time']:.2f}s")
        print(f"  99th Percentile: {summary['p99_response_time']:.2f}s")
        
        # Cache Performance
        print(f"\n{Colors.BOLD}Cache Performance:{Colors.ENDC}")
        print(f"  Cache Hit Rate: {summary['cache_hit_rate']:.1f}%")
        print(f"  Cache Hits: {self.metrics.cache_hits}")
        print(f"  Cache Misses: {self.metrics.cache_misses}")
        
        # Quality Analysis
        avg_quality = summary.get('avg_quality_score', 0)
        if isinstance(avg_quality, (int, float)) and avg_quality > 0:
            print(f"\n{Colors.BOLD}Quality Analysis:{Colors.ENDC}")
            print(f"  Average QA Score: {avg_quality:.1f}%")
        
        # Error Breakdown
        error_breakdown = summary.get('error_breakdown', {})
        if error_breakdown and isinstance(error_breakdown, dict):
            print(f"\n{Colors.BOLD}Error Breakdown:{Colors.ENDC}")
            for error_code, count in error_breakdown.items():
                print(f"  HTTP {error_code}: {count} occurrences")
        
        # Performance Assessment
        self.assess_performance(summary)
        
        return summary

    def assess_performance(self, summary):
        """Provide performance assessment and recommendations"""
        print(f"\n{Colors.BOLD}Performance Assessment:{Colors.ENDC}")
        
        issues = []
        recommendations = []
        
        # Response time assessment
        if summary['avg_response_time'] > 10:
            issues.append("High average response time")
            recommendations.append("Consider optimizing AI model processing")
        elif summary['avg_response_time'] < 1:
            print_success("Excellent response times")
        
        # Success rate assessment
        if summary['error_rate'] > 20:
            issues.append("High error rate")
            recommendations.append("Investigate error causes and improve error handling")
        elif summary['error_rate'] < 5:
            print_success("Low error rate - good reliability")
        
        # Cache effectiveness
        if summary['cache_hit_rate'] > 50:
            print_success("Good cache performance")
        elif summary['cache_hit_rate'] < 20:
            issues.append("Low cache hit rate")
            recommendations.append("Review cache strategy and TTL settings")
        
        # Rate limiting
        if summary['rate_limited'] > 0:
            print_info("Rate limiting is active - protecting system resources")
        
        # Display issues and recommendations
        if issues:
            print(f"\n{Colors.YELLOW}Issues Identified:{Colors.ENDC}")
            for issue in issues:
                print(f"  • {issue}")
        
        if recommendations:
            print(f"\n{Colors.BLUE}Recommendations:{Colors.ENDC}")
            for rec in recommendations:
                print(f"  • {rec}")
        
        if not issues:
            print_success("No significant performance issues detected")

def main():
    print_header("ADVANCED PERFORMANCE & LOAD TESTING SUITE")
    print_info("Starting comprehensive API performance testing...")
    
    runner = LoadTestRunner()
    
    # Run test suite
    test_results = {}
    
    # 1. Baseline Performance
    test_results['baseline'] = runner.test_baseline_performance()
    time.sleep(2)
    
    # 2. Cache Performance
    test_results['cache'] = runner.test_cache_performance()
    time.sleep(2)
    
    # 3. Quality Level Performance
    test_results['quality_levels'] = runner.test_quality_level_performance()
    time.sleep(2)
    
    # 4. Error Handling Performance
    test_results['error_handling'] = runner.test_error_handling_performance()
    time.sleep(2)
    
    # 5. Security & Monitoring
    test_results['security'] = runner.test_security_endpoints()
    time.sleep(2)
    
    # 6. Concurrent Load Test
    test_results['concurrent_load'] = runner.test_concurrent_load(num_workers=4, requests_per_worker=2)
    
    # Generate comprehensive report
    performance_summary = runner.generate_performance_report()
    
    # Final assessment
    print_header("FINAL ASSESSMENT")
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    if passed_tests == total_tests:
        print_success(f"All tests passed ({passed_tests}/{total_tests})")
        print_success("API performance is excellent!")
    elif passed_tests >= total_tests * 0.8:
        print_warning(f"Most tests passed ({passed_tests}/{total_tests})")
        print_info("API performance is good with minor issues")
    else:
        print_error(f"Several tests failed ({passed_tests}/{total_tests})")
        print_info("API performance needs improvement")
    
    return test_results, performance_summary

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\nTesting interrupted by user")
    except Exception as e:
        print_error(f"Testing failed with error: {e}")
        sys.exit(1)
