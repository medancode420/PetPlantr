#!/usr/bin/env python3
"""
Google Images Breed Scraper
Collect images for any dog breed using Google Images
"""

from google_images_search import GoogleImagesSearch
import os
from pathlib import Path

def setup_google_images_api():
    """Setup Google Custom Search API"""
    
    # You need to get these from Google Cloud Console
    api_key = "YOUR_GOOGLE_API_KEY"  # Get from Google Cloud Console
    cx = "YOUR_CUSTOM_SEARCH_ENGINE_ID"  # Create custom search engine
    
    return GoogleImagesSearch(api_key, cx)

def collect_breed_images(breed_name, num_images=500):
    """Collect images for specific breed"""
    
    gis = setup_google_images_api()
    
    search_params = {
        'q': f'{breed_name} dog breed',
        'num': num_images,
        'fileType': 'jpg|png',
        'imgSize': 'MEDIUM|LARGE',
        'imgType': 'photo'
    }
    
    # Create breed directory
    breed_dir = Path(f"./datasets/google_images/{breed_name.replace(' ', '_')}")
    breed_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📥 Collecting {num_images} images for {breed_name}...")
    
    try:
        gis.search(search_params, path_to_dir=str(breed_dir))
        print(f"✅ {breed_name}: {len(list(breed_dir.glob('*')))} images collected")
    except Exception as e:
        print(f"❌ Error collecting {breed_name}: {e}")
    
    return breed_dir

# List of all dog breeds to collect
ALL_BREEDS = [
    "Golden Retriever", "German Shepherd", "Labrador Retriever",
    "French Bulldog", "Border Collie", "Beagle", "Poodle",
    "Rottweiler", "Yorkshire Terrier", "Siberian Husky",
    # Add all 450 breeds here...
]

def collect_all_breeds():
    """Collect images for all breeds"""
    
    for breed in ALL_BREEDS:
        collect_breed_images(breed, num_images=500)
        print(f"Progress: {ALL_BREEDS.index(breed)+1}/{len(ALL_BREEDS)}")

if __name__ == "__main__":
    collect_all_breeds()
