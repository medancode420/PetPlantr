#!/usr/bin/env python3
"""
Animal3D Multi-View Extractor for PetPlantr
============================================

Extracts canonical multi-view pet images from the Animal3D dataset (ICCV 2023).
Selects 5 specific camera views (front, left, right, rear, top) per pet identity
and copies them to a standardized directory structure for training.

Dataset Citation:
-----------------
Animal3D: A Comprehensive Dataset of 3D Animal Pose and Shape
Jiacong Xu, Yi Zhang, Jiawei Chang,Ke Ma, Jos Stam, Dimitris N. Metaxas, Jian Zhao
ICCV 2023

Dataset URL: https://animal3d.github.io/
License: CC BY-NC-SA 4.0

Usage:
------
chmod +x extract_animal3d_views.py
python extract_animal3d_views.py --src_dir data/animal3d --dst_dir data/proprietary_raw --limit 10

Requirements:
-------------
pip install pillow
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install pillow")
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments with validation."""
    parser = argparse.ArgumentParser(
        description="Extract canonical multi-view images from Animal3D dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_animal3d_views.py --src_dir data/animal3d
  python extract_animal3d_views.py --src_dir /path/to/animal3d --dst_dir output --limit 15
        """
    )
    
    parser.add_argument(
        "--src_dir",
        type=Path,
        required=True,
        help="Root path to Animal3D dataset (contains dog/ and cat/ subdirs)"
    )
    
    parser.add_argument(
        "--dst_dir", 
        type=Path,
        default=Path("data/proprietary_raw"),
        help="Output directory for extracted views (default: data/proprietary_raw)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of identities to extract per species (optional)"
    )
    
    parser.add_argument(
        "--min_resolution",
        type=int,
        default=1500,
        help="Minimum resolution on shortest side (default: 1500px)"
    )
    
    args = parser.parse_args()
    
    # Validate source directory
    if not args.src_dir.exists():
        print(f"ERROR: Source directory does not exist: {args.src_dir}")
        sys.exit(1)
    
    if not args.src_dir.is_dir():
        print(f"ERROR: Source path is not a directory: {args.src_dir}")
        sys.exit(1)
    
    # Check for expected Animal3D structure
    dog_dir = args.src_dir / "dog"
    cat_dir = args.src_dir / "cat"
    
    if not dog_dir.exists() or not cat_dir.exists():
        print(f"ERROR: Invalid Animal3D structure. Expected dog/ and cat/ subdirs in {args.src_dir}")
        print("Expected structure:")
        print("  animal3d/")
        print("  ├── dog/")
        print("  │   └── {identity_id}/view_{cam_id}.jpg")
        print("  └── cat/")
        print("      └── {identity_id}/view_{cam_id}.jpg")
        sys.exit(1)
    
    return args


def is_high_res(image_path: Path, min_resolution: int) -> bool:
    """
    Check if image meets minimum resolution requirement.
    
    Args:
        image_path: Path to image file
        min_resolution: Minimum pixels on shortest side
        
    Returns:
        True if image meets resolution requirement
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            shortest_side = min(width, height)
            return shortest_side >= min_resolution
    except Exception as e:
        print(f"WARNING: Could not read image {image_path}: {e}")
        return False


def copy_views(
    species_dir: Path, 
    dst_dir: Path, 
    species_name: str, 
    min_resolution: int,
    limit: Optional[int] = None
) -> Tuple[int, int]:
    """
    Copy canonical views from a species directory.
    
    Args:
        species_dir: Source directory containing identity subdirs
        dst_dir: Destination directory 
        species_name: Species name (dog/cat)
        min_resolution: Minimum resolution requirement
        limit: Maximum identities to process
        
    Returns:
        Tuple of (identities_kept, identities_skipped)
    """
    # Camera mapping: Animal3D view_id -> our naming
    CAMERA_MAPPING = {
        0: "front",    # front view
        1: "left",     # left profile  
        2: "right",    # right profile
        3: "back",     # rear view
        4: "top"       # top view
    }
    
    REQUIRED_VIEWS = list(CAMERA_MAPPING.keys())
    
    identities_kept = 0
    identities_skipped = 0
    
    # Get all identity directories
    identity_dirs = [d for d in species_dir.iterdir() if d.is_dir()]
    identity_dirs.sort()  # Consistent ordering
    
    if limit:
        identity_dirs = identity_dirs[:limit]
    
    print(f"\n🔍 Processing {species_name} identities: {len(identity_dirs)} found")
    
    for identity_dir in identity_dirs:
        identity_id = identity_dir.name
        
        # Check if all required views exist and meet resolution
        views_valid = True
        view_paths = {}
        
        for view_id in REQUIRED_VIEWS:
            view_file = identity_dir / f"view_{view_id}.jpg"
            
            if not view_file.exists():
                print(f"   ⚠️  {identity_id}: Missing view_{view_id}.jpg")
                views_valid = False
                break
            
            if not is_high_res(view_file, min_resolution):
                print(f"   ⚠️  {identity_id}: view_{view_id}.jpg below {min_resolution}px")
                views_valid = False
                break
                
            view_paths[view_id] = view_file
        
        if not views_valid:
            identities_skipped += 1
            continue
        
        # Create destination directory
        dst_identity_dir = dst_dir / f"{species_name}_{identities_kept + 1:03d}"
        dst_identity_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all views
        try:
            for view_id, view_path in view_paths.items():
                dst_name = f"{CAMERA_MAPPING[view_id]}.jpg"
                dst_path = dst_identity_dir / dst_name
                
                shutil.copy2(view_path, dst_path)
            
            print(f"   ✅ {identity_id} → {dst_identity_dir.name} (5 views)")
            identities_kept += 1
            
        except Exception as e:
            print(f"   ❌ {identity_id}: Copy failed: {e}")
            identities_skipped += 1
            
            # Clean up partial copy
            if dst_identity_dir.exists():
                shutil.rmtree(dst_identity_dir)
    
    return identities_kept, identities_skipped


def summary(results: Dict[str, Tuple[int, int]]) -> None:
    """
    Print summary table of extraction results.
    
    Args:
        results: Dict mapping species name to (kept, skipped) counts
    """
    print("\n" + "="*60)
    print("📊 EXTRACTION SUMMARY")
    print("="*60)
    
    print(f"{'Species':<12} | {'Kept':<8} | {'Skipped':<8} | {'Total':<8}")
    print("-" * 60)
    
    total_kept = 0
    total_skipped = 0
    
    for species, (kept, skipped) in results.items():
        total = kept + skipped
        print(f"{species:<12} | {kept:<8} | {skipped:<8} | {total:<8}")
        total_kept += kept
        total_skipped += skipped
    
    print("-" * 60)
    print(f"{'TOTAL':<12} | {total_kept:<8} | {total_skipped:<8} | {total_kept + total_skipped:<8}")
    
    print(f"\n🎯 Result: {total_kept} identities with complete high-resolution view sets")
    
    if total_kept >= 5:
        print("✅ SUCCESS: Sufficient identities extracted for training")
    else:
        print("❌ INSUFFICIENT: Need at least 5 identities for training")


def main() -> None:
    """Main extraction pipeline."""
    args = parse_args()
    
    print("🚀 Animal3D Multi-View Extractor")
    print(f"   Source: {args.src_dir}")
    print(f"   Destination: {args.dst_dir}")
    print(f"   Min resolution: {args.min_resolution}px")
    if args.limit:
        print(f"   Limit per species: {args.limit}")
    
    # Create destination directory
    args.dst_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each species
    results = {}
    
    for species in ["dog", "cat"]:
        species_dir = args.src_dir / species
        
        if not species_dir.exists():
            print(f"⚠️  Skipping {species}: directory not found")
            results[species] = (0, 0)
            continue
        
        kept, skipped = copy_views(
            species_dir=species_dir,
            dst_dir=args.dst_dir,
            species_name=species,
            min_resolution=args.min_resolution,
            limit=args.limit
        )
        
        results[species] = (kept, skipped)
    
    # Print summary
    summary(results)
    
    # Exit with appropriate status
    total_kept = sum(kept for kept, _ in results.values())
    
    if total_kept < 5:
        print("\n❌ FAILED: Less than 5 identities extracted")
        sys.exit(1)
    else:
        print(f"\n✅ SUCCESS: Ready for training with {total_kept} identities")
        print(f"📁 Output directory: {args.dst_dir}")
        sys.exit(0)


if __name__ == "__main__":
    main()
