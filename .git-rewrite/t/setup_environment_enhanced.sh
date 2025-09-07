#!/bin/bash
# Enhanced Environment Setup Script for PetPlantr
# Handles Homebrew-managed Python environments properly

set -e  # Exit on any error

echo "🔧 PetPlantr Environment Setup (Enhanced)"
echo "=========================================="

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

# Check if we're on macOS with Homebrew Python
if [[ "$OSTYPE" == "darwin"* ]] && command -v brew &> /dev/null; then
    echo "🍺 Detected Homebrew environment on macOS"
    HOMEBREW_ENV=true
else
    HOMEBREW_ENV=false
fi

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d" " -f2)
echo "Python version: $python_version"

# Handle virtual environment setup
VENV_DIR="petplantr_env"
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
elif [[ -d "$VENV_DIR" ]]; then
    echo "🔄 Activating existing virtual environment..."
    source "$VENV_DIR/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "✅ Virtual environment created and activated"
fi

# Upgrade pip in virtual environment
echo "📦 Upgrading pip in virtual environment..."
pip install --upgrade pip

# Install packages from requirements.txt
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed successfully"
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
    print('Some packages may need manual installation.')
    print('Try: pip install <package_name>')
else:
    print('\\n🎉 All critical packages imported successfully!')
"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p outputs temp models logs test_images stl_files generated_models

# Set proper permissions
chmod +x *.py 2>/dev/null || true

# Test basic functionality
echo "🧪 Testing basic functionality..."
python3 -c "
import numpy as np
import trimesh
from pathlib import Path

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
    
    print('✅ All basic functionality tests passed')
    
except Exception as e:
    print(f'❌ Basic functionality test failed: {e}')
    exit(1)
"

# Create activation script
echo "📜 Creating activation script..."
cat > activate_petplantr.sh << 'EOF'
#!/bin/bash
# Activation script for PetPlantr environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

if [[ -d "petplantr_env" ]]; then
    source petplantr_env/bin/activate
    echo "🐕🪴 PetPlantr environment activated!"
    echo "Available commands:"
    echo "  python3 complete_dog_to_planter_demo.py  - Full pipeline demo"
    echo "  python3 test_100_percent_achievement.py  - Comprehensive tests"
    echo "  python3 enhanced_stl_analyzer.py <file>  - Analyze STL files"
    echo "  python3 start_petplantr_web.py          - Web interface"
else
    echo "❌ Virtual environment not found. Run setup_environment.sh first."
    exit 1
fi
EOF

chmod +x activate_petplantr.sh

echo ""
echo "🎉 Environment setup complete!"
echo "==============================="
echo ""
echo "🔧 Virtual environment: $PWD/petplantr_env"
echo "📁 Project directory: $PWD"
echo ""
echo "To use PetPlantr:"
echo "1. Activate: source activate_petplantr.sh"
echo "2. Run demo: python3 complete_dog_to_planter_demo.py"
echo "3. Or test: python3 test_100_percent_achievement.py"
echo ""
echo "Environment is ready for PetPlantr development! 🐕🪴"
