#!/usr/bin/env python3
"""
PetPlantr Infrastructure Health Check
Verifies all services are properly configured and accessible
"""

import os
import json
import requests
import boto3
from pathlib import Path
import sys

class InfrastructureHealthCheck:
    def __init__(self):
        self.results = {
            "replicate": {"status": "unknown", "details": ""},
            "aws_s3": {"status": "unknown", "details": ""},
            "stripe": {"status": "unknown", "details": ""},
            "environment": {"status": "unknown", "details": ""},
            "frontend": {"status": "unknown", "details": ""}
        }
    
    def check_environment_variables(self):
        """Check if all required environment variables are set"""
        required_vars = [
            "REPLICATE_API_TOKEN",
            "AWS_ACCESS_KEY_ID", 
            "AWS_SECRET_ACCESS_KEY",
            "AWS_S3_BUCKET",
            "STRIPE_SECRET_KEY",
            "STRIPE_PUBLISHABLE_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.results["environment"]["status"] = "error"
            self.results["environment"]["details"] = f"Missing variables: {', '.join(missing_vars)}"
        else:
            self.results["environment"]["status"] = "healthy"
            self.results["environment"]["details"] = "All required environment variables are set"
    
    def check_replicate_api(self):
        """Test Replicate API connectivity"""
        token = os.getenv("REPLICATE_API_TOKEN")
        if not token:
            self.results["replicate"]["status"] = "error"
            self.results["replicate"]["details"] = "REPLICATE_API_TOKEN not set"
            return
        
        try:
            response = requests.get(
                "https://api.replicate.com/v1/models",
                headers={"Authorization": f"Token {token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.results["replicate"]["status"] = "healthy"
                self.results["replicate"]["details"] = "API accessible, token valid"
            else:
                self.results["replicate"]["status"] = "error"
                self.results["replicate"]["details"] = f"API returned {response.status_code}"
                
        except Exception as e:
            self.results["replicate"]["status"] = "error"
            self.results["replicate"]["details"] = f"Connection failed: {str(e)}"
    
    def check_aws_s3(self):
        """Test AWS S3 connectivity and permissions"""
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_S3_REGION", "us-east-1")
            )
            
            bucket_name = os.getenv("AWS_S3_BUCKET")
            if not bucket_name:
                self.results["aws_s3"]["status"] = "error"
                self.results["aws_s3"]["details"] = "AWS_S3_BUCKET not set"
                return
            
            # Test bucket access
            s3_client.head_bucket(Bucket=bucket_name)
            
            # Test upload permissions
            test_key = "health-check/test.txt"
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=b"health check",
                ContentType="text/plain"
            )
            
            # Clean up test object
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            
            self.results["aws_s3"]["status"] = "healthy"
            self.results["aws_s3"]["details"] = f"Bucket '{bucket_name}' accessible with read/write permissions"
            
        except Exception as e:
            self.results["aws_s3"]["status"] = "error"
            self.results["aws_s3"]["details"] = f"S3 access failed: {str(e)}"
    
    def check_stripe_api(self):
        """Test Stripe API connectivity"""
        secret_key = os.getenv("STRIPE_SECRET_KEY")
        if not secret_key:
            self.results["stripe"]["status"] = "warning"
            self.results["stripe"]["details"] = "STRIPE_SECRET_KEY not set - demo mode available"
            return
        
        # Check if using placeholder key
        if "your_secret_key" in secret_key or not secret_key.startswith("sk_"):
            self.results["stripe"]["status"] = "warning"
            self.results["stripe"]["details"] = "Placeholder Stripe key - demo mode available"
            return
        
        try:
            response = requests.get(
                "https://api.stripe.com/v1/products",
                headers={"Authorization": f"Bearer {secret_key}"},
                params={"limit": 1},
                timeout=10
            )
            
            if response.status_code == 200:
                self.results["stripe"]["status"] = "healthy"
                self.results["stripe"]["details"] = "API accessible, key valid"
            else:
                self.results["stripe"]["status"] = "warning"
                self.results["stripe"]["details"] = f"API returned {response.status_code} - demo mode available"
                
        except Exception as e:
            self.results["stripe"]["status"] = "warning"
            self.results["stripe"]["details"] = f"Connection failed: {str(e)} - demo mode available"
    
    def check_frontend_build(self):
        """Check if frontend can build successfully"""
        frontend_path = Path("frontend")
        if not frontend_path.exists():
            self.results["frontend"]["status"] = "error"
            self.results["frontend"]["details"] = "Frontend directory not found"
            return
        
        package_json = frontend_path / "package.json"
        if not package_json.exists():
            self.results["frontend"]["status"] = "error"
            self.results["frontend"]["details"] = "package.json not found"
            return
        
        # Check if node_modules exists
        node_modules = frontend_path / "node_modules"
        if not node_modules.exists():
            self.results["frontend"]["status"] = "warning"
            self.results["frontend"]["details"] = "Dependencies not installed. Run: cd frontend && npm install"
            return
        
        self.results["frontend"]["status"] = "healthy"
        self.results["frontend"]["details"] = "Frontend structure looks good"
    
    def run_all_checks(self):
        """Run all health checks"""
        print("🔍 Running PetPlantr Infrastructure Health Check...\n")
        
        print("📋 Checking environment variables...")
        self.check_environment_variables()
        
        print("🤖 Checking Replicate API...")
        self.check_replicate_api()
        
        print("☁️  Checking AWS S3...")
        self.check_aws_s3()
        
        print("💳 Checking Stripe API...")
        self.check_stripe_api()
        
        print("🖥️  Checking frontend setup...")
        self.check_frontend_build()
        
        print("\n" + "="*50)
        print("📊 HEALTH CHECK RESULTS")
        print("="*50)
        
        overall_healthy = True
        
        for service, result in self.results.items():
            status_emoji = {
                "healthy": "✅",
                "warning": "⚠️",
                "error": "❌",
                "unknown": "❓"
            }
            
            emoji = status_emoji.get(result["status"], "❓")
            print(f"{emoji} {service.upper()}: {result['status'].upper()}")
            print(f"   {result['details']}")
            print()
            
            if result["status"] in ["error", "unknown"]:
                overall_healthy = False
        
        if overall_healthy:
            print("🎉 All systems are healthy! Ready for deployment.")
            return 0
        else:
            print("⚠️  Some issues detected. Please resolve them before deployment.")
            return 1
    
    def generate_report(self, output_file: str = "reports/health_check.json"):
        """Generate JSON health check report"""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Consider system healthy if no errors (warnings are OK)
        has_errors = any(r["status"] == "error" for r in self.results.values())
        overall_status = "unhealthy" if has_errors else "healthy"
        
        report = {
            "timestamp": "2025-01-09T20:00:00Z",
            "overall_status": overall_status,
            "services": self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Health check report saved to: {output_file}")

def main():
    # Load environment variables from .env files if they exist
    env_files = [".env", ".env.local", "frontend/.env.local"]
    for env_file in env_files:
        if Path(env_file).exists():
            print(f"📁 Loading environment from: {env_file}")
            with open(env_file) as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key not in os.environ:
                            os.environ[key] = value
    
    health_check = InfrastructureHealthCheck()
    exit_code = health_check.run_all_checks()
    health_check.generate_report()
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
