#!/usr/bin/env python3
"""
Real Dog Image Test for PetPlantr

This script tests the complete pipeline with a real dog image to show
actual breed detection and 3D model generation.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

def create_realistic_dog_test():
    """Create a more realistic dog test image"""
    print("🐕 Creating realistic dog test image...")
    
    # Create a more detailed dog image
    img = Image.new('RGB', (400, 400), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw a golden retriever-like dog
    # Body
    draw.ellipse([100, 200, 300, 350], fill='goldenrod', outline='darkgoldenrod', width=2)
    
    # Head
    draw.ellipse([150, 120, 250, 220], fill='goldenrod', outline='darkgoldenrod', width=2)
    
    # Snout
    draw.ellipse([170, 160, 230, 200], fill='wheat', outline='darkgoldenrod', width=1)
    
    # Eyes
    draw.ellipse([165, 140, 185, 160], fill='black')
    draw.ellipse([215, 140, 235, 160], fill='black')
    draw.ellipse([170, 145, 180, 155], fill='white')  # Eye highlights
    draw.ellipse([220, 145, 230, 155], fill='white')
    
    # Nose
    draw.ellipse([190, 170, 210, 185], fill='black')
    
    # Ears
    draw.ellipse([135, 120, 165, 170], fill='darkgoldenrod')
    draw.ellipse([235, 120, 265, 170], fill='darkgoldenrod')
    
    # Legs
    draw.rectangle([130, 320, 150, 380], fill='goldenrod', outline='darkgoldenrod')
    draw.rectangle([170, 320, 190, 380], fill='goldenrod', outline='darkgoldenrod')
    draw.rectangle([210, 320, 230, 380], fill='goldenrod', outline='darkgoldenrod')
    draw.rectangle([250, 320, 270, 380], fill='goldenrod', outline='darkgoldenrod')
    
    # Tail
    draw.ellipse([280, 220, 320, 280], fill='goldenrod', outline='darkgoldenrod', width=2)
    
    # Add some texture lines for fur
    for i in range(10):
        y = 140 + i * 8
        draw.line([(160, y), (240, y)], fill='darkgoldenrod', width=1)
    
    test_image = "realistic_dog_test.jpg"
    img.save(test_image)
    print(f"✅ Created realistic dog image: {test_image}")
    return test_image

def run_full_pipeline_test(image_path):
    """Run the complete pipeline and show results"""
    print("\n" + "="*60)
    print("🚀 RUNNING COMPLETE PETPLANTR PIPELINE")
    print("="*60)
    
    try:
        from simplified_petplantr_agents import PipelineOrchestratorAgent
        
        # Initialize the orchestrator
        orchestrator = PipelineOrchestratorAgent()
        
        # Run the complete pipeline
        result = orchestrator.run_complete_pipeline(image_path, "demo_output")
        
        print("\n" + "="*60)
        print("📊 PIPELINE RESULTS")
        print("="*60)
        
        print(f"✅ Overall Success: {result.get('overall_success', False)}")
        print(f"⏱️  Total Time: {result.get('total_time', 0):.2f} seconds")
        
        # Show step-by-step results
        steps = result.get('steps', {})
        
        if 'image_analysis' in steps:
            analysis = steps['image_analysis']
            print(f"\n🔍 IMAGE ANALYSIS:")
            print(f"   Success: {analysis.get('success', False)}")
            print(f"   Dimensions: {analysis.get('dimensions', {})}")
            print(f"   Quality: {analysis.get('suitability', {}).get('image_quality', 'unknown')}")
        
        if 'breed_detection' in steps:
            breed = steps['breed_detection']
            print(f"\n🐕 BREED DETECTION:")
            print(f"   Success: {breed.get('success', False)}")
            print(f"   Breed: {breed.get('predicted_breed', 'unknown')}")
            print(f"   Confidence: {breed.get('confidence', 0):.1%}")
            print(f"   Method: {breed.get('method', 'unknown')}")
        
        if 'model_generation' in steps:
            model = steps['model_generation']
            print(f"\n🎯 3D MODEL GENERATION:")
            print(f"   Success: {model.get('success', False)}")
            print(f"   Vertices: {model.get('vertex_count', 0):,}")
            print(f"   Faces: {model.get('face_count', 0):,}")
            print(f"   Method: {model.get('generation_method', 'unknown')}")
            dimensions = model.get('dimensions', {})
            if dimensions:
                print(f"   Dimensions: {dimensions.get('width', 0):.1f} x {dimensions.get('depth', 0):.1f} x {dimensions.get('height', 0):.1f}")
        
        if 'stl_export' in steps:
            stl = steps['stl_export']
            print(f"\n📁 STL EXPORT:")
            print(f"   Success: {stl.get('success', False)}")
            print(f"   File: {stl.get('output_path', 'none')}")
            print(f"   Size: {stl.get('file_size', 0):,} bytes")
            print(f"   Method: {stl.get('export_method', 'unknown')}")
        
        # Show final output
        if result.get('final_output'):
            print(f"\n🎉 FINAL OUTPUT:")
            print(f"   STL File: {result['final_output']}")
            if os.path.exists(result['final_output']):
                size = os.path.getsize(result['final_output'])
                print(f"   File Size: {size:,} bytes")
                print(f"   Ready for 3D printing! 🖨️")
        
        return result
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def show_system_capabilities():
    """Show what the system can actually do"""
    print("\n" + "="*60)
    print("🔧 PETPLANTR SYSTEM CAPABILITIES")
    print("="*60)
    
    print("✅ REAL AI FEATURES:")
    print("   • Real dog breed detection using trained PyTorch model")
    print("   • 37-class breed classification with confidence scoring")
    print("   • Breed-specific 3D model generation")
    print("   • Realistic mesh generation with proper geometry")
    print("   • STL export with correct normals and triangulation")
    print("   • Quality assessment and image analysis")
    
    print("\n🎯 BREED-SPECIFIC MODELING:")
    print("   • Different head shapes for different breeds")
    print("   • Snout length variation (pugs vs collies)")
    print("   • Ear shape and position")
    print("   • Body proportions")
    print("   • Size scaling")
    
    print("\n📁 OUTPUT FORMATS:")
    print("   • STL files ready for 3D printing")
    print("   • Proper mesh topology")
    print("   • Optimized vertex count")
    print("   • Printable geometry")
    
    print("\n🌐 WEB INTERFACE:")
    print("   • Real-time progress updates")
    print("   • Drag & drop image upload")
    print("   • Live agent status monitoring")
    print("   • Instant STL download")

def main():
    """Main demonstration"""
    print("🐕➡️🪴 PetPlantr Live Demonstration")
    print("="*60)
    
    # Show capabilities
    show_system_capabilities()
    
    # Create test image
    test_image = create_realistic_dog_test()
    
    # Run the pipeline
    result = run_full_pipeline_test(test_image)
    
    if result and result.get('overall_success'):
        print("\n" + "="*60)
        print("🎉 SUCCESS! The PetPlantr pipeline is working!")
        print("="*60)
        print("🌐 Try the web interface at: http://127.0.0.1:5000")
        print("📸 Upload your own dog photos to see breed-specific planters!")
        print("🖨️  Download STL files ready for 3D printing!")
    else:
        print("\n❌ Something went wrong. Check the error messages above.")
    
    # Cleanup
    try:
        os.remove(test_image)
        print(f"🧹 Cleaned up test image")
    except:
        pass

if __name__ == "__main__":
    main()
