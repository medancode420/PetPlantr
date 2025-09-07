#!/usr/bin/env python3
"""
PetPlantr Training Completion Monitor
Watches for "Checkpoint saved / Upload to S3 complete" and triggers weight promotion
"""

import subprocess
import time
import os
import sys
from datetime import datetime
import re

class TrainingCompletionMonitor:
    def __init__(self):
        self.job_ids = {
            'oxford_backbone': 'ap-aAUGz3CuBS5kl1ukUREqmn',
            'unet128_stage1': 'ap-gH9eddhDGmFz06gBOj6Dci'
        }
        self.completion_triggers = [
            'Checkpoint saved',
            'Upload to S3 complete',
            'Training complete',
            'Best model saved',
            'Weights uploaded to S3'
        ]
        
    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
        
    def check_modal_logs(self, job_id, job_name):
        """Check Modal logs for completion triggers"""
        try:
            result = subprocess.run([
                'modal', 'logs', job_id, '--lines', '20'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logs = result.stdout
                
                # Check for completion triggers
                for trigger in self.completion_triggers:
                    if trigger.lower() in logs.lower():
                        self.log(f"🎉 {job_name} COMPLETION DETECTED: '{trigger}' found in logs")
                        return True, logs
                        
                return False, logs
            else:
                self.log(f"⚠️  Could not fetch logs for {job_name}: {result.stderr}")
                return False, ""
                
        except subprocess.TimeoutExpired:
            self.log(f"⚠️  Timeout fetching logs for {job_name}")
            return False, ""
        except Exception as e:
            self.log(f"❌ Error checking {job_name} logs: {e}")
            return False, ""
    
    def check_s3_weights(self):
        """Check S3 for new weight uploads"""
        try:
            # Check stage1 weights
            result = subprocess.run([
                'aws', 's3', 'ls', 's3://petplantr-models/stage1/', '--recursive'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and '.pth' in result.stdout:
                self.log("🎯 Stage 1 weights detected in S3!")
                return True, 'stage1'
                
            # Check backbone weights
            result = subprocess.run([
                'aws', 's3', 'ls', 's3://petplantr-models/backbone/', '--recursive'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and '.pt' in result.stdout:
                self.log("🎯 Backbone weights detected in S3!")
                return True, 'backbone'
                
            return False, None
            
        except Exception as e:
            self.log(f"❌ Error checking S3: {e}")
            return False, None
    
    def run_weight_promotion(self):
        """Execute weight promotion script"""
        self.log("🚀 Starting weight promotion...")
        
        try:
            # Make sure script is executable
            subprocess.run(['chmod', '+x', './promote_weights.sh'], check=True)
            
            # Run promotion script
            result = subprocess.run([
                './promote_weights.sh', 
                's3://petplantr-models/stage1/unet128_stage1_best.pth'
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            if result.returncode == 0:
                self.log("✅ Weight promotion successful!")
                self.log(f"Output: {result.stdout}")
                return True
            else:
                self.log(f"❌ Weight promotion failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Weight promotion timed out (>5 min)")
            return False
        except Exception as e:
            self.log(f"❌ Error running promotion: {e}")
            return False
    
    def run_smoke_test(self):
        """Execute end-to-end smoke test"""
        self.log("🧪 Starting smoke test...")
        
        try:
            # Change to backend directory and run smoke test
            result = subprocess.run([
                'npm', 'run', 'test:smoke-e2e'
            ], cwd='backend', capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                self.log("✅ Smoke test passed!")
                self.log("🎉 READY FOR PUBLIC BETA!")
                return True
            else:
                self.log(f"❌ Smoke test failed: {result.stderr}")
                self.log("🚨 Need to investigate before beta launch")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Smoke test timed out (>10 min)")
            return False
        except Exception as e:
            self.log(f"❌ Error running smoke test: {e}")
            return False
    
    def monitor_training_completion(self):
        """Main monitoring loop"""
        self.log("🔄 Starting training completion monitoring...")
        self.log("   Watching for: 'Checkpoint saved / Upload to S3 complete'")
        self.log("   Will auto-trigger: ./promote_weights.sh && npm run smoke:e2e")
        self.log("")
        
        weight_promotion_done = False
        smoke_test_done = False
        
        while True:
            try:
                # Check Modal logs for completion
                for job_name, job_id in self.job_ids.items():
                    completed, logs = self.check_modal_logs(job_id, job_name)
                    
                    if completed and not weight_promotion_done:
                        self.log(f"🎯 Training completion detected for {job_name}!")
                        
                        # Wait a bit for S3 upload to complete
                        self.log("⏳ Waiting 30s for S3 upload to complete...")
                        time.sleep(30)
                        
                        # Check S3 and run promotion
                        weights_ready, weight_type = self.check_s3_weights()
                        if weights_ready:
                            if self.run_weight_promotion():
                                weight_promotion_done = True
                            else:
                                self.log("🚨 ALERT: Weight promotion failed - manual intervention needed")
                                return False
                
                # If promotion is done but smoke test isn't, run it
                if weight_promotion_done and not smoke_test_done:
                    self.log("⏳ Waiting 60s before smoke test...")
                    time.sleep(60)
                    
                    if self.run_smoke_test():
                        smoke_test_done = True
                        self.log("")
                        self.log("🎉" * 20)
                        self.log("🎉 MISSION ACCOMPLISHED!")
                        self.log("🎉 PetPlantr is ready for public Beta!")
                        self.log("🎉" * 20)
                        return True
                    else:
                        self.log("🚨 ALERT: Smoke test failed - check CloudWatch logs")
                        return False
                
                # If everything is done, we're finished
                if weight_promotion_done and smoke_test_done:
                    return True
                
                # Regular status update
                self.log("⏳ Still monitoring... (training in progress)")
                
                # Sleep between checks
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                self.log("\n🛑 Monitoring stopped by user")
                return False
            except Exception as e:
                self.log(f"❌ Unexpected error: {e}")
                time.sleep(60)  # Continue monitoring despite errors

if __name__ == "__main__":
    monitor = TrainingCompletionMonitor()
    
    success = monitor.monitor_training_completion()
    
    if success:
        print("\n✅ Training pipeline completed successfully!")
        print("🎯 Next: Ping user that we're 2 checkmarks away from public Beta!")
        sys.exit(0)
    else:
        print("\n❌ Training pipeline encountered issues")
        print("🚨 Manual intervention required")
        sys.exit(1)
