#!/bin/bash
# 🚀 RAPID TIER A DEPLOYMENT - Get to training in 2 hours
set -e

echo "🎯 RAPID TIER A DEPLOYMENT"
echo "========================="
echo "Goal: Get to Tier A training ASAP with minimal viable dataset"
echo ""

# Step 1: Restore Oxford dataset (5 minutes)
echo "📋 STEP 1: Oxford Dataset Restoration"
echo "------------------------------------"
cd /Users/medan/Downloads/PetPlantr/backend/datasets

if [ ! -d "/Users/medan/Downloads/PetPlantr/PetPlantr_Dataset/enhanced_training" ]; then
    echo "🔄 Creating enhanced Oxford dataset..."
    python3 create_enhanced_dataset.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Oxford dataset created successfully"
    else
        echo "❌ Oxford dataset creation failed"
        exit 1
    fi
else
    echo "✅ Oxford dataset already exists"
fi

echo ""

# Step 2: Quick Animal3D setup (manual step)
echo "📋 STEP 2: Animal3D Quick Setup"
echo "-------------------------------"
echo "⚡ MANUAL ACTION REQUIRED:"
echo "1. Visit: https://xujiacong.github.io/AnimalNeRF/"
echo "2. Download minimal subset: dogs/cats multi-view images"
echo "3. Extract to: /Users/medan/Desktop/PetPlantr_Dataset/animal3d_subset/"
echo ""
echo "🏃‍♂️ SKIP FOR NOW - Proceed with Oxford + Proprietary minimal"
echo ""

# Step 3: Proprietary photo guide
echo "📋 STEP 3: Minimal Proprietary Collection (30 minutes)"
echo "-----------------------------------------------------"
echo "🎯 TARGET: 5 pets minimum for demo training"
echo "📸 Priority pets (easy to photograph):"
echo "   • pet_001_golden_retriever"
echo "   • pet_002_labrador" 
echo "   • pet_005_beagle"
echo "   • pet_007_british_shorthair"
echo "   • pet_008_persian_cat"
echo ""
echo "📁 Photo locations:"
echo "   /Users/medan/Desktop/PetPlantr_Dataset/proprietary_raw/pet_XXX_name/"
echo ""
echo "📋 Per pet: front.jpg, left.jpg, right.jpg, back.jpg"
echo "💡 Use phone/tablet, good lighting, plain background"
echo ""

# Step 4: Processing pipeline
echo "📋 STEP 4: Processing Pipeline (5 minutes)"
echo "-----------------------------------------"
echo "⚡ Once photos are ready:"
echo ""
echo "# Process proprietary photos"
echo "cd /Users/medan/Downloads/PetPlantr/backend/datasets"
echo "python3 process_proprietary_photos.py"
echo ""
echo "# Upload all datasets to S3"
echo "bash /Users/medan/Desktop/PetPlantr_Dataset/process_and_upload.sh"
echo ""

# Step 5: Training launch  
echo "📋 STEP 5: Launch Training (2 minutes)"
echo "-------------------------------------"
echo "🚀 Demo Training (5+ pets):"
echo "cd /Users/medan/Downloads/PetPlantr/backend/datasets"
echo "modal run enhanced_shape_mvd_training.py --demo"
echo ""
echo "🎯 Tier A Fast (10+ pets):"
echo "modal run enhanced_shape_mvd_training.py --tier-a-fast"
echo ""
echo "🏆 Tier A Full (20+ pets):"
echo "modal run enhanced_shape_mvd_training.py --tier-a-full"
echo ""

# Step 6: Photo quality guide
echo "📋 STEP 6: Photo Quality Checklist"
echo "---------------------------------"
cat > /tmp/photo_guide.txt << 'EOF'
📸 RAPID PHOTO COLLECTION GUIDE
==============================

🎯 MINIMUM VIABLE: 5 pets × 4 views = 20 photos
🏆 TIER A QUALITY: 10+ pets × 4 views = 40+ photos

📋 PER PET CHECKLIST:
□ front.jpg - Pet facing camera, centered
□ left.jpg  - Pet profile, left side visible  
□ right.jpg - Pet profile, right side visible
□ back.jpg  - Pet from behind, tail/rear visible

💡 QUICK TIPS:
• Plain background (white wall/sheet)
• Good lighting (window light)
• Pet sitting/standing still
• 1024x1024+ resolution
• Sharp focus on pet

⚡ PRIORITY PETS (easy subjects):
1. pet_001_golden_retriever - friendly, poses well
2. pet_002_labrador - calm, photogenic  
3. pet_005_beagle - medium size, cooperative
4. pet_007_british_shorthair - sits still
5. pet_008_persian_cat - fluffy, distinctive

🏃‍♂️ SPEED TIPS:
• Use burst mode for moving pets
• Treats for attention/positioning
• Multiple sessions if needed
• Phone camera is fine (good lighting)
EOF

echo "📄 Created photo guide: /tmp/photo_guide.txt"
echo ""

echo "🎯 DEPLOYMENT TIMELINE:"
echo "====================="
echo "⏰ Now     : Oxford dataset ✅"
echo "⏰ +30min  : 5 proprietary pet photos"
echo "⏰ +35min  : Process & upload datasets"
echo "⏰ +40min  : Launch demo training"
echo "⏰ +60min  : Training completes (estimated)"
echo "⏰ +65min  : Deploy to production"
echo ""
echo "🚀 NEXT IMMEDIATE ACTION:"
echo "Take photos of 5 pets using the guide above!"
echo ""
echo "✅ Setup complete - Ready for photo collection!"
