#!/usr/bin/env python3
"""
LangChain Agent System for PetPlantr Pipeline

This creates specialized agents for each step:
1. Image Analysis Agent - Analyzes dog images and extracts features
2. Breed Detection Agent - Identifies dog breeds with high confidence
3. 3D Model Generation Agent - Creates breed-specific 3D models
4. STL Export Agent - Handles file export and validation
5. Pipeline Orchestrator Agent - Coordinates the entire workflow
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# LangChain imports
try:
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.agents.agent_types import AgentType
    from langchain.agents import initialize_agent
    from langchain.tools import BaseTool, StructuredTool, tool
    from langchain.schema import AgentAction, AgentFinish
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.memory import ConversationBufferMemory
    from langchain_openai import ChatOpenAI
    from langchain.callbacks.manager import CallbackManagerForToolRun
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
    print("✅ LangChain dependencies loaded successfully")
except ImportError as e:
    print(f"❌ LangChain not available: {e}")
    print("📦 Install with: pip install langchain langchain-openai")
    LANGCHAIN_AVAILABLE = False

# AI/ML imports
try:
    import torch
    import torchvision.transforms as transforms
    from PIL import Image
    import numpy as np
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️  AI dependencies not available - using mock mode")

# Import our existing pipeline components
try:
    from integrated_pipeline import IntegratedPetPlantrPipeline
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    print("⚠️  Integrated pipeline not available - using mock mode")

class ImageAnalysisInput(BaseModel):
    """Input schema for image analysis"""
    image_path: str = Field(description="Path to the dog image to analyze")
    analysis_depth: str = Field(default="standard", description="Analysis depth: quick, standard, or thorough")

class BreedDetectionInput(BaseModel):
    """Input schema for breed detection"""
    image_features: Dict[str, Any] = Field(description="Extracted image features")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence threshold")

class Model3DInput(BaseModel):
    """Input schema for 3D model generation"""
    breed_info: Dict[str, Any] = Field(description="Breed information and characteristics")
    model_size: str = Field(default="standard", description="Model size: small, standard, or large")

class STLExportInput(BaseModel):
    """Input schema for STL export"""
    model_data: Dict[str, Any] = Field(description="3D model vertices and faces")
    output_path: str = Field(description="Output path for STL file")
    quality: str = Field(default="high", description="Export quality: low, medium, or high")

class PetPlantrAgentSystem:
    """Main agent system that orchestrates the PetPlantr pipeline"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the agent system"""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not LANGCHAIN_AVAILABLE:
            print("❌ LangChain not available - running in mock mode")
            self.mock_mode = True
            return
        
        if not self.openai_api_key:
            print("⚠️  No OpenAI API key found - using mock responses")
            self.mock_mode = True
            return
        
        self.mock_mode = False
        self.llm = ChatOpenAI(
            api_key=self.openai_api_key,
            model="gpt-4",
            temperature=0.1
        )
        
        # Initialize memory for conversation
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize pipeline components
        if PIPELINE_AVAILABLE:
            self.pipeline = IntegratedPetPlantrPipeline()
        
        # Create specialized tools
        self.tools = self._create_tools()
        
        # Create specialized agents
        self.agents = self._create_agents()
        
        print("✅ PetPlantr Agent System initialized successfully!")
    
    def _create_tools(self) -> List[BaseTool]:
        """Create specialized tools for each pipeline step"""
        
        @tool
        def analyze_dog_image(image_path: str, analysis_depth: str = "standard") -> Dict[str, Any]:
            """
            Analyze a dog image to extract visual features, composition, and quality metrics.
            
            Args:
                image_path: Path to the dog image file
                analysis_depth: Analysis depth (quick, standard, thorough)
            
            Returns:
                Dictionary with image analysis results including features, quality, and metadata
            """
            try:
                if not os.path.exists(image_path):
                    return {"error": f"Image file not found: {image_path}"}
                
                # Load and analyze image
                image = Image.open(image_path).convert('RGB')
                width, height = image.size
                
                # Basic image metrics
                analysis = {
                    "image_path": image_path,
                    "dimensions": {"width": width, "height": height},
                    "aspect_ratio": width / height,
                    "file_size": os.path.getsize(image_path),
                    "format": image.format or "Unknown"
                }
                
                # Quality assessment
                if analysis_depth in ["standard", "thorough"]:
                    # Convert to numpy for analysis
                    img_array = np.array(image)
                    
                    # Basic quality metrics
                    brightness = np.mean(img_array)
                    contrast = np.std(img_array)
                    
                    analysis.update({
                        "quality_metrics": {
                            "brightness": float(brightness),
                            "contrast": float(contrast),
                            "sharpness_estimate": float(contrast / brightness) if brightness > 0 else 0,
                        },
                        "color_analysis": {
                            "dominant_colors": self._analyze_colors(img_array),
                            "color_diversity": float(np.std(img_array.reshape(-1, 3), axis=0).mean())
                        }
                    })
                
                # Thorough analysis
                if analysis_depth == "thorough":
                    analysis.update({
                        "advanced_features": {
                            "edge_density": self._calculate_edge_density(img_array),
                            "texture_complexity": self._calculate_texture_complexity(img_array),
                            "composition_score": self._analyze_composition(img_array)
                        }
                    })
                
                analysis["analysis_timestamp"] = time.time()
                analysis["success"] = True
                
                return analysis
                
            except Exception as e:
                return {"error": f"Image analysis failed: {str(e)}", "success": False}
        
        @tool
        def detect_dog_breed(image_path: str, confidence_threshold: float = 0.7) -> Dict[str, Any]:
            """
            Detect dog breed from image using AI model with confidence scoring.
            
            Args:
                image_path: Path to the dog image
                confidence_threshold: Minimum confidence threshold for prediction
            
            Returns:
                Dictionary with breed prediction, confidence, and alternative predictions
            """
            try:
                if self.mock_mode or not PIPELINE_AVAILABLE:
                    # Mock breed detection
                    mock_breeds = ["pug", "golden_retriever", "german_shepherd", "beagle", "bulldog"]
                    import random
                    predicted_breed = random.choice(mock_breeds)
                    confidence = random.uniform(0.75, 0.95)
                    
                    return {
                        "predicted_breed": predicted_breed,
                        "confidence": confidence,
                        "method": "mock_ai_model",
                        "alternatives": [
                            {"breed": random.choice(mock_breeds), "confidence": random.uniform(0.1, 0.4)}
                            for _ in range(3)
                        ],
                        "success": True
                    }
                
                # Use real AI pipeline
                self.pipeline.image_path = image_path
                result = self.pipeline.analyze_image_with_ai()
                
                if result and result.get('confidence', 0) >= confidence_threshold:
                    return {
                        "predicted_breed": result.get('predicted_breed', 'unknown'),
                        "confidence": result.get('confidence', 0),
                        "method": result.get('method', 'ai_model'),
                        "features": result.get('features', {}),
                        "success": True
                    }
                else:
                    return {
                        "error": "Breed detection confidence below threshold",
                        "predicted_breed": result.get('predicted_breed', 'unknown') if result else 'unknown',
                        "confidence": result.get('confidence', 0) if result else 0,
                        "threshold": confidence_threshold,
                        "success": False
                    }
                    
            except Exception as e:
                return {"error": f"Breed detection failed: {str(e)}", "success": False}
        
        @tool
        def generate_3d_model(breed_info: str, model_size: str = "standard") -> Dict[str, Any]:
            """
            Generate 3D model based on breed characteristics and specifications.
            
            Args:
                breed_info: JSON string with breed information and characteristics
                model_size: Model size specification (small, standard, large)
            
            Returns:
                Dictionary with 3D model data, statistics, and generation info
            """
            try:
                # Parse breed info
                if isinstance(breed_info, str):
                    breed_data = json.loads(breed_info)
                else:
                    breed_data = breed_info
                
                breed_name = breed_data.get('predicted_breed', 'default')
                confidence = breed_data.get('confidence', 0.75)
                
                # Size specifications
                size_configs = {
                    "small": {"base_size": 70, "detail_level": "low"},
                    "standard": {"base_size": 100, "detail_level": "medium"},
                    "large": {"base_size": 150, "detail_level": "high"}
                }
                
                config = size_configs.get(model_size, size_configs["standard"])
                
                if self.mock_mode or not PIPELINE_AVAILABLE:
                    # Mock 3D model generation
                    import random
                    vertex_count = random.randint(800, 1200)
                    face_count = random.randint(600, 1000)
                    
                    return {
                        "breed": breed_name,
                        "model_size": model_size,
                        "vertex_count": vertex_count,
                        "face_count": face_count,
                        "dimensions": {
                            "width": config["base_size"],
                            "depth": config["base_size"],
                            "height": config["base_size"] * 0.8
                        },
                        "generation_time": random.uniform(2, 8),
                        "quality_score": random.uniform(0.8, 0.95),
                        "mock_data": True,
                        "success": True
                    }
                
                # Use real 3D generation
                vertices, faces = self.pipeline.generate_breed_specific_model(breed_data)
                
                if vertices and faces:
                    # Calculate model statistics
                    vertex_count = len(vertices)
                    face_count = len(faces)
                    
                    # Calculate dimensions
                    if vertices:
                        xs = [v[0] for v in vertices]
                        ys = [v[1] for v in vertices]
                        zs = [v[2] for v in vertices]
                        
                        dimensions = {
                            "width": max(xs) - min(xs),
                            "depth": max(ys) - min(ys),
                            "height": max(zs) - min(zs)
                        }
                    else:
                        dimensions = {"width": 0, "depth": 0, "height": 0}
                    
                    return {
                        "breed": breed_name,
                        "model_size": model_size,
                        "vertex_count": vertex_count,
                        "face_count": face_count,
                        "dimensions": dimensions,
                        "vertices": vertices[:10],  # Sample for preview
                        "model_data": {"vertices": vertices, "faces": faces},
                        "success": True
                    }
                else:
                    return {"error": "3D model generation failed", "success": False}
                    
            except Exception as e:
                return {"error": f"3D model generation failed: {str(e)}", "success": False}
        
        @tool
        def export_stl_file(model_data: str, output_path: str, quality: str = "high") -> Dict[str, Any]:
            """
            Export 3D model data to STL file with quality control.
            
            Args:
                model_data: JSON string with 3D model vertices and faces
                output_path: Output path for the STL file
                quality: Export quality level (low, medium, high)
            
            Returns:
                Dictionary with export results, file info, and validation
            """
            try:
                # Parse model data
                if isinstance(model_data, str):
                    data = json.loads(model_data)
                else:
                    data = model_data
                
                vertices = data.get('vertices', [])
                faces = data.get('faces', [])
                
                if not vertices or not faces:
                    return {"error": "Invalid model data - missing vertices or faces", "success": False}
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Quality settings
                quality_settings = {
                    "low": {"precision": 1, "validation": False},
                    "medium": {"precision": 2, "validation": True},
                    "high": {"precision": 3, "validation": True}
                }
                
                settings = quality_settings.get(quality, quality_settings["high"])
                
                # Generate STL content
                stl_content = self._generate_stl_content(vertices, faces, settings["precision"])
                
                # Write STL file
                with open(output_path, 'w') as f:
                    f.write(stl_content)
                
                # Validation
                file_size = os.path.getsize(output_path)
                
                validation_result = {
                    "file_exists": os.path.exists(output_path),
                    "file_size": file_size,
                    "size_reasonable": 1000 < file_size < 10000000,  # 1KB to 10MB
                }
                
                if settings["validation"]:
                    validation_result.update(self._validate_stl_file(output_path))
                
                return {
                    "output_path": output_path,
                    "file_size": file_size,
                    "quality": quality,
                    "vertex_count": len(vertices),
                    "face_count": len(faces),
                    "validation": validation_result,
                    "export_timestamp": time.time(),
                    "success": all(validation_result.values())
                }
                
            except Exception as e:
                return {"error": f"STL export failed: {str(e)}", "success": False}
        
        @tool
        def orchestrate_pipeline(image_path: str, output_directory: str = "agent_output") -> Dict[str, Any]:
            """
            Orchestrate the complete PetPlantr pipeline from image to STL.
            
            Args:
                image_path: Path to input dog image
                output_directory: Directory for output files
            
            Returns:
                Dictionary with complete pipeline results and timing
            """
            start_time = time.time()
            pipeline_results = {
                "input_image": image_path,
                "output_directory": output_directory,
                "steps": {},
                "overall_success": False
            }
            
            try:
                # Ensure output directory exists
                os.makedirs(output_directory, exist_ok=True)
                
                # Step 1: Image Analysis
                print("🔍 Step 1: Analyzing image...")
                image_analysis = analyze_dog_image(image_path, "thorough")
                pipeline_results["steps"]["image_analysis"] = image_analysis
                
                if not image_analysis.get("success"):
                    return pipeline_results
                
                # Step 2: Breed Detection
                print("🐕 Step 2: Detecting breed...")
                breed_detection = detect_dog_breed(image_path, 0.6)
                pipeline_results["steps"]["breed_detection"] = breed_detection
                
                if not breed_detection.get("success"):
                    return pipeline_results
                
                # Step 3: 3D Model Generation
                print("🎯 Step 3: Generating 3D model...")
                model_generation = generate_3d_model(json.dumps(breed_detection), "standard")
                pipeline_results["steps"]["model_generation"] = model_generation
                
                if not model_generation.get("success"):
                    return pipeline_results
                
                # Step 4: STL Export
                print("📁 Step 4: Exporting STL...")
                breed_name = breed_detection.get("predicted_breed", "unknown")
                timestamp = int(time.time())
                stl_filename = f"{breed_name}_planter_{timestamp}.stl"
                stl_path = os.path.join(output_directory, stl_filename)
                
                stl_export = export_stl_file(json.dumps(model_generation.get("model_data", {})), stl_path, "high")
                pipeline_results["steps"]["stl_export"] = stl_export
                
                # Pipeline summary
                pipeline_results["overall_success"] = all(
                    step.get("success", False) for step in pipeline_results["steps"].values()
                )
                pipeline_results["total_time"] = time.time() - start_time
                pipeline_results["final_output"] = stl_path if stl_export.get("success") else None
                
                if pipeline_results["overall_success"]:
                    print(f"✅ Pipeline completed successfully!")
                    print(f"   🎯 Breed: {breed_name}")
                    print(f"   📊 Confidence: {breed_detection.get('confidence', 0):.1%}")
                    print(f"   📁 Output: {stl_path}")
                    print(f"   ⏱️  Time: {pipeline_results['total_time']:.1f}s")
                
                return pipeline_results
                
            except Exception as e:
                pipeline_results["error"] = f"Pipeline orchestration failed: {str(e)}"
                return pipeline_results
        
        return [analyze_dog_image, detect_dog_breed, generate_3d_model, export_stl_file, orchestrate_pipeline]
    
    def _create_agents(self) -> Dict[str, Any]:
        """Create specialized agents for different pipeline steps"""
        
        if self.mock_mode:
            return {"mock": "agents not available"}
        
        # Base prompt template
        base_prompt = ChatPromptTemplate.from_messages([
            ("system", "{agent_role}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agents = {}
        
        # Image Analysis Agent
        image_analysis_role = """
        You are an expert Image Analysis Agent for the PetPlantr system. Your role is to:
        
        1. Analyze dog images for quality, composition, and visual features
        2. Assess image suitability for breed detection
        3. Extract relevant visual characteristics
        4. Provide recommendations for image preprocessing
        
        You have access to advanced image analysis tools. Always provide detailed, 
        actionable insights about the images you analyze.
        """
        
        agents["image_analyzer"] = initialize_agent(
            tools=self.tools[:1],  # Just image analysis tool
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            memory=self.memory,
            verbose=True
        )
        
        # Breed Detection Agent
        breed_detection_role = """
        You are a specialized Breed Detection Agent for PetPlantr. Your expertise includes:
        
        1. Identifying dog breeds with high accuracy
        2. Analyzing breed-specific characteristics
        3. Providing confidence assessments
        4. Suggesting alternative breed possibilities
        
        You use state-of-the-art AI models and should always explain your reasoning
        for breed identification decisions.
        """
        
        agents["breed_detector"] = initialize_agent(
            tools=self.tools[1:2],  # Just breed detection tool
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            memory=self.memory,
            verbose=True
        )
        
        # 3D Model Generation Agent
        model_generation_role = """
        You are a 3D Model Generation Agent specializing in creating breed-specific
        dog planters. Your capabilities include:
        
        1. Translating breed characteristics into 3D geometry
        2. Optimizing models for 3D printing
        3. Ensuring proper planter functionality
        4. Balancing aesthetic appeal with practical use
        
        Always consider both the artistic representation of the breed and the
        functional requirements of a planter.
        """
        
        agents["model_generator"] = initialize_agent(
            tools=self.tools[2:3],  # Just 3D model tool
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            memory=self.memory,
            verbose=True
        )
        
        # STL Export Agent
        stl_export_role = """
        You are an STL Export and Quality Control Agent. Your responsibilities:
        
        1. Export 3D models to high-quality STL files
        2. Validate file integrity and printability
        3. Optimize file size and quality
        4. Ensure manufacturing compatibility
        
        You should always verify that exported files meet 3D printing standards
        and provide quality assessments.
        """
        
        agents["stl_exporter"] = initialize_agent(
            tools=self.tools[3:4],  # Just STL export tool
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            memory=self.memory,
            verbose=True
        )
        
        # Pipeline Orchestrator
        orchestrator_role = """
        You are the Pipeline Orchestrator Agent responsible for coordinating the
        complete PetPlantr workflow. Your role encompasses:
        
        1. Managing the end-to-end pipeline execution
        2. Handling errors and recovery
        3. Optimizing workflow efficiency
        4. Providing comprehensive status updates
        
        You have access to all pipeline tools and should ensure seamless
        coordination between different processing steps.
        """
        
        agents["orchestrator"] = initialize_agent(
            tools=self.tools,  # All tools
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            memory=self.memory,
            verbose=True
        )
        
        return agents
    
    def _analyze_colors(self, img_array: np.ndarray) -> List[List[int]]:
        """Analyze dominant colors in image"""
        # Simple color analysis - get mean colors for R, G, B channels
        colors = []
        for channel in range(3):
            mean_val = int(np.mean(img_array[:, :, channel]))
            colors.append([mean_val if i == channel else 0 for i in range(3)])
        return colors
    
    def _calculate_edge_density(self, img_array: np.ndarray) -> float:
        """Calculate edge density as a measure of detail"""
        # Simple edge detection using gradient
        gray = np.mean(img_array, axis=2)
        gradient_x = np.gradient(gray, axis=1)
        gradient_y = np.gradient(gray, axis=0)
        edge_strength = np.sqrt(gradient_x**2 + gradient_y**2)
        return float(np.mean(edge_strength))
    
    def _calculate_texture_complexity(self, img_array: np.ndarray) -> float:
        """Calculate texture complexity"""
        # Use standard deviation as a simple texture measure
        gray = np.mean(img_array, axis=2)
        return float(np.std(gray))
    
    def _analyze_composition(self, img_array: np.ndarray) -> float:
        """Analyze image composition quality"""
        # Simple composition score based on brightness distribution
        gray = np.mean(img_array, axis=2)
        height, width = gray.shape
        
        # Check for rule of thirds
        third_h, third_w = height // 3, width // 3
        center_brightness = np.mean(gray[third_h:2*third_h, third_w:2*third_w])
        overall_brightness = np.mean(gray)
        
        # Simple composition score
        return float(abs(center_brightness - overall_brightness) / 255.0)
    
    def _generate_stl_content(self, vertices: List, faces: List, precision: int) -> str:
        """Generate STL file content"""
        stl_lines = ["solid PetPlantrModel"]
        
        format_str = f"{{:.{precision}f}}"
        
        for face in faces:
            if len(face) >= 3:
                # Get vertices for this face
                v1 = vertices[face[0]] if face[0] < len(vertices) else [0, 0, 0]
                v2 = vertices[face[1]] if face[1] < len(vertices) else [0, 0, 0]
                v3 = vertices[face[2]] if face[2] < len(vertices) else [0, 0, 0]
                
                # Calculate normal (simplified)
                stl_lines.append("  facet normal 0.0 0.0 1.0")
                stl_lines.append("    outer loop")
                stl_lines.append(f"      vertex {format_str.format(v1[0])} {format_str.format(v1[1])} {format_str.format(v1[2])}")
                stl_lines.append(f"      vertex {format_str.format(v2[0])} {format_str.format(v2[1])} {format_str.format(v2[2])}")
                stl_lines.append(f"      vertex {format_str.format(v3[0])} {format_str.format(v3[1])} {format_str.format(v3[2])}")
                stl_lines.append("    endloop")
                stl_lines.append("  endfacet")
        
        stl_lines.append("endsolid PetPlantrModel")
        return "\n".join(stl_lines)
    
    def _validate_stl_file(self, filepath: str) -> Dict[str, bool]:
        """Validate STL file structure"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            validation = {
                "has_solid_header": content.startswith("solid"),
                "has_solid_footer": content.rstrip().endswith("endsolid PetPlantrModel"),
                "has_facets": "facet normal" in content,
                "has_vertices": "vertex" in content,
                "proper_structure": ("outer loop" in content and "endloop" in content)
            }
            
            return validation
            
        except Exception as e:
            return {"validation_error": False}
    
    def run_pipeline(self, image_path: str, output_dir: str = "agent_output") -> Dict[str, Any]:
        """Run the complete pipeline using the orchestrator agent"""
        if self.mock_mode:
            print("🤖 Running in mock mode...")
            # Simple mock pipeline
            return {
                "success": True,
                "message": "Mock pipeline completed",
                "breed": "mock_breed",
                "confidence": 0.85,
                "output_file": f"{output_dir}/mock_planter.stl"
            }
        
        try:
            # Use the orchestrator agent
            result = self.agents["orchestrator"].run(
                f"Process the dog image at {image_path} through the complete PetPlantr pipeline and save results to {output_dir}"
            )
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Run just the image analysis step"""
        if self.mock_mode:
            return {"success": True, "analysis": "Mock image analysis"}
        
        try:
            result = self.agents["image_analyzer"].run(
                f"Analyze the dog image at {image_path} and provide detailed insights"
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def detect_breed(self, image_path: str) -> Dict[str, Any]:
        """Run just the breed detection step"""
        if self.mock_mode:
            return {"success": True, "breed": "mock_breed", "confidence": 0.85}
        
        try:
            result = self.agents["breed_detector"].run(
                f"Detect the dog breed in the image at {image_path} with high confidence"
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    """Test the LangChain agent system"""
    print("🚀 PetPlantr LangChain Agent System")
    print("=" * 60)
    
    # Initialize agent system
    agent_system = PetPlantrAgentSystem()
    
    # Test with a sample image
    test_image = "test_pug_dog.jpg"
    
    if os.path.exists(test_image):
        print(f"\n🧪 Testing with image: {test_image}")
        
        # Test individual components
        print("\n1. 🔍 Testing Image Analysis Agent...")
        analysis_result = agent_system.analyze_image(test_image)
        print(f"Analysis result: {analysis_result}")
        
        print("\n2. 🐕 Testing Breed Detection Agent...")
        breed_result = agent_system.detect_breed(test_image)
        print(f"Breed result: {breed_result}")
        
        print("\n3. 🎯 Testing Complete Pipeline...")
        pipeline_result = agent_system.run_pipeline(test_image)
        print(f"Pipeline result: {pipeline_result}")
        
    else:
        print(f"\n⚠️  Test image {test_image} not found - running agent system setup test only")
        print("✅ Agent system initialized successfully!")
        
        # Show available agents
        if hasattr(agent_system, 'agents'):
            print(f"\n📋 Available Agents: {list(agent_system.agents.keys())}")
        
        print(f"\n🔧 Available Tools: {len(agent_system.tools) if hasattr(agent_system, 'tools') else 0}")

if __name__ == "__main__":
    main()
