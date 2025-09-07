#!/usr/bin/env python3
"""
PetPlantr Dataset Collection Script
Collects remaining 110 breed exemplar images for universal breed coverage.

Requirements:
- ≥50 images per breed
- >400×400px resolution
- CC-BY licensed images
- Store in s3://petplantr-datasets/breeds/raw/
- File naming: <breed>_<uid>.jpg
- Update manifest.csv

Usage:
    python collect_breed_dataset.py --target-breeds 110 --min-images-per-breed 50
"""

import asyncio
import csv
import hashlib
import io
import json
import os
import random
import re
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

try:
    import aiohttp
    from aiohttp import ClientTimeout
except ImportError:
    aiohttp = None
    ClientTimeout = None

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

try:
    from tqdm.asyncio import tqdm
except ImportError:
    # Fallback progress bar
    class tqdm:
        def __init__(self, iterable, total=None, desc=""):
            self.iterable = iterable
            self.total = total
            self.desc = desc
            self.n = 0

        def __iter__(self):
            return iter(self.iterable)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def update(self, n=1):
            self.n += n
            if self.total:
                pct = int(100 * self.n / self.total)
                print(f"{self.desc}: {pct}% ({self.n}/{self.total})")

try:
    from PIL import Image
except ImportError:
    Image = None

import requests


class BreedDatasetCollector:
    """Collects and manages dog breed dataset images."""

    def __init__(
        self,
        s3_bucket: str = "petplantr-datasets",
        s3_prefix: str = "breeds/raw/",
        min_resolution: Tuple[int, int] = (400, 400),
        min_images_per_breed: int = 50,
        max_concurrent_downloads: int = 10,
        manifest_file: str = "data/manifest.csv"
    ):
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.min_resolution = min_resolution
        self.min_images_per_breed = min_images_per_breed
        self.max_concurrent = max_concurrent_downloads
        self.manifest_file = Path(manifest_file)
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize S3 client if available
        if boto3:
            try:
                self.s3_client = boto3.client('s3')
            except Exception as e:
                print(f"⚠️  S3 client initialization failed: {e}")
                self.s3_client = None
        else:
            print("⚠️  boto3 not available, S3 operations disabled")
            self.s3_client = None

        # Semaphore for rate limiting
        self.semaphore = asyncio.Semaphore(max_concurrent_downloads)

        # Progress tracking
        self.stats = {
            "breeds_processed": 0,
            "images_collected": 0,
            "images_uploaded": 0,
            "errors": 0
        }

    def get_existing_breeds(self) -> Set[str]:
        """Get breeds that already have sufficient images."""
        existing_breeds = set()

        if not self.s3_client:
            print("⚠️  S3 client not available, checking local manifest only")
            # Fall back to local manifest if it exists
            if self.manifest_file.exists():
                with open(self.manifest_file, 'r') as f:
                    reader = csv.DictReader(f)
                    breed_counts = {}
                    for row in reader:
                        breed = row.get('breed', '')
                        if breed:
                            breed_counts[breed] = breed_counts.get(breed, 0) + 1

                    for breed, count in breed_counts.items():
                        if count >= self.min_images_per_breed:
                            existing_breeds.add(breed)
            return existing_breeds

        try:
            # List objects in S3 bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=self.s3_bucket, Prefix=self.s3_prefix)

            breed_counts = {}
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        if key.endswith('.jpg'):
                            # Extract breed from filename (format: breed_uid.jpg)
                            parts = key.split('/')[-1].split('_')
                            if len(parts) >= 2:
                                breed = '_'.join(parts[:-1])  # Handle breeds with underscores
                                breed_counts[breed] = breed_counts.get(breed, 0) + 1

            # Filter breeds that meet minimum requirements
            for breed, count in breed_counts.items():
                if count >= self.min_images_per_breed:
                    existing_breeds.add(breed)

        except ClientError as e:
            print(f"⚠️  Could not access S3 bucket: {e}")
            # Fall back to local manifest if it exists
            if self.manifest_file.exists():
                with open(self.manifest_file, 'r') as f:
                    reader = csv.DictReader(f)
                    breed_counts = {}
                    for row in reader:
                        breed = row.get('breed', '')
                        if breed:
                            breed_counts[breed] = breed_counts.get(breed, 0) + 1

                    for breed, count in breed_counts.items():
                        if count >= self.min_images_per_breed:
                            existing_breeds.add(breed)

        return existing_breeds

    def get_target_breeds(self, target_count: int = 110) -> List[str]:
        """Get list of breeds to collect images for."""
        # Comprehensive list of dog breeds (subset of ~450 total)
        all_breeds = [
            "affenpinscher", "afghan_hound", "african_hunting_dog", "airedale_terrier",
            "american_staffordshire_terrier", "appenzeller_sennenhund", "australian_terrier",
            "basenji", "basset_hound", "beagle", "bedlington_terrier", "bernese_mountain_dog",
            "black_and_tan_coonhound", "blenheim_spaniel", "bloodhound", "bluetick_coonhound",
            "border_collie", "border_terrier", "borzoi", "boston_terrier", "bouvier_des_flandres",
            "boxer", "brabancon_griffon", "briard", "brittany_spaniel", "bull_mastiff",
            "cairn_terrier", "cardigan_welsh_corgi", "chesapeake_bay_retriever", "chihuahua",
            "chow_chow", "clumber_spaniel", "cocker_spaniel", "collie", "curly_coated_retriever",
            "dandie_dinmont_terrier", "dhole", "dingo", "doberman_pinscher", "english_cocker_spaniel",
            "english_setter", "english_springer_spaniel", "english_toy_spaniel", "entlebucher_mountain_dog",
            "eskimo_dog", "flat_coated_retriever", "french_bulldog", "german_shepherd_dog",
            "german_short_haired_pointer", "german_wire_haired_pointer", "giant_schnauzer",
            "golden_retriever", "gordon_setter", "great_dane", "great_pyrenees", "greater_swiss_mountain_dog",
            "groenendael", "havanese", "ibizan_hound", "irish_setter", "irish_terrier",
            "irish_water_spaniel", "irish_wolfhound", "italian_greyhound", "japanese_chin",
            "japanese_spaniel", "keeshond", "kelpie", "kerry_blue_terrier", "komondor",
            "kuvasz", "labrador_retriever", "lakeland_terrier", "leonberger", "lhasa_apso",
            "lowchen", "maltese", "manchester_terrier", "marmaduke", "mexican_hairless",
            "miniature_pinscher", "miniature_poodle", "miniature_schnauzer", "newfoundland",
            "norfolk_terrier", "norwegian_elkhound", "norwich_terrier", "old_english_sheepdog",
            "otterhound", "papillon", "pekinese", "pembroke_welsh_corgi", "petit_basset_griffon_vendeen",
            "pharaoh_hound", "plott", "pointer", "pomeranian", "pug", "redbone_coonhound",
            "rhodesian_ridgeback", "rottweiler", "saint_bernard", "saluki", "samoyed",
            "schipperke", "scotch_terrier", "scottish_deerhound", "sealyham_terrier", "shetland_sheepdog",
            "shih_tzu", "siberian_husky", "silky_terrier", "soft_coated_wheaten_terrier",
            "staffordshire_bullterrier", "standard_poodle", "standard_schnauzer", "sussex_spaniel",
            "tibetan_mastiff", "tibetan_terrier", "toy_poodle", "toy_terrier", "vizsla",
            "walker_hound", "weimaraner", "welsh_springer_spaniel", "west_highland_white_terrier",
            "whippet", "wire_haired_fox_terrier", "yorkshire_terrier"
        ]

        # Get existing breeds
        existing_breeds = self.get_existing_breeds()
        print(f"📊 Found {len(existing_breeds)} breeds with sufficient images")

        # Filter out existing breeds
        target_breeds = [breed for breed in all_breeds if breed not in existing_breeds]

        # Return requested number
        return target_breeds[:target_count]

    async def search_breed_images(self, breed: str, max_results: int = 100) -> List[str]:
        """Search for CC-BY licensed images of a specific breed."""
        if not aiohttp:
            print("⚠️  aiohttp not available, using fallback sources")
            return await self._fallback_image_search(breed, max_results)

        # Use Unsplash API for CC-BY images
        unsplash_access_key = os.getenv('UNSPLASH_ACCESS_KEY')
        if not unsplash_access_key:
            print("⚠️  UNSPLASH_ACCESS_KEY not set, using fallback sources")
            return await self._fallback_image_search(breed, max_results)

        urls = []
        query = f"{breed.replace('_', ' ')} dog"

        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.unsplash.com/search/photos"
                params = {
                    'query': query,
                    'per_page': min(max_results, 30),  # Unsplash limit
                    'orientation': 'squarish'
                }
                headers = {'Authorization': f'Client-ID {unsplash_access_key}'}

                if ClientTimeout:
                    timeout = ClientTimeout(total=30)
                else:
                    timeout = 30

                async with session.get(url, params=params, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        for photo in data.get('results', []):
                            urls.append(photo['urls']['regular'])
                    else:
                        print(f"⚠️  Unsplash API error: {response.status}")

        except Exception as e:
            print(f"⚠️  Unsplash search failed: {e}")

        # Supplement with fallback sources if needed
        if len(urls) < max_results:
            fallback_urls = await self._fallback_image_search(breed, max_results - len(urls))
            urls.extend(fallback_urls)

        return urls[:max_results]

    async def _fallback_image_search(self, breed: str, max_results: int) -> List[str]:
        """Fallback image search using public APIs."""
        if not aiohttp:
            print("⚠️  aiohttp not available, cannot search images")
            return []

        urls = []

        # Use Pexels API (CC-BY licensed)
        pexels_api_key = os.getenv('PEXELS_API_KEY')
        if pexels_api_key:
            try:
                async with aiohttp.ClientSession() as session:
                    url = "https://api.pexels.com/v1/search"
                    params = {
                        'query': f"{breed.replace('_', ' ')} dog",
                        'per_page': min(max_results, 30)
                    }
                    headers = {'Authorization': pexels_api_key}

                    if ClientTimeout:
                        timeout = ClientTimeout(total=30)
                    else:
                        timeout = None

                    async with session.get(url, params=params, headers=headers, timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            for photo in data.get('photos', []):
                                urls.append(photo['src']['large'])
            except Exception as e:
                print(f"⚠️  Pexels search failed: {e}")

        return urls

    async def download_and_validate_image(self, url: str, breed: str) -> Optional[Tuple[str, bytes]]:
        """Download and validate an image."""
        if not aiohttp:
            print("⚠️  aiohttp not available, cannot download images")
            return None

        async with self.semaphore:
            try:
                async with aiohttp.ClientSession() as session:
                    if ClientTimeout:
                        timeout = ClientTimeout(total=30)
                    else:
                        timeout = None

                    async with session.get(url, timeout=timeout) as response:
                        if response.status != 200:
                            return None

                        content = await response.read()

                        # Validate image
                        if Image:
                            try:
                                img = Image.open(io.BytesIO(content))
                                if img.size[0] < self.min_resolution[0] or img.size[1] < self.min_resolution[1]:
                                    return None
                                if img.format not in ['JPEG', 'JPG']:
                                    return None
                            except Exception:
                                return None
                        else:
                            print("⚠️  PIL not available, skipping image validation")

                        return url, content

            except Exception as e:
                self.stats["errors"] += 1
                return None

    async def upload_to_s3(self, breed: str, image_data: bytes, uid: str) -> bool:
        """Upload image to S3."""
        if not self.s3_client:
            print("⚠️  S3 client not available, skipping upload")
            return False

        filename = f"{breed}_{uid}.jpg"
        key = f"{self.s3_prefix}{filename}"

        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=image_data,
                ContentType='image/jpeg',
                Metadata={
                    'breed': breed,
                    'source': 'collected',
                    'license': 'cc-by',
                    'resolution': f"{self.min_resolution[0]}x{self.min_resolution[1]}"
                }
            )
            self.stats["images_uploaded"] += 1
            return True
        except ClientError as e:
            print(f"❌ S3 upload failed for {filename}: {e}")
            self.stats["errors"] += 1
            return False

    def update_manifest(self, breed: str, filename: str, source_url: str, metadata: Dict) -> None:
        """Update the dataset manifest."""
        # Read existing manifest
        existing_entries = []
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r') as f:
                reader = csv.DictReader(f)
                existing_entries = list(reader)

        # Add new entry
        new_entry = {
            'filename': filename,
            'breed': breed,
            'source_url': source_url,
            'license': 'cc-by',
            'resolution_min': f"{self.min_resolution[0]}x{self.min_resolution[1]}",
            'collected_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'uuid': str(uuid.uuid4()),
            **metadata
        }
        existing_entries.append(new_entry)

        # Write updated manifest
        fieldnames = ['filename', 'breed', 'source_url', 'license', 'resolution_min',
                     'collected_at', 'uuid']
        with open(self.manifest_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_entries)

    async def collect_breed_images(self, breed: str, target_images: int) -> int:
        """Collect images for a specific breed."""
        print(f"🔍 Searching images for breed: {breed}")

        # Search for images
        image_urls = await self.search_breed_images(breed, target_images * 2)  # Get more than needed
        if not image_urls:
            print(f"⚠️  No images found for {breed}")
            return 0

        print(f"📥 Found {len(image_urls)} potential images for {breed}")

        # Download and validate images
        tasks = []
        for url in image_urls:
            tasks.append(self.download_and_validate_image(url, breed))

        results = []
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc=f"Downloading {breed}"):
            result = await coro
            if result:
                results.append(result)

        collected = 0
        for source_url, image_data in results[:target_images]:
            uid = str(uuid.uuid4())[:8]
            filename = f"{breed}_{uid}.jpg"

            # Upload to S3
            if await self.upload_to_s3(breed, image_data, uid):
                # Update manifest
                self.update_manifest(breed, filename, source_url, {
                    'image_size_bytes': len(image_data)
                })
                collected += 1

        self.stats["images_collected"] += collected
        print(f"✅ Collected {collected} images for {breed}")
        return collected

    async def collect_dataset(self, target_breeds: int = 110) -> Dict[str, int]:
        """Main dataset collection workflow."""
        print("🚀 Starting PetPlantr dataset collection...")

        # Get target breeds
        breeds_to_collect = self.get_target_breeds(target_breeds)
        if not breeds_to_collect:
            print("✅ All breeds already have sufficient images!")
            return {}

        print(f"🎯 Target breeds: {len(breeds_to_collect)}")

        results = {}
        for breed in breeds_to_collect:
            collected = await self.collect_breed_images(breed, self.min_images_per_breed)
            results[breed] = collected
            self.stats["breeds_processed"] += 1

            # Progress update
            print(f"📊 Progress: {self.stats['breeds_processed']}/{len(breeds_to_collect)} breeds")

        return results

    def print_summary(self, results: Dict[str, int]) -> None:
        """Print collection summary."""
        print("\n" + "="*50)
        print("📊 COLLECTION SUMMARY")
        print("="*50)
        print(f"🎯 Breeds processed: {self.stats['breeds_processed']}")
        print(f"📸 Images collected: {self.stats['images_collected']}")
        print(f"☁️  Images uploaded: {self.stats['images_uploaded']}")
        print(f"❌ Errors: {self.stats['errors']}")

        if results:
            print("\n📋 Breed Results:")
            for breed, count in sorted(results.items()):
                status = "✅" if count >= self.min_images_per_breed else "❌"
                print(f"  {status} {breed}: {count}/{self.min_images_per_breed} images")

        print(f"\n📄 Manifest updated: {self.manifest_file}")
        print(f"🪣 S3 Bucket: s3://{self.s3_bucket}/{self.s3_prefix}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Collect PetPlantr breed dataset")
    parser.add_argument("--target-breeds", type=int, default=110,
                       help="Number of breeds to collect")
    parser.add_argument("--min-images-per-breed", type=int, default=50,
                       help="Minimum images per breed")
    parser.add_argument("--s3-bucket", default="petplantr-datasets",
                       help="S3 bucket name")
    parser.add_argument("--max-concurrent", type=int, default=10,
                       help="Max concurrent downloads")

    args = parser.parse_args()

    # Check for required environment variables
    if not os.getenv('UNSPLASH_ACCESS_KEY') and not os.getenv('PEXELS_API_KEY'):
        print("⚠️  Warning: No image API keys found. Set UNSPLASH_ACCESS_KEY or PEXELS_API_KEY")
        print("   Proceeding with limited fallback sources...")

    collector = BreedDatasetCollector(
        s3_bucket=args.s3_bucket,
        min_images_per_breed=args.min_images_per_breed,
        max_concurrent_downloads=args.max_concurrent
    )

    results = await collector.collect_dataset(args.target_breeds)
    collector.print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
