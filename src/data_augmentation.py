#!/usr/bin/env python3
"""
PetPlantr Data Augmentation System
Story 1.3: Data augmentation scripts (flip, crop, color-jitter) containerised
"""

import os
import argparse
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps
import random
import json
from typing import List, Tuple, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAugmenter:
    """Data augmentation system for PetPlantr dataset"""

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Augmentation parameters
        self.augmentations = {
            'original': self._original,
            'flip_horizontal': self._flip_horizontal,
            'flip_vertical': self._flip_vertical,
            'crop_center': self._crop_center,
            'crop_random': self._crop_random,
            'color_jitter': self._color_jitter,
            'brightness_jitter': self._brightness_jitter,
            'contrast_jitter': self._contrast_jitter,
            'rotation_90': self._rotation_90,
            'rotation_180': self._rotation_180,
            'rotation_270': self._rotation_270
        }

    def _original(self, img: Image.Image) -> Image.Image:
        """Return original image"""
        return img

    def _flip_horizontal(self, img: Image.Image) -> Image.Image:
        """Horizontal flip"""
        return ImageOps.mirror(img)

    def _flip_vertical(self, img: Image.Image) -> Image.Image:
        """Vertical flip"""
        return ImageOps.flip(img)

    def _crop_center(self, img: Image.Image) -> Image.Image:
        """Center crop to 80% of original size"""
        width, height = img.size
        new_width = int(width * 0.8)
        new_height = int(height * 0.8)
        left = (width - new_width) // 2
        top = (height - new_height) // 2
        right = left + new_width
        bottom = top + new_height
        return img.crop((left, top, right, bottom))

    def _crop_random(self, img: Image.Image) -> Image.Image:
        """Random crop"""
        width, height = img.size
        crop_size = min(width, height) // 2
        left = random.randint(0, width - crop_size)
        top = random.randint(0, height - crop_size)
        right = left + crop_size
        bottom = top + crop_size
        return img.crop((left, top, right, bottom))

    def _color_jitter(self, img: Image.Image) -> Image.Image:
        """Color jitter"""
        enhancer = ImageEnhance.Color(img)
        factor = random.uniform(0.5, 1.5)
        return enhancer.enhance(factor)

    def _brightness_jitter(self, img: Image.Image) -> Image.Image:
        """Brightness jitter"""
        enhancer = ImageEnhance.Brightness(img)
        factor = random.uniform(0.7, 1.3)
        return enhancer.enhance(factor)

    def _contrast_jitter(self, img: Image.Image) -> Image.Image:
        """Contrast jitter"""
        enhancer = ImageEnhance.Contrast(img)
        factor = random.uniform(0.7, 1.3)
        return enhancer.enhance(factor)

    def _rotation_90(self, img: Image.Image) -> Image.Image:
        """Rotate 90 degrees"""
        return img.rotate(90, expand=True)

    def _rotation_180(self, img: Image.Image) -> Image.Image:
        """Rotate 180 degrees"""
        return img.rotate(180, expand=True)

    def _rotation_270(self, img: Image.Image) -> Image.Image:
        """Rotate 270 degrees"""
        return img.rotate(270, expand=True)

    def augment_image(self, image_path: Path, breed: str, augmentations: List[str]) -> List[Dict[str, Any]]:
        """Augment a single image with specified augmentations"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                augmented_images = []

                for aug_name in augmentations:
                    if aug_name in self.augmentations:
                        aug_img = self.augmentations[aug_name](img)

                        # Generate output filename
                        stem = image_path.stem
                        suffix = image_path.suffix
                        output_filename = f"{stem}_{aug_name}{suffix}"
                        output_path = self.output_dir / breed / output_filename
                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        # Save augmented image
                        aug_img.save(output_path, quality=95)

                        augmented_images.append({
                            'original_path': str(image_path),
                            'output_path': str(output_path),
                            'breed': breed,
                            'augmentation': aug_name,
                            'size': aug_img.size
                        })

                        logger.debug(f"Augmented {image_path.name} with {aug_name}")

                return augmented_images

        except Exception as e:
            logger.error(f"Failed to augment {image_path}: {e}")
            return []

    def augment_dataset(self, manifest_path: str, augmentations: List[str], max_images: Optional[int] = None) -> Dict[str, Any]:
        """Augment entire dataset based on manifest"""
        manifest_df = self._load_manifest(manifest_path)

        total_processed = 0
        total_augmented = 0
        results = []

        for _, row in manifest_df.iterrows():
            if max_images and total_processed >= max_images:
                break

            # Handle both pandas and simple dict rows
            if hasattr(row, 'get'):  # Simple dict
                image_filename = row.get('filename', '')
                breed = row.get('breed', '')
            else:  # Pandas series
                image_filename = str(row['filename'])
                breed = str(row['breed'])

            image_path = Path(image_filename)
            breed = str(breed)

            # Check if image exists (for mock data, we'll skip)
            if not image_path.exists():
                logger.debug(f"Image not found: {image_path}, skipping")
                continue

            augmented = self.augment_image(image_path, breed, augmentations)
            results.extend(augmented)
            total_augmented += len(augmented)
            total_processed += 1

            if total_processed % 100 == 0:
                logger.info(f"Processed {total_processed} images, generated {total_augmented} augmentations")

        # Save results
        results_file = self.output_dir / "augmentation_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Augmentation complete: {total_processed} images processed, {total_augmented} augmentations generated")

        return {
            'total_processed': total_processed,
            'total_augmented': total_augmented,
            'results_file': str(results_file),
            'augmentations': augmentations
        }

    def _load_manifest(self, manifest_path: str):
        """Load dataset manifest"""
        try:
            import pandas as pd
            return pd.read_csv(manifest_path)
        except ImportError:
            # Fallback without pandas
            import csv
            data = []
            with open(manifest_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            # Convert to simple dataframe-like structure
            class SimpleDF:
                def __init__(self, data):
                    self.data = data
                def iterrows(self):
                    for i, row in enumerate(self.data):
                        yield i, row
                def __len__(self):
                    return len(self.data)
            return SimpleDF(data)

def main():
    """Main entry point for data augmentation"""
    parser = argparse.ArgumentParser(description="PetPlantr Data Augmentation")
    parser.add_argument("--input-dir", default="data", help="Input directory containing images")
    parser.add_argument("--output-dir", default="data/augmented", help="Output directory for augmented images")
    parser.add_argument("--manifest", default="data/manifest.csv", help="Dataset manifest file")
    parser.add_argument("--augmentations", nargs="+",
                       default=["flip_horizontal", "crop_center", "color_jitter"],
                       help="Augmentation types to apply")
    parser.add_argument("--max-images", type=int, help="Maximum number of images to process")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()

    # Set random seed
    random.seed(args.seed)

    # Create augmenter
    augmenter = DataAugmenter(args.input_dir, args.output_dir)

    # Run augmentation
    logger.info(f"Starting data augmentation with {len(args.augmentations)} augmentations: {args.augmentations}")

    results = augmenter.augment_dataset(
        manifest_path=args.manifest,
        augmentations=args.augmentations,
        max_images=args.max_images
    )

    print("🎯 Data Augmentation Complete")
    print("=" * 50)
    print(f"Images processed: {results['total_processed']}")
    print(f"Augmentations generated: {results['total_augmented']}")
    print(f"Results saved to: {results['results_file']}")
    print(f"Output directory: {args.output_dir}")

if __name__ == "__main__":
    main()
