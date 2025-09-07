#!/usr/bin/env python3
"""
Smart Flickr Dog Breed Collector with Real-Time Progress
Shows live progress bars for data collection
"""

import flickrapi
import urllib.request
from pathlib import Path
import json
import time
from tqdm import tqdm
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os

class SmartBreedCollector:
    def __init__(self):
        # Your Flickr API credentials
        self.api_key = "cb6981143fa250c8971237e932e50e09"
        self.api_secret = "c0b2bb59e42c7cb2"
        self.flickr = flickrapi.FlickrAPI(self.api_key, self.api_secret, format='parsed-json')
        
        # Collection settings
        self.max_photos_per_breed = 500  # Reasonable limit
        self.max_workers = 4  # Parallel downloads
        self.base_dir = Path("./datasets/flickr_breeds")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Progress tracking
        self.stats = {
            "breeds_processed": 0,
            "total_photos_downloaded": 0,
            "failed_downloads": 0,
            "start_time": time.time()
        }
        
        # Progress file for resuming
        self.progress_file = self.base_dir / "collection_progress.json"
        self.load_progress()
    
    def load_progress(self):
        """Load previous progress if exists"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                saved_progress = json.load(f)
                self.completed_breeds = set(saved_progress.get("completed_breeds", []))
                self.stats.update(saved_progress.get("stats", {}))
            print(f"📋 Resuming from previous session: {len(self.completed_breeds)} breeds already completed")
        else:
            self.completed_breeds = set()
    
    def save_progress(self):
        """Save current progress"""
        progress_data = {
            "completed_breeds": list(self.completed_breeds),
            "stats": self.stats,
            "last_updated": time.time()
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def search_breed_photos(self, breed_name):
        """Search for photos of specific breed"""
        try:
            search_results = self.flickr.photos.search(
                tags=f'{breed_name},dog,breed',
                tag_mode='all',
                license='1,2,3,4,5,6',  # Creative Commons licenses
                media='photos',
                per_page=min(500, self.max_photos_per_breed),
                extras='url_o,url_l,url_m,license,owner_name',
                sort='relevance'
            )
            
            photos = search_results['photos']['photo']
            print(f"🔍 Found {len(photos)} {breed_name} photos")
            return photos
            
        except Exception as e:
            print(f"❌ Error searching {breed_name}: {e}")
            return []
    
    def download_photo(self, photo, breed_dir):
        """Download single photo with error handling"""
        try:
            # Try different sizes: original, large, medium
            photo_url = photo.get('url_o') or photo.get('url_l') or photo.get('url_m')
            
            if not photo_url:
                return False, "No suitable URL found"
            
            # Create filename with photo ID
            filename = f"{photo['id']}.jpg"
            file_path = breed_dir / filename
            
            # Skip if already exists
            if file_path.exists():
                return True, "Already exists"
            
            # Download with timeout
            response = requests.get(photo_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Save file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Save metadata
            metadata = {
                "photo_id": photo['id'],
                "license": photo.get('license', ''),
                "owner": photo.get('owner_name', ''),
                "url": photo_url,
                "downloaded_at": time.time()
            }
            
            metadata_file = breed_dir / f"{photo['id']}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True, "Downloaded successfully"
            
        except Exception as e:
            return False, str(e)
    
    def collect_breed_photos(self, breed_name):
        """Collect photos for a single breed with progress bar"""
        
        if breed_name in self.completed_breeds:
            print(f"⏭️  Skipping {breed_name} (already completed)")
            return
        
        print(f"\n🐕 Collecting {breed_name} photos...")
        
        # Create breed directory
        breed_dir = self.base_dir / breed_name.replace(' ', '_').lower()
        breed_dir.mkdir(exist_ok=True)
        
        # Search for photos
        photos = self.search_breed_photos(breed_name)
        
        if not photos:
            print(f"❌ No photos found for {breed_name}")
            return
        
        # Limit to max_photos_per_breed
        photos = photos[:self.max_photos_per_breed]
        
        # Progress bar for this breed
        breed_progress = tqdm(
            total=len(photos),
            desc=f"📸 {breed_name}",
            unit="photos",
            ncols=100,
            colour="green"
        )
        
        # Download stats for this breed
        downloaded = 0
        failed = 0
        
        # Download photos with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_photo = {
                executor.submit(self.download_photo, photo, breed_dir): photo 
                for photo in photos
            }
            
            # Process completed downloads
            for future in as_completed(future_to_photo):
                photo = future_to_photo[future]
                try:
                    success, message = future.result()
                    if success:
                        downloaded += 1
                        self.stats["total_photos_downloaded"] += 1
                    else:
                        failed += 1
                        self.stats["failed_downloads"] += 1
                    
                    # Update progress bar
                    breed_progress.set_postfix({
                        "✅": downloaded,
                        "❌": failed,
                        "📊": f"{downloaded+failed}/{len(photos)}"
                    })
                    breed_progress.update(1)
                    
                except Exception as e:
                    failed += 1
                    self.stats["failed_downloads"] += 1
                    breed_progress.update(1)
        
        breed_progress.close()
        
        # Mark breed as completed
        self.completed_breeds.add(breed_name)
        self.stats["breeds_processed"] += 1
        
        print(f"✅ {breed_name}: {downloaded} photos downloaded, {failed} failed")
        
        # Save progress after each breed
        self.save_progress()
    
    def collect_multiple_breeds(self, breed_list):
        """Collect photos for multiple breeds with overall progress"""
        
        print(f"🚀 Starting collection for {len(breed_list)} breeds")
        print(f"📁 Saving to: {self.base_dir}")
        print(f"🎯 Target: {self.max_photos_per_breed} photos per breed")
        print(f"⚙️  Parallel downloads: {self.max_workers} threads")
        print()
        
        # Overall progress bar
        overall_progress = tqdm(
            total=len(breed_list),
            desc="🌍 Overall Progress",
            unit="breeds",
            position=0,
            colour="blue",
            ncols=100
        )
        
        # Real-time stats display
        def update_stats_display():
            while True:
                elapsed = time.time() - self.stats["start_time"]
                photos_per_minute = (self.stats["total_photos_downloaded"] / elapsed) * 60 if elapsed > 0 else 0
                
                overall_progress.set_postfix({
                    "📸": self.stats["total_photos_downloaded"],
                    "🐕": self.stats["breeds_processed"],
                    "⚡": f"{photos_per_minute:.1f}/min",
                    "⏱️": f"{elapsed/60:.1f}min"
                })
                time.sleep(1)
        
        # Start stats thread
        stats_thread = threading.Thread(target=update_stats_display, daemon=True)
        stats_thread.start()
        
        try:
            # Process each breed
            for breed in breed_list:
                self.collect_breed_photos(breed)
                overall_progress.update(1)
                
                # Small delay to prevent API rate limiting
                time.sleep(0.5)
            
        except KeyboardInterrupt:
            print(f"\n⏹️  Collection interrupted by user")
            print(f"📊 Progress saved. Resume by running the script again.")
        
        finally:
            overall_progress.close()
            self.save_progress()
            self.print_final_stats()
    
    def print_final_stats(self):
        """Print final collection statistics"""
        elapsed = time.time() - self.stats["start_time"]
        
        print(f"\n📊 COLLECTION COMPLETE!")
        print("=" * 50)
        print(f"🐕 Breeds processed: {self.stats['breeds_processed']}")
        print(f"📸 Photos downloaded: {self.stats['total_photos_downloaded']}")
        print(f"❌ Failed downloads: {self.stats['failed_downloads']}")
        print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        print(f"⚡ Average speed: {(self.stats['total_photos_downloaded']/elapsed)*60:.1f} photos/minute")
        print(f"📁 Dataset location: {self.base_dir}")
        print()
        
        # Calculate success rate
        total_attempts = self.stats["total_photos_downloaded"] + self.stats["failed_downloads"]
        if total_attempts > 0:
            success_rate = (self.stats["total_photos_downloaded"] / total_attempts) * 100
            print(f"✅ Success rate: {success_rate:.1f}%")

def main():
    """Main collection function"""
    
    # Priority breed list (start with most important)
    priority_breeds = [
        "Golden Retriever",
        "German Shepherd", 
        "Labrador Retriever",
        "French Bulldog",
        "Border Collie",
        "Beagle",
        "Poodle",
        "Rottweiler",
        "Yorkshire Terrier",
        "Siberian Husky",
        "Bulldog",
        "Boston Terrier",
        "Shih Tzu",
        "Chihuahua",
        "Pug"
    ]
    
    print("🐕 Smart Flickr Dog Breed Collector")
    print("=" * 50)
    print("Features:")
    print("• Real-time progress bars")
    print("• Parallel downloads")
    print("• Resume capability")
    print("• Creative Commons licensed photos")
    print("• Automatic metadata saving")
    print()
    
    # Initialize collector
    collector = SmartBreedCollector()
    
    # Start collection
    collector.collect_multiple_breeds(priority_breeds)

if __name__ == "__main__":
    main()
