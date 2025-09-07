#!/usr/bin/env python3
"""
System Resource Monitor for Performance Testing
Monitors CPU, memory, and network usage during API testing
"""

import psutil
import time
import threading
import json
from collections import deque
import requests

class SystemMonitor:
    def __init__(self, api_url="http://localhost:3000"):
        self.api_url = api_url
        self.monitoring = False
        self.data = {
            'cpu_usage': deque(maxlen=1000),
            'memory_usage': deque(maxlen=1000),
            'network_stats': deque(maxlen=1000),
            'disk_io': deque(maxlen=1000),
            'timestamps': deque(maxlen=1000)
        }
        self.monitor_thread = None
        self.lock = threading.Lock()

    def start_monitoring(self, interval=1.0):
        """Start system monitoring in background thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("🖥️  System monitoring started")

    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("🖥️  System monitoring stopped")

    def _monitor_loop(self, interval):
        """Main monitoring loop"""
        last_network = psutil.net_io_counters()
        last_disk = psutil.disk_io_counters()
        
        while self.monitoring:
            try:
                current_time = time.time()
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=None)
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Network I/O
                current_network = psutil.net_io_counters()
                network_sent_rate = (current_network.bytes_sent - last_network.bytes_sent) / interval
                network_recv_rate = (current_network.bytes_recv - last_network.bytes_recv) / interval
                last_network = current_network
                
                # Disk I/O
                current_disk = psutil.disk_io_counters()
                if current_disk and last_disk:
                    disk_read_rate = (current_disk.read_bytes - last_disk.read_bytes) / interval
                    disk_write_rate = (current_disk.write_bytes - last_disk.write_bytes) / interval
                    last_disk = current_disk
                else:
                    disk_read_rate = disk_write_rate = 0
                
                with self.lock:
                    self.data['timestamps'].append(current_time)
                    self.data['cpu_usage'].append(cpu_percent)
                    self.data['memory_usage'].append(memory_percent)
                    self.data['network_stats'].append({
                        'sent_rate': network_sent_rate,
                        'recv_rate': network_recv_rate
                    })
                    self.data['disk_io'].append({
                        'read_rate': disk_read_rate,
                        'write_rate': disk_write_rate
                    })
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(interval)

    def get_current_stats(self):
        """Get current system statistics"""
        try:
            # Process info for the current Python process
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # System-wide stats
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return {
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_free_gb': disk.free / (1024**3),
                    'network_sent_mb': network.bytes_sent / (1024**2),
                    'network_recv_mb': network.bytes_recv / (1024**2)
                },
                'process': {
                    'memory_rss_mb': process_memory.rss / (1024**2),
                    'memory_vms_mb': process_memory.vms / (1024**2),
                    'cpu_percent': process.cpu_percent(),
                    'num_threads': process.num_threads()
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def get_performance_summary(self):
        """Get performance summary of monitoring data"""
        if not self.data['cpu_usage']:
            return {'error': 'No monitoring data collected'}
        
        with self.lock:
            cpu_data = list(self.data['cpu_usage'])
            memory_data = list(self.data['memory_usage'])
            network_data = list(self.data['network_stats'])
            disk_data = list(self.data['disk_io'])
        
        # Calculate statistics
        avg_cpu = sum(cpu_data) / len(cpu_data) if cpu_data else 0
        max_cpu = max(cpu_data) if cpu_data else 0
        avg_memory = sum(memory_data) / len(memory_data) if memory_data else 0
        max_memory = max(memory_data) if memory_data else 0
        
        # Network stats
        total_sent = sum(stat['sent_rate'] for stat in network_data) if network_data else 0
        total_recv = sum(stat['recv_rate'] for stat in network_data) if network_data else 0
        
        # Disk stats
        total_disk_read = sum(stat['read_rate'] for stat in disk_data) if disk_data else 0
        total_disk_write = sum(stat['write_rate'] for stat in disk_data) if disk_data else 0
        
        return {
            'monitoring_duration': len(cpu_data),
            'cpu_usage': {
                'average': avg_cpu,
                'maximum': max_cpu,
                'samples': len(cpu_data)
            },
            'memory_usage': {
                'average': avg_memory,
                'maximum': max_memory,
                'samples': len(memory_data)
            },
            'network_activity': {
                'total_sent_mb': total_sent / (1024**2),
                'total_recv_mb': total_recv / (1024**2),
                'samples': len(network_data)
            },
            'disk_activity': {
                'total_read_mb': total_disk_read / (1024**2),
                'total_write_mb': total_disk_write / (1024**2),
                'samples': len(disk_data)
            }
        }

    def check_system_health(self):
        """Check if system is healthy for performance testing"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            warnings = []
            
            # CPU check
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 60:
                warnings.append(f"Moderate CPU usage: {cpu_percent:.1f}%")
            
            # Memory check
            if memory.percent > 90:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 75:
                warnings.append(f"Moderate memory usage: {memory.percent:.1f}%")
            
            # Disk space check
            if disk.percent > 95:
                issues.append(f"Low disk space: {100-disk.percent:.1f}% free")
            elif disk.percent > 85:
                warnings.append(f"Moderate disk usage: {100-disk.percent:.1f}% free")
            
            return {
                'healthy': len(issues) == 0,
                'issues': issues,
                'warnings': warnings,
                'stats': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_free_gb': disk.free / (1024**3)
                }
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }

    def monitor_api_endpoint(self, endpoint_url, duration=30):
        """Monitor API endpoint response times and availability"""
        print(f"🌐 Monitoring API endpoint for {duration} seconds...")
        
        start_time = time.time()
        response_times = []
        error_count = 0
        total_requests = 0
        
        while time.time() - start_time < duration:
            try:
                req_start = time.time()
                response = requests.get(f"{endpoint_url}?health=true", timeout=10)
                req_duration = time.time() - req_start
                
                response_times.append(req_duration)
                total_requests += 1
                
                if response.status_code != 200:
                    error_count += 1
                    
            except Exception:
                error_count += 1
                total_requests += 1
            
            time.sleep(2)  # Check every 2 seconds
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            availability = ((total_requests - error_count) / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_checks': total_requests,
                'errors': error_count,
                'availability_percent': availability,
                'avg_response_time': avg_response_time,
                'min_response_time': min_response_time,
                'max_response_time': max_response_time,
                'response_times': response_times
            }
        else:
            return {
                'error': 'No successful health checks completed'
            }

def main():
    """Example usage of SystemMonitor"""
    monitor = SystemMonitor()
    
    print("🔍 System Health Check")
    health = monitor.check_system_health()
    
    if health['healthy']:
        print("✅ System is healthy for testing")
    else:
        print("⚠️  System issues detected:")
        for issue in health['issues']:
            print(f"  • {issue}")
    
    if health['warnings']:
        print("⚠️  Warnings:")
        for warning in health['warnings']:
            print(f"  • {warning}")
    
    print("\n📊 Current System Stats:")
    current_stats = monitor.get_current_stats()
    if isinstance(current_stats, dict) and 'error' not in current_stats:
        system = current_stats.get('system', {})
        process = current_stats.get('process', {})
        
        if isinstance(system, dict) and isinstance(process, dict):
            print(f"  CPU: {system.get('cpu_percent', 0):.1f}%")
            print(f"  Memory: {system.get('memory_percent', 0):.1f}% ({system.get('memory_available_gb', 0):.1f}GB available)")
            disk_free = system.get('disk_free_gb', 0)
            if isinstance(disk_free, (int, float)):
                print(f"  Disk: {disk_free:.1f}GB free")
            print(f"  Process Memory: {process.get('memory_rss_mb', 0):.1f}MB")
            print(f"  Process CPU: {process.get('cpu_percent', 0):.1f}%")
    else:
        print("  Unable to retrieve system stats")
    
    # Test API monitoring
    print("\n🌐 Testing API Monitoring...")
    api_health = monitor.monitor_api_endpoint("http://localhost:3000/api/generate-enhanced-3d-simple", duration=10)
    
    if 'error' not in api_health:
        print(f"  API Availability: {api_health['availability_percent']:.1f}%")
        print(f"  Average Response Time: {api_health['avg_response_time']:.3f}s")
        print(f"  Total Health Checks: {api_health['total_checks']}")
    else:
        print(f"  API Monitoring Error: {api_health['error']}")

if __name__ == "__main__":
    main()
