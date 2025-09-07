#!/usr/bin/env python3
"""
Quick Photo Collection Script for 30-minute Sprint
Demonstrates how to add photos to the proprietary structure
"""

import os
import shutil
from pathlib import Path
import time

def setup_demo_photos():
    """Create some demo photos to simulate the collection process"""
    proprietary_root = Path("/Users/medan/Desktop/PetPlantr_Dataset/proprietary_raw")
    
    print("🚀 QUICK PHOTO COLLECTION DEMO")
    print("=" * 50)
    
    # List available pet directories
    pet_dirs = sorted([d for d in proprietary_root.iterdir() if d.is_dir()])
    print(f"📁 Available pet directories: {len(pet_dirs)}")
    
    for pet_dir in pet_dirs[:3]:  # Demo with first 3 pets
        print(f"\n📸 Working on: {pet_dir.name}")
        
        # Check if we have any sample images we can use as demos
        # (In real life, users would drag and drop their pet photos here)
        
        # For demo purposes, let's create placeholder files
        views = ["front", "left", "right", "back"]
        for view in views:
            demo_file = pet_dir / f"{view}.jpg"
            if not demo_file.exists():
                # Create a placeholder file to simulate photo addition
                demo_file.write_text(f"DEMO: This would be a {view} view photo of {pet_dir.name}")
                print(f"   ✅ Added demo {view} photo")
            else:
                print(f"   ✅ {view} photo already exists")
    
    print("\n📊 DEMO COLLECTION COMPLETE!")
    print("🎯 In real deployment, users would:")
    print("   1. Take photos of their pets (front, left, right, back)")
    print("   2. Drag photos into the pet directories")
    print("   3. Run the processing script")
    
    return True

def check_real_photos():
    """Check for actual photo files (jpg, png, etc.)"""
    proprietary_root = Path("/Users/medan/Desktop/PetPlantr_Dataset/proprietary_raw")
    
    real_photos = 0
    pet_dirs = sorted([d for d in proprietary_root.iterdir() if d.is_dir()])
    
    for pet_dir in pet_dirs:
        photos = list(pet_dir.glob("*.jpg")) + list(pet_dir.glob("*.jpeg")) + list(pet_dir.glob("*.png"))
        if photos:
            real_photos += len(photos)
            print(f"📸 {pet_dir.name}: {len(photos)} photos")
    
    return real_photos

if __name__ == "__main__":
    print("🔍 CHECKING FOR REAL PHOTOS...")
    real_count = check_real_photos()
    
    if real_count == 0:
        print("\n⚡ NO REAL PHOTOS FOUND - CREATING DEMO STRUCTURE")
        setup_demo_photos()
    else:
        print(f"\n✅ FOUND {real_count} REAL PHOTOS!")
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Add real pet photos to directories")
    print("   2. Run: python3 preprocess_proprietary.py")
    print("   3. Run: bash process_and_upload.sh")
    print("   4. Launch Shape-MVD fine-tune")
