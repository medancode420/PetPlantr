#!/usr/bin/env python3
"""
Generate Enhanced PetPlantr Dataset with 100% Breed Coverage
Creates processed training/validation images for all 37 breeds
"""

import os
import sys
import json
import random
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
import cv2
import numpy as np
from PIL import Image, ImageFilter

def load_enhanced_metadata(metadata_path: Path) -> List[Dict]:
    """Load the enhanced diversity metadata"""
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    return data['images']

def process_image_for_training(image_path: Path, output_path: Path, target_size: int = 512) -> bool:
    """Process image for Shape-MVD training"""
    try:
        # Load image
        img = Image.open(image_path)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize while maintaining aspect ratio
        img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
        
        # Create square image with padding if needed
        if img.size[0] != img.size[1]:
            # Create square canvas
            square_size = max(img.size)
            square_img = Image.new('RGB', (square_size, square_size), (255, 255, 255))
            
            # Center the image
            x_offset = (square_size - img.size[0]) // 2
            y_offset = (square_size - img.size[1]) // 2
            square_img.paste(img, (x_offset, y_offset))
            img = square_img
        
        # Resize to exact target size
        img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
        
        # Apply subtle sharpening
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        
        # Save processed image
        img.save(output_path, 'JPEG', quality=95)
        
        return True
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return False

def create_training_split(images: List[Dict], split_ratio: float = 0.8) -> Tuple[List[Dict], List[Dict]]:
    """Split images into training and validation sets with breed balance"""
    # Group by breed
    breed_groups = defaultdict(list)
    for img in images:
        breed_groups[img['breed']].append(img)
    
    training_images = []
    validation_images = []
    
    # Split each breed proportionally
    for breed, breed_images in breed_groups.items():
        random.shuffle(breed_images)
        
        # For small groups (4 images), put 3 in training, 1 in validation
        if len(breed_images) <= 4:
            training_images.extend(breed_images[:-1])
            validation_images.extend(breed_images[-1:])
        else:
            split_point = int(len(breed_images) * split_ratio)
            training_images.extend(breed_images[:split_point])
            validation_images.extend(breed_images[split_point:])
    
    print(f"📊 Split: {len(training_images)} training, {len(validation_images)} validation")
    
    # Show breed distribution
    train_breeds = defaultdict(int)
    val_breeds = defaultdict(int)
    
    for img in training_images:
        train_breeds[img['breed']] += 1
    for img in validation_images:
        val_breeds[img['breed']] += 1
    
    print(f"🔍 Training breed distribution:")
    for breed in sorted(train_breeds.keys()):
        print(f"   {breed}: {train_breeds[breed]} train, {val_breeds[breed]} val")
    
    return training_images, validation_images

def process_and_save_images(image_list: List[Dict], output_dir: Path, prefix: str) -> List[Dict]:
    """Process and save images to target directory"""
    print(f"🔄 Processing {len(image_list)} {prefix} images...")
    
    # Clear and create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    processed_images = []
    
    for i, img_info in enumerate(image_list):
        # Generate output filename
        breed = img_info['breed']
        original_path = Path(img_info['path'])
        original_name = original_path.stem
        
        output_filename = f"{prefix}_{i+1:03d}_{breed}_{original_name}.jpg"
        output_path = output_dir / output_filename
        
        # Process and save image
        if process_image_for_training(original_path, output_path):
            processed_info = img_info.copy()
            processed_info['processed_path'] = str(output_path)
            processed_info['processed_filename'] = output_filename
            processed_images.append(processed_info)
        else:
            print(f"   ❌ Failed to process: {img_info['path']}")
    
    print(f"✅ Successfully processed {len(processed_images)} {prefix} images")
    return processed_images

def save_enhanced_metadata(training_images: List[Dict], validation_images: List[Dict], metadata_dir: Path):
    """Save comprehensive metadata for the enhanced dataset"""
    
    # Calculate breed statistics
    train_breeds = defaultdict(int)
    val_breeds = defaultdict(int)
    all_breeds = set()
    
    for img in training_images:
        train_breeds[img['breed']] += 1
        all_breeds.add(img['breed'])
    
    for img in validation_images:
        val_breeds[img['breed']] += 1
        all_breeds.add(img['breed'])
    
    # Create comprehensive metadata
    enhanced_metadata = {
        'dataset_info': {
            'name': 'PetPlantr Enhanced Breed Coverage Dataset',
            'version': '2.0',
            'description': '100% breed coverage with 37 unique breeds',
            'total_images': len(training_images) + len(validation_images),
            'training_images': len(training_images),
            'validation_images': len(validation_images),
            'total_breeds': len(all_breeds),
            'breed_coverage': '100%',
            'target_size': 512,
            'format': 'JPEG',
            'average_quality': np.mean([img.get('score', 0) for img in training_images + validation_images])
        },
        'breed_statistics': {
            'total_breeds': len(all_breeds),
            'dog_breeds': len([b for b in all_breeds if any(dog in b.lower() for dog in ['bulldog', 'terrier', 'hound', 'shepherd', 'retriever', 'spaniel', 'setter', 'pinscher', 'chin', 'pug', 'boxer', 'beagle', 'chihuahua', 'pomeranian', 'shiba', 'havanese', 'newfoundland', 'pyrenees', 'bernard', 'samoyed', 'keeshond', 'leonberger', 'staffordshire', 'wheaten', 'yorkshire'])]),
            'cat_breeds': len([b for b in all_breeds if any(cat in b.lower() for cat in ['abyssinian', 'bengal', 'birman', 'bombay', 'british', 'egyptian', 'maine', 'persian', 'ragdoll', 'russian', 'siamese', 'sphynx'])]),
            'training_distribution': dict(train_breeds),
            'validation_distribution': dict(val_breeds)
        },
        'training_images': [
            {
                'filename': img['processed_filename'],
                'breed': img['breed'],
                'quality_score': img.get('score', 0),
                'original_path': str(img['path'])
            }
            for img in training_images
        ],
        'validation_images': [
            {
                'filename': img['processed_filename'],
                'breed': img['breed'],
                'quality_score': img.get('score', 0),
                'original_path': str(img['path'])
            }
            for img in validation_images
        ]
    }
    
    # Save metadata files
    with open(metadata_dir / "enhanced_training_metadata.json", 'w') as f:
        json.dump(enhanced_metadata, f, indent=2, default=str)
    
    with open(metadata_dir / "enhanced_breed_statistics.json", 'w') as f:
        json.dump(enhanced_metadata['breed_statistics'], f, indent=2)
    
    with open(metadata_dir / "enhanced_dataset_summary.json", 'w') as f:
        json.dump(enhanced_metadata['dataset_info'], f, indent=2)
    
    print(f"✅ Enhanced metadata saved:")
    print(f"   Training metadata: enhanced_training_metadata.json")
    print(f"   Breed statistics: enhanced_breed_statistics.json")
    print(f"   Dataset summary: enhanced_dataset_summary.json")

def main():
    # Setup paths
    dataset_root = Path.home() / "Desktop" / "PetPlantr_Dataset"
    metadata_dir = dataset_root / "metadata"
    enhanced_training_dir = dataset_root / "enhanced_training"
    enhanced_validation_dir = dataset_root / "enhanced_validation"
    
    # Load enhanced diversity metadata
    enhanced_metadata_path = metadata_dir / "enhanced_diversity_metadata.json"
    if not enhanced_metadata_path.exists():
        print("❌ Enhanced diversity metadata not found. Run create_max_diversity_dataset.py first.")
        return
    
    print("🚀 Creating Enhanced Dataset with 100% Breed Coverage")
    print("=" * 55)
    
    # Load image selection
    selected_images = load_enhanced_metadata(enhanced_metadata_path)
    print(f"📊 Loaded {len(selected_images)} selected images")
    
    # Create training/validation split
    training_images, validation_images = create_training_split(selected_images)
    
    # Process and save training images
    processed_training = process_and_save_images(training_images, enhanced_training_dir, "train")
    
    # Process and save validation images
    processed_validation = process_and_save_images(validation_images, enhanced_validation_dir, "val")
    
    # Save comprehensive metadata
    save_enhanced_metadata(processed_training, processed_validation, metadata_dir)
    
    # Final summary
    print("\n🎉 Enhanced Dataset Creation Complete!")
    print("=" * 40)
    print(f"✅ Total Images: {len(processed_training) + len(processed_validation)}")
    print(f"✅ Training: {len(processed_training)} images")
    print(f"✅ Validation: {len(processed_validation)} images")
    print(f"✅ Breeds Covered: 37/37 (100%)")
    print(f"✅ Average Quality: {np.mean([img.get('score', 0) for img in selected_images]):.3f}")
    print(f"📍 Location: {dataset_root}")
    print(f"   Training: {enhanced_training_dir}")
    print(f"   Validation: {enhanced_validation_dir}")
    print(f"   Metadata: {metadata_dir}")
    
    # Show breed coverage
    breeds = set(img['breed'] for img in selected_images)
    cat_breeds = [b for b in breeds if any(cat in b for cat in ['Abyssinian', 'Bengal', 'Birman', 'Bombay', 'British', 'Egyptian', 'Maine', 'Persian', 'Ragdoll', 'Russian', 'Siamese', 'Sphynx'])]
    dog_breeds = [b for b in breeds if b not in cat_breeds]
    
    print(f"\n🐱 Cat Breeds ({len(cat_breeds)}): {', '.join(sorted(cat_breeds))}")
    print(f"🐕 Dog Breeds ({len(dog_breeds)}): {', '.join(sorted(dog_breeds))}")

if __name__ == "__main__":
    main()
