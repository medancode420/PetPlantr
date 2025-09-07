#!/bin/bash
# 🚀 LAUNCH OXFORD TRAINING NOW - Get baseline model while collecting photos
set -e

cd /Users/medan/Downloads/PetPlantr/backend/datasets

echo "🎯 LAUNCHING OXFORD-ONLY TRAINING"
echo "================================="
echo "📊 Dataset: 150 images, 37 breeds"
echo "⏱️  Duration: ~15-20 minutes"
echo "🎯 Purpose: Baseline model while collecting proprietary photos"
echo ""

# Check Modal CLI
if ! /Users/medan/Downloads/PetPlantr/.venv/bin/modal --help &> /dev/null; then
    echo "❌ Modal CLI not working!"
    echo "🔧 Install: pip install modal"
    exit 1
fi

# Check training script
if [ ! -f "enhanced_shape_mvd_training.py" ]; then
    echo "❌ Training script not found!"
    echo "📁 Expected: enhanced_shape_mvd_training.py"
    exit 1
fi

echo "✅ Prerequisites verified"
echo ""

echo "🚀 Launching Oxford backbone training..."
echo "📋 Command: modal run oxford_backbone_training.py"
echo ""

# Launch training
/Users/medan/Downloads/PetPlantr/.venv/bin/modal run oxford_backbone_training.py

echo ""
echo "🎉 Oxford training launched!"
echo "⏰ Training in progress (~15-20 minutes)"
echo ""
echo "📸 NEXT ACTIONS (while training runs):"
echo "1. Collect 5+ proprietary pet photos"
echo "2. Process: python3 process_proprietary_photos.py"
echo "3. Upload: bash process_and_upload.sh"
echo "4. Launch demo: modal run enhanced_shape_mvd_training.py --demo"
echo ""
echo "🎯 60 minutes to production-quality pet likeness!"
