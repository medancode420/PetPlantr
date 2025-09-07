#!/usr/bin/env python3
"""
Quick test to generate a model and open it in the web viewer
"""

import webbrowser
import time
from integrated_pipeline import IntegratedPetPlantrPipeline

def quick_visual_test():
    """Generate a model and open it in the browser"""
    print("🎯 QUICK VISUAL TEST")
    print("=" * 30)
    
    # Generate a pug model
    pipeline = IntegratedPetPlantrPipeline()
    
    analysis_result = {
        'predicted_breed': 'pug',
        'confidence': 0.95,
        'method': 'test'
    }
    
    print("🐕 Generating pug model...")
    vertices, faces = pipeline.generate_breed_specific_model(analysis_result)
    
    # Save it
    stl_path = pipeline.save_integrated_stl(vertices, faces, analysis_result)
    print(f"💾 Saved: {stl_path}")
    
    # Get just the filename for direct static access
    filename = stl_path.split('/')[-1]
    
    # Try different approaches to view the model
    print("\n🌐 Testing different viewer URLs...")
    
    # 1. Check if STL file is accessible
    stl_url = f"http://localhost:5001/generated_models/{filename}"
    print(f"📁 STL URL: {stl_url}")
    
    # 2. Check if viewer HTML is accessible  
    viewer_base_url = "http://localhost:5001/working_model_viewer.html"
    print(f"🌐 Viewer base: {viewer_base_url}")
    
    # 3. Full viewer URL with model parameter
    full_viewer_url = f"http://localhost:5001/working_model_viewer.html?model=generated_models/{filename}"
    print(f"🎯 Full viewer: {full_viewer_url}")
    
    # Open the full viewer URL
    webbrowser.open(full_viewer_url)
    
    print("👀 Check the browser to see if the model loads!")
    print("� If it doesn't work, try the main interface: http://localhost:5001")
    print("📝 Expected shape:")
    print("   - Elongated dog body (not random triangles)")
    print("   - Visible snout/nose area") 
    print("   - Breed-specific features (pug = flat face)")
    print("   - Planter cavity on the back")

if __name__ == "__main__":
    quick_visual_test()
