#!/usr/bin/env python3
"""
Flickr Creative Commons Dog Breed Collector
Free images with proper licensing
"""

import flickrapi
import urllib.request
from pathlib import Path
import json

def setup_flickr_api():
    """Setup Flickr API - get key from https://www.flickr.com/services/apps/create/"""
    
    api_key = "cb6981143fa250c8971237e932e50e09"
    api_secret = "c0b2bb59e42c7cb2"
    
    return flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')

def collect_flickr_breed_photos(breed_name, max_photos=200):
    """Collect Creative Commons licensed photos for breed"""
    
    flickr = setup_flickr_api()
    
    # Search for breed photos with Creative Commons license
    search_results = flickr.photos.search(
        tags=f'{breed_name},dog,breed',
        license='1,2,3,4,5,6',  # Creative Commons licenses
        media='photos',
        per_page=max_photos,
        extras='url_o,url_l,license'
    )
    
    breed_dir = Path(f"./datasets/flickr/{breed_name.replace(' ', '_')}")
    breed_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📥 Downloading {breed_name} photos from Flickr...")
    
    downloaded = 0
    for photo in search_results['photos']['photo']:
        try:
            # Try original size first, then large
            photo_url = photo.get('url_o') or photo.get('url_l')
            if photo_url:
                filename = f"{photo['id']}.jpg"
                urllib.request.urlretrieve(photo_url, breed_dir / filename)
                downloaded += 1
        except Exception as e:
            print(f"Failed to download {photo['id']}: {e}")
    
    print(f"✅ {breed_name}: {downloaded} images downloaded")
    return breed_dir

if __name__ == "__main__":
    breeds = ["Golden Retriever", "German Shepherd", "Border Collie"]
    for breed in breeds:
        collect_flickr_breed_photos(breed)
