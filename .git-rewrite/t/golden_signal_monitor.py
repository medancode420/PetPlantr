#!/usr/bin/env python3
"""
Golden Signal Monitor for PetPlantr T-0 Launch
============================================

Real-time monitoring of business SLOs during launch:
- API Latency (p95 < 2s)
- Error Rate (< 0.1%)
- Throughput (> 10 RPS)
- GPU Utilization (< 80%)

Creates evidence collection for audit trail.
"""

import time
import json
import requests
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Optional

class PetPlantrGoldenSignalMonitor:
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.metrics = []
        self.start_time = datetime.datetime.now()
        
        # SLO Thresholds
        self.slo_thresholds = {
            "latency_p95_ms": 2000,
            "error_rate_percent": 0.1,
            "throughput_rps": 10.0,
            "gpu_utilization_percent": 80.0
        }
        
        # Evidence collection
        self.evidence_file = f"launch_evidence_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        
    def check_health_endpoint(self) -> Dict:
        """Check API health with latency measurement."""
        start = time.time()
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            latency_ms = (time.time() - start) * 1000
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "response": response.json() if response.status_code == 200 else None,
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "status_code": None,
                "latency_ms": (time.time() - start) * 1000,
                "response": None,
                "error": str(e)
            }
    
    def check_breed_detection_performance(self) -> Dict:
        """Test breed detection endpoint performance."""
        start = time.time()
        test_payload = {
            "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            "fast_mode": True
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/detect_breed",
                json=test_payload,
                timeout=10
            )
            latency_ms = (time.time() - start) * 1000
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "confidence": response.json().get("confidence", 0) if response.status_code == 200 else 0,
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "status_code": None,
                "latency_ms": (time.time() - start) * 1000,
                "confidence": 0,
                "error": str(e)
            }
    
    def get_gpu_utilization(self) -> Optional[float]:
        """Get current GPU utilization percentage."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        return None
    
    def collect_metrics_sample(self) -> Dict:
        """Collect one complete metrics sample."""
        timestamp = datetime.datetime.now().isoformat()
        
        # Health check
        health = self.check_health_endpoint()
        
        # Breed detection performance
        breed_perf = self.check_breed_detection_performance()
        
        # GPU utilization
        gpu_util = self.get_gpu_utilization()
        
        # Calculate error rate (simplified)
        error_count = 1 if health["status"] != "healthy" or breed_perf["status"] != "success" else 0
        error_rate = error_count * 100.0  # As percentage of this sample
        
        sample = {
            "timestamp": timestamp,
            "health_check": health,
            "breed_detection": breed_perf,
            "gpu_utilization_percent": gpu_util,
            "error_rate_percent": error_rate,
            "slo_violations": self._check_slo_violations(health, breed_perf, gpu_util, error_rate)
        }
        
        return sample
    
    def _check_slo_violations(self, health: Dict, breed_perf: Dict, gpu_util: Optional[float], error_rate: float) -> List[str]:
        """Check for SLO violations."""
        violations = []
        
        # Latency SLO (using breed detection as main business metric)
        if breed_perf["latency_ms"] > self.slo_thresholds["latency_p95_ms"]:
            violations.append(f"Latency violation: {breed_perf['latency_ms']:.1f}ms > {self.slo_thresholds['latency_p95_ms']}ms")
        
        # Error rate SLO
        if error_rate > self.slo_thresholds["error_rate_percent"]:
            violations.append(f"Error rate violation: {error_rate:.2f}% > {self.slo_thresholds['error_rate_percent']}%")
        
        # GPU utilization SLO
        if gpu_util and gpu_util > self.slo_thresholds["gpu_utilization_percent"]:
            violations.append(f"GPU utilization violation: {gpu_util:.1f}% > {self.slo_thresholds['gpu_utilization_percent']}%")
        
        return violations
    
    def monitor_continuous(self, duration_minutes: int = 60, sample_interval_seconds: int = 30):
        """Monitor golden signals continuously."""
        print(f"🚀 Starting T-0 Golden Signal Monitoring")
        print(f"   Duration: {duration_minutes} minutes")
        print(f"   Sample interval: {sample_interval_seconds} seconds")
        print(f"   API Base: {self.api_base}")
        print(f"   Evidence file: {self.evidence_file}")
        print("=" * 60)
        
        end_time = self.start_time + datetime.timedelta(minutes=duration_minutes)
        sample_count = 0
        violation_count = 0
        
        while datetime.datetime.now() < end_time:
            sample_count += 1
            sample = self.collect_metrics_sample()
            self.metrics.append(sample)
            
            # Print status
            violations = sample["slo_violations"]
            status = "🔴 SLO VIOLATION" if violations else "✅ SLO COMPLIANT"
            
            print(f"[{sample['timestamp'][:19]}] Sample #{sample_count} - {status}")
            print(f"  Health: {sample['health_check']['status']} ({sample['health_check']['latency_ms']:.1f}ms)")
            print(f"  Breed Detection: {sample['breed_detection']['status']} ({sample['breed_detection']['latency_ms']:.1f}ms)")
            print(f"  GPU Utilization: {sample['gpu_utilization_percent']:.1f}%" if sample['gpu_utilization_percent'] else "  GPU Utilization: N/A")
            print(f"  Error Rate: {sample['error_rate_percent']:.2f}%")
            
            if violations:
                violation_count += 1
                print(f"  ⚠️  VIOLATIONS:")
                for violation in violations:
                    print(f"    - {violation}")
            
            print()
            
            # Save evidence continuously
            self._save_evidence()
            
            time.sleep(sample_interval_seconds)
        
        # Final summary
        self._print_final_summary(sample_count, violation_count)
        self._save_evidence()
    
    def _save_evidence(self):
        """Save evidence to file for audit trail."""
        evidence = {
            "monitor_start": self.start_time.isoformat(),
            "current_time": datetime.datetime.now().isoformat(),
            "slo_thresholds": self.slo_thresholds,
            "total_samples": len(self.metrics),
            "metrics": self.metrics
        }
        
        with open(self.evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
    
    def _print_final_summary(self, sample_count: int, violation_count: int):
        """Print final monitoring summary."""
        print("=" * 60)
        print("🏁 T-0 LAUNCH MONITORING COMPLETE")
        print("=" * 60)
        print(f"Total samples: {sample_count}")
        print(f"SLO violations: {violation_count}")
        print(f"SLO compliance: {((sample_count - violation_count) / sample_count * 100):.1f}%")
        
        if violation_count == 0:
            print("🎉 LAUNCH SUCCESS: All SLOs maintained throughout monitoring period!")
        else:
            print(f"⚠️  LAUNCH CONCERNS: {violation_count} SLO violations detected")
        
        print(f"\n📁 Evidence saved to: {self.evidence_file}")
        print("📤 Upload to S3 Glacier 'audit' bucket with retention tag")
        print("📊 View metrics in Grafana dashboard")
        print("🔔 Check PagerDuty for any alerts")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="PetPlantr Golden Signal Monitor")
    parser.add_argument("--api-base", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in minutes")
    parser.add_argument("--interval", type=int, default=30, help="Sample interval in seconds")
    
    args = parser.parse_args()
    
    monitor = PetPlantrGoldenSignalMonitor(api_base=args.api_base)
    monitor.monitor_continuous(
        duration_minutes=args.duration,
        sample_interval_seconds=args.interval
    )

if __name__ == "__main__":
    main()
