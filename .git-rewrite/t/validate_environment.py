#!/usr/bin/env python3
"""
Final Environment Validation and Status Report for PetPlantr
This script validates that the permanent environment fix is working correctly
"""

import sys
import os
import subprocess
import importlib
import json
from pathlib import Path
from datetime import datetime


def validate_environment():
    """Comprehensive environment validation"""
    print("🔍 PetPlantr Environment Validation Report")
    print("=" * 60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'validation_status': 'unknown',
        'python_info': {},
        'virtual_env': {},
        'dependencies': {},
        'functionality': {},
        'file_structure': {}
    }
    
    # Python version
    print("🐍 Python Environment:")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"   Version: {python_version}")
    print(f"   Executable: {sys.executable}")
    
    report['python_info'] = {
        'version': python_version,
        'executable': sys.executable,
        'platform': sys.platform
    }
    
    # Virtual environment
    print("\n🏠 Virtual Environment:")
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"   Active: ✅ {venv_path}")
        report['virtual_env'] = {'active': True, 'path': venv_path}
    else:
        print("   Active: ❌ No virtual environment detected")
        report['virtual_env'] = {'active': False, 'path': None}
    
    # Dependencies
    print("\n📦 Dependency Status:")
    core_packages = [
        'numpy', 'scipy', 'matplotlib', 'PIL', 'cv2', 'trimesh', 
        'stl', 'torch', 'torchvision', 'sklearn', 'skimage',
        'pandas', 'requests', 'flask', 'flask_cors'
    ]
    
    dependency_status = {}
    success_count = 0
    
    for package in core_packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"   ✅ {package}: {version}")
            dependency_status[package] = {'status': 'ok', 'version': version}
            success_count += 1
        except ImportError as e:
            print(f"   ❌ {package}: {e}")
            dependency_status[package] = {'status': 'missing', 'error': str(e)}
    
    print(f"\n   Summary: {success_count}/{len(core_packages)} dependencies available")
    report['dependencies'] = {
        'total': len(core_packages),
        'available': success_count,
        'success_rate': success_count / len(core_packages),
        'details': dependency_status
    }
    
    # File structure
    print("\n📁 File Structure:")
    important_files = [
        'requirements.txt',
        'setup_environment_enhanced.sh',
        'activate_petplantr.sh',
        'check_environment.py',
        'complete_dog_to_planter_demo.py',
        'test_100_percent_achievement.py',
        'enhanced_stl_analyzer.py'
    ]
    
    file_status = {}
    for file in important_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
            file_status[file] = True
        else:
            print(f"   ❌ {file}")
            file_status[file] = False
    
    report['file_structure'] = file_status
    
    # Functionality tests
    print("\n🧪 Functionality Tests:")
    functionality_results = {}
    
    # Test 1: Basic mesh creation
    try:
        import numpy as np
        import trimesh
        
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        faces = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]])
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        print("   ✅ 3D mesh creation")
        functionality_results['mesh_creation'] = True
    except Exception as e:
        print(f"   ❌ 3D mesh creation: {e}")
        functionality_results['mesh_creation'] = False
    
    # Test 2: STL export
    try:
        test_path = Path('temp/validation_test.stl')
        test_path.parent.mkdir(exist_ok=True)
        mesh.export(test_path)
        test_path.unlink(missing_ok=True)
        
        print("   ✅ STL export")
        functionality_results['stl_export'] = True
    except Exception as e:
        print(f"   ❌ STL export: {e}")
        functionality_results['stl_export'] = False
    
    # Test 3: Image processing
    try:
        from PIL import Image
        import numpy as np
        
        img = Image.new('RGB', (100, 100), 'red')
        arr = np.array(img)
        
        print("   ✅ Image processing")
        functionality_results['image_processing'] = True
    except Exception as e:
        print(f"   ❌ Image processing: {e}")
        functionality_results['image_processing'] = False
    
    # Test 4: Enhanced STL analyzer
    try:
        from enhanced_stl_analyzer import analyze_stl_quality
        print("   ✅ Enhanced STL analyzer import")
        functionality_results['stl_analyzer'] = True
    except Exception as e:
        print(f"   ❌ Enhanced STL analyzer: {e}")
        functionality_results['stl_analyzer'] = False
    
    report['functionality'] = functionality_results
    
    # Overall status
    dependency_ok = success_count >= len(core_packages) * 0.9  # 90% threshold
    functionality_ok = all(functionality_results.values())
    files_ok = all(file_status[f] for f in ['requirements.txt', 'enhanced_stl_analyzer.py'])
    
    if dependency_ok and functionality_ok and files_ok:
        status = "EXCELLENT"
        status_emoji = "🎉"
        status_description = "Environment is fully configured and working perfectly"
    elif dependency_ok and functionality_ok:
        status = "GOOD"
        status_emoji = "✅"
        status_description = "Environment is working well with minor issues"
    elif dependency_ok:
        status = "PARTIAL"
        status_emoji = "⚠️"
        status_description = "Dependencies available but functionality issues detected"
    else:
        status = "ISSUES"
        status_emoji = "❌"
        status_description = "Environment has significant issues requiring attention"
    
    report['validation_status'] = status
    
    print(f"\n{status_emoji} OVERALL STATUS: {status}")
    print(f"   {status_description}")
    
    # Save report
    report_path = f"temp/environment_validation_{int(datetime.now().timestamp())}.json"
    Path("temp").mkdir(exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📋 Validation report saved: {report_path}")
    
    # Summary and recommendations
    print(f"\n📊 SUMMARY:")
    print(f"   Dependencies: {success_count}/{len(core_packages)} available")
    print(f"   Functionality: {sum(functionality_results.values())}/{len(functionality_results)} working")
    print(f"   Virtual Environment: {'Active' if venv_path else 'Not active'}")
    
    if status == "EXCELLENT":
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"   • Environment is production-ready!")
        print(f"   • Run: python3 complete_dog_to_planter_demo.py")
        print(f"   • Run: python3 test_100_percent_achievement.py")
        print(f"   • Activate anytime with: source activate_petplantr.sh")
    elif status == "GOOD":
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"   • Environment is usable for most features")
        print(f"   • Consider reinstalling missing optional packages")
    else:
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"   • Re-run setup: ./setup_environment_enhanced.sh")
        print(f"   • Check individual dependency issues above")
    
    return report


def main():
    """Main validation function"""
    try:
        report = validate_environment()
        
        # Exit with appropriate code
        if report['validation_status'] in ['EXCELLENT', 'GOOD']:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
