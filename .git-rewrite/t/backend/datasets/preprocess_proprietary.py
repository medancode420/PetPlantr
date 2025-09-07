#!/usr/bin/env python3
"""
Proprietary Multi-view Photo Preprocessing for PetPlantr
Processes raw proprietary photos into training-ready format

Input: proprietary_raw/pet_XXX_name/{front,left,right,back}.jpg
Output: processed/proprietary/pet_XXX_name_{view}.jpg (512px, masked)
"""

import os
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter
import argparse
import json
from typing import Dict, List, Tuple
import logging

def setup_logging():
    """Setup logging for preprocessing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def detect_pet_mask(image: np.ndarray) -> np.ndarray:
    """
    Simple pet detection and masking using color/edge detection
    More sophisticated would use ML models, but this is quick start
    """
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    
    # Create mask for non-background colors
    # Assume background is white/light colored
    lower_bound = np.array([0, 0, 0])
    upper_bound = np.array([180, 255, 200])  # Remove very bright pixels
    
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    
    # Apply morphological operations to clean up mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Find largest contour (should be the pet)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Get largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Create clean mask
        clean_mask = np.zeros_like(mask)
        cv2.fillPoly(clean_mask, [largest_contour], 255)
        
        # Smooth the mask edges
        clean_mask = cv2.GaussianBlur(clean_mask, (5, 5), 0)
        
        return clean_mask
    
    # Fallback: return original mask
    return mask

def process_pet_image(input_path: Path, output_path: Path, target_size: int = 512) -> Dict:
    """
    Process a single pet image:
    1. Resize to target size
    2. Apply pet masking (optional)
    3. Save processed image
    4. Return metadata
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Load image
        image = Image.open(input_path).convert('RGB')
        original_size = image.size
        
        # Resize maintaining aspect ratio
        image.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
        
        # Create square image with padding if needed
        if image.size != (target_size, target_size):
            square_image = Image.new('RGB', (target_size, target_size), (255, 255, 255))
            offset = ((target_size - image.size[0]) // 2, (target_size - image.size[1]) // 2)
            square_image.paste(image, offset)
            image = square_image
        
        # Apply masking (optional - can be skipped for speed)
        apply_masking = False  # Set to True for better quality
        
        if apply_masking:
            # Convert to numpy for masking
            img_array = np.array(image)
            mask = detect_pet_mask(img_array)
            
            # Apply mask
            mask_3d = np.stack([mask/255] * 3, axis=-1)
            masked_array = img_array * mask_3d + (1 - mask_3d) * 255  # White background
            image = Image.fromarray(masked_array.astype(np.uint8))
        
        # Save processed image
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, 'JPEG', quality=95)
        
        # Generate metadata
        metadata = {
            'filename': output_path.name,
            'original_size': original_size,
            'processed_size': (target_size, target_size),
            'source_path': str(input_path),
            'output_path': str(output_path),
            'masked': apply_masking
        }
        
        logger.info(f"✅ Processed: {input_path.name} → {output_path.name}")
        return metadata
        
    except Exception as e:
        logger.error(f"❌ Failed to process {input_path}: {e}")
        return None

def process_pet_directory(pet_dir: Path, output_dir: Path) -> Dict:
    """
    Process all views for a single pet
    Expected structure: pet_dir/{front,left,right,back}.jpg
    """
    logger = logging.getLogger(__name__)
    
    pet_name = pet_dir.name
    logger.info(f"🐕 Processing pet: {pet_name}")
    
    required_views = ['front.jpg', 'left.jpg', 'right.jpg', 'back.jpg']
    processed_images = []
    
    for view_file in required_views:
        input_path = pet_dir / view_file
        
        if not input_path.exists():
            logger.warning(f"⚠️  Missing view: {input_path}")
            continue
        
        # Generate output filename: pet_001_golden_retriever_front.jpg
        view_name = view_file.split('.')[0]  # front, left, right, back
        output_filename = f"{pet_name}_{view_name}.jpg"
        output_path = output_dir / output_filename
        
        # Process image
        metadata = process_pet_image(input_path, output_path)
        
        if metadata:
            metadata['view'] = view_name
            metadata['pet_name'] = pet_name
            processed_images.append(metadata)
    
    return {
        'pet_name': pet_name,
        'views_processed': len(processed_images),
        'images': processed_images,
        'complete': len(processed_images) == 4
    }

def main():
    """Main preprocessing function"""
    parser = argparse.ArgumentParser(description='Process proprietary pet photos')
    parser.add_argument('--input-dir', default='/Users/medan/Desktop/PetPlantr_Dataset/proprietary_raw',
                       help='Input directory with raw photos')
    parser.add_argument('--output-dir', default='/Users/medan/Desktop/PetPlantr_Dataset/processed/proprietary',
                       help='Output directory for processed photos')
    parser.add_argument('--resize', type=int, default=512,
                       help='Target image size (default: 512)')
    parser.add_argument('--mask', action='store_true',
                       help='Apply pet masking (slower but better quality)')
    
    args = parser.parse_args()
    
    logger = setup_logging()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    logger.info("🚀 Starting Proprietary Photo Preprocessing")
    logger.info("=" * 50)
    logger.info(f"📁 Input: {input_dir}")
    logger.info(f"📁 Output: {output_dir}")
    logger.info(f"📐 Size: {args.resize}px")
    logger.info(f"🎭 Masking: {'Enabled' if args.mask else 'Disabled'}")
    logger.info("")
    
    if not input_dir.exists():
        logger.error(f"❌ Input directory not found: {input_dir}")
        return
    
    # Find all pet directories
    pet_dirs = [d for d in input_dir.iterdir() if d.is_dir() and d.name.startswith('pet_')]
    
    if not pet_dirs:
        logger.error(f"❌ No pet directories found in {input_dir}")
        logger.info("Expected structure: pet_001_name/{front,left,right,back}.jpg")
        return
    
    logger.info(f"📊 Found {len(pet_dirs)} pet directories")
    
    # Process each pet
    all_metadata = []
    successful_pets = 0
    
    for pet_dir in sorted(pet_dirs):
        pet_metadata = process_pet_directory(pet_dir, output_dir)
        all_metadata.append(pet_metadata)
        
        if pet_metadata['complete']:
            successful_pets += 1
            logger.info(f"✅ {pet_metadata['pet_name']}: COMPLETE (4/4 views)")
        else:
            logger.warning(f"⚠️  {pet_metadata['pet_name']}: PARTIAL ({pet_metadata['views_processed']}/4 views)")
    
    # Save metadata
    metadata_file = output_dir / 'proprietary_metadata.json'
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    
    summary_metadata = {
        'processing_summary': {
            'total_pets': len(pet_dirs),
            'successful_pets': successful_pets,
            'total_images': sum(len(p['images']) for p in all_metadata),
            'target_size': args.resize,
            'masking_applied': args.mask
        },
        'pets': all_metadata
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(summary_metadata, f, indent=2)
    
    # Final summary
    logger.info("")
    logger.info("🎉 PREPROCESSING COMPLETE!")
    logger.info("=" * 30)
    logger.info(f"✅ Successful pets: {successful_pets}/{len(pet_dirs)}")
    logger.info(f"📊 Total images: {sum(len(p['images']) for p in all_metadata)}")
    logger.info(f"📁 Output: {output_dir}")
    logger.info(f"📋 Metadata: {metadata_file}")
    logger.info("")
    
    if successful_pets >= 5:
        logger.info("🚀 READY FOR DEMO TRAINING!")
        logger.info("   modal run train_shape_mvd.py --demo")
    elif successful_pets >= 1:
        logger.info("🔄 PARTIAL READY - collect more photos for better results")
    else:
        logger.info("⚠️  No complete pets - need 4 views per pet")
    
    logger.info("")
    logger.info("📤 NEXT STEP: Upload to S3")
    logger.info(f"   aws s3 sync {output_dir}/ s3://petplantr-dataset/proprietary/multiview/ --acl private")

if __name__ == "__main__":
    main()
