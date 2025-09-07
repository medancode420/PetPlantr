#!/usr/bin/env python3
"""
Tier A Proprietary Multi-view Photo Processor for PetPlantr
Creates production-ready multi-view datasets for Shape-MVD training
"""

import os
import json
import time
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from datetime import datetime

class TierAPhotoProcessor:
    """Process proprietary multi-view photos to Tier A quality standards"""
    
    def __init__(self, base_dir="/Users/medan/Desktop/PetPlantr_Dataset"):
        self.base_dir = Path(base_dir)
        self.input_dir = self.base_dir / "proprietary_raw"
        self.output_dir = self.base_dir / "proprietary_multiview"
        self.target_size = 512
        self.quality_threshold = 0.85
        
        # Create directories
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
    def process_all_pets(self):
        """Process all pets in the raw directory"""
        
        print("🎯 Processing Tier A Proprietary Multi-view Photos")
        print("=" * 50)
        
        processed_pets = []
        
        # Find all pet directories
        for pet_dir in self.input_dir.glob("pet_*"):
            if pet_dir.is_dir():
                result = self.process_pet(pet_dir)
                if result:
                    processed_pets.append(result)
        
        # Generate summary
        self.generate_summary(processed_pets)
        return len(processed_pets)
    
    def process_pet(self, pet_dir):
        """Process a single pet's multi-view photos"""
        
        pet_name = pet_dir.name
        print(f"📸 Processing {pet_name}...")
        
        # Expected views
        required_views = ['front', 'left', 'right', 'back']
        views_found = {}
        
        # Find images for each view
        for view in required_views:
            candidates = list(pet_dir.glob(f"{view}.*"))
            if candidates:
                views_found[view] = candidates[0]
            else:
                print(f"   ⚠️  Missing {view} view")
                return None
        
        if len(views_found) < 4:
            print(f"   ❌ Incomplete set ({len(views_found)}/4 views)")
            return None
        
        # Create output directory
        output_pet_dir = self.output_dir / pet_name
        output_pet_dir.mkdir(exist_ok=True)
        
        # Process each view
        quality_scores = []
        for view, image_path in views_found.items():
            quality = self.process_image(image_path, output_pet_dir / f"{view}.jpg")
            quality_scores.append(quality)
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        if avg_quality >= self.quality_threshold:
            print(f"   ✅ {pet_name}: {avg_quality:.3f} quality")
            return {
                'name': pet_name,
                'quality': avg_quality,
                'views': len(views_found),
                'timestamp': datetime.now().isoformat()
            }
        else:
            print(f"   ⚠️  {pet_name}: {avg_quality:.3f} quality (below threshold)")
            return None
    
    def process_image(self, input_path, output_path):
        """Process a single image to Tier A standards"""
        
        try:
            # Load image
            img = Image.open(input_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Quality assessment
            quality_score = self.assess_quality(img)
            
            # Enhancement pipeline
            img = self.enhance_image(img)
            
            # Resize to target size
            img = self.resize_image(img)
            
            # Save with high quality
            img.save(output_path, 'JPEG', quality=95, optimize=True)
            
            return quality_score
            
        except Exception as e:
            print(f"   ❌ Error processing {input_path}: {e}")
            return 0.0
    
    def assess_quality(self, img):
        """Assess image quality (sharpness, contrast, etc.)"""
        
        # Convert to numpy array
        img_array = np.array(img.convert('L'))
        
        # Sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(img_array, cv2.CV_64F).var()
        sharpness = min(laplacian_var / 1000.0, 1.0)
        
        # Contrast (standard deviation)
        contrast = img_array.std() / 255.0
        
        # Brightness distribution
        hist = cv2.calcHist([img_array], [0], None, [256], [0, 256])
        brightness_score = 1.0 - abs(np.mean(img_array) - 128) / 128.0
        
        # Composite quality score
        quality = (sharpness * 0.4 + contrast * 0.3 + brightness_score * 0.3)
        return min(quality, 1.0)
    
    def enhance_image(self, img):
        """Apply subtle enhancements for optimal training"""
        
        # Slight sharpening
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        # Contrast adjustment
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.05)
        
        # Subtle noise reduction
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        return img
    
    def resize_image(self, img):
        """Resize image while maintaining aspect ratio"""
        
        # Get current size
        width, height = img.size
        
        # Calculate new size maintaining aspect ratio
        if width != height:
            # Create square canvas
            max_dim = max(width, height)
            square_img = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
            
            # Center the image
            x_offset = (max_dim - width) // 2
            y_offset = (max_dim - height) // 2
            square_img.paste(img, (x_offset, y_offset))
            img = square_img
        
        # Resize to target size
        img = img.resize((self.target_size, self.target_size), Image.Resampling.LANCZOS)
        
        return img
    
    def generate_summary(self, processed_pets):
        """Generate processing summary"""
        
        if not processed_pets:
            print("\n❌ No pets processed successfully")
            return
        
        avg_quality = sum(p['quality'] for p in processed_pets) / len(processed_pets)
        
        summary = {
            "processing_date": datetime.now().isoformat(),
            "total_pets": len(processed_pets),
            "average_quality": avg_quality,
            "quality_threshold": self.quality_threshold,
            "target_resolution": f"{self.target_size}x{self.target_size}",
            "pets": processed_pets
        }
        
        # Save summary
        with open(self.output_dir / "processing_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✅ Processing Summary:")
        print(f"   📊 Pets processed: {len(processed_pets)}")
        print(f"   📊 Average quality: {avg_quality:.3f}")
        print(f"   📁 Output: {self.output_dir}")
        print(f"   📄 Summary: {self.output_dir}/processing_summary.json")

def main():
    processor = TierAPhotoProcessor()
    
    # Check for raw images
    raw_pets = list(processor.input_dir.glob("pet_*"))
    
    if not raw_pets:
        print("📝 No raw photos found. Directory structure needed:")
        print(f"   {processor.input_dir}/")
        print("   ├── pet_001_golden_retriever/")
        print("   │   ├── front.jpg")
        print("   │   ├── left.jpg")
        print("   │   ├── right.jpg")
        print("   │   └── back.jpg")
        print("   ├── pet_002_siamese_cat/")
        print("   │   ├── front.jpg")
        print("   │   ├── left.jpg")
        print("   │   ├── right.jpg")
        print("   │   └── back.jpg")
        print("   └── ...")
        return
    
    # Process all pets
    count = processor.process_all_pets()
    
    if count >= 30:
        print("\n🎉 Tier A dataset ready for training!")
        print("🚀 Next: Upload to S3 and launch Shape-MVD training")
    else:
        print(f"\n⚡ Need {30 - count} more pets for full Tier A dataset")

if __name__ == "__main__":
    main()
