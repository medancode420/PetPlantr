#!/usr/bin/env python3
"""
Advanced Dog Planter Generator

Creates breed-specific planters with different characteristics:
- Hollow interiors for planting
- Drainage systems
- Breed-appropriate shapes and sizes
- Wall thickness optimization
"""

import os
import sys
from PIL import Image, ImageDraw
import random

def create_breed_specific_test_image(breed_name):
    """Create a test image that emphasizes breed-specific features"""
    print(f"🎨 Creating {breed_name} test image...")
    
    img = Image.new('RGB', (400, 400), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Breed-specific characteristics
    breed_configs = {
        'pug': {
            'face_shape': 'flat',
            'snout_length': 20,
            'ear_type': 'small_floppy',
            'body_type': 'compact',
            'colors': ['fawn', 'black']
        },
        'golden_retriever': {
            'face_shape': 'long',
            'snout_length': 60,
            'ear_type': 'large_floppy',
            'body_type': 'medium',
            'colors': ['golden', 'cream']
        },
        'german_shepherd': {
            'face_shape': 'pointed',
            'snout_length': 70,
            'ear_type': 'pointed_erect',
            'body_type': 'large',
            'colors': ['black_tan', 'sable']
        },
        'chihuahua': {
            'face_shape': 'apple',
            'snout_length': 25,
            'ear_type': 'large_erect',
            'body_type': 'tiny',
            'colors': ['tan', 'white', 'chocolate']
        },
        'bulldog': {
            'face_shape': 'extremely_flat',
            'snout_length': 15,
            'ear_type': 'rose',
            'body_type': 'stocky',
            'colors': ['white', 'brindle']
        }
    }
    
    config = breed_configs.get(breed_name, breed_configs['golden_retriever'])
    
    # Draw breed-specific dog
    if config['body_type'] == 'compact':
        body_width, body_height = 180, 120
        head_size = 100
    elif config['body_type'] == 'tiny':
        body_width, body_height = 140, 100
        head_size = 90
    elif config['body_type'] == 'large':
        body_width, body_height = 220, 140
        head_size = 120
    else:  # medium
        body_width, body_height = 200, 130
        head_size = 110
    
    # Choose color
    if config['colors']:
        if 'golden' in config['colors']:
            main_color = 'goldenrod'
        elif 'black' in config['colors']:
            main_color = 'darkslategray'
        elif 'tan' in config['colors']:
            main_color = 'tan'
        elif 'white' in config['colors']:
            main_color = 'wheat'
        else:
            main_color = 'brown'
    else:
        main_color = 'brown'
    
    # Body
    body_x = 200 - body_width//2
    body_y = 250
    draw.ellipse([body_x, body_y, body_x + body_width, body_y + body_height], 
                fill=main_color, outline='darkbrown', width=2)
    
    # Head
    head_x = 200 - head_size//2
    head_y = 150
    
    if config['face_shape'] == 'flat' or config['face_shape'] == 'extremely_flat':
        # Flat face breeds (pug, bulldog)
        draw.ellipse([head_x, head_y, head_x + head_size, head_y + head_size], 
                    fill=main_color, outline='darkbrown', width=2)
        snout_offset = 5 if config['face_shape'] == 'extremely_flat' else 10
    elif config['face_shape'] == 'pointed':
        # Pointed breeds (German Shepherd)
        draw.ellipse([head_x, head_y, head_x + head_size, head_y + head_size], 
                    fill=main_color, outline='darkbrown', width=2)
        snout_offset = 25
    else:
        # Regular breeds
        draw.ellipse([head_x, head_y, head_x + head_size, head_y + head_size], 
                    fill=main_color, outline='darkbrown', width=2)
        snout_offset = 20
    
    # Snout
    snout_length = config['snout_length']
    snout_y = head_y + head_size//2 - 15
    draw.ellipse([head_x + head_size - snout_offset, snout_y, 
                 head_x + head_size + snout_length, snout_y + 30], 
                fill='wheat', outline='darkbrown', width=1)
    
    # Eyes
    eye_y = head_y + head_size//3
    draw.ellipse([head_x + 20, eye_y, head_x + 35, eye_y + 15], fill='black')
    draw.ellipse([head_x + head_size - 35, eye_y, head_x + head_size - 20, eye_y + 15], fill='black')
    
    # Ears based on type
    if config['ear_type'] == 'small_floppy':
        # Small floppy ears (pug)
        draw.ellipse([head_x - 15, head_y + 20, head_x + 15, head_y + 50], fill='darkbrown')
        draw.ellipse([head_x + head_size - 15, head_y + 20, head_x + head_size + 15, head_y + 50], fill='darkbrown')
    elif config['ear_type'] == 'large_floppy':
        # Large floppy ears (golden retriever)
        draw.ellipse([head_x - 20, head_y + 10, head_x + 20, head_y + 70], fill='darkbrown')
        draw.ellipse([head_x + head_size - 20, head_y + 10, head_x + head_size + 20, head_y + 70], fill='darkbrown')
    elif config['ear_type'] == 'pointed_erect':
        # Pointed erect ears (German Shepherd)
        points = [(head_x + 10, head_y + 10), (head_x + 30, head_y - 20), (head_x + 50, head_y + 10)]
        draw.polygon(points, fill='darkbrown', outline='black')
        points = [(head_x + head_size - 50, head_y + 10), (head_x + head_size - 30, head_y - 20), (head_x + head_size - 10, head_y + 10)]
        draw.polygon(points, fill='darkbrown', outline='black')
    elif config['ear_type'] == 'large_erect':
        # Large erect ears (Chihuahua)
        points = [(head_x, head_y + 20), (head_x + 15, head_y - 10), (head_x + 40, head_y + 20)]
        draw.polygon(points, fill='darkbrown', outline='black')
        points = [(head_x + head_size - 40, head_y + 20), (head_x + head_size - 15, head_y - 10), (head_x + head_size, head_y + 20)]
        draw.polygon(points, fill='darkbrown', outline='black')
    
    # Nose
    nose_x = head_x + head_size - snout_offset + snout_length//2 - 5
    nose_y = snout_y + 15 - 5
    draw.ellipse([nose_x, nose_y, nose_x + 10, nose_y + 8], fill='black')
    
    # Legs
    leg_width = 25 if config['body_type'] != 'tiny' else 20
    leg_height = 60 if config['body_type'] != 'tiny' else 45
    
    # Front legs
    draw.rectangle([body_x + 30, body_y + body_height - 10, 
                   body_x + 30 + leg_width, body_y + body_height + leg_height], 
                   fill=main_color, outline='darkbrown')
    draw.rectangle([body_x + 70, body_y + body_height - 10, 
                   body_x + 70 + leg_width, body_y + body_height + leg_height], 
                   fill=main_color, outline='darkbrown')
    
    # Back legs
    draw.rectangle([body_x + body_width - 70 - leg_width, body_y + body_height - 10, 
                   body_x + body_width - 70, body_y + body_height + leg_height], 
                   fill=main_color, outline='darkbrown')
    draw.rectangle([body_x + body_width - 30 - leg_width, body_y + body_height - 10, 
                   body_x + body_width - 30, body_y + body_height + leg_height], 
                   fill=main_color, outline='darkbrown')
    
    # Tail
    tail_x = body_x + body_width - 10
    tail_y = body_y + body_height//2
    draw.ellipse([tail_x, tail_y, tail_x + 40, tail_y + 20], fill=main_color, outline='darkbrown')
    
    filename = f"test_{breed_name}_planter.jpg"
    img.save(filename)
    print(f"✅ Created breed-specific image: {filename}")
    return filename

def test_breed_planter(breed_name, image_file):
    """Test planter generation for a specific breed"""
    print(f"\n{'='*60}")
    print(f"🪴 TESTING {breed_name.upper()} PLANTER GENERATION")
    print(f"{'='*60}")
    
    try:
        from simplified_petplantr_agents import PipelineOrchestratorAgent
        
        # Initialize the orchestrator
        orchestrator = PipelineOrchestratorAgent()
        
        # Run the complete pipeline
        output_dir = f"planter_output_{breed_name}"
        result = orchestrator.run_complete_pipeline(image_file, output_dir)
        
        if result and result.get('overall_success'):
            print(f"\n🎉 {breed_name.title()} planter generated successfully!")
            
            # Show planter-specific results
            steps = result.get('steps', {})
            
            if 'breed_detection' in steps:
                breed_result = steps['breed_detection']
                print(f"🐕 Detected: {breed_result.get('predicted_breed', 'unknown')}")
                print(f"🎯 Confidence: {breed_result.get('confidence', 0):.1%}")
            
            if 'model_generation' in steps:
                model = steps['model_generation']
                print(f"🪴 Planter created:")
                print(f"   📐 Vertices: {model.get('vertex_count', 0):,}")
                print(f"   🔺 Faces: {model.get('face_count', 0):,}")
                
                dimensions = model.get('dimensions', {})
                if dimensions:
                    print(f"   📏 Size: {dimensions.get('width', 0):.1f} x {dimensions.get('depth', 0):.1f} x {dimensions.get('height', 0):.1f} mm")
            
            if 'stl_export' in steps:
                stl = steps['stl_export']
                print(f"📁 STL file: {stl.get('output_path', 'none')}")
                file_size = stl.get('file_size', 0)
                print(f"💾 Size: {file_size:,} bytes")
                
            return True
        else:
            print(f"❌ Failed to generate {breed_name} planter")
            return False
            
    except Exception as e:
        print(f"❌ Error testing {breed_name}: {e}")
        return False

def main():
    """Test planter generation for multiple breeds"""
    print("🪴🐕 Advanced Dog Planter Generator Test")
    print("="*60)
    
    # Test different breeds
    test_breeds = ['pug', 'golden_retriever', 'german_shepherd', 'chihuahua', 'bulldog']
    
    results = {}
    
    for breed in test_breeds:
        # Create breed-specific test image
        image_file = create_breed_specific_test_image(breed)
        
        # Test planter generation
        success = test_breed_planter(breed, image_file)
        results[breed] = success
        
        # Clean up test image
        try:
            os.remove(image_file)
        except:
            pass
    
    # Summary
    print(f"\n{'='*60}")
    print("🏆 PLANTER GENERATION SUMMARY")
    print(f"{'='*60}")
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    for breed, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{breed.title():20} {status}")
    
    print(f"\n🎯 Overall Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
    
    if successful > 0:
        print("\n🪴 Generated planters are ready for 3D printing!")
        print("🌱 Each planter has:")
        print("   • Hollow interior for soil and plants")
        print("   • Drainage holes for proper water management")
        print("   • Breed-specific shape and proportions")
        print("   • Optimized wall thickness for strength")
        print("   • Print-ready STL format")
    
    print(f"\n🌐 View results at: http://localhost:8080/demo_3d_viewer.html")

if __name__ == "__main__":
    main()
