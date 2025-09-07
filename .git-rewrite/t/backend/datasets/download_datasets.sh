#!/bin/bash

# PetPlantr Dataset Collection Script
# Downloads and prepares high-quality pet datasets for Shape-MVD training

set -e

echo "🐕🐱 PetPlantr Dataset Collection"
echo "================================"

# Configuration
DATASET_ROOT="$HOME/Desktop/PetPlantr_Dataset"
RAW_DIR="$DATASET_ROOT/raw"
PROCESSED_DIR="$DATASET_ROOT/processed"
TRAINING_DIR="$DATASET_ROOT/training"
VALIDATION_DIR="$DATASET_ROOT/validation"

# Dataset URLs and info
OXFORD_PETS_URL="https://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz"
STANFORD_DOGS_URL="https://vision.stanford.edu/aditya86/ImageNetDogs/images.tar"

# Check dependencies
echo "🔍 Checking dependencies..."
command -v wget >/dev/null 2>&1 || { echo "❌ wget is required but not installed"; exit 1; }
command -v tar >/dev/null 2>&1 || { echo "❌ tar is required but not installed"; exit 1; }
command -v unzip >/dev/null 2>&1 || { echo "❌ unzip is required but not installed"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 is required but not installed"; exit 1; }

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p "$RAW_DIR"
mkdir -p "$PROCESSED_DIR"
mkdir -p "$TRAINING_DIR"
mkdir -p "$VALIDATION_DIR"

echo "✅ Created directories:"
echo "   Raw: $RAW_DIR"
echo "   Processed: $PROCESSED_DIR"
echo "   Training: $TRAINING_DIR"
echo "   Validation: $VALIDATION_DIR"

# Function to download and extract datasets
download_oxford_pets() {
    echo ""
    echo "🎓 Downloading Oxford-IIIT Pet Dataset..."
    echo "Dataset: 7,400 images (dogs & cats)"
    echo "Resolution: 200-1,400px"
    echo "License: CC-BY-SA 4.0 (commercial OK with attribution)"
    echo "Size: ~1GB"
    
    if [ ! -f "$RAW_DIR/oxford_pets_downloaded" ]; then
        cd "$RAW_DIR"
        wget -O pets.tgz "$OXFORD_PETS_URL"
        tar -xzf pets.tgz
        
        # Clean up and organize
        if [ -d "images" ]; then
            mv images oxford_pets
            rm -f pets.tgz
            touch oxford_pets_downloaded
            echo "✅ Oxford-IIIT Pet dataset downloaded and extracted"
        else
            echo "❌ Failed to extract Oxford-IIIT Pet dataset"
            return 1
        fi
    else
        echo "✅ Oxford-IIIT Pet dataset already downloaded"
    fi
}

download_stanford_dogs() {
    echo ""
    echo "🎓 Downloading Stanford Dogs Dataset..."
    echo "Dataset: 20,580 images (120 dog breeds)"
    echo "Resolution: Variable"
    echo "License: Research use"
    echo "Size: ~760MB"
    
    if [ ! -f "$RAW_DIR/stanford_dogs_downloaded" ]; then
        cd "$RAW_DIR"
        wget "$STANFORD_DOGS_URL"
        tar -xf images.tar
        
        # Clean up and organize
        if [ -d "Images" ]; then
            mv Images stanford_dogs
            rm -f images.tar
            touch stanford_dogs_downloaded
            echo "✅ Stanford Dogs dataset downloaded and extracted"
        else
            echo "❌ Failed to extract Stanford Dogs dataset"
            return 1
        fi
    else
        echo "✅ Stanford Dogs dataset already downloaded"
    fi
}

download_afhq_kaggle() {
    echo ""
    echo "🎭 Downloading AFHQ Dataset (via Kaggle)..."
    echo "Dataset: Animal Faces HQ"
    echo "Resolution: 512x512px"
    echo "License: Custom (check Kaggle)"
    echo "Size: Variable"
    
    if command -v kaggle >/dev/null 2>&1; then
        if [ ! -f "$RAW_DIR/afhq_downloaded" ]; then
            cd "$RAW_DIR"
            kaggle datasets download -d dimensi0n/afhq-512
            unzip -q afhq-512.zip
            
            # Clean up and organize
            if [ -d "afhq" ] || [ -f "*.jpg" ] || [ -d "cat" ] || [ -d "dog" ]; then
                mkdir -p afhq
                mv cat dog wild afhq/ 2>/dev/null || true
                mv *.jpg afhq/ 2>/dev/null || true
                rm -f afhq-512.zip
                touch afhq_downloaded
                echo "✅ AFHQ dataset downloaded and extracted"
            else
                echo "❌ Failed to extract AFHQ dataset"
                return 1
            fi
        else
            echo "✅ AFHQ dataset already downloaded"
        fi
    else
        echo "⚠️  Kaggle CLI not installed - skipping AFHQ dataset"
        echo "   Install with: pip install kaggle"
        echo "   Configure with: kaggle config"
    fi
}

# Function to analyze downloaded datasets
analyze_datasets() {
    echo ""
    echo "📊 Analyzing downloaded datasets..."
    
    if [ -d "$RAW_DIR/oxford_pets" ]; then
        oxford_count=$(find "$RAW_DIR/oxford_pets" -name "*.jpg" -o -name "*.png" | wc -l)
        echo "   Oxford-IIIT Pets: $oxford_count images"
    fi
    
    if [ -d "$RAW_DIR/stanford_dogs" ]; then
        stanford_count=$(find "$RAW_DIR/stanford_dogs" -name "*.jpg" -o -name "*.png" | wc -l)
        echo "   Stanford Dogs: $stanford_count images"
    fi
    
    if [ -d "$RAW_DIR/afhq" ]; then
        afhq_count=$(find "$RAW_DIR/afhq" -name "*.jpg" -o -name "*.png" | wc -l)
        echo "   AFHQ: $afhq_count images"
    fi
    
    total_count=$(find "$RAW_DIR" -name "*.jpg" -o -name "*.png" | wc -l)
    echo "   Total: $total_count images"
}

# Function to check dataset licenses and attribution
show_license_info() {
    echo ""
    echo "📜 Dataset Licenses & Attribution"
    echo "================================="
    echo ""
    echo "📚 Oxford-IIIT Pet Dataset:"
    echo "   License: CC-BY-SA 4.0"
    echo "   Commercial Use: ✅ OK with attribution"
    echo "   Attribution: O. M. Parkhi et al. 'Cats and dogs.' IEEE CVPR, 2012."
    echo "   URL: https://www.robots.ox.ac.uk/~vgg/data/pets/"
    echo ""
    echo "📚 Stanford Dogs Dataset:"
    echo "   License: Research use"
    echo "   Commercial Use: ⚠️  Check with Stanford"
    echo "   Citation: Aditya Khosla et al. 'Novel dataset for FGVC.' CVPR Workshop, 2011."
    echo "   URL: http://vision.stanford.edu/aditya86/ImageNetDogs/"
    echo ""
    echo "📚 AFHQ Dataset:"
    echo "   License: Custom (check Kaggle page)"
    echo "   Commercial Use: ⚠️  Review license terms"
    echo "   Citation: Yunjey Choi et al. 'StarGAN v2.' CVPR, 2020."
    echo "   URL: https://www.kaggle.com/datasets/dimensi0n/afhq-512"
    echo ""
}

# Main execution
main() {
    echo "🎯 Target: High-quality pet images for Shape-MVD training"
    echo "📍 Dataset location: $DATASET_ROOT"
    echo ""
    
    # Download datasets
    download_oxford_pets
    download_stanford_dogs
    download_afhq_kaggle
    
    # Analyze what we got
    analyze_datasets
    
    # Show license information
    show_license_info
    
    echo ""
    echo "🎉 Dataset Collection Complete!"
    echo "==============================="
    echo ""
    echo "📊 Summary:"
    total_images=$(find "$RAW_DIR" -name "*.jpg" -o -name "*.png" 2>/dev/null | wc -l)
    total_size=$(du -sh "$RAW_DIR" 2>/dev/null | cut -f1)
    echo "   Total Images: $total_images"
    echo "   Total Size: $total_size"
    echo "   Location: $RAW_DIR"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Run dataset preprocessing script"
    echo "2. Filter and curate images for Shape-MVD training"
    echo "3. Create training/validation splits"
    echo "4. Upload curated dataset for Modal training"
    echo ""
    echo "💡 Recommended for Shape-MVD training:"
    echo "   • Use 120 high-quality, diverse pet images"
    echo "   • Focus on clear facial features and good lighting"
    echo "   • Include various breeds, angles, and expressions"
    echo "   • Ensure commercial licensing compliance"
}

# Run main function
main
