#!/bin/bash
# Performance optimization script for PetPlantr

echo "⚡ PetPlantr Performance Optimization..."

# Check current performance
echo "📊 Current Performance Status:"
python3 -c "
import performance_monitor
report = performance_monitor.get_performance_report()
print(f'Response Time (avg): {report.get(\"metrics\", {}).get(\"response_time\", {}).get(\"average\", 0):.3f}s')
print(f'Memory Usage: {report.get(\"metrics\", {}).get(\"memory\", {}).get(\"current\", 0):.1f}%')
print(f'CPU Usage: {report.get(\"metrics\", {}).get(\"cpu\", {}).get(\"current\", 0):.1f}%')
"

# Apply optimizations
echo "🔧 Applying Performance Optimizations..."

# Optimize Python performance
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# Optimize system settings
echo "never" > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
echo "never" > /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || true

# Optimize network settings
sysctl -w net.core.somaxconn=65536 2>/dev/null || true
sysctl -w net.ipv4.tcp_max_syn_backlog=65536 2>/dev/null || true

echo "✅ Performance optimizations applied!"
echo "📋 Recommendations:"
echo "  - Monitor memory usage with performance_monitor.py"
echo "  - Use connection pooling for database connections"
echo "  - Implement response caching for frequent requests"
echo "  - Consider using async/await for I/O operations"
