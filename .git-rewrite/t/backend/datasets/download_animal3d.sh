#!/bin/bash
# Animal3D Dataset Integration for PetPlantr Multi-view Training
# Source: https://xujiacong.github.io/AnimalNeRF/

echo "🐕🐱 Animal3D Dataset Integration for PetPlantr"
echo "=============================================="

# Configuration
DATASET_ROOT="/Users/medan/Desktop/PetPlantr_Dataset"
ANIMAL3D_ROOT="$DATASET_ROOT/animal3d_subset"
S3_BUCKET="petplantr-dataset"

echo "📁 Dataset root: $DATASET_ROOT"
echo "📁 Animal3D target: $ANIMAL3D_ROOT"

# Create directories
mkdir -p "$ANIMAL3D_ROOT"/{dogs,cats,processing}

echo "🔄 Animal3D Dataset Download Instructions"
echo "========================================"
echo "📍 Visit: https://xujiacong.github.io/AnimalNeRF/"
echo "📋 Download sections needed:"
echo "   • Multi-view images (cats & dogs)"
echo "   • SMAL mesh annotations" 
echo "   • Camera parameters"
echo ""
echo "🎯 Priority species for PetPlantr:"
echo "   DOGS: Golden Retriever, Labrador, German Shepherd, Bulldog, Beagle, Pug"
echo "   CATS: British Shorthair, Persian, Maine Coon, Ragdoll, Siamese, Bengal"
echo ""
echo "📁 Extract files to:"
echo "   Dogs: $ANIMAL3D_ROOT/dogs/"
echo "   Cats: $ANIMAL3D_ROOT/cats/"
echo ""

# Create processing script for Animal3D data
cat > "$ANIMAL3D_ROOT/process_animal3d.py" << 'EOF'
#!/usr/bin/env python3
"""
Process Animal3D dataset for PetPlantr Shape-MVD training
Extracts multi-view images and prepares for S3 upload
"""

import os
import json
import shutil
from pathlib import Path
from PIL import Image
import cv2
import numpy as np

def process_animal3d_subset():
    """Process Animal3D images for PetPlantr training"""
    
    animal3d_root = Path("/Users/medan/Desktop/PetPlantr_Dataset/animal3d_subset")
    output_root = Path("/Users/medan/Desktop/PetPlantr_Dataset/processed/animal3d")
    
    output_root.mkdir(parents=True, exist_ok=True)
    
    print("🔄 Processing Animal3D subset...")
    
    # Target species for PetPlantr
    target_species = {
        'dogs': ['golden_retriever', 'labrador', 'german_shepherd', 'bulldog', 'beagle', 'pug'],
        'cats': ['british_shorthair', 'persian', 'maine_coon', 'ragdoll', 'siamese', 'bengal']
    }
    
    processed_count = 0
    
    for category in ['dogs', 'cats']:
        category_path = animal3d_root / category
        if not category_path.exists():
            print(f"⚠️  {category_path} not found. Download Animal3D data first.")
            continue
            
        for species in target_species[category]:
            species_path = category_path / species
            if species_path.exists():
                print(f"📸 Processing {species}...")
                
                # Find multi-view images
                for view_dir in species_path.glob("*/"):
                    if view_dir.is_dir():
                        processed_count += process_view_set(view_dir, output_root, species)
    
    print(f"✅ Processed {processed_count} multi-view sets from Animal3D")
    
    # Create metadata
    metadata = {
        "source": "Animal3D Dataset",
        "license": "CC-BY-NC 4.0",
        "url": "https://xujiacong.github.io/AnimalNeRF/",
        "processed_sets": processed_count,
        "target_resolution": 512,
        "categories": list(target_species.keys())
    }
    
    with open(output_root / "animal3d_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return processed_count

def process_view_set(view_dir, output_root, species):
    """Process a single multi-view set"""
    
    images = list(view_dir.glob("*.jpg")) + list(view_dir.glob("*.png"))
    if len(images) < 4:
        return 0  # Need at least 4 views
    
    # Create output directory
    set_name = f"{species}_{view_dir.name}"
    output_dir = output_root / set_name
    output_dir.mkdir(exist_ok=True)
    
    # Process images
    view_names = ['front', 'left', 'right', 'back']
    for i, img_path in enumerate(images[:4]):
        
        # Load and resize image
        img = Image.open(img_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to 512x512
        img = img.resize((512, 512), Image.Resampling.LANCZOS)
        
        # Save with standard view name
        output_path = output_dir / f"{view_names[i]}.jpg"
        img.save(output_path, 'JPEG', quality=95)
    
    return 1

if __name__ == "__main__":
    count = process_animal3d_subset()
    print(f"🎉 Animal3D processing complete: {count} multi-view sets")
EOF

chmod +x "$ANIMAL3D_ROOT/process_animal3d.py"

echo "📄 Created processing script: $ANIMAL3D_ROOT/process_animal3d.py"
echo ""
echo "🚀 Next Steps:"
echo "1. Download Animal3D dataset from https://xujiacong.github.io/AnimalNeRF/"
echo "2. Extract to $ANIMAL3D_ROOT/{dogs,cats}/"
echo "3. Run: python3 $ANIMAL3D_ROOT/process_animal3d.py"
echo "4. Upload processed data: aws s3 sync processed/animal3d s3://$S3_BUCKET/public/animal3d/"
echo ""
echo "⚡ This provides immediate multi-view data while you collect proprietary photos!"

# Make script executable
chmod +x "$DATASET_ROOT/download_animal3d.sh"
