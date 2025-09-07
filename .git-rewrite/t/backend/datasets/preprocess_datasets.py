#!/Users/medan/.pyenv/versions/3.12.3/bin/python
"""
PetPlantr Dataset Preprocessing Script
Prepares high-quality pet images for Shape-MVD training

This script:
1. Filters downloaded datasets for quality
2. Extracts the best 120 images for training
3. Preprocesses images (resize, normalize, face detection)
4. Creates training/validation splits
5. Generates metadata for Modal training
"""

import os
import sys
import json
import shutil
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import cv2
import numpy as np
from PIL import Image, ImageFilter
import argparse

def setup_directories(base_path: str) -> Dict[str, Path]:
    """Create directory structure for processed datasets"""
    base = Path(base_path)
    dirs = {
        'raw': base / 'raw',
        'processed': base / 'processed',
        'training': base / 'training',
        'validation': base / 'validation',
        'metadata': base / 'metadata'
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return dirs

def assess_image_quality(image_path: Path) -> Dict[str, float]:
    """Assess image quality for Shape-MVD training suitability"""
    try:
        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            return {'score': 0.0, 'error': 'Failed to load image'}
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate quality metrics
        metrics = {}
        
        # 1. Sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        metrics['sharpness'] = min(laplacian_var / 1000, 1.0)  # Normalize
        
        # 2. Brightness (avoid too dark/bright)
        brightness = np.mean(gray) / 255.0
        metrics['brightness'] = 1.0 - abs(brightness - 0.5) * 2  # Optimal around 0.5
        
        # 3. Contrast
        contrast = gray.std() / 255.0
        metrics['contrast'] = min(contrast * 2, 1.0)  # Normalize
        
        # 4. Size score (prefer larger images)
        h, w = img.shape[:2]
        size_score = min((h * w) / (512 * 512), 1.0)  # Prefer >= 512x512
        metrics['size'] = size_score
        
        # 5. Face detection (prefer images with clear faces)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        face_score = min(len(faces) * 0.5, 1.0)  # Bonus for detected faces
        metrics['face_detection'] = face_score
        
        # Calculate overall score
        weights = {
            'sharpness': 0.3,
            'brightness': 0.2, 
            'contrast': 0.2,
            'size': 0.2,
            'face_detection': 0.1
        }
        
        overall_score = sum(metrics[key] * weights[key] for key in weights)
        metrics['score'] = overall_score
        
        return metrics
        
    except Exception as e:
        return {'score': 0.0, 'error': str(e)}

def detect_breed_from_filename(filename: str) -> Optional[str]:
    """Extract breed information from filename if available"""
    filename_lower = filename.lower()
    
    # Common breed patterns in dataset filenames
    breed_patterns = {
        'golden_retriever': ['golden', 'retriever'],
        'labrador': ['labrador', 'lab'],
        'german_shepherd': ['german', 'shepherd'],
        'bulldog': ['bulldog', 'bull_dog'],
        'poodle': ['poodle'],
        'husky': ['husky', 'siberian'],
        'beagle': ['beagle'],
        'dachshund': ['dachshund', 'doxie'],
        'chihuahua': ['chihuahua'],
        'border_collie': ['border', 'collie'],
        'persian_cat': ['persian'],
        'siamese_cat': ['siamese'],
        'maine_coon': ['maine', 'coon'],
        'ragdoll': ['ragdoll'],
        'british_shorthair': ['british', 'shorthair']
    }
    
    for breed, patterns in breed_patterns.items():
        if all(pattern in filename_lower for pattern in patterns):
            return breed
        if any(pattern in filename_lower for pattern in patterns):
            return breed
    
    # Default classification
    if any(word in filename_lower for word in ['cat', 'kitten', 'feline']):
        return 'cat'
    elif any(word in filename_lower for word in ['dog', 'puppy', 'canine']):
        return 'dog'
    
    return 'unknown'

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

def collect_and_filter_images(dirs: Dict[str, Path], target_count: int = 120) -> List[Dict]:
    """Collect images from all datasets and filter for best quality"""
    print("🔍 Scanning downloaded datasets...")
    
    # Collect all images
    all_images = []
    
    # Scan Oxford Pets
    oxford_dir = dirs['raw'] / 'oxford_pets'
    if oxford_dir.exists():
        print(f"   Scanning Oxford-IIIT Pets: {oxford_dir}")
        for img_path in oxford_dir.glob('*.jpg'):
            all_images.append({
                'path': img_path,
                'dataset': 'oxford_pets',
                'breed': detect_breed_from_filename(img_path.name)
            })
    
    # Scan Stanford Dogs
    stanford_dir = dirs['raw'] / 'stanford_dogs'
    if stanford_dir.exists():
        print(f"   Scanning Stanford Dogs: {stanford_dir}")
        for breed_dir in stanford_dir.iterdir():
            if breed_dir.is_dir():
                for img_path in breed_dir.glob('*.jpg'):
                    all_images.append({
                        'path': img_path,
                        'dataset': 'stanford_dogs',
                        'breed': breed_dir.name.lower().replace('-', '_')
                    })
    
    # Scan AFHQ
    afhq_dir = dirs['raw'] / 'afhq'
    if afhq_dir.exists():
        print(f"   Scanning AFHQ: {afhq_dir}")
        for animal_dir in ['cat', 'dog']:
            animal_path = afhq_dir / animal_dir
            if animal_path.exists():
                for img_path in animal_path.glob('*.jpg'):
                    all_images.append({
                        'path': img_path,
                        'dataset': 'afhq',
                        'breed': animal_dir
                    })
    
    print(f"✅ Found {len(all_images)} total images")
    
    # Assess quality for all images
    print("📊 Assessing image quality...")
    for i, img_info in enumerate(all_images):
        if i % 100 == 0:
            print(f"   Progress: {i}/{len(all_images)}")
        
        quality = assess_image_quality(img_info['path'])
        img_info.update(quality)
    
    # Filter out failed images
    valid_images = [img for img in all_images if img.get('score', 0) > 0.1]
    print(f"✅ {len(valid_images)} images passed quality filter")
    
    # Sort by quality score
    valid_images.sort(key=lambda x: x['score'], reverse=True)
    
    # Ensure breed diversity in top selections
    selected_images = []
    breed_counts = {}
    max_per_breed = max(10, target_count // 10)  # At least 10 different breeds
    
    for img_info in valid_images:
        breed = img_info['breed']
        
        # Limit images per breed for diversity
        if breed_counts.get(breed, 0) < max_per_breed:
            selected_images.append(img_info)
            breed_counts[breed] = breed_counts.get(breed, 0) + 1
            
            if len(selected_images) >= target_count:
                break
    
    print(f"✅ Selected {len(selected_images)} diverse, high-quality images")
    print(f"   Breed distribution: {dict(breed_counts)}")
    
    return selected_images

def create_training_split(selected_images: List[Dict], split_ratio: float = 0.8) -> Tuple[List[Dict], List[Dict]]:
    """Split selected images into training and validation sets"""
    # Shuffle for random split
    random.shuffle(selected_images)
    
    split_point = int(len(selected_images) * split_ratio)
    training_images = selected_images[:split_point]
    validation_images = selected_images[split_point:]
    
    print(f"📊 Split: {len(training_images)} training, {len(validation_images)} validation")
    
    return training_images, validation_images

def process_and_save_images(image_list: List[Dict], output_dir: Path, prefix: str) -> List[Dict]:
    """Process and save images to target directory"""
    print(f"🔄 Processing {len(image_list)} {prefix} images...")
    
    processed_images = []
    
    for i, img_info in enumerate(image_list):
        # Generate output filename
        breed = img_info['breed']
        dataset = img_info['dataset']
        original_name = img_info['path'].stem
        
        output_filename = f"{prefix}_{i+1:03d}_{breed}_{dataset}_{original_name}.jpg"
        output_path = output_dir / output_filename
        
        # Process and save image
        if process_image_for_training(img_info['path'], output_path):
            processed_info = img_info.copy()
            processed_info['processed_path'] = output_path
            processed_info['processed_filename'] = output_filename
            processed_images.append(processed_info)
        else:
            print(f"   ❌ Failed to process: {img_info['path']}")
    
    print(f"✅ Successfully processed {len(processed_images)} {prefix} images")
    return processed_images

def save_metadata(training_images: List[Dict], validation_images: List[Dict], metadata_dir: Path):
    """Save metadata for training"""
    
    # Create training metadata
    training_metadata = {
        'dataset_info': {
            'name': 'PetPlantr Shape-MVD Training Dataset',
            'version': '1.0',
            'total_images': len(training_images) + len(validation_images),
            'training_images': len(training_images),
            'validation_images': len(validation_images),
            'target_size': 512,
            'format': 'JPEG'
        },
        'training_images': [
            {
                'filename': img['processed_filename'],
                'breed': img['breed'],
                'dataset': img['dataset'],
                'quality_score': img.get('score', 0),
                'sharpness': img.get('sharpness', 0),
                'brightness': img.get('brightness', 0),
                'contrast': img.get('contrast', 0)
            }
            for img in training_images
        ],
        'validation_images': [
            {
                'filename': img['processed_filename'],
                'breed': img['breed'],
                'dataset': img['dataset'],
                'quality_score': img.get('score', 0)
            }
            for img in validation_images
        ]
    }
    
    # Save training metadata
    with open(metadata_dir / 'training_metadata.json', 'w') as f:
        json.dump(training_metadata, f, indent=2)
    
    # Create breed statistics
    breed_stats = {}
    all_images = training_images + validation_images
    for img in all_images:
        breed = img['breed']
        breed_stats[breed] = breed_stats.get(breed, 0) + 1
    
    with open(metadata_dir / 'breed_statistics.json', 'w') as f:
        json.dump(breed_stats, f, indent=2)
    
    # Create dataset summary
    summary = {
        'total_processed': len(all_images),
        'unique_breeds': len(breed_stats),
        'average_quality_score': np.mean([img.get('score', 0) for img in all_images]),
        'quality_distribution': {
            'excellent': len([img for img in all_images if img.get('score', 0) > 0.8]),
            'good': len([img for img in all_images if 0.6 < img.get('score', 0) <= 0.8]),
            'fair': len([img for img in all_images if 0.4 < img.get('score', 0) <= 0.6]),
            'poor': len([img for img in all_images if img.get('score', 0) <= 0.4])
        },
        'breed_distribution': breed_stats
    }
    
    with open(metadata_dir / 'dataset_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✅ Metadata saved:")
    print(f"   training_metadata.json: Complete training dataset info")
    print(f"   breed_statistics.json: Breed distribution")
    print(f"   dataset_summary.json: Quality and composition summary")

def main():
    parser = argparse.ArgumentParser(description='Process pet datasets for Shape-MVD training')
    parser.add_argument('--dataset-root', default='~/Desktop/PetPlantr_Dataset', 
                       help='Root directory for datasets')
    parser.add_argument('--target-count', type=int, default=120,
                       help='Target number of training images')
    parser.add_argument('--validation-split', type=float, default=0.2,
                       help='Fraction of images for validation')
    
    args = parser.parse_args()
    
    # Setup paths
    dataset_root = Path(args.dataset_root).expanduser()
    dirs = setup_directories(dataset_root)
    
    print("🎯 PetPlantr Dataset Preprocessing")
    print("=================================")
    print(f"Dataset Root: {dataset_root}")
    print(f"Target Images: {args.target_count}")
    print(f"Validation Split: {args.validation_split}")
    print("")
    
    # Check if raw datasets exist
    if not any((dirs['raw'] / dataset).exists() for dataset in ['oxford_pets', 'stanford_dogs', 'afhq']):
        print("❌ No raw datasets found!")
        print("Please run download_datasets.sh first")
        return 1
    
    # Collect and filter images
    selected_images = collect_and_filter_images(dirs, args.target_count)
    
    if len(selected_images) < args.target_count:
        print(f"⚠️  Only found {len(selected_images)} suitable images (target: {args.target_count})")
    
    # Create training/validation split
    training_images, validation_images = create_training_split(
        selected_images, 1 - args.validation_split
    )
    
    # Process and save images
    processed_training = process_and_save_images(training_images, dirs['training'], 'train')
    processed_validation = process_and_save_images(validation_images, dirs['validation'], 'val')
    
    # Save metadata
    save_metadata(processed_training, processed_validation, dirs['metadata'])
    
    print("")
    print("🎉 Dataset Preprocessing Complete!")
    print("==================================")
    print(f"✅ Training Images: {len(processed_training)}")
    print(f"✅ Validation Images: {len(processed_validation)}")
    print(f"✅ Location: {dataset_root}")
    print("")
    print("📋 Next Steps:")
    print("1. Review processed images and metadata")
    print("2. Upload dataset to Modal for Shape-MVD training")
    print("3. Configure training parameters")
    print("4. Run 20-epoch fine-tuning (~$2 on Modal)")
    
    return 0

if __name__ == '__main__':
    # Set random seed for reproducible splits
    random.seed(42)
    np.random.seed(42)
    
    sys.exit(main())
