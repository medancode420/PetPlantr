#!/usr/bin/env python3
"""
Quick status check for Tier A photo collection progress
"""
import os
from pathlib import Path

def check_photo_status():
    # Check dataset directories
    dataset_root = Path("/Users/medan/Desktop/PetPlantr_Dataset")
    proprietary_raw = dataset_root / "proprietary_raw"
    proprietary_processed = dataset_root / "proprietary_multiview"
    animal3d_subset = dataset_root / "animal3d_subset"
    
    print("🎯 TIER A PHOTO COLLECTION STATUS")
    print("="*50)
    
    # Check proprietary photos
    print("\n📸 PROPRIETARY MULTI-VIEW PHOTOS:")
    if proprietary_raw.exists():
        pet_dirs = [d for d in proprietary_raw.iterdir() if d.is_dir() and d.name.startswith('pet_')]
        print(f"   📁 Pet directories created: {len(pet_dirs)}")
        
        complete_pets = 0
        for pet_dir in pet_dirs:
            views = ['front.jpg', 'left.jpg', 'right.jpg', 'back.jpg']
            existing_views = [v for v in views if (pet_dir / v).exists()]
            if len(existing_views) == 4:
                complete_pets += 1
                print(f"   ✅ {pet_dir.name}: COMPLETE ({len(existing_views)}/4 views)")
            elif len(existing_views) > 0:
                print(f"   🔄 {pet_dir.name}: PARTIAL ({len(existing_views)}/4 views)")
            else:
                print(f"   ⚪ {pet_dir.name}: EMPTY")
        
        print(f"\n   📊 Summary: {complete_pets}/30 pets complete")
        if complete_pets >= 10:
            print("   🚀 READY FOR PARTIAL TRAINING!")
        elif complete_pets >= 5:
            print("   🔄 MINIMUM FOR DEMO TRAINING")
        else:
            print("   ⚡ NEED MORE PHOTOS!")
    else:
        print("   ❌ Directory not found - run setup_tier_a_photos.sh")
    
    # Check Animal3D
    print("\n🐕🐱 ANIMAL3D DATASET:")
    if animal3d_subset.exists():
        dogs_dir = animal3d_subset / "dogs"
        cats_dir = animal3d_subset / "cats"
        
        if dogs_dir.exists() and any(dogs_dir.iterdir()):
            print("   ✅ Dogs data available")
        else:
            print("   ⚪ Dogs data needed")
            
        if cats_dir.exists() and any(cats_dir.iterdir()):
            print("   ✅ Cats data available") 
        else:
            print("   ⚪ Cats data needed")
    else:
        print("   ⚪ Download from https://xujiacong.github.io/AnimalNeRF/")
    
    # Check Oxford status
    oxford_training = Path("/Users/medan/Desktop/PetPlantr_Dataset/enhanced_training")
    print("\n🎓 OXFORD-IIIT ENHANCED:")
    if oxford_training.exists():
        oxford_count = len(list(oxford_training.glob("*.jpg")))
        print(f"   ✅ {oxford_count} images ready (need S3 upload)")
    else:
        print("   ❌ Oxford dataset missing")
    
    # Training readiness
    print("\n🚀 TRAINING READINESS:")
    if complete_pets >= 10:
        print("   ✅ TIER A READY: Oxford + Proprietary (10+ pets)")
        print("   🎯 Command: modal run enhanced_shape_mvd_training.py --tier-a-fast")
    elif complete_pets >= 5:
        print("   🔄 DEMO READY: Oxford + Proprietary (5+ pets)")
        print("   🎯 Command: modal run enhanced_shape_mvd_training.py --demo")
    else:
        print("   ⚡ OXFORD ONLY: Need more proprietary photos")
        print("   🎯 Command: modal run enhanced_shape_mvd_training.py --oxford-only")

if __name__ == "__main__":
    check_photo_status()
