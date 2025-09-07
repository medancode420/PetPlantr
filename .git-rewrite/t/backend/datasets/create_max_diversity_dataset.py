#!/usr/bin/env python3
"""
Enhanced PetPlantr Dataset Preprocessing with Maximum Breed Diversity
Creates a dataset with the best possible breed coverage from available data
"""

import os
import sys
import json
import random
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
import cv2
import numpy as np
from PIL import Image, ImageFilter

def get_all_available_breeds(oxford_dir: Path) -> Dict[str, List[Path]]:
    """Get all available breeds and their image paths"""
    breed_images = defaultdict(list)
    
    for img_path in oxford_dir.glob('*.jpg'):
        # Extract breed from filename
        filename = img_path.stem
        breed_name = '_'.join(filename.split('_')[:-1])  # Remove number suffix
        breed_images[breed_name].append(img_path)
    
    return dict(breed_images)

def assess_image_quality_fast(image_path: Path) -> float:
    """Fast quality assessment focusing on key metrics"""
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return 0.0
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Quick quality metrics
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var() / 1000
        brightness = abs(np.mean(gray) / 255.0 - 0.5) * 2  # Prefer balanced brightness
        contrast = gray.std() / 255.0
        size_score = min((img.shape[0] * img.shape[1]) / (512 * 512), 1.0)
        
        # Overall score
        score = (min(sharpness, 1.0) * 0.4 + 
                (1.0 - brightness) * 0.2 + 
                min(contrast * 2, 1.0) * 0.2 + 
                size_score * 0.2)
        
        return score
        
    except Exception:
        return 0.0

def create_max_diversity_dataset(oxford_dir: Path, target_count: int = 150) -> List[Dict]:
    """Create dataset with maximum breed diversity"""
    print("🎯 Creating Maximum Breed Diversity Dataset")
    print(f"Target: {target_count} images with best possible breed coverage")
    
    # Get all breeds and their images
    breed_images = get_all_available_breeds(oxford_dir)
    
    print(f"📊 Found {len(breed_images)} unique breeds:")
    for breed, images in sorted(breed_images.items()):
        print(f"   {breed}: {len(images)} images")
    
    # Calculate images per breed for even distribution
    num_breeds = len(breed_images)
    base_per_breed = target_count // num_breeds
    extra_images = target_count % num_breeds
    
    print(f"\n🎲 Distribution Strategy:")
    print(f"   Base per breed: {base_per_breed}")
    print(f"   Extra images: {extra_images} (for top quality breeds)")
    
    selected_images = []
    
    # First pass: Select base_per_breed images from each breed
    for breed, images in breed_images.items():
        print(f"   Processing {breed}...")
        
        # Assess quality for all images in this breed
        breed_quality = []
        for img_path in images:
            quality_score = assess_image_quality_fast(img_path)
            breed_quality.append({
                'path': img_path,
                'breed': breed,
                'dataset': 'oxford_pets',
                'score': quality_score
            })
        
        # Sort by quality and take the best
        breed_quality.sort(key=lambda x: x['score'], reverse=True)
        breed_selected = breed_quality[:base_per_breed]
        selected_images.extend(breed_selected)
        
        print(f"     Selected {len(breed_selected)} best images (avg quality: {np.mean([img['score'] for img in breed_selected]):.3f})")
    
    # Second pass: Distribute extra images to breeds with highest quality
    if extra_images > 0:
        print(f"\n🌟 Distributing {extra_images} bonus images to highest quality breeds...")
        
        # Calculate average quality per breed
        breed_avg_quality = {}
        for breed, images in breed_images.items():
            qualities = [assess_image_quality_fast(img) for img in images[:10]]  # Sample first 10
            breed_avg_quality[breed] = np.mean(qualities)
        
        # Sort breeds by average quality
        top_breeds = sorted(breed_avg_quality.items(), key=lambda x: x[1], reverse=True)
        
        for i in range(extra_images):
            breed_name = top_breeds[i % len(top_breeds)][0]
            
            # Find next best image from this breed that wasn't already selected
            breed_paths = {img['path'] for img in selected_images if img['breed'] == breed_name}
            remaining_images = [img for img in breed_images[breed_name] if img not in breed_paths]
            
            if remaining_images:
                best_remaining = max(remaining_images, key=assess_image_quality_fast)
                selected_images.append({
                    'path': best_remaining,
                    'breed': breed_name,
                    'dataset': 'oxford_pets',
                    'score': assess_image_quality_fast(best_remaining)
                })
                print(f"     Bonus image for {breed_name}")
    
    print(f"\n✅ Final Selection: {len(selected_images)} images")
    
    # Show final breed distribution
    final_distribution = defaultdict(int)
    for img in selected_images:
        final_distribution[img['breed']] += 1
    
    print(f"📋 Final Breed Distribution ({len(final_distribution)} breeds):")
    for breed, count in sorted(final_distribution.items()):
        print(f"   {breed}: {count} images")
    
    avg_quality = np.mean([img['score'] for img in selected_images])
    print(f"📊 Average Quality Score: {avg_quality:.3f}")
    
    return selected_images

def main():
    # Paths
    dataset_root = Path.home() / "Desktop" / "PetPlantr_Dataset"
    oxford_dir = dataset_root / "raw" / "oxford_pets"
    
    if not oxford_dir.exists():
        print("❌ Oxford pets directory not found")
        return
    
    # Create enhanced dataset with max diversity
    enhanced_images = create_max_diversity_dataset(oxford_dir, target_count=150)
    
    # Save enhanced metadata
    metadata_dir = dataset_root / "metadata"
    metadata_dir.mkdir(exist_ok=True)
    
    enhanced_metadata = {
        'dataset_info': {
            'name': 'PetPlantr Enhanced Breed Diversity Dataset',
            'total_images': len(enhanced_images),
            'strategy': 'Maximum breed diversity with quality filtering',
            'breeds_covered': len(set(img['breed'] for img in enhanced_images))
        },
        'images': enhanced_images
    }
    
    with open(metadata_dir / "enhanced_diversity_metadata.json", 'w') as f:
        json.dump(enhanced_metadata, f, indent=2, default=str)
    
    print(f"\n🎉 Enhanced dataset metadata saved!")
    print(f"   Location: {metadata_dir / 'enhanced_diversity_metadata.json'}")
    print(f"   Total breeds: {len(set(img['breed'] for img in enhanced_images))}/37")
    print(f"   Coverage: {len(set(img['breed'] for img in enhanced_images))/37*100:.1f}%")

if __name__ == "__main__":
    main()
