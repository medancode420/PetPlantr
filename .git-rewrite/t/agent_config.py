#!/usr/bin/env python3
"""
Configuration for PetPlantr LangChain Agents

This file contains all configuration settings for the agent system.
"""

import os
from typing import Dict, Any

class AgentConfig:
    """Configuration class for PetPlantr agents"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4"
    OPENAI_TEMPERATURE = 0.1
    
    # Agent Settings
    AGENT_VERBOSE = True
    AGENT_MAX_ITERATIONS = 10
    AGENT_MEMORY_SIZE = 50
    
    # Pipeline Settings
    DEFAULT_OUTPUT_DIR = "agent_output"
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7
    DEFAULT_MODEL_SIZE = "standard"
    DEFAULT_STL_QUALITY = "high"
    
    # Image Analysis Settings
    IMAGE_ANALYSIS_DEPTH = "standard"  # quick, standard, thorough
    MAX_IMAGE_SIZE_MB = 10
    SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
    
    # Breed Detection Settings
    BREED_CONFIDENCE_THRESHOLD = 0.6
    MAX_ALTERNATIVE_BREEDS = 3
    BREED_FEATURE_ANALYSIS = True
    
    # 3D Model Settings
    MODEL_SIZES = {
        "small": {"base_size": 70, "detail_level": "low", "triangle_limit": 800},
        "standard": {"base_size": 100, "detail_level": "medium", "triangle_limit": 1200},
        "large": {"base_size": 150, "detail_level": "high", "triangle_limit": 2000}
    }
    
    # STL Export Settings
    STL_QUALITY_LEVELS = {
        "low": {"precision": 1, "validation": False, "compression": True},
        "medium": {"precision": 2, "validation": True, "compression": False},
        "high": {"precision": 3, "validation": True, "compression": False}
    }
    
    # Error Handling
    MAX_RETRY_ATTEMPTS = 3
    FALLBACK_TO_MOCK = True
    ERROR_LOGGING = True
    
    # Performance Settings
    PARALLEL_PROCESSING = False  # For future implementation
    CACHE_RESULTS = True
    CACHE_DURATION_HOURS = 24
    
    @classmethod
    def get_agent_prompts(cls) -> Dict[str, str]:
        """Get specialized prompts for each agent"""
        return {
            "image_analyzer": """
            You are an expert Image Analysis Agent for PetPlantr. Analyze dog images for:
            - Image quality and clarity
            - Composition and framing
            - Visual features and characteristics
            - Suitability for breed detection
            
            Provide detailed, actionable insights and recommendations.
            """,
            
            "breed_detector": """
            You are a Breed Detection Specialist. Your expertise includes:
            - Identifying dog breeds with high accuracy
            - Analyzing breed-specific physical characteristics
            - Providing confidence assessments
            - Suggesting alternative possibilities
            
            Always explain your reasoning and provide confidence scores.
            """,
            
            "model_generator": """
            You are a 3D Model Generation Expert specializing in breed-specific planters:
            - Translate breed characteristics into 3D geometry
            - Optimize for 3D printing requirements
            - Balance aesthetic appeal with functionality
            - Ensure proper planter specifications
            
            Consider both artistic representation and practical use.
            """,
            
            "stl_exporter": """
            You are an STL Export and Quality Control Specialist:
            - Export models to high-quality STL files
            - Validate file integrity and printability
            - Optimize file size and manufacturing compatibility
            - Ensure 3D printing standards compliance
            
            Always verify quality and provide assessments.
            """,
            
            "orchestrator": """
            You are the Pipeline Orchestrator managing the complete PetPlantr workflow:
            - Coordinate end-to-end pipeline execution
            - Handle errors and implement recovery strategies
            - Optimize workflow efficiency
            - Provide comprehensive status updates
            
            Ensure seamless coordination between all processing steps.
            """
        }
    
    @classmethod
    def get_tool_descriptions(cls) -> Dict[str, str]:
        """Get detailed descriptions for each tool"""
        return {
            "analyze_dog_image": """
            Advanced image analysis tool that extracts visual features, quality metrics,
            and composition data from dog images. Supports multiple analysis depths.
            """,
            
            "detect_dog_breed": """
            AI-powered breed detection using trained neural networks. Provides breed
            predictions with confidence scores and alternative possibilities.
            """,
            
            "generate_3d_model": """
            3D model generator that creates breed-specific planter designs based on
            physical characteristics and user specifications.
            """,
            
            "export_stl_file": """
            STL file export tool with quality control and validation. Optimizes for
            3D printing and ensures manufacturing compatibility.
            """,
            
            "orchestrate_pipeline": """
            Complete pipeline orchestration tool that manages the full workflow from
            image input to STL output with error handling and optimization.
            """
        }
    
    @classmethod
    def get_error_messages(cls) -> Dict[str, str]:
        """Get standardized error messages"""
        return {
            "image_not_found": "Image file not found at specified path",
            "invalid_image_format": "Unsupported image format",
            "image_too_large": "Image file exceeds maximum size limit",
            "low_confidence": "Breed detection confidence below threshold",
            "model_generation_failed": "3D model generation failed",
            "stl_export_failed": "STL file export failed",
            "validation_failed": "File validation failed",
            "api_key_missing": "OpenAI API key not found",
            "langchain_unavailable": "LangChain dependencies not available"
        }
    
    @classmethod
    def get_success_messages(cls) -> Dict[str, str]:
        """Get standardized success messages"""
        return {
            "image_analyzed": "Image analysis completed successfully",
            "breed_detected": "Breed detection completed with high confidence",
            "model_generated": "3D model generated successfully",
            "stl_exported": "STL file exported and validated",
            "pipeline_complete": "Complete pipeline executed successfully"
        }
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validate configuration settings"""
        validation = {
            "openai_key_available": bool(cls.OPENAI_API_KEY),
            "output_dir_writable": True,  # Will be checked at runtime
            "image_formats_valid": len(cls.SUPPORTED_IMAGE_FORMATS) > 0,
            "model_sizes_valid": len(cls.MODEL_SIZES) > 0,
            "quality_levels_valid": len(cls.STL_QUALITY_LEVELS) > 0
        }
        
        try:
            # Test output directory
            os.makedirs(cls.DEFAULT_OUTPUT_DIR, exist_ok=True)
            test_file = os.path.join(cls.DEFAULT_OUTPUT_DIR, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except:
            validation["output_dir_writable"] = False
        
        return validation

# Example usage configurations
EXAMPLE_CONFIGS = {
    "quick_analysis": {
        "image_analysis_depth": "quick",
        "confidence_threshold": 0.5,
        "model_size": "small",
        "stl_quality": "medium"
    },
    
    "standard_processing": {
        "image_analysis_depth": "standard",
        "confidence_threshold": 0.7,
        "model_size": "standard",
        "stl_quality": "high"
    },
    
    "thorough_analysis": {
        "image_analysis_depth": "thorough",
        "confidence_threshold": 0.8,
        "model_size": "large",
        "stl_quality": "high"
    },
    
    "production_ready": {
        "image_analysis_depth": "thorough",
        "confidence_threshold": 0.9,
        "model_size": "standard",
        "stl_quality": "high",
        "validation": True,
        "backup_models": True
    }
}

def get_config_for_use_case(use_case: str) -> Dict[str, Any]:
    """Get configuration for specific use case"""
    return EXAMPLE_CONFIGS.get(use_case, EXAMPLE_CONFIGS["standard_processing"])

def main():
    """Test configuration validation"""
    print("🔧 PetPlantr Agent Configuration")
    print("=" * 50)
    
    # Validate configuration
    validation = AgentConfig.validate_config()
    
    print("📋 Configuration Validation:")
    for key, value in validation.items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {value}")
    
    # Show available configurations
    print(f"\n📦 Available Use Cases:")
    for use_case in EXAMPLE_CONFIGS.keys():
        print(f"   • {use_case}")
    
    # Show agent prompts
    print(f"\n🤖 Available Agents:")
    for agent_name in AgentConfig.get_agent_prompts().keys():
        print(f"   • {agent_name}")
    
    print(f"\n🔧 Available Tools:")
    for tool_name in AgentConfig.get_tool_descriptions().keys():
        print(f"   • {tool_name}")

if __name__ == "__main__":
    main()
