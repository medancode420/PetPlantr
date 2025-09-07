#!/usr/bin/env python3
"""
PetPlantr Proprietary Photo Preprocessing
Processes raw proprietary multi-view pet photos for training

Usage:
    python preprocess.py --input-dir proprietary_raw --output-dir processed/proprietary --resize 512 --mask
"""

import os
import argparse
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageFilter
import json
from typing import List, Dict, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mask(image: np.ndarray, threshold: int = 240) -> np.ndarray:
    """Create a simple background mask for pet photos"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Create mask where background (bright areas) are removed
    mask = gray < threshold
    
    # Apply morphological operations to clean up mask
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    return mask

def resize_with_aspect_ratio(image: np.ndarray, target_size: int = 512) -> np.ndarray:
    """Resize image maintaining aspect ratio and pad to square"""
    h, w = image.shape[:2]
    
    # Calculate scaling factor
    scale = target_size / max(h, w)
    new_h, new_w = int(h * scale), int(w * scale)
    
    # Resize
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    # Create square canvas and center the image
    canvas = np.ones((target_size, target_size, 3), dtype=np.uint8) * 255
    
    # Calculate position to center the image
    y_offset = (target_size - new_h) // 2
    x_offset = (target_size - new_w) // 2
    
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    
    return canvas

def process_pet_directory(
    pet_dir: Path, 
    output_dir: Path, 
    target_size: int = 512, 
    apply_mask: bool = True
) -> Dict:
    """Process all views for a single pet"""
    
    pet_name = pet_dir.name
    views = ['front', 'left', 'right', 'back']
    
    logger.info(f"🔄 Processing {pet_name}...")
    
    processed_info = {
        'pet_name': pet_name,
        'views': {},
        'total_views': 0,
        'quality_score': 0.0
    }
    
    # Create output directory for this pet
    pet_output_dir = output_dir / pet_name
    pet_output_dir.mkdir(parents=True, exist_ok=True)
    
    quality_scores = []
    
    for view in views:
        img_path = pet_dir / f"{view}.jpg"
        
        if not img_path.exists():
            logger.warning(f"⚠️ Missing {view}.jpg for {pet_name}")
            continue
        
        try:
            # Load image
            image = cv2.imread(str(img_path))
            if image is None:
                logger.error(f"❌ Failed to load {img_path}")
                continue
                
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Calculate quality score (based on sharpness and size)
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Quality factors
            size_score = min(image.shape[0] * image.shape[1] / (1024 * 1024), 1.0)  # Prefer higher resolution
            sharpness_score = min(laplacian_var / 1000, 1.0)  # Prefer sharper images
            quality_score = (size_score + sharpness_score) / 2
            
            quality_scores.append(quality_score)
            
            # Resize image
            processed_image = resize_with_aspect_ratio(image_rgb, target_size)
            
            # Apply masking if requested
            if apply_mask:
                mask = create_mask(processed_image)
                
                # Apply mask (set background to white)
                processed_image = processed_image.copy()
                processed_image[mask == 0] = [255, 255, 255]  # White background
            
            # Save processed image
            output_path = pet_output_dir / f"{view}.jpg"
            pil_image = Image.fromarray(processed_image)
            pil_image.save(output_path, quality=95, optimize=True)
            
            # Store view info
            processed_info['views'][view] = {
                'filename': f"{view}.jpg",
                'size': [target_size, target_size],
                'quality_score': quality_score,
                'original_size': list(image.shape[:2]),
                'masked': apply_mask
            }
            
            logger.info(f"   ✅ {view}: {quality_score:.3f} quality")
            
        except Exception as e:
            logger.error(f"❌ Error processing {view} for {pet_name}: {e}")
            continue
    
    processed_info['total_views'] = len(processed_info['views'])
    processed_info['quality_score'] = np.mean(quality_scores) if quality_scores else 0.0
    
    # Save metadata for this pet
    metadata_path = pet_output_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(processed_info, f, indent=2)
    
    logger.info(f"✅ {pet_name}: {processed_info['total_views']}/4 views, {processed_info['quality_score']:.3f} avg quality")
    
    return processed_info

def main():
    parser = argparse.ArgumentParser(description='Process proprietary pet photos for training')
    parser.add_argument('--input-dir', type=str, default='proprietary_raw',
                        help='Input directory containing pet subdirectories')
    parser.add_argument('--output-dir', type=str, default='processed/proprietary',
                        help='Output directory for processed images')
    parser.add_argument('--resize', type=int, default=512,
                        help='Target image size (square)')
    parser.add_argument('--mask', action='store_true',
                        help='Apply background masking')
    
    args = parser.parse_args()
    
    # Resolve paths
    if args.input_dir.startswith('/'):
        input_dir = Path(args.input_dir)
    else:
        input_dir = Path("/Users/medan/Desktop/PetPlantr_Dataset") / args.input_dir
        
    if args.output_dir.startswith('/'):
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path("/Users/medan/Desktop/PetPlantr_Dataset") / args.output_dir
    
    logger.info("🔄 PROPRIETARY PHOTO PREPROCESSING")
    logger.info("="*45)
    logger.info(f"📂 Input: {input_dir}")
    logger.info(f"📁 Output: {output_dir}")
    logger.info(f"📐 Size: {args.resize}x{args.resize}")
    logger.info(f"🎭 Masking: {'Enabled' if args.mask else 'Disabled'}")
    logger.info("")
    
    if not input_dir.exists():
        logger.error(f"❌ Input directory not found: {input_dir}")
        return
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all pet directories
    pet_dirs = [d for d in input_dir.iterdir() if d.is_dir() and d.name.startswith('pet_')]
    
    if not pet_dirs:
        logger.error(f"❌ No pet directories found in {input_dir}")
        logger.info("Expected: pet_001_name/, pet_002_name/, etc.")
        return
    
    logger.info(f"📊 Found {len(pet_dirs)} pet directories")
    logger.info("")
    
    # Process each pet
    all_metadata = []
    successful_pets = 0
    total_views = 0
    
    for pet_dir in sorted(pet_dirs):
        try:
            metadata = process_pet_directory(pet_dir, output_dir, args.resize, args.mask)
            all_metadata.append(metadata)
            
            if metadata['total_views'] >= 4:
                successful_pets += 1
            
            total_views += metadata['total_views']
            
        except Exception as e:
            logger.error(f"❌ Failed to process {pet_dir.name}: {e}")
    
    # Save overall metadata
    summary = {
        'processing_config': {
            'target_size': args.resize,
            'masking_enabled': args.mask,
            'input_directory': str(input_dir),
            'output_directory': str(output_dir)
        },
        'summary': {
            'total_pets_processed': len(all_metadata),
            'complete_pets': successful_pets,
            'total_views': total_views,
            'average_quality': np.mean([p['quality_score'] for p in all_metadata]) if all_metadata else 0.0
        },
        'pets': all_metadata
    }
    
    summary_path = output_dir / "processing_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("")
    logger.info("🎉 PROCESSING COMPLETE!")
    logger.info("="*25)
    logger.info(f"📊 Processed: {len(all_metadata)} pets")
    logger.info(f"✅ Complete: {successful_pets} pets (4/4 views)")
    logger.info(f"📸 Total views: {total_views}")
    logger.info(f"⭐ Avg quality: {summary['summary']['average_quality']:.3f}")
    logger.info(f"📁 Output: {output_dir}")
    logger.info("")
    
    if successful_pets >= 5:
        logger.info("🚀 READY FOR DEMO TRAINING!")
        logger.info("   Command: modal run enhanced_shape_mvd_training.py --demo")
    elif successful_pets >= 1:
        logger.info("🔄 READY FOR TESTING:")
        logger.info(f"   {successful_pets} complete pets available")
    else:
        logger.info("⚠️ Need more complete pet sets for training")
    
    logger.info("")
    logger.info("📤 NEXT STEP: Upload to S3")
    logger.info(f"   aws s3 sync {output_dir} s3://petplantr-dataset/proprietary/multiview/ --acl private")

if __name__ == "__main__":
    main()
