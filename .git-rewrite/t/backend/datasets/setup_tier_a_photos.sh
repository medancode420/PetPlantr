#!/bin/bash
# Quick setup for Tier A proprietary multi-view photo collection

echo "🎯 Setting up Tier A Multi-view Photo Collection"
echo "=============================================="

# Base directories
DATASET_ROOT="/Users/medan/Desktop/PetPlantr_Dataset"
RAW_DIR="$DATASET_ROOT/proprietary_raw"
PROCESSED_DIR="$DATASET_ROOT/proprietary_multiview"

# Create directory structure
mkdir -p "$RAW_DIR"
mkdir -p "$PROCESSED_DIR"

echo "📁 Created directories:"
echo "   Raw photos: $RAW_DIR"
echo "   Processed: $PROCESSED_DIR"

# Create sample pet directories for immediate use
priority_pets=(
    "pet_001_golden_retriever"
    "pet_002_labrador"
    "pet_003_german_shepherd"
    "pet_004_bulldog" 
    "pet_005_beagle"
    "pet_006_pug"
    "pet_007_british_shorthair"
    "pet_008_persian_cat"
    "pet_009_maine_coon"
    "pet_010_ragdoll"
)

echo ""
echo "📸 Creating sample pet directories:"
for pet in "${priority_pets[@]}"; do
    mkdir -p "$RAW_DIR/$pet"
    echo "   📁 $pet/"
    echo "      (place front.jpg, left.jpg, right.jpg, back.jpg here)"
done

# Create quick photo checklist
cat > "$RAW_DIR/PHOTO_CHECKLIST.md" << 'EOF'
# 🎯 Tier A Multi-view Photo Checklist

## ⚡ URGENT: 30 pets × 4 views needed ASAP

### 📸 Photo Requirements (CRITICAL)
- [ ] **Resolution**: 1024×1024 minimum (higher preferred)
- [ ] **Background**: White/neutral seamless
- [ ] **Lighting**: Soft, even lighting (no harsh shadows)
- [ ] **Focus**: Sharp, no motion blur
- [ ] **Views**: Exactly 4 per pet

### 🎭 Required Views
1. **front.jpg**: Pet facing camera directly
2. **left.jpg**: 90° left profile 
3. **right.jpg**: 90° right profile
4. **back.jpg**: Rear view

### 📱 Quick Mobile Setup
- Use portrait mode if available
- Consistent distance (3-4 feet)
- Same height for all views
- Take 3-5 shots per view, keep best

### 🏆 Priority Pets (photograph first)
1. Golden Retriever
2. Labrador 
3. German Shepherd
4. Bulldog
5. Beagle
6. Pug
7. British Shorthair
8. Persian Cat
9. Maine Coon
10. Ragdoll

### 🚀 Processing Command
```bash
python3 process_proprietary_photos.py
```

### ⏱️ Timeline
- **TODAY**: Photograph 10 priority pets
- **TONIGHT**: Process and upload to S3
- **TOMORROW**: Launch full Shape-MVD training
EOF

echo ""
echo "📋 Created photo checklist: $RAW_DIR/PHOTO_CHECKLIST.md"
echo ""
echo "🎯 IMMEDIATE ACTIONS:"
echo "1. 📸 Photograph pets using the checklist"
echo "2. 📁 Place photos in $RAW_DIR/pet_XXX_name/ directories"
echo "3. 🔄 Run: python3 process_proprietary_photos.py"
echo "4. ☁️  Upload: aws s3 sync $PROCESSED_DIR s3://petplantr-dataset/proprietary/multiview/"
echo ""
echo "⚡ Priority: Get 30 complete pet sets for Tier A quality!"

# Create quick processing script
cat > "$DATASET_ROOT/process_and_upload.sh" << 'EOF'
#!/bin/bash
echo "🔄 Processing and uploading Tier A photos..."

cd /Users/medan/Downloads/PetPlantr/backend/datasets
python3 process_proprietary_photos.py

if [ $? -eq 0 ]; then
    echo "📤 Uploading to S3..."
    aws s3 sync /Users/medan/Desktop/PetPlantr_Dataset/proprietary_multiview \
                s3://petplantr-dataset/proprietary/multiview/ --acl private
    echo "✅ Upload complete!"
else
    echo "❌ Processing failed"
fi
EOF

chmod +x "$DATASET_ROOT/process_and_upload.sh"

echo "🚀 Created processing script: $DATASET_ROOT/process_and_upload.sh"
echo ""
echo "✅ Tier A photo collection setup complete!"
