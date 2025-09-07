#!/usr/bin/env python3
"""
Health check script for depth estimation service
"""

import sys
import torch
import requests

def main():
    try:
        # Check GPU availability
        if not torch.cuda.is_available():
            print("WARNING: CUDA not available")
        
        # Check service health endpoint
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("Service healthy")
            sys.exit(0)
        else:
            print(f"Service unhealthy: {response.status_code}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
