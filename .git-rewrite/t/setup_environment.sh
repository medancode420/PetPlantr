#!/bin/bash
# Environment Setup Script for PetPlantr
# This script ensures all dependencies are correctly installed

set -e  # Exit on any error

echo "🔧 Setting up PetPlantr environment..."
echo "======================================="

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d" " -f2)
echo "Python version: $python_version"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected. Highly recommended to use one!"
    echo "   Create one with: python3 -m venv petplantr_env"
    echo "   Activate with: source petplantr_env/bin/activate"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install requirements
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Verify critical imports
echo "🔍 Verifying critical imports..."
python3 -c "
import sys
import importlib

packages = [
    'numpy', 'scipy', 'matplotlib', 'PIL', 'cv2', 'trimesh', 
    'stl', 'torch', 'torchvision', 'sklearn', 'skimage',
    'pandas', 'requests', 'flask', 'flask_cors'
]

failed = []
for package in packages:
    try:
        importlib.import_module(package)
        print(f'✅ {package}')
    except ImportError as e:
        print(f'❌ {package}: {e}')
        failed.append(package)

if failed:
    print(f'\\n❌ Failed to import: {failed}')
    print('Try installing missing packages manually.')
    sys.exit(1)
else:
    print('\\n🎉 All critical packages imported successfully!')
"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p outputs
mkdir -p temp
mkdir -p models
mkdir -p logs
mkdir -p test_images
mkdir -p stl_files
mkdir -p generated_models

# Set proper permissions
chmod +x *.py 2>/dev/null || true

# Test basic functionality
echo "🧪 Testing basic functionality..."
python3 -c "
import numpy as np
import trimesh
from pathlib import Path

# Test basic trimesh functionality
try:
    # Create a simple test mesh
    vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
    faces = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    print('✅ Trimesh basic functionality works')
    
    # Test STL export
    test_path = Path('temp/test_mesh.stl')
    mesh.export(test_path)
    print('✅ STL export works')
    
    # Clean up
    test_path.unlink(missing_ok=True)
    
except Exception as e:
    print(f'❌ Basic functionality test failed: {e}')
    exit(1)
"

echo ""
echo "🎉 Environment setup complete!"
echo "==============================="
echo ""
echo "Next steps:"
echo "1. Run: python3 test_100_percent_achievement.py"
echo "2. Or run: python3 enhanced_stl_analyzer.py <stl_file>"
echo "3. For web interface: python3 start_petplantr_web.py"
echo ""
echo "Environment is ready for PetPlantr development! 🐕🪴"
