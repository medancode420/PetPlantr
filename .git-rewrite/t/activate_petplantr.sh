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
