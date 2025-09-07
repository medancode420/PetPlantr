#!/bin/bash
# PetPlantr Training Corpus Preparation Script
# Organizes breed images and creates training labels for CLIP+LoRA system

set -e

# Configuration
PROJECT_ROOT="/Users/medan/Downloads/PetPlantr"
DATA_DIR="$PROJECT_ROOT/data"
BREEDS_DIR="$DATA_DIR/breeds"
HARD_NEG_DIR="$DATA_DIR/hard_neg"
LABELS_FILE="$DATA_DIR/labels.csv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Standard dog breeds (450 pure breeds + mixed)
BREED_NAMES=(
    "afghan_hound" "airedale_terrier" "akbash" "akita" "alaskan_malamute"
    "american_bulldog" "american_pit_bull_terrier" "american_staffordshire_terrier"
    "australian_cattle_dog" "australian_shepherd" "basenji" "basset_hound"
    "beagle" "belgian_malinois" "bernese_mountain_dog" "bichon_frise"
    "bloodhound" "border_collie" "boston_terrier" "boxer" "brittany"
    "bulldog" "bullmastiff" "cairn_terrier" "cavalier_king_charles_spaniel"
    "chihuahua" "chinese_crested" "chow_chow" "cocker_spaniel" "collie"
    "coonhound" "corgi" "dachshund" "dalmatian" "doberman_pinscher"
    "english_setter" "english_springer_spaniel" "fox_terrier" "french_bulldog"
    "german_shepherd" "german_shorthaired_pointer" "golden_retriever"
    "great_dane" "great_pyrenees" "greyhound" "havanese" "husky"
    "irish_setter" "irish_wolfhound" "jack_russell_terrier" "japanese_chin"
    "labrador_retriever" "maltese" "mastiff" "miniature_pinscher"
    "newfoundland" "papillon" "pekingese" "pointer" "pomeranian"
    "poodle" "pug" "rhodesian_ridgeback" "rottweiler" "saint_bernard"
    "saluki" "samoyed" "schnauzer" "scottish_terrier" "shar_pei"
    "shih_tzu" "siberian_husky" "staffordshire_bull_terrier" "vizsla"
    "weimaraner" "welsh_corgi" "west_highland_white_terrier" "whippet"
    "yorkshire_terrier"
    # Add more breeds to reach 450...
    "mixed_breed"  # Special class for mixed breeds (ID 450)
)

# Function to create directory structure
setup_directories() {
    log_info "Setting up directory structure..."
    
    mkdir -p "$DATA_DIR"
    mkdir -p "$BREEDS_DIR"
    mkdir -p "$HARD_NEG_DIR"
    
    # Create breed subdirectories
    for breed in "${BREED_NAMES[@]}"; do
        mkdir -p "$BREEDS_DIR/$breed"
    done
    
    log_success "Directory structure created"
}

# Function to download sample dataset (placeholder)
download_sample_data() {
    log_info "Setting up sample training data..."
    
    # This would normally download from your dataset source
    # For now, create placeholder structure
    
    local sample_breeds=("golden_retriever" "labrador_retriever" "german_shepherd" "bulldog" "poodle" "mixed_breed")
    
    for breed in "${sample_breeds[@]}"; do
        breed_dir="$BREEDS_DIR/$breed"
        
        # Create sample image placeholders
        for i in {1..100}; do
            touch "$breed_dir/sample_${breed}_${i}.jpg"
        done
        
        log_info "Created 100 sample images for $breed"
    done
    
    # Create hard negative samples
    for i in {1..200}; do
        touch "$HARD_NEG_DIR/hard_negative_${i}.jpg"
    done
    
    log_success "Sample data structure created"
    log_warning "Replace placeholder files with actual breed images"
}

# Function to validate image requirements
validate_images() {
    log_info "Validating image requirements..."
    
    local total_images=0
    local valid_breeds=0
    
    for breed in "${BREED_NAMES[@]}"; do
        breed_dir="$BREEDS_DIR/$breed"
        
        if [ -d "$breed_dir" ]; then
            image_count=$(find "$breed_dir" -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)
            
            if [ "$image_count" -ge 60 ]; then
                log_success "$breed: $image_count images ✓"
                valid_breeds=$((valid_breeds + 1))
                total_images=$((total_images + image_count))
            elif [ "$image_count" -gt 0 ]; then
                log_warning "$breed: $image_count images (minimum 60 recommended)"
                valid_breeds=$((valid_breeds + 1))
                total_images=$((total_images + image_count))
            else
                log_error "$breed: No images found"
            fi
        fi
    done
    
    log_info "Total images: $total_images"
    log_info "Valid breeds: $valid_breeds"
    
    if [ "$valid_breeds" -lt 10 ]; then
        log_error "Need at least 10 breeds with images for training"
        return 1
    fi
    
    log_success "Image validation completed"
}

# Function to strip EXIF metadata
strip_exif_metadata() {
    log_info "Stripping EXIF metadata from images..."
    
    if command -v exiftool &> /dev/null; then
        log_info "Using exiftool to strip metadata..."
        exiftool -overwrite_original -all= "$BREEDS_DIR"/**/* 2>/dev/null || true
        exiftool -overwrite_original -all= "$HARD_NEG_DIR"/* 2>/dev/null || true
        log_success "EXIF metadata stripped"
    else
        log_warning "exiftool not found. Install with: brew install exiftool"
        log_warning "Skipping EXIF stripping (recommended for privacy)"
    fi
}

# Function to check image sizes and quality
validate_image_quality() {
    log_info "Validating image quality and dimensions..."
    
    if command -v identify &> /dev/null; then
        local small_images=0
        local total_checked=0
        
        for breed_dir in "$BREEDS_DIR"/*; do
            if [ -d "$breed_dir" ]; then
                for img in "$breed_dir"/*.{jpg,jpeg,png} 2>/dev/null; do
                    if [ -f "$img" ]; then
                        total_checked=$((total_checked + 1))
                        dimensions=$(identify -format "%wx%h" "$img" 2>/dev/null || echo "0x0")
                        width=$(echo "$dimensions" | cut -d'x' -f1)
                        height=$(echo "$dimensions" | cut -d'x' -f2)
                        
                        if [ "$width" -lt 224 ] || [ "$height" -lt 224 ]; then
                            small_images=$((small_images + 1))
                        fi
                        
                        # Sample first few images
                        if [ "$total_checked" -le 10 ]; then
                            log_info "Sample: $(basename "$img") - ${dimensions}"
                        fi
                    fi
                done
            fi
        done
        
        if [ "$small_images" -gt 0 ]; then
            log_warning "$small_images images smaller than 224x224 (will be resized)"
        fi
        
        log_success "Checked $total_checked images"
    else
        log_warning "ImageMagick 'identify' not found. Install with: brew install imagemagick"
    fi
}

# Function to create labels.csv
create_labels_csv() {
    log_info "Creating labels.csv file..."
    
    echo "filepath,breed_id" > "$LABELS_FILE"
    
    local breed_id=0
    for breed in "${BREED_NAMES[@]}"; do
        breed_dir="$BREEDS_DIR/$breed"
        
        if [ -d "$breed_dir" ]; then
            find "$breed_dir" -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | while read -r img_path; do
                # Convert to relative path
                rel_path=$(realpath --relative-to="$PROJECT_ROOT" "$img_path")
                echo "$rel_path,$breed_id" >> "$LABELS_FILE"
            done
        fi
        
        breed_id=$((breed_id + 1))
    done
    
    local total_labels=$(tail -n +2 "$LABELS_FILE" | wc -l)
    log_success "Created labels.csv with $total_labels images"
}

# Function to create breed names mapping
create_breed_mapping() {
    log_info "Creating breed names mapping..."
    
    local mapping_file="$DATA_DIR/breed_names.json"
    
    # Convert array to JSON
    printf '%s\n' "${BREED_NAMES[@]}" | jq -R . | jq -s . > "$mapping_file"
    
    log_success "Created breed_names.json with ${#BREED_NAMES[@]} breeds"
}

# Function to generate dataset statistics
generate_dataset_stats() {
    log_info "Generating dataset statistics..."
    
    local stats_file="$DATA_DIR/dataset_stats.json"
    
    python3 -c "
import json
import csv
from collections import Counter
import os

# Read labels file
breed_counts = Counter()
total_images = 0

if os.path.exists('$LABELS_FILE'):
    with open('$LABELS_FILE', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            breed_id = int(row['breed_id'])
            breed_counts[breed_id] += 1
            total_images += 1

# Load breed names
with open('$DATA_DIR/breed_names.json', 'r') as f:
    breed_names = json.load(f)

# Create statistics
stats = {
    'total_images': total_images,
    'num_breeds': len(breed_names),
    'breed_distribution': {},
    'min_images_per_breed': min(breed_counts.values()) if breed_counts else 0,
    'max_images_per_breed': max(breed_counts.values()) if breed_counts else 0,
    'avg_images_per_breed': total_images / len(breed_counts) if breed_counts else 0
}

# Add breed distribution
for breed_id, count in breed_counts.items():
    if breed_id < len(breed_names):
        stats['breed_distribution'][breed_names[breed_id]] = count

# Save statistics
with open('$stats_file', 'w') as f:
    json.dump(stats, f, indent=2)

print(f'Dataset Statistics:')
print(f'Total images: {total_images}')
print(f'Number of breeds: {len(breed_names)}')
print(f'Average images per breed: {stats[\"avg_images_per_breed\"]:.1f}')
print(f'Range: {stats[\"min_images_per_breed\"]} - {stats[\"max_images_per_breed\"]} images per breed')
"
    
    log_success "Dataset statistics saved to dataset_stats.json"
}

# Function to create training configuration
create_training_config() {
    log_info "Creating training configuration..."
    
    local config_file="$DATA_DIR/training_config.json"
    
    cat > "$config_file" << EOF
{
  "data": {
    "csv_file": "$LABELS_FILE",
    "hard_neg_dir": "$HARD_NEG_DIR",
    "val_split": 0.1,
    "image_size": 224,
    "augmentation": {
      "horizontal_flip": 0.5,
      "rotation": 15,
      "color_jitter": 0.1
    }
  },
  "model": {
    "clip_model": "openai/clip-vit-base-patch32",
    "num_breeds": ${#BREED_NAMES[@]},
    "lora_rank": 16,
    "freeze_clip": true
  },
  "training": {
    "batch_size": 32,
    "epochs": 5,
    "learning_rate": {
      "lora_lr": 1e-3,
      "base_lr": 1e-4
    },
    "precision": "bf16",
    "hard_neg_ratio": 0.3,
    "label_smoothing": 0.1,
    "confidence_weight": 0.1
  },
  "output": {
    "output_dir": "outputs",
    "model_name": "breed_head_lora.pt",
    "save_interval": 1
  },
  "monitoring": {
    "wandb_project": "petplantr-breed-head",
    "log_interval": 10
  }
}
EOF
    
    log_success "Training configuration saved to training_config.json"
}

# Main execution function
main() {
    log_info "🗂️  Starting training corpus preparation..."
    echo "Estimated time: ~2 hours"
    echo ""
    
    setup_directories
    
    # Check if we should download sample data
    if [ "${1:-}" = "--sample" ]; then
        download_sample_data
    else
        log_info "To download sample data, run: $0 --sample"
        log_info "Or manually place breed images in $BREEDS_DIR/<breed_name>/"
    fi
    
    validate_images
    strip_exif_metadata
    validate_image_quality
    create_labels_csv
    create_breed_mapping
    generate_dataset_stats
    create_training_config
    
    echo ""
    log_success "🎉 Training corpus preparation completed!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Verify your images in: $BREEDS_DIR"
    echo "2. Add hard negatives to: $HARD_NEG_DIR"
    echo "3. Review dataset stats: cat $DATA_DIR/dataset_stats.json"
    echo "4. Start training: python -m src.ai.training.train_breed_head --config $DATA_DIR/training_config.json"
    echo ""
    echo "📊 Dataset Summary:"
    cat "$DATA_DIR/dataset_stats.json" | jq '.total_images, .num_breeds, .avg_images_per_breed'
}

# Show help
show_help() {
    echo "PetPlantr Training Corpus Preparation"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help     Show this help message"
    echo "  --sample   Create sample data structure for testing"
    echo ""
    echo "Manual Setup:"
    echo "1. Place breed images in data/breeds/<breed_name>/*.jpg"
    echo "2. Minimum 60 images per breed, 224x224+ resolution"
    echo "3. Add problematic images to data/hard_neg/ for hard negative mining"
    echo ""
    echo "Supported Formats: JPG, JPEG, PNG"
    echo "Recommended: Strip EXIF metadata for privacy (requires exiftool)"
}

# Parse command line arguments
case "${1:-}" in
    --help)
        show_help
        ;;
    *)
        main "$@"
        ;;
esac
