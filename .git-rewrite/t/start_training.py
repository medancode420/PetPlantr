#!/usr/bin/env python3
"""
Start Training with Downloaded Datasets
Ready to train universal breed classifier with free data!
"""

import os
from pathlib import Path
import json

def prepare_training_data():
    """Prepare downloaded datasets for CLIP training"""
    
    datasets_dir = Path("./datasets")
    
    # Check what we have
    info_file = datasets_dir / "dataset_info.json"
    if info_file.exists():
        with open(info_file, 'r') as f:
            info = json.load(f)
        
        print("🎯 READY TO START TRAINING!")
        print("=" * 40)
        print(f"Available datasets: {len(info['datasets'])}")
        print(f"Total breeds: {info['total_breeds']}")
        print(f"Total images: {info['total_images']:,}")
        
        print(f"\n🚀 NEXT STEPS:")
        print("1. Install training requirements:")
        print("   pip install torch transformers accelerate")
        print("\n2. Start with proof-of-concept training:")
        print("   python train_breed_classifier.py")
        print("\n3. Scale up with more data sources")
        
        return True
    else:
        print("❌ No datasets found. Run download_free_datasets.py first!")
        return False

if __name__ == "__main__":
    prepare_training_data()
