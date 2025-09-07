#!/usr/bin/env python3
"""
PetPlantr System Monitor - Simple version using system commands
"""

import subprocess
import time
from flask import Flask, Response
import json
from datetime import datetime

app = Flask(__name__)

def run_command(cmd):
    """Run system command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "0"

@app.route('/metrics')
def metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics = []

    # CPU Usage (using top command)
    cpu_output = run_command("top -l 1 | grep 'CPU usage' | awk '{print $3}' | tr -d '%'")
    try:
        cpu_percent = float(cpu_output) if cpu_output else 0.0
    except:
        cpu_percent = 0.0

    metrics.append('# HELP cpu_usage_percent CPU usage percentage')
    metrics.append('# TYPE cpu_usage_percent gauge')
    metrics.append(f'cpu_usage_percent {cpu_percent}')

    # Memory Usage
    mem_output = run_command("vm_stat | grep 'Pages active' | awk '{print $3}' | tr -d '.'")
    try:
        mem_active = int(mem_output) * 4096 / 1024 / 1024 if mem_output else 0  # MB
    except:
        mem_active = 0

    metrics.append('# HELP memory_used_mb Memory used in MB')
    metrics.append('# TYPE memory_used_mb gauge')
    metrics.append(f'memory_used_mb {mem_active}')

    # Disk Usage
    disk_output = run_command("df / | tail -1 | awk '{print $5}' | tr -d '%'")
    try:
        disk_percent = int(disk_output) if disk_output else 0
    except:
        disk_percent = 0

    metrics.append('# HELP disk_usage_percent Disk usage percentage')
    metrics.append('# TYPE disk_usage_percent gauge')
    metrics.append(f'disk_usage_percent {disk_percent}')

    # System Load
    load_output = run_command("uptime | awk -F'load averages:' '{print $2}' | awk '{print $1}'")
    try:
        load_1m = float(load_output) if load_output else 0.0
    except:
        load_1m = 0.0

    metrics.append('# HELP system_load1 1-minute load average')
    metrics.append('# TYPE system_load1 gauge')
    metrics.append(f'system_load1 {load_1m}')

    # Process count
    proc_output = run_command("ps aux | wc -l")
    try:
        proc_count = int(proc_output) if proc_output else 0
    except:
        proc_count = 0

    metrics.append('# HELP process_count_total Total number of processes')
    metrics.append('# TYPE process_count_total gauge')
    metrics.append(f'process_count_total {proc_count}')

    return Response('\n'.join(metrics) + '\n', mimetype='text/plain')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

if __name__ == '__main__':
    print("🚀 Starting PetPlantr System Monitor on port 9100...")
    app.run(host='0.0.0.0', port=9100, debug=False)
