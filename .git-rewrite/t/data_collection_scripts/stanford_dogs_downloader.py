#!/usr/bin/env python3
"""
Stanford Dogs Dataset Downloader
120 breeds, 20,580 images - FREE
"""

import urllib.request
import tarfile
import os
from pathlib import Path

def download_stanford_dogs():
    """Download and extract Stanford Dogs dataset"""
    
    base_dir = Path("./datasets/stanford_dogs")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    print("📥 Downloading Stanford Dogs Dataset (120 breeds)...")
    
    # Download images
    images_url = "http://vision.stanford.edu/aditya86/ImageNetDogs/images.tar"
    urllib.request.urlretrieve(images_url, base_dir / "images.tar")
    
    # Download annotations  
    annotations_url = "http://vision.stanford.edu/aditya86/ImageNetDogs/annotation.tar"
    urllib.request.urlretrieve(annotations_url, base_dir / "annotations.tar")
    
    # Download lists
    lists_url = "http://vision.stanford.edu/aditya86/ImageNetDogs/lists.tar"
    urllib.request.urlretrieve(lists_url, base_dir / "lists.tar")
    
    print("📂 Extracting files...")
    
    # Extract all archives
    for tar_file in ["images.tar", "annotations.tar", "lists.tar"]:
        with tarfile.open(base_dir / tar_file, 'r') as tar:
            tar.extractall(base_dir)
        os.remove(base_dir / tar_file)
    
    print("✅ Stanford Dogs Dataset ready!")
    print(f"📊 Location: {base_dir}")
    print("📋 Includes 120 breeds with breed labels")
    
    return base_dir

if __name__ == "__main__":
    download_stanford_dogs()
