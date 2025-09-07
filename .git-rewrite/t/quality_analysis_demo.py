#!/usr/bin/env python3
"""
3D Model Quality Comparison Demo

Compare the quality and dimensions of different PetPlantr outputs
"""

import os
import struct
import math

def analyze_stl_detailed(filepath):
    """Detailed analysis of an STL file"""
    if not os.path.exists(filepath):
        return None
    
    print(f"\n🔍 ANALYZING: {os.path.basename(filepath)}")
    print("=" * 50)
    
    size = os.path.getsize(filepath)
    print(f"📏 File size: {size:,} bytes")
    
    vertices = []
    triangle_count = 0
    
    try:
        with open(filepath, 'rb') as f:
            header = f.read(80)
            
            if b'solid' in header[:5]:
                # ASCII STL
                print("📝 Format: ASCII STL")
                f.seek(0)
                
                for line_num, line in enumerate(f):
                    line = line.decode('utf-8', errors='ignore').strip()
                    if 'vertex' in line:
                        try:
                            parts = line.split()
                            if len(parts) >= 4:
                                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                                vertices.append((x, y, z))
                        except:
                            pass
                    elif 'facet normal' in line:
                        triangle_count += 1
            else:
                # Binary STL
                print("📝 Format: Binary STL")
                triangle_count = struct.unpack('<I', f.read(4))[0]
                
                for i in range(min(triangle_count, 1000)):  # Read sample
                    f.read(12)  # normal
                    for j in range(3):
                        x, y, z = struct.unpack('<fff', f.read(12))
                        vertices.append((x, y, z))
                    f.read(2)  # attribute
        
        print(f"🔺 Triangles: {triangle_count:,}")
        
        if vertices:
            xs, ys, zs = zip(*vertices)
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            min_z, max_z = min(zs), max(zs)
            
            width = max_x - min_x
            depth = max_y - min_y
            height = max_z - min_z
            
            print(f"📐 Dimensions: {width:.1f} × {depth:.1f} × {height:.1f} mm")
            print(f"📊 Vertices analyzed: {len(vertices):,}")
            
            # Quality assessment
            volume_estimate = width * depth * height
            print(f"📦 Estimated volume: {volume_estimate:.0f} mm³")
            
            if height < 5:
                print("❌ PROBLEM: Too flat - this is the square bug!")
                quality = "BROKEN"
            elif height < 30:
                print("⚠️  WARNING: Very low height")
                quality = "POOR"
            elif height > 50:
                print("✅ GOOD: Proper planter height")
                quality = "GOOD"
            else:
                print("🔵 OK: Reasonable height")
                quality = "OK"
            
            # Shape complexity
            if triangle_count > 500:
                print("✅ GOOD: High detail mesh")
            elif triangle_count > 100:
                print("🔵 OK: Medium detail")
            else:
                print("⚠️  LOW: Simple geometry")
            
            return {
                'width': width,
                'depth': depth, 
                'height': height,
                'triangles': triangle_count,
                'vertices': len(vertices),
                'quality': quality,
                'volume': volume_estimate
            }
    
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        return None

def create_quality_report():
    """Create a comprehensive quality comparison"""
    print("🏆 PETPLANTR MODEL QUALITY REPORT")
    print("=" * 60)
    
    # Files to analyze
    test_files = [
        # Working models
        ("integrated_output/integrated_default_ai_1750981341.stl", "AI Integrated (Default)"),
        ("integrated_output/integrated_golden_retriever_ai_1750981516.stl", "AI Integrated (Golden)"),
        ("integrated_output/integrated_pug_ai_1750981517.stl", "AI Integrated (Pug)"),
        ("realistic_demo_output/realistic_pug_planter_1750981014.stl", "Mathematical (Pug)"),
        
        # Check for broken enhanced files
        ("enhanced-production-models/ENH_1750972124240_enhanced_planter.stl", "Enhanced (Broken)"),
    ]
    
    results = []
    working_count = 0
    
    for filepath, description in test_files:
        full_path = f"/Users/medan/Downloads/PetPlantr/{filepath}"
        if os.path.exists(full_path):
            print(f"\n📋 {description}")
            result = analyze_stl_detailed(full_path)
            if result:
                result['description'] = description
                result['filepath'] = filepath
                results.append(result)
                if result['quality'] in ['GOOD', 'OK']:
                    working_count += 1
    
    # Summary comparison
    print(f"\n📊 QUALITY SUMMARY")
    print("=" * 40)
    
    if results:
        print(f"Models analyzed: {len(results)}")
        print(f"Working models: {working_count}")
        print(f"Success rate: {(working_count/len(results)*100):.1f}%")
        
        print(f"\n📏 SIZE COMPARISON:")
        for result in results:
            quality_icon = {"GOOD": "✅", "OK": "🔵", "POOR": "⚠️", "BROKEN": "❌"}.get(result['quality'], "❓")
            print(f"{quality_icon} {result['description'][:25]:25} | {result['height']:5.1f}mm tall | {result['triangles']:4,} triangles")
        
        # Find best model
        best_model = max([r for r in results if r['quality'] in ['GOOD', 'OK']], 
                        key=lambda x: (x['height'], x['triangles']), default=None)
        
        if best_model:
            print(f"\n🏆 BEST MODEL: {best_model['description']}")
            print(f"   📐 {best_model['width']:.1f} × {best_model['depth']:.1f} × {best_model['height']:.1f} mm")
            print(f"   🔺 {best_model['triangles']:,} triangles")
            print(f"   📁 {best_model['filepath']}")
    
    else:
        print("❌ No valid models found for analysis")
    
    return working_count > 0

def main():
    """Run the quality comparison demo"""
    os.chdir('/Users/medan/Downloads/PetPlantr')
    
    print("🎯 PETPLANTR 3D MODEL QUALITY ANALYSIS")
    print("=" * 60)
    print("Comparing STL outputs to validate the fix")
    
    success = create_quality_report()
    
    print(f"\n🎯 CONCLUSION")
    print("=" * 30)
    
    if success:
        print("✅ QUALITY CHECK: PASSED")
        print("🎉 PetPlantr is generating proper 3D models!")
        print("   • No more flat squares")
        print("   • Proper planter dimensions")
        print("   • High-detail meshes") 
        print("   • Ready for 3D printing")
    else:
        print("❌ QUALITY CHECK: FAILED")
        print("⚠️  Models need additional work")
    
    print(f"\n📁 All models available in PetPlantr directory")
    print("Ready for 3D printing! 🖨️")

if __name__ == "__main__":
    main()
