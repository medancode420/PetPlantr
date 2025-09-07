#!/usr/bin/env python3
"""
Simple validation test for PetPlantr breed detection system
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all key modules can be imported"""
    try:
        print("🧪 Testing imports...")
        
        # Test AI models
        from src.ai.models.clip_breed import CLIPBreedDetector
        print("✅ CLIP+LoRA model imports successfully")
        
        # Test API routes
        from src.api.routes.breed import router
        print("✅ Breed detection API route imports successfully")
        
        # Test inference engine
        from src.core.inference import get_inference_engine
        print("✅ Inference engine imports successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_file_structure():
    """Test that required files exist"""
    print("📁 Testing file structure...")
    
    required_files = [
        "src/ai/models/clip_breed.py",
        "src/ai/training/train_breed_head.py", 
        "src/api/routes/breed.py",
        "src/core/inference.py",
        "requirements.txt",
        "Dockerfile.enhanced",
        "test_enhanced_system.sh",
        "frontend/src/test-utils/index.ts"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_data_structure():
    """Test data directory structure"""
    print("📂 Testing data structure...")
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("❌ data/ directory missing")
        return False
    
    breeds_dir = data_dir / "breeds"
    if breeds_dir.exists():
        breed_count = len(list(breeds_dir.iterdir()))
        print(f"✅ data/breeds/ exists with {breed_count} subdirectories")
    else:
        print("⚠️  data/breeds/ directory missing")
    
    hard_neg_dir = data_dir / "hard_neg"
    if hard_neg_dir.exists():
        print("✅ data/hard_neg/ directory exists")
    else:
        print("⚠️  data/hard_neg/ directory missing")
    
    labels_file = data_dir / "labels.csv"
    if labels_file.exists():
        print("✅ data/labels.csv exists")
    else:
        print("⚠️  data/labels.csv missing")
    
    return True

def test_pytorch():
    """Test PyTorch and CUDA availability"""
    try:
        print("🔥 Testing PyTorch...")
        import torch
        print(f"✅ PyTorch {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.device_count()} GPU(s)")
        else:
            print("⚠️  CUDA not available (CPU inference only)")
        
        return True
    except ImportError:
        print("❌ PyTorch not installed")
        return False

def main():
    """Run all validation tests"""
    print("🐕 PetPlantr Implementation Validation")
    print("=====================================")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Data Structure", test_data_structure), 
        ("PyTorch Setup", test_pytorch),
        ("Module Imports", test_imports),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        print("\n🚀 Ready to run:")
        print("  bash complete_pipeline.sh prepare")
        print("  bash complete_pipeline.sh train") 
        print("  bash test_enhanced_system.sh all")
        return 0
    else:
        print("❌ Some tests failed. Check missing components.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
