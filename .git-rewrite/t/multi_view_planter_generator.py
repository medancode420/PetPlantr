#!/usr/bin/env python3
"""
Multi-View Planter Generator
===========================
Generates 4 synthetic photos of dog planters from different angles,
then combines them for superior 3D reconstruction.
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any
import requests
from openai import AsyncOpenAI
from enhanced_planter_prompts import EnhancedPlanterPrompts
from advanced_breed_detector import AdvancedPlanterPrompts

class MultiViewPlanterGenerator:
    """Generate multiple synthetic views of dog planters for 3D reconstruction"""
    
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.prompt_generator = EnhancedPlanterPrompts()
        self.advanced_prompts = AdvancedPlanterPrompts()
        
    def get_view_specific_prompts(self, breed: str, pet_name: str = "") -> Dict[str, str]:
        """Generate view-specific prompts for different angles"""
        name_part = f" named {pet_name}" if pet_name else ""
        
        base_description = (
            f"professional product photography, museum-quality ceramic planter "
            f"shaped like a {breed} dog{name_part}, sitting upright position, "
            f"realistic fur texture details, hollow cylindrical planter cavity "
            f"clearly visible on the dog's back, pure white seamless studio background, "
            f"no shadows, no reflections, studio lighting, commercial photography style, "
            f"8k resolution, isolated subject, pottery craftsmanship quality"
        )
        
        return {
            "front": f"{base_description}, front orthographic view, facing camera directly, chest and head forward, symmetrical composition",
            
            "side_left": f"{base_description}, left side profile view, 90-degree angle, showing full body silhouette, planter cavity visible from side",
            
            "back": f"{base_description}, rear view, back of dog facing camera, planter cavity opening prominently displayed, tail visible",
            
            "three_quarter": f"{base_description}, three-quarter view angle (45 degrees), showing both front and side features, dynamic perspective"
        }
    
    async def generate_view(self, prompt: str, view_name: str, attempt: int = 1) -> bytes:
        """Generate a single view with the given prompt"""
        try:
            print(f"🎨 Generating {view_name} view (attempt {attempt})...")
            
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="hd",
                style="natural",
                n=1
            )
            
            image_url = response.data[0].url
            print(f"✅ Generated {view_name} URL: {image_url}")
            
            # Download the image
            img_response = requests.get(image_url)
            if img_response.status_code == 200:
                print(f"✅ {view_name} view generated successfully ({len(img_response.content)} bytes)")
                return img_response.content
            else:
                raise Exception(f"Failed to download {view_name} image")
                
        except Exception as e:
            print(f"⚠️ {view_name} generation attempt {attempt} failed: {e}")
            raise
    
    async def generate_multi_view_set(self, breed: str, pet_name: str = "", 
                                    output_dir: str = "multi_view_designs",
                                    debug_dir: Path = None,
                                    analysis_text: str = "") -> Dict[str, Any]:
        """Generate complete set of 4 planter views with advanced breed detection"""
        
        timestamp = int(time.time())
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Use advanced breed detection if analysis text is provided
        if analysis_text:
            prompt_data = self.advanced_prompts.analyze_and_generate_prompts(analysis_text, pet_name)
            view_prompts = prompt_data["prompts"]
            detected_breed = prompt_data["breed"]
            print(f"🎯 Using advanced prompts for {detected_breed}")
        else:
            # Fallback to original method
            view_prompts = self.get_view_specific_prompts(breed, pet_name)
            detected_breed = breed
        
        # Generate all views concurrently for speed
        print(f"🎨 Generating 4-view planter set for {detected_breed} dog...")
        
        view_results = {}
        view_files = {}
        
        for view_name, prompt in view_prompts.items():
            max_attempts = 3  # Increased attempts for better quality
            
            for attempt in range(1, max_attempts + 1):
                try:
                    image_bytes = await self.generate_view(prompt, view_name, attempt)
                    
                    # Save the view
                    filename = f"{pet_name}_{detected_breed.replace(' ', '_')}_{view_name}_{timestamp}.png"
                    file_path = output_path / filename
                    file_path.write_bytes(image_bytes)
                    
                    view_results[view_name] = {
                        'success': True,
                        'file_path': str(file_path),
                        'size_bytes': len(image_bytes),
                        'prompt_used': prompt
                    }
                    view_files[view_name] = str(file_path)
                    
                    # Save to debug directory if provided
                    if debug_dir:
                        debug_file = debug_dir / f"view_{view_name}.png"
                        debug_file.write_bytes(image_bytes)
                    
                    break  # Success, move to next view
                    
                except Exception as e:
                    if attempt == max_attempts:
                        view_results[view_name] = {
                            'success': False,
                            'error': str(e),
                            'attempts': attempt
                        }
                        print(f"❌ Failed to generate {view_name} after {max_attempts} attempts")
                    else:
                        print(f"⚠️ Retrying {view_name} (attempt {attempt + 1})...")
                        await asyncio.sleep(3)  # Longer delay for better results
        
        # Check results
        successful_views = [v for v in view_results.values() if v.get('success')]
        
        result = {
            'success': len(successful_views) >= 3,  # Need at least 3 views
            'views_generated': len(successful_views),
            'total_views': len(view_prompts),
            'view_files': view_files,
            'view_results': view_results,
            'timestamp': timestamp,
            'breed': detected_breed,
            'pet_name': pet_name
        }
        
        if result['success']:
            print(f"✅ Multi-view set complete: {len(successful_views)}/{len(view_prompts)} views generated")
        else:
            print(f"⚠️ Insufficient views generated: {len(successful_views)}/{len(view_prompts)}")
        
        return result

# Example usage and testing
async def test_multi_view_generation():
    """Test the multi-view generation system"""
    try:
        generator = MultiViewPlanterGenerator()
        
        # Test with Golden Retriever
        result = await generator.generate_multi_view_set(
            breed="Golden Retriever",
            pet_name="TestDog",
            output_dir="test_multi_view"
        )
        
        print(f"\n🎯 Test Results:")
        print(f"Success: {result['success']}")
        print(f"Views: {result['views_generated']}/{result['total_views']}")
        
        for view_name, view_data in result['view_results'].items():
            if view_data.get('success'):
                print(f"✅ {view_name}: {view_data['file_path']}")
            else:
                print(f"❌ {view_name}: {view_data.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_multi_view_generation())
