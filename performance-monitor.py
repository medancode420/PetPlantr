"""
PetPlantr Performance Monitoring and Optimization
"""

import time
import psutil
import threading
from collections import deque
import json
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'response_times': deque(maxlen=1000),
            'memory_usage': deque(maxlen=100),
            'cpu_usage': deque(maxlen=100),
            'active_connections': 0
        }
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            self._collect_metrics()
            time.sleep(1)  # Collect metrics every second

    def _collect_metrics(self):
        """Collect system metrics"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].append(memory.percent)

            # CPU usage
            cpu = psutil.cpu_percent(interval=0.1)
            self.metrics['cpu_usage'].append(cpu)

        except Exception as e:
            print(f"Error collecting metrics: {e}")

    def record_response_time(self, response_time):
        """Record API response time"""
        self.metrics['response_times'].append(response_time)

    def get_performance_report(self):
        """Generate performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {}
        }

        # Response time statistics
        if self.metrics['response_times']:
            response_times = list(self.metrics['response_times'])
            report['metrics']['response_time'] = {
                'average': sum(response_times) / len(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'p95': sorted(response_times)[int(len(response_times) * 0.95)],
                'count': len(response_times)
            }

        # Memory statistics
        if self.metrics['memory_usage']:
            memory_usage = list(self.metrics['memory_usage'])
            report['metrics']['memory'] = {
                'current': memory_usage[-1] if memory_usage else 0,
                'average': sum(memory_usage) / len(memory_usage),
                'peak': max(memory_usage) if memory_usage else 0
            }

        # CPU statistics
        if self.metrics['cpu_usage']:
            cpu_usage = list(self.metrics['cpu_usage'])
            report['metrics']['cpu'] = {
                'current': cpu_usage[-1] if cpu_usage else 0,
                'average': sum(cpu_usage) / len(cpu_usage),
                'peak': max(cpu_usage) if cpu_usage else 0
            }

        return report

    def optimize_memory(self):
        """Memory optimization recommendations"""
        report = self.get_performance_report()

        recommendations = []

        if report['metrics'].get('memory', {}).get('current', 0) > 80:
            recommendations.append("High memory usage detected. Consider:")
            recommendations.append("- Implement memory pooling for ML models")
            recommendations.append("- Add memory limits to worker processes")
            recommendations.append("- Implement model unloading for inactive models")

        if report['metrics'].get('response_time', {}).get('p95', 0) > 2.0:
            recommendations.append("Slow response times detected. Consider:")
            recommendations.append("- Implement response caching")
            recommendations.append("- Optimize ML model inference")
            recommendations.append("- Add request queuing for high load")

        return recommendations

# Global performance monitor
performance_monitor = PerformanceMonitor()

def start_performance_monitoring():
    """Start the global performance monitor"""
    performance_monitor.start_monitoring()

def stop_performance_monitoring():
    """Stop the global performance monitor"""
    performance_monitor.stop_monitoring()

def get_performance_report():
    """Get current performance report"""
    return performance_monitor.get_performance_report()

def record_response_time(response_time):
    """Record response time for monitoring"""
    performance_monitor.record_response_time(response_time)

def get_optimization_recommendations():
    """Get performance optimization recommendations"""
    return performance_monitor.optimize_memory()

if __name__ == "__main__":
    # Example usage
    start_performance_monitoring()

    # Simulate some activity
    for i in range(10):
        record_response_time(0.1 + (i * 0.01))
        time.sleep(0.1)

    # Get report
    report = get_performance_report()
    print(json.dumps(report, indent=2))

    # Get recommendations
    recommendations = get_optimization_recommendations()
    if recommendations:
        print("\nOptimization Recommendations:")
        for rec in recommendations:
            print(f"- {rec}")

    stop_performance_monitoring()
