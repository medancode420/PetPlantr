#!/usr/bin/env python3
"""
Mock dataset collection for PetPlantr development.
Creates manifest entries without actual image downloads for testing.
"""

import csv
import time
import uuid
from pathlib import Path
from typing import Dict, List, Set, Tuple


class MockBreedDatasetCollector:
    """Mock dataset collector for development/testing."""

    def __init__(
        self,
        min_resolution: Tuple[int, int] = (400, 400),
        min_images_per_breed: int = 50,
        manifest_file: str = "data/manifest.csv"
    ):
        self.min_resolution = min_resolution
        self.min_images_per_breed = min_images_per_breed
        self.manifest_file = Path(manifest_file)
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)

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
        # Comprehensive list of dog breeds
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
                     'collected_at', 'uuid', 'image_size_bytes', 'mock']
        with open(self.manifest_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_entries)

    def collect_breed_images_mock(self, breed: str, target_images: int) -> int:
        """Mock collection of images for a specific breed."""
        print(f"🔍 Mock collecting images for breed: {breed}")

        collected = 0
        for i in range(target_images):
            uid = str(uuid.uuid4())[:8]
            filename = f"{breed}_{uid}.jpg"

            # Mock source URL
            source_url = f"https://picsum.photos/seed/{hash(breed + str(i)) % 10000}/600/400.jpg"

            # Update manifest
            self.update_manifest(breed, filename, source_url, {
                'image_size_bytes': 150000,  # Mock size
                'mock': 'true'
            })
            collected += 1

        self.stats["images_collected"] += collected
        self.stats["images_uploaded"] += collected
        print(f"✅ Mock collected {collected} images for {breed}")
        return collected

    def collect_dataset_mock(self, target_breeds: int = 110) -> Dict[str, int]:
        """Mock dataset collection workflow."""
        print("🚀 Starting PetPlantr mock dataset collection...")

        # Get target breeds
        breeds_to_collect = self.get_target_breeds(target_breeds)
        if not breeds_to_collect:
            print("✅ All breeds already have sufficient images!")
            return {}

        print(f"🎯 Target breeds: {len(breeds_to_collect)}")

        results = {}
        for breed in breeds_to_collect:
            collected = self.collect_breed_images_mock(breed, self.min_images_per_breed)
            results[breed] = collected
            self.stats["breeds_processed"] += 1

            # Progress update
            print(f"📊 Progress: {self.stats['breeds_processed']}/{len(breeds_to_collect)} breeds")

        return results

    def print_summary(self, results: Dict[str, int]) -> None:
        """Print collection summary."""
        print("\n" + "="*50)
        print("📊 MOCK COLLECTION SUMMARY")
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
        print("📁 Mock data (no actual images downloaded)")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Mock collect PetPlantr breed dataset")
    parser.add_argument("--target-breeds", type=int, default=110,
                       help="Number of breeds to collect")
    parser.add_argument("--min-images-per-breed", type=int, default=50,
                       help="Minimum images per breed")

    args = parser.parse_args()

    collector = MockBreedDatasetCollector(
        min_images_per_breed=args.min_images_per_breed
    )

    results = collector.collect_dataset_mock(args.target_breeds)
    collector.print_summary(results)


if __name__ == "__main__":
    main()
