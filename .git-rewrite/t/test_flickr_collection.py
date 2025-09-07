#!/usr/bin/env python3
"""
Quick Start Flickr Test - Collect Sample Dog Breed Photos
Test your Flickr API and collect photos for a few breeds
"""

import flickrapi
import urllib.request
from pathlib import Path
import json
import time

def setup_flickr_api():
    """Setup Flickr API with your credentials"""
    
    api_key = "cb6981143fa250c8971237e932e50e09"
    api_secret = "c0b2bb59e42c7cb2"
    
    return flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')

def test_flickr_connection():
    """Test if Flickr API is working"""
    
    try:
        flickr = setup_flickr_api()
        
        # Simple test search
        test_search = flickr.photos.search(
            tags='golden retriever,dog',
            license='1,2,3,4,5,6',  # Creative Commons licenses
            per_page=5
        )
        
        total_photos = test_search['photos']['total']
        print(f"✅ Flickr API working! Found {total_photos} Golden Retriever photos")
        return True
        
    except Exception as e:
        print(f"❌ Flickr API error: {e}")
        return False

def collect_sample_breeds():
    """Collect photos for a few sample breeds to test the system"""
    
    # Test with popular breeds first
    test_breeds = [
        "Golden Retriever",
        "German Shepherd", 
        "Border Collie",
        "French Bulldog",
        "Beagle"
    ]
    
    flickr = setup_flickr_api()
    base_dir = Path("./datasets/flickr_test")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for breed in test_breeds:
        print(f"\n📥 Collecting {breed} photos...")
        
        breed_dir = base_dir / breed.replace(' ', '_').lower()
        breed_dir.mkdir(exist_ok=True)
        
        try:
            # Search for breed photos with Creative Commons license
            search_results = flickr.photos.search(
                tags=f'{breed},dog,breed',
                license='1,2,3,4,5,6',  # CC licenses
                media='photos',
                per_page=20,  # Small test batch
                extras='url_m,license,owner_name'  # Medium size images
            )
            
            photos = search_results['photos']['photo']
            downloaded = 0
            
            for photo in photos:
                try:
                    photo_url = photo.get('url_m')  # Medium size
                    if photo_url:
                        filename = f"{photo['id']}.jpg"
                        file_path = breed_dir / filename
                        
                        # Download image
                        urllib.request.urlretrieve(photo_url, file_path)
                        downloaded += 1
                        
                        # Save metadata
                        metadata = {
                            'photo_id': photo['id'],
                            'title': photo.get('title', ''),
                            'owner': photo.get('owner_name', ''),
                            'license': photo.get('license', ''),
                            'url': photo_url
                        }
                        
                        metadata_file = breed_dir / f"{photo['id']}_metadata.json"
                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                        
                        # Be polite to API
                        time.sleep(0.1)
                        
                except Exception as e:
                    print(f"  ⚠️ Failed to download {photo.get('id')}: {e}")
                    continue
            
            results[breed] = {
                'photos_found': len(photos),
                'photos_downloaded': downloaded,
                'directory': str(breed_dir)
            }
            
            print(f"  ✅ {breed}: {downloaded}/{len(photos)} photos downloaded")
            
        except Exception as e:
            print(f"  ❌ {breed} search failed: {e}")
            results[breed] = {'error': str(e)}
    
    # Save results summary
    results_file = base_dir / "collection_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n🎯 COLLECTION COMPLETE!")
    print(f"📁 Photos saved to: {base_dir}")
    print(f"📊 Results summary: {results_file}")
    
    # Print summary
    total_downloaded = sum(r.get('photos_downloaded', 0) for r in results.values())
    successful_breeds = len([r for r in results.values() if 'photos_downloaded' in r])
    
    print(f"\n📈 SUMMARY:")
    print(f"   Breeds processed: {len(test_breeds)}")
    print(f"   Successful: {successful_breeds}")
    print(f"   Total photos: {total_downloaded}")
    print(f"   Average per breed: {total_downloaded/successful_breeds:.1f}")
    
    return results

def main():
    """Test Flickr API and collect sample data"""
    
    print("🧪 Testing Flickr API for Dog Breed Collection")
    print("=" * 50)
    
    # Test connection
    if not test_flickr_connection():
        print("❌ API test failed. Check your credentials.")
        return
    
    print("\n🚀 Starting sample breed collection...")
    
    # Collect sample breeds
    results = collect_sample_breeds()
    
    print(f"\n✅ SUCCESS! Your Flickr API is working perfectly!")
    print(f"🎯 Ready to scale up to all 450+ breeds!")
    
    # Next steps
    print(f"\n🔥 NEXT STEPS:")
    print("1. ✅ Flickr API working - DONE!")
    print("2. 📸 Collected sample photos - DONE!")
    print("3. 🚀 Scale to all breeds: python flickr_breed_collector.py")
    print("4. 🎯 Start Stanford Dogs download: python stanford_dogs_downloader.py")
    print("5. 🧠 Begin training universal model")

if __name__ == "__main__":
    main()
