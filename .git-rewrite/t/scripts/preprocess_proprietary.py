#!/usr/bin/env python3
"""
PetPlantr Proprietary Photo Preprocessing Script
Processes multi-view pet photos for Stage 2 training
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image, ImageOps
import numpy as np
from typing import Dict, List, Tuple

class ProprietaryPhotoProcessor:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.data_path = self.base_path / "data"
        self.raw_path = self.data_path / "proprietary_raw" 
        self.processed_path = self.data_path / "proprietary_processed"
        self.target_size = (512, 512)
        self.required_views = ['front.jpg', 'left.jpg', 'right.jpg', 'back.jpg']
        
    def log(self, message: str):
        """Log with timestamp"""
        from datetime import datetime
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def validate_pet_folder(self, pet_folder: Path) -> Dict:
        """Validate that a pet folder has all required views"""
        photos = list(pet_folder.glob("*.jpg")) + list(pet_folder.glob("*.jpeg"))
        photo_names = [p.name.lower() for p in photos]
        
        missing_views = []
        found_views = []
        
        for required_view in self.required_views:
            if required_view.lower() in photo_names:
                found_views.append(required_view)
            else:
                missing_views.append(required_view)
                
        return {
            'pet_id': pet_folder.name,
            'total_photos': len(photos),
            'found_views': found_views,
            'missing_views': missing_views,
            'is_complete': len(missing_views) == 0,
            'photos': photos
        }
    
    def preprocess_image(self, image_path: Path, output_path: Path) -> bool:
        """Preprocess a single image"""
        try:
            # Load image
            img = Image.open(image_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize with aspect ratio preservation
            img = ImageOps.fit(img, self.target_size, Image.Resampling.LANCZOS)
            
            # Enhance contrast slightly
            img = ImageOps.autocontrast(img, cutoff=2)
            
            # Save processed image
            img.save(output_path, 'JPEG', quality=95, optimize=True)
            
            self.log(f"   ✅ Processed: {image_path.name} → {output_path.name}")
            return True
            
        except Exception as e:
            self.log(f"   ❌ Error processing {image_path.name}: {e}")
            return False
    
    def process_pet(self, pet_validation: Dict) -> Dict:
        """Process all photos for a single pet"""
        pet_id = pet_validation['pet_id']
        self.log(f"📸 Processing pet: {pet_id}")
        
        if not pet_validation['is_complete']:
            self.log(f"   ⚠️  Skipping {pet_id} - missing views: {pet_validation['missing_views']}")
            return {
                'pet_id': pet_id,
                'success': False,
                'reason': f"Missing views: {pet_validation['missing_views']}"
            }
        
        # Create output directory
        output_dir = self.processed_path / pet_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        processed_count = 0
        failed_count = 0
        
        for photo_path in pet_validation['photos']:
            output_path = output_dir / photo_path.name
            
            if self.preprocess_image(photo_path, output_path):
                processed_count += 1
            else:
                failed_count += 1
        
        # Create metadata file
        metadata = {
            'pet_id': pet_id,
            'processed_photos': processed_count,
            'failed_photos': failed_count,
            'views': pet_validation['found_views'],
            'target_size': self.target_size,
            'processing_date': str(datetime.now())
        }
        
        metadata_path = output_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        success = processed_count >= 4 and failed_count == 0
        self.log(f"   📊 {pet_id}: {processed_count} processed, {failed_count} failed")
        
        return {
            'pet_id': pet_id,
            'success': success,
            'processed_photos': processed_count,
            'failed_photos': failed_count
        }
    
    def generate_training_manifest(self, results: List[Dict]):
        """Generate training manifest for Stage 2"""
        successful_pets = [r for r in results if r['success']]
        
        manifest = {
            'dataset': 'proprietary_multiview',
            'version': '1.0',
            'total_pets': len(successful_pets),
            'total_photos': sum(r['processed_photos'] for r in successful_pets),
            'target_size': self.target_size,
            'views': self.required_views,
            'pets': successful_pets,
            'ready_for_stage2': len(successful_pets) >= 5
        }
        
        manifest_path = self.processed_path / 'training_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        self.log(f"📋 Training manifest saved: {manifest_path}")
        return manifest
    
    def run_preprocessing(self):
        """Main preprocessing pipeline"""
        self.log("🚀 Starting proprietary photo preprocessing...")
        
        if not self.raw_path.exists():
            self.log(f"❌ Raw data path not found: {self.raw_path}")
            return False
        
        # Find all pet folders
        pet_folders = [f for f in self.raw_path.iterdir() if f.is_dir()]
        
        if not pet_folders:
            self.log("❌ No pet folders found in proprietary_raw/")
            return False
        
        self.log(f"📁 Found {len(pet_folders)} pet folders")
        
        # Validate each pet folder
        validations = []
        for pet_folder in pet_folders:
            validation = self.validate_pet_folder(pet_folder)
            validations.append(validation)
            
            status = "✅ Complete" if validation['is_complete'] else f"⚠️  Missing: {validation['missing_views']}"
            self.log(f"   {pet_folder.name}: {validation['total_photos']} photos, {status}")
        
        # Count complete pets
        complete_pets = [v for v in validations if v['is_complete']]
        self.log(f"\n📊 Summary: {len(complete_pets)}/{len(validations)} pets have all 4 views")
        
        if len(complete_pets) < 5:
            self.log(f"⚠️  Need at least 5 complete pets, only have {len(complete_pets)}")
            self.log("📸 Please add missing photos and run again")
            return False
        
        # Process all complete pets
        self.processed_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        for validation in validations:
            if validation['is_complete']:
                result = self.process_pet(validation)
                results.append(result)
        
        # Generate training manifest
        manifest = self.generate_training_manifest(results)
        
        # Summary
        successful_results = [r for r in results if r['success']]
        total_photos = sum(r['processed_photos'] for r in successful_results)
        
        self.log(f"\n🎉 Preprocessing complete!")
        self.log(f"   ✅ {len(successful_results)} pets processed successfully")
        self.log(f"   📸 {total_photos} photos ready for training")
        self.log(f"   📁 Output: {self.processed_path}")
        
        if manifest['ready_for_stage2']:
            self.log(f"   🚀 Ready for Stage 2 training!")
            self.log(f"   📋 Next: bash scripts/process_and_upload.sh")
        
        return len(successful_results) >= 5

if __name__ == "__main__":
    from datetime import datetime
    
    processor = ProprietaryPhotoProcessor()
    success = processor.run_preprocessing()
    
    if not success:
        sys.exit(1)
