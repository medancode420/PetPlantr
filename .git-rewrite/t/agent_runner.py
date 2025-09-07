#!/usr/bin/env python3
"""
PetPlantr Agent Runner - Simple interface for running the agent system

This provides an easy way to test and run the agent system with mock data
or real AI if available.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from langchain_petplantr_agents import PetPlantrAgentSystem
    from agent_config import AgentConfig, get_config_for_use_case
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Agent system not fully available: {e}")
    AGENTS_AVAILABLE = False

class PetPlantrAgentRunner:
    """Simple runner for the PetPlantr agent system"""
    
    def __init__(self, use_case: str = "standard_processing"):
        """Initialize the agent runner"""
        self.config = get_config_for_use_case(use_case)
        self.use_case = use_case
        
        print(f"🚀 Initializing PetPlantr Agent System ({use_case})")
        print("=" * 60)
        
        if AGENTS_AVAILABLE:
            try:
                self.agent_system = PetPlantrAgentSystem()
                self.available = True
                print("✅ Agent system initialized successfully!")
            except Exception as e:
                print(f"⚠️  Agent system failed to initialize: {e}")
                print("🤖 Running in mock mode...")
                self.available = False
                self.agent_system = None
        else:
            self.available = False
            self.agent_system = None
            print("🤖 Running in mock mode - no dependencies")
    
    def create_test_image(self, breed: str = "pug") -> str:
        """Create a simple test image for demonstration"""
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple test image
            img = Image.new('RGB', (224, 224), 'lightblue')
            draw = ImageDraw.Draw(img)
            
            # Draw a simple dog-like shape based on breed
            if breed == "pug":
                # Round face for pug
                draw.ellipse([50, 50, 174, 174], fill='brown')
                draw.ellipse([80, 90, 144, 134], fill='black')  # Short snout
                draw.ellipse([90, 70, 110, 90], fill='black')   # Eye
                draw.ellipse([114, 70, 134, 90], fill='black')  # Eye
            elif breed == "golden_retriever":
                # Longer snout for golden retriever
                draw.ellipse([40, 40, 184, 184], fill='gold')
                draw.ellipse([70, 100, 154, 144], fill='darkgoldenrod')
                draw.ellipse([80, 70, 100, 90], fill='black')   # Eye
                draw.ellipse([124, 70, 144, 90], fill='black')  # Eye
            else:
                # Default dog
                draw.ellipse([60, 60, 164, 164], fill='tan')
                draw.ellipse([80, 110, 144, 154], fill='brown')
                draw.ellipse([90, 80, 110, 100], fill='black')
                draw.ellipse([114, 80, 134, 100], fill='black')
            
            filename = f"test_{breed}_agent.jpg"
            img.save(filename)
            print(f"📸 Created test image: {filename}")
            return filename
            
        except ImportError:
            # Create a mock image file
            filename = f"test_{breed}_agent.jpg"
            with open(filename, 'w') as f:
                f.write("mock image data")
            print(f"📸 Created mock image: {filename}")
            return filename
    
    def run_mock_pipeline(self, image_path: str) -> Dict[str, Any]:
        """Run a mock version of the pipeline for testing"""
        print("🤖 Running Mock Pipeline...")
        
        import random
        
        # Mock image analysis
        print("   🔍 Step 1: Mock Image Analysis...")
        time.sleep(0.5)
        image_analysis = {
            "dimensions": {"width": 224, "height": 224},
            "quality_score": random.uniform(0.7, 0.95),
            "composition_score": random.uniform(0.6, 0.9),
            "success": True
        }
        
        # Mock breed detection
        print("   🐕 Step 2: Mock Breed Detection...")
        time.sleep(1.0)
        breeds = ["pug", "golden_retriever", "german_shepherd", "beagle", "bulldog", "chihuahua"]
        predicted_breed = random.choice(breeds)
        confidence = random.uniform(0.75, 0.95)
        
        breed_detection = {
            "predicted_breed": predicted_breed,
            "confidence": confidence,
            "method": "mock_ai_model",
            "alternatives": [
                {"breed": random.choice(breeds), "confidence": random.uniform(0.1, 0.4)}
                for _ in range(2)
            ],
            "success": True
        }
        
        # Mock 3D model generation
        print("   🎯 Step 3: Mock 3D Model Generation...")
        time.sleep(1.5)
        model_generation = {
            "breed": predicted_breed,
            "vertex_count": random.randint(800, 1200),
            "face_count": random.randint(600, 1000),
            "dimensions": {
                "width": 100,
                "depth": 100,
                "height": 80
            },
            "generation_time": random.uniform(2, 5),
            "success": True
        }
        
        # Mock STL export
        print("   📁 Step 4: Mock STL Export...")
        time.sleep(0.8)
        
        # Create output directory
        output_dir = self.config.get("output_directory", "agent_output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create mock STL file
        timestamp = int(time.time())
        stl_filename = f"{predicted_breed}_planter_agent_{timestamp}.stl"
        stl_path = os.path.join(output_dir, stl_filename)
        
        # Write simple STL content
        stl_content = f"""solid {predicted_breed}_planter
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex 1.0 0.0 0.0
      vertex 0.5 1.0 0.0
    endloop
  endfacet
endsolid {predicted_breed}_planter"""
        
        with open(stl_path, 'w') as f:
            f.write(stl_content)
        
        stl_export = {
            "output_path": stl_path,
            "file_size": len(stl_content),
            "quality": "mock_high",
            "validation": {"file_exists": True, "format_valid": True},
            "success": True
        }
        
        # Compile results
        pipeline_result = {
            "input_image": image_path,
            "use_case": self.use_case,
            "steps": {
                "image_analysis": image_analysis,
                "breed_detection": breed_detection,
                "model_generation": model_generation,
                "stl_export": stl_export
            },
            "overall_success": True,
            "final_output": stl_path,
            "total_time": 4.0,
            "mode": "mock"
        }
        
        return pipeline_result
    
    def run_pipeline(self, image_path: str, output_dir: str = None) -> Dict[str, Any]:
        """Run the complete pipeline"""
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": f"Image file not found: {image_path}"
            }
        
        # Use configured output directory if not specified
        if output_dir is None:
            output_dir = self.config.get("output_directory", "agent_output")
        
        start_time = time.time()
        
        if self.available and self.agent_system:
            # Run real agent system
            try:
                print("🤖 Running Real Agent Pipeline...")
                result = self.agent_system.run_pipeline(image_path, output_dir)
                result["total_time"] = time.time() - start_time
                result["mode"] = "real_agents"
                return result
            except Exception as e:
                print(f"⚠️  Real agent pipeline failed: {e}")
                print("🔄 Falling back to mock pipeline...")
        
        # Run mock pipeline
        result = self.run_mock_pipeline(image_path)
        result["total_time"] = time.time() - start_time
        return result
    
    def analyze_image_only(self, image_path: str) -> Dict[str, Any]:
        """Run only image analysis"""
        if self.available and self.agent_system:
            try:
                return self.agent_system.analyze_image(image_path)
            except:
                pass
        
        # Mock analysis
        return {
            "success": True,
            "mode": "mock",
            "analysis": {
                "quality": "good",
                "composition": "centered",
                "breed_detectability": "high"
            }
        }
    
    def detect_breed_only(self, image_path: str) -> Dict[str, Any]:
        """Run only breed detection"""
        if self.available and self.agent_system:
            try:
                return self.agent_system.detect_breed(image_path)
            except:
                pass
        
        # Mock detection
        import random
        breeds = ["pug", "golden_retriever", "german_shepherd", "beagle"]
        return {
            "success": True,
            "mode": "mock",
            "predicted_breed": random.choice(breeds),
            "confidence": random.uniform(0.8, 0.95)
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted results"""
        print("\n🎯 PIPELINE RESULTS")
        print("=" * 50)
        
        if results.get("success", False):
            print(f"✅ Status: SUCCESS")
            print(f"🎲 Mode: {results.get('mode', 'unknown')}")
            print(f"⏱️  Total Time: {results.get('total_time', 0):.1f}s")
            
            if "steps" in results:
                steps = results["steps"]
                
                # Image Analysis
                if "image_analysis" in steps:
                    analysis = steps["image_analysis"]
                    print(f"\n🔍 Image Analysis:")
                    if "dimensions" in analysis:
                        dims = analysis["dimensions"]
                        print(f"   📐 Dimensions: {dims['width']}×{dims['height']}")
                    if "quality_score" in analysis:
                        print(f"   ⭐ Quality Score: {analysis['quality_score']:.2f}")
                
                # Breed Detection
                if "breed_detection" in steps:
                    breed = steps["breed_detection"]
                    print(f"\n🐕 Breed Detection:")
                    print(f"   🎯 Breed: {breed.get('predicted_breed', 'unknown')}")
                    print(f"   📊 Confidence: {breed.get('confidence', 0):.1%}")
                    
                    if "alternatives" in breed:
                        print(f"   🔄 Alternatives:")
                        for alt in breed["alternatives"][:2]:
                            print(f"      • {alt.get('breed', 'unknown')}: {alt.get('confidence', 0):.1%}")
                
                # 3D Model
                if "model_generation" in steps:
                    model = steps["model_generation"]
                    print(f"\n🎯 3D Model Generation:")
                    print(f"   🔺 Vertices: {model.get('vertex_count', 0):,}")
                    print(f"   📐 Faces: {model.get('face_count', 0):,}")
                    if "dimensions" in model:
                        dims = model["dimensions"]
                        print(f"   📏 Size: {dims['width']}×{dims['depth']}×{dims['height']}mm")
                
                # STL Export
                if "stl_export" in steps:
                    stl = steps["stl_export"]
                    print(f"\n📁 STL Export:")
                    print(f"   📄 File: {stl.get('output_path', 'unknown')}")
                    print(f"   💾 Size: {stl.get('file_size', 0):,} bytes")
                    
                    validation = stl.get('validation', {})
                    if validation:
                        valid_count = sum(1 for v in validation.values() if v)
                        total_count = len(validation)
                        print(f"   ✅ Validation: {valid_count}/{total_count} checks passed")
            
            if "final_output" in results:
                print(f"\n🎉 Final Output: {results['final_output']}")
        
        else:
            print(f"❌ Status: FAILED")
            if "error" in results:
                print(f"💥 Error: {results['error']}")

def main():
    """Main function to test the agent runner"""
    print("🚀 PetPlantr Agent Runner Test")
    print("=" * 60)
    
    # Test different use cases
    use_cases = ["quick_analysis", "standard_processing", "thorough_analysis"]
    
    for use_case in use_cases:
        print(f"\n🧪 Testing Use Case: {use_case}")
        print("-" * 40)
        
        # Initialize runner
        runner = PetPlantrAgentRunner(use_case)
        
        # Create test image
        test_image = runner.create_test_image("pug")
        
        # Test individual functions
        print("\n1. 🔍 Testing Image Analysis...")
        analysis_result = runner.analyze_image_only(test_image)
        print(f"   Result: {analysis_result.get('success', False)}")
        
        print("\n2. 🐕 Testing Breed Detection...")
        breed_result = runner.detect_breed_only(test_image)
        print(f"   Result: {breed_result.get('success', False)}")
        
        print("\n3. 🎯 Testing Complete Pipeline...")
        pipeline_result = runner.run_pipeline(test_image)
        runner.print_results(pipeline_result)
        
        # Clean up test image
        try:
            os.remove(test_image)
        except:
            pass
        
        print("\n" + "="*60)

if __name__ == "__main__":
    main()
