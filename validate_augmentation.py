#!/usr/bin/env python3
"""
Data Augmentation Validation Script
Tests the acceptance criteria for Story 1.3
"""

import random
from pathlib import Path
from PIL import Image
import json
import argparse

def validate_augmentation_outputs(output_dir: str, num_samples: int = 100) -> dict:
    """Validate augmentation outputs according to acceptance criteria"""

    output_path = Path(output_dir)

    if not output_path.exists():
        return {
            'valid': False,
            'error': f'Output directory {output_dir} does not exist',
            'total_tested': 0,
            'valid_count': 0
        }

    # Load results file
    results_file = output_path / "augmentation_results.json"
    if not results_file.exists():
        return {
            'valid': False,
            'error': 'augmentation_results.json not found',
            'total_tested': 0,
            'valid_count': 0
        }

    with open(results_file, 'r') as f:
        results = json.load(f)

    if not results:
        return {
            'valid': False,
            'error': 'No augmentation results found',
            'total_tested': 0,
            'valid_count': 0
        }

    # Sample outputs for testing
    test_samples = random.sample(results, min(num_samples, len(results)))
    valid_count = 0
    errors = []

    print(f"🔍 Validating {len(test_samples)} augmentation outputs...")

    for result in test_samples:
        output_file = Path(result['output_path'])

        # Check if file exists
        if not output_file.exists():
            errors.append(f"File not found: {output_file}")
            continue

        # Check if image is readable
        try:
            with Image.open(output_file) as img:
                img.verify()

                # Check breed label in path
                breed = result['breed']
                if breed not in str(output_file):
                    errors.append(f"Breed label mismatch: {output_file} (expected: {breed})")
                    continue

                valid_count += 1

        except Exception as e:
            errors.append(f"Image validation failed: {output_file} - {e}")

    # Summary
    total_tested = len(test_samples)
    is_valid = valid_count == total_tested and len(errors) == 0

    result = {
        'valid': is_valid,
        'total_tested': total_tested,
        'valid_count': valid_count,
        'error_count': len(errors),
        'errors': errors[:10]  # Show first 10 errors
    }

    return result

def main():
    parser = argparse.ArgumentParser(description="Validate data augmentation outputs")
    parser.add_argument("--output-dir", default="data/augmented", help="Output directory to validate")
    parser.add_argument("--num-samples", type=int, default=100, help="Number of samples to test")

    args = parser.parse_args()

    print("🎯 Data Augmentation Validation")
    print("=" * 50)

    result = validate_augmentation_outputs(args.output_dir, args.num_samples)

    if result['valid']:
        print("✅ VALIDATION PASSED")
        print(f"   All {result['total_tested']} tested images are valid")
        print("   ✓ Images are readable")
        print("   ✓ Breed labels match directory structure")
        print("   ✓ File formats are correct")
    else:
        print("❌ VALIDATION FAILED")
        print(f"   Valid: {result['valid_count']}/{result['total_tested']}")
        if result.get('error'):
            print(f"   Error: {result['error']}")
        if result.get('errors'):
            print("   Sample errors:")
            for error in result['errors'][:5]:
                print(f"     - {error}")

    print(f"\n📊 Summary: {result['valid_count']}/{result['total_tested']} images passed validation")

if __name__ == "__main__":
    main()
