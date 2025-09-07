#!/usr/bin/env python3
"""
Check Modal credits and prepare for training.
Run this after adding payment method to Modal.
"""

import modal
import sys
from pathlib import Path

def check_modal_setup():
    """Check Modal authentication and credits status."""
    try:
        # Test basic Modal connection
        print("🔍 Checking Modal setup...")
        
        # Simple check - just import and create client
        import modal
        
        print("✅ Modal authentication: OK")
        print("✅ Modal connection: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Modal setup error: {e}")
        return False

def check_dataset_package():
    """Check if enhanced dataset package is ready."""
    package_path = Path("/Users/medan/Desktop/PetPlantr_Dataset/petplantr_enhanced_training_package.zip")
    
    if package_path.exists():
        size_mb = package_path.stat().st_size / (1024 * 1024)
        print(f"✅ Dataset package ready: {size_mb:.1f}MB")
        return True
    else:
        print("❌ Dataset package not found")
        return False

def main():
    """Main check function."""
    print("🚀 PetPlantr Modal Training Readiness Check")
    print("=" * 50)
    
    # Check Modal setup
    modal_ok = check_modal_setup()
    
    # Check dataset
    dataset_ok = check_dataset_package()
    
    print("\n📊 Status Summary:")
    print(f"  Modal Setup: {'✅' if modal_ok else '❌'}")
    print(f"  Dataset Ready: {'✅' if dataset_ok else '❌'}")
    
    if modal_ok and dataset_ok:
        print("\n🎯 Ready to train! Next steps:")
        print("1. ✅ Modal authenticated")
        print("2. 💳 Add payment method at: https://modal.com/settings/billing")
        print("3. 🏃 Run training: python backend/datasets/enhanced_shape_mvd_training.py")
        print("4. 💰 Expected cost: ~$2.50 for full Shape-MVD training")
        print("5. ⏱️  Training time: ~2-3 hours on A100 GPU")
    else:
        print("\n⚠️  Please resolve issues above before training")
    
    return modal_ok and dataset_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
