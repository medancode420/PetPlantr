#!/usr/bin/env python3
"""
Enhanced DALL-E Prompt Generator - ANTI-TERRAIN VERSION
======================================================
Prevents "terrain drift" by using highly specific prompts that force
DALL-E to generate proper dog planters instead of height maps.
"""

class EnhancedPlanterPrompts:
    """Anti-terrain prompt templates that force proper 3D planter generation"""
    
    @staticmethod
    def get_primary_prompt(breed: str, pet_name: str = "") -> str:
        """Primary prompt template - prevents terrain generation"""
        name_part = f" named {pet_name}" if pet_name else ""
        
        return (
            f"professional product photography, museum-quality ceramic planter shaped like a {breed} dog{name_part}, "
            f"dog sitting upright with chest forward, realistic fur texture details, "
            f"hollow cylindrical planter cavity clearly visible on the dog's back, "
            f"pure white seamless studio background, no shadows, no reflections, "
            f"front orthographic view, center composition, studio lighting setup, "
            f"no landscape elements, no terrain, no topographic patterns, no height maps, "
            f"no ground plane, no grass, no outdoor elements, no environmental context, "
            f"clean isolated product shot, 8k resolution, pottery craftsmanship quality, "
            f"white backdrop extends to all edges, commercial product photography style"
        )
    
    @staticmethod
    def get_fallback_prompt(breed: str, pet_name: str = "") -> str:
        """Fallback prompt if primary fails"""
        name_part = f" named {pet_name}" if pet_name else ""
        
        return (
            f"studio photograph of ceramic {breed} dog{name_part} planter sculpture, "
            f"sitting position with planter cavity on back, detailed breed features, "
            f"pure white studio background with no texture, professional lighting, "
            f"front view composition, no terrain or landscape elements, "
            f"clean commercial product photography, isolated subject, "
            f"white seamless backdrop, museum quality craftsmanship"
        )
    
    @staticmethod
    def get_emergency_prompt(breed: str, pet_name: str = "") -> str:
        """Emergency prompt for maximum specificity"""
        name_part = f" named {pet_name}" if pet_name else ""
        
        return (
            f"ceramic {breed} dog{name_part} planter sculpture, sitting upright, "
            f"3D pottery object, hollow cavity for plants, realistic dog features, "
            f"white studio background, product photography, NOT a landscape, "
            f"NOT a terrain map, NOT topographic, sculptural art piece"
        )
    
    @staticmethod
    def get_ultra_clean_prompt(breed: str, pet_name: str = "") -> str:
        """Ultra-clean prompt for maximum studio quality"""
        name_part = f" named {pet_name}" if pet_name else ""
        
        return (
            f"minimalist product photo: ceramic {breed} dog{name_part} planter on pure white, "
            f"sitting pose, planter hole visible on back, no background texture, "
            f"no shadows, no reflections, completely white backdrop, "
            f"front view, centered, studio quality, isolated object, "
            f"commercial photography style, clean edges, no environment"
        )
    
    @staticmethod
    def detect_terrain_keywords(description: str) -> bool:
        """Check if image analysis suggests terrain instead of planter"""
        terrain_keywords = [
            'landscape', 'terrain', 'topographic', 'map', 'height map',
            'elevation', 'contour', 'geographical', 'satellite', 'aerial',
            'flat surface', 'ground plane', 'outdoor scene', 'field', 'grass field'
        ]
        
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in terrain_keywords)
    
    @staticmethod
    def get_anti_terrain_suffix() -> str:
        """Suffix to append to any prompt to prevent terrain generation"""
        return (
            " --no landscape --no terrain --no topographic map --no height map "
            "--no outdoor scene --style product photography --background white studio"
        )
    
    @staticmethod
    def get_anti_terrain_prompt(breed, pet_analysis=""):
        """
        Generate prompt that specifically prevents terrain/height-map generation
        """
        
        # Core prompt structure that prevents terrain interpretation
        base_prompt = f"""Ultra-realistic ceramic planter shaped like a {breed} dog, 
dog sitting upright in a noble pose, chest forward, detailed fur texture, 
functional planter with cavity opening on the back/top, 
professional product photography, studio lighting, 
seamless white backdrop, museum quality ceramic sculpture, 
8k photorealistic render"""
        
        # Anti-terrain reinforcement
        anti_terrain = """NO grass, NO landscape, NO topographic map, NO height map, 
NO terrain tiles, NO flat surface patterns, NOT a relief carving, 
NOT a top-down view, this is a full 3D sculptural object"""
        
        # Positive reinforcement for 3D structure
        positive_3d = """three-dimensional sculpture, fully rounded form, 
visible from all angles, solid ceramic construction, 
clearly defined dog features including ears, snout, and body, 
sitting position with recognizable dog anatomy"""
        
        # Planter-specific details
        planter_details = """functional planter design with plant cavity, 
suitable for small plants or succulents, 
drainage considerations, stable base for tabletop display"""
        
        # Combine with specific breed characteristics if available
        breed_specific = ""
        if "golden retriever" in breed.lower():
            breed_specific = "long flowing coat, friendly expression, medium to large size"
        elif "pug" in breed.lower():
            breed_specific = "wrinkled face, compact body, short coat, small size"
        elif "german shepherd" in breed.lower():
            breed_specific = "erect ears, alert expression, medium-long coat"
        elif "labrador" in breed.lower():
            breed_specific = "friendly face, short coat, sturdy build"
        elif "chihuahua" in breed.lower():
            breed_specific = "small size, large ears, compact build"
        elif "beagle" in breed.lower():
            breed_specific = "tri-color coat, floppy ears, compact body"
        
        # Final assembly
        complete_prompt = f"{base_prompt}. {positive_3d}. {planter_details}."
        
        if breed_specific:
            complete_prompt += f" Breed characteristics: {breed_specific}."
            
        complete_prompt += f" {anti_terrain}."
        
        return complete_prompt
    
    @staticmethod
    def get_fallback_prompts(breed):
        """
        Alternative prompts if the first attempt fails
        """
        return [
            # Prompt 2: Product photography angle
            f"""Professional product photograph of a {breed} dog ceramic planter, 
            3D sculptural form, sitting dog pose, hollow cavity for plants, 
            white studio background, high-end pottery, museum piece quality, 
            orthographic front view, no landscape elements""",
            
            # Prompt 3: Sculpture emphasis
            f"""Handcrafted ceramic sculpture of a {breed} dog designed as a planter, 
            three-dimensional art piece, sitting upright position, 
            detailed canine features, functional plant container, 
            professional art photography, gallery lighting, 
            solid sculptural form, not a relief or pattern""",
            
            # Prompt 4: Technical description
            f"""3D rendered {breed} dog planter model, 
            volumetric sculpture with depth and dimension, 
            realistic dog anatomy in sitting position, 
            ceramic material finish, plant cavity integration, 
            technical product visualization, 
            neutral background, no topographical elements"""
        ]
    
    @staticmethod
    def validate_concept_image(image_path):
        """
        Basic validation to check if the generated image looks like a 3D dog planter
        vs. a terrain/height map
        """
        try:
            from PIL import Image
            import numpy as np
            
            img = Image.open(image_path).convert('RGB')
            img_array = np.array(img)
            
            # Check for terrain-like patterns
            # Terrain images tend to have:
            # 1. Very uniform color gradients
            # 2. Lack of distinct object boundaries
            # 3. Repeating patterns
            
            # Simple heuristics
            height, width, _ = img_array.shape
            
            # Check color variance (terrain tends to be very uniform)
            color_variance = np.var(img_array)
            
            # Check for distinct object vs. background
            gray = np.mean(img_array, axis=2)
            edge_intensity = np.sum(np.abs(np.diff(gray, axis=0))) + np.sum(np.abs(np.diff(gray, axis=1)))
            edge_ratio = edge_intensity / (height * width)
            
            # Scoring
            is_likely_3d_object = True
            issues = []
            
            if color_variance < 1000:  # Very low variance suggests flat pattern
                is_likely_3d_object = False
                issues.append("Low color variance - may be flat pattern")
            
            if edge_ratio < 0.5:  # Very few edges suggests smooth gradient
                is_likely_3d_object = False
                issues.append("Low edge definition - may be smooth terrain")
            
            return {
                'is_valid_3d_object': is_likely_3d_object,
                'color_variance': float(color_variance),
                'edge_ratio': float(edge_ratio),
                'issues': issues,
                'confidence': 'high' if is_likely_3d_object else 'low'
            }
            
        except Exception as e:
            return {
                'is_valid_3d_object': False,
                'error': str(e),
                'confidence': 'unknown'
            }

def test_prompt_generation():
    """Test the prompt generation system"""
    
    prompts = EnhancedPlanterPrompts()
    
    # Test different breeds
    breeds = ["Golden Retriever", "Pug", "German Shepherd", "Chihuahua", "Mixed Breed"]
    
    print("🎨 ENHANCED PROMPT GENERATION TESTS")
    print("=" * 60)
    
    for breed in breeds:
        print(f"\n🐕 {breed.upper()}:")
        print("-" * 40)
        
        main_prompt = prompts.get_anti_terrain_prompt(breed)
        print(f"Main prompt ({len(main_prompt)} chars):")
        print(f"'{main_prompt[:100]}...'")
        
        fallbacks = prompts.get_fallback_prompts(breed)
        print(f"Fallback prompts: {len(fallbacks)} available")
        
        # Test validation placeholder
        validation = prompts.validate_concept_image("test_placeholder.png")
        print(f"Validation framework: Ready")

if __name__ == "__main__":
    test_prompt_generation()
