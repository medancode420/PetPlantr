#!/usr/bin/env python3
"""
Test the improved DALL-E prompts
"""

import os
from dalle_planter_generator import DallePlanterGenerator

def test_enhanced_prompts():
    """Test the enhanced DALL-E prompts"""
    generator = DallePlanterGenerator()
    
    # Test pet analysis examples
    test_analyses = [
        {
            'description': 'This is a pug dog with a flat, wrinkled face and compact stocky body. The dog has large round eyes and a curly tail. Medium size breed with distinctive brachycephalic features.',
            'timestamp': 1234567890
        },
        {
            'description': 'Golden retriever with long feathery coat, gentle expression, and medium-length snout. Large breed dog with sturdy but elegant build and friendly demeanor.',
            'timestamp': 1234567890  
        },
        {
            'description': 'Small chihuahua with large erect ears and apple-shaped skull. Tiny delicate build with confident expression despite small stature.',
            'timestamp': 1234567890
        }
    ]
    
    print("🧪 Testing Enhanced DALL-E Prompts")
    print("=" * 50)
    
    for i, analysis in enumerate(test_analyses, 1):
        print(f"\n🐕 Test {i}: {analysis['description'][:50]}...")
        
        # Test breed enhancement
        base_prompt = "Create a 3D planter design for this pet"
        enhanced = generator.enhance_prompt_for_breed(base_prompt, analysis)
        
        print(f"📝 Enhanced prompt preview:")
        print(f"   {enhanced[:200]}...")
        
        # Test alternative prompts
        alternatives = generator.generate_alternative_prompts(analysis)
        print(f"🔄 Generated {len(alternatives)} alternative prompts")
        
        for j, alt in enumerate(alternatives):
            print(f"   Alt {j+1}: {alt[:100]}...")
    
    print(f"\n✅ Prompt testing complete!")
    print(f"💡 The prompts now include:")
    print(f"   • Breed-specific anatomical details")
    print(f"   • 3D printing optimization notes") 
    print(f"   • Professional product photography specs")
    print(f"   • Size-appropriate design guidance")
    print(f"   • Multiple fallback prompt styles")

if __name__ == "__main__":
    test_enhanced_prompts()
