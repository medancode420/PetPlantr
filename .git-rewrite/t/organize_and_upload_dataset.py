#!/usr/bin/env python3
"""
Dataset Organization and Upload Script
Validates the proprietary photo dataset and uploads to S3 for training
"""

import os
import json
import boto3
from pathlib import Path
import mimetypes
from PIL import Image
import hashlib

# Configuration
BUCKET_NAME = "petplantr-dataset"
REGION = "us-west-2"
LOCAL_DATA_PATH = "data/proprietary_photos"
S3_PREFIX = "proprietary_photos/"
MANIFEST_FILE = "training_manifest.json"

def validate_images():
    """Validate all images in the proprietary photos directory"""
    print("🔍 Validating proprietary photos...")
    
    photo_dir = Path(LOCAL_DATA_PATH)
    if not photo_dir.exists():
        print(f"❌ Directory {LOCAL_DATA_PATH} does not exist")
        return False
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    photo_files = list(photo_dir.glob('*'))
    image_files = [f for f in photo_files if f.suffix in valid_extensions]
    
    print(f"📁 Found {len(image_files)} image files in {LOCAL_DATA_PATH}")
    
    validated_count = 0
    for img_file in image_files:
        try:
            # Validate image can be opened
            with Image.open(img_file) as img:
                width, height = img.size
                print(f"✅ {img_file.name}: {width}x{height} pixels, {img.mode} mode")
                validated_count += 1
        except Exception as e:
            print(f"❌ {img_file.name}: Invalid image - {e}")
    
    print(f"🎯 Validated {validated_count}/{len(image_files)} images")
    return validated_count == len(image_files)

def upload_to_s3():
    """Upload photos and manifest to S3"""
    print("\n🚀 Uploading dataset to S3...")
    
    try:
        s3 = boto3.client('s3', region_name=REGION)
        
        # Upload photos
        photo_dir = Path(LOCAL_DATA_PATH)
        uploaded_count = 0
        
        for img_file in photo_dir.glob('*'):
            if img_file.is_file():
                s3_key = f"{S3_PREFIX}{img_file.name}"
                
                # Get content type
                content_type, _ = mimetypes.guess_type(str(img_file))
                if not content_type:
                    content_type = 'application/octet-stream'
                
                # Upload file
                s3.upload_file(
                    str(img_file),
                    BUCKET_NAME,
                    s3_key,
                    ExtraArgs={'ContentType': content_type}
                )
                print(f"📤 Uploaded: {img_file.name} -> s3://{BUCKET_NAME}/{s3_key}")
                uploaded_count += 1
        
        # Upload manifest
        manifest_s3_key = f"manifests/{MANIFEST_FILE}"
        s3.upload_file(
            MANIFEST_FILE,
            BUCKET_NAME,
            manifest_s3_key,
            ExtraArgs={'ContentType': 'application/json'}
        )
        print(f"📤 Uploaded: {MANIFEST_FILE} -> s3://{BUCKET_NAME}/{manifest_s3_key}")
        
        print(f"🎉 Successfully uploaded {uploaded_count} photos and 1 manifest to S3")
        return True
        
    except Exception as e:
        print(f"❌ S3 upload failed: {e}")
        return False

def generate_dataset_summary():
    """Generate a summary of the organized dataset"""
    print("\n📊 Generating dataset summary...")
    
    try:
        with open(MANIFEST_FILE, 'r') as f:
            manifest = json.load(f)
        
        summary = {
            "dataset_version": manifest["version"],
            "total_pets": manifest["total_pets"],
            "total_photos": manifest["total_photos"],
            "proprietary_pets": len([p for p in manifest["pets"] if p.get("dataset") == "proprietary"]),
            "proprietary_photos": sum(len(p["views"]) for p in manifest["pets"] if p.get("dataset") == "proprietary"),
            "species_breakdown": {},
            "size_breakdown": {},
            "photo_files": []
        }
        
        # Analyze pets
        for pet in manifest["pets"]:
            species = pet["species"]
            size = pet["size"]
            
            summary["species_breakdown"][species] = summary["species_breakdown"].get(species, 0) + 1
            summary["size_breakdown"][size] = summary["size_breakdown"].get(size, 0) + 1
        
        # List photo files
        photo_dir = Path(LOCAL_DATA_PATH)
        if photo_dir.exists():
            summary["photo_files"] = [f.name for f in photo_dir.glob('*') if f.is_file()]
        
        # Save summary
        summary_file = "dataset_organization_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Dataset summary saved to {summary_file}")
        
        # Print key stats
        print(f"\n📈 DATASET SUMMARY:")
        print(f"   Version: {summary['dataset_version']}")
        print(f"   Total pets: {summary['total_pets']}")
        print(f"   Total photos: {summary['total_photos']}")
        print(f"   Proprietary pets: {summary['proprietary_pets']}")
        print(f"   Proprietary photos: {summary['proprietary_photos']}")
        print(f"   Species: {summary['species_breakdown']}")
        print(f"   Sizes: {summary['size_breakdown']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate summary: {e}")
        return False

def main():
    """Main execution function"""
    print("🐕 PetPlantr Dataset Organization & Upload")
    print("=" * 50)
    
    # Step 1: Validate images
    if not validate_images():
        print("❌ Image validation failed. Aborting.")
        return False
    
    # Step 2: Generate summary
    if not generate_dataset_summary():
        print("❌ Summary generation failed. Continuing...")
    
    # Step 3: Upload to S3
    if not upload_to_s3():
        print("❌ S3 upload failed. Check AWS credentials and permissions.")
        return False
    
    print("\n🎉 Dataset organization and upload completed successfully!")
    print("📋 Next steps:")
    print("   1. Run Stage-2 training with updated manifest")
    print("   2. Monitor training progress on Modal")
    print("   3. Test end-to-end pipeline with new photos")
    
    return True

if __name__ == "__main__":
    main()
