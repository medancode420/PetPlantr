#!/usr/bin/env python3
"""
Quality Gate and Radar Scoring for PetPlantr
Quick Win #4 - Automated quality validation
"""

import os
import numpy as np
from pathlib import Path
import json
import time
import argparse
from typing import Dict, List, Tuple
import subprocess
import sys

try:
    import trimesh
    import open3d as o3d
    from PIL import Image
    STL_PROCESSING_AVAILABLE = True
except ImportError:
    print("⚠️  3D processing libraries not available. Install: pip install trimesh open3d")
    STL_PROCESSING_AVAILABLE = False

class STLQualityAnalyzer:
    def __init__(self):
        self.quality_thresholds = {
            "min_radar_score": 90,
            "min_vertices": 1000,
            "max_vertices": 100000,
            "min_faces": 500,
            "max_faces": 50000,
            "min_volume": 0.1,
            "max_aspect_ratio": 5.0,
            "min_manifold_score": 0.8
        }
        
        self.scoring_weights = {
            "shape_complexity": 0.30,    # 30% - geometric complexity
            "dog_likeness": 0.40,        # 40% - dog-specific features
            "mesh_quality": 0.20,        # 20% - technical mesh quality
            "printability": 0.10         # 10% - 3D printing feasibility
        }

    def analyze_stl_file(self, stl_path: str) -> Dict:
        """Comprehensive STL file analysis"""
        if not STL_PROCESSING_AVAILABLE:
            return self._mock_analysis()
        
        try:
            # Load mesh
            mesh = trimesh.load(stl_path)
            
            if mesh is None:
                raise ValueError("Failed to load STL file")
            
            # Basic mesh properties
            analysis = {
                "file_path": stl_path,
                "file_size_mb": os.path.getsize(stl_path) / (1024 * 1024),
                "vertex_count": len(mesh.vertices),
                "face_count": len(mesh.faces),
                "volume": float(mesh.volume) if hasattr(mesh, 'volume') else 0.0,
                "surface_area": float(mesh.area) if hasattr(mesh, 'area') else 0.0,
                "is_watertight": mesh.is_watertight if hasattr(mesh, 'is_watertight') else False,
                "bounds": mesh.bounds.tolist() if hasattr(mesh, 'bounds') else [[0,0,0], [1,1,1]]
            }
            
            # Calculate derived metrics
            bounds = np.array(analysis["bounds"])
            dimensions = bounds[1] - bounds[0]
            analysis["dimensions"] = dimensions.tolist()
            analysis["aspect_ratio"] = np.max(dimensions) / np.min(dimensions) if np.min(dimensions) > 0 else 999
            
            # Quality scores
            analysis.update(self._calculate_quality_scores(mesh, analysis))
            
            return analysis
            
        except Exception as e:
            return {
                "error": str(e),
                "file_path": stl_path,
                "radar_score": 0
            }

    def _calculate_quality_scores(self, mesh, basic_analysis: Dict) -> Dict:
        """Calculate quality scoring components"""
        
        scores = {}
        
        # 1. Shape Complexity Score (30%)
        vertex_count = basic_analysis["vertex_count"]
        face_count = basic_analysis["face_count"]
        
        complexity_score = min(100, (vertex_count / 5000) * 50 + (face_count / 2500) * 50)
        scores["shape_complexity_score"] = complexity_score
        
        # 2. Dog-likeness Score (40%)
        # Analyze geometric features that suggest dog-like characteristics
        dog_score = self._analyze_dog_features(mesh, basic_analysis)
        scores["dog_likeness_score"] = dog_score
        
        # 3. Mesh Quality Score (20%)
        mesh_quality = self._analyze_mesh_quality(mesh, basic_analysis)
        scores["mesh_quality_score"] = mesh_quality
        
        # 4. Printability Score (10%)
        print_score = self._analyze_printability(mesh, basic_analysis)
        scores["printability_score"] = print_score
        
        # Calculate weighted radar score
        radar_score = (
            complexity_score * self.scoring_weights["shape_complexity"] +
            dog_score * self.scoring_weights["dog_likeness"] +
            mesh_quality * self.scoring_weights["mesh_quality"] +
            print_score * self.scoring_weights["printability"]
        )
        
        scores["radar_score"] = round(radar_score, 1)
        scores["quality_grade"] = self._get_quality_grade(radar_score)
        
        return scores

    def _analyze_dog_features(self, mesh, analysis: Dict) -> float:
        """Analyze geometric features suggesting dog-like characteristics"""
        
        dog_score = 50.0  # Base score
        
        # Check proportions (dogs have certain aspect ratios)
        dimensions = np.array(analysis["dimensions"])
        aspect_ratio = analysis["aspect_ratio"]
        
        # Dogs typically have length > height > width
        if 1.5 <= aspect_ratio <= 3.0:
            dog_score += 20
        elif 1.2 <= aspect_ratio <= 4.0:
            dog_score += 10
        
        # Volume analysis (reasonable dog size)
        volume = analysis["volume"]
        if 0.1 <= volume <= 10.0:  # Reasonable planter size
            dog_score += 15
        
        # Complexity suggests detailed features
        vertex_count = analysis["vertex_count"]
        if vertex_count > 2000:  # Enough detail for features
            dog_score += 15
        
        # Check for potential head/body separation (simple heuristic)
        if hasattr(mesh, 'convex_hull'):
            try:
                hull_volume = mesh.convex_hull.volume
                volume_ratio = volume / hull_volume if hull_volume > 0 else 0
                if 0.3 <= volume_ratio <= 0.8:  # Suggests internal structure
                    dog_score += 10
            except:
                pass
        
        return min(100, max(0, dog_score))

    def _analyze_mesh_quality(self, mesh, analysis: Dict) -> float:
        """Analyze technical mesh quality"""
        
        quality_score = 50.0
        
        # Watertight mesh (essential for 3D printing)
        if analysis["is_watertight"]:
            quality_score += 25
        
        # Reasonable triangle count
        face_count = analysis["face_count"]
        if 1000 <= face_count <= 20000:
            quality_score += 20
        elif 500 <= face_count <= 50000:
            quality_score += 10
        
        # Check for degenerate triangles (simple test)
        try:
            if hasattr(mesh, 'remove_degenerate_faces'):
                clean_mesh = mesh.copy()
                clean_mesh.remove_degenerate_faces()
                degenerate_ratio = 1.0 - (len(clean_mesh.faces) / len(mesh.faces))
                if degenerate_ratio < 0.05:  # Less than 5% degenerate
                    quality_score += 15
        except:
            pass
        
        # Surface area to volume ratio (efficiency)
        volume = analysis["volume"]
        surface_area = analysis["surface_area"]
        if volume > 0 and surface_area > 0:
            sa_vol_ratio = surface_area / (volume ** (2/3))
            if 5 <= sa_vol_ratio <= 20:  # Reasonable efficiency
                quality_score += 10
        
        return min(100, max(0, quality_score))

    def _analyze_printability(self, mesh, analysis: Dict) -> float:
        """Analyze 3D printing feasibility"""
        
        print_score = 60.0  # Base printability
        
        # Reasonable size for 3D printing
        dimensions = np.array(analysis["dimensions"])
        max_dim = np.max(dimensions)
        min_dim = np.min(dimensions)
        
        if 20 <= max_dim <= 200:  # Reasonable print size (mm)
            print_score += 20
        
        if min_dim >= 2:  # Minimum feature size
            print_score += 10
        
        # Check for overhangs (simplified)
        try:
            # Simple overhang detection based on face normals
            if hasattr(mesh, 'face_normals'):
                normals = mesh.face_normals
                up_vector = np.array([0, 0, 1])
                angles = np.arccos(np.clip(np.dot(normals, up_vector), -1, 1))
                overhang_faces = np.sum(angles > np.pi/4)  # >45 degree overhangs
                overhang_ratio = overhang_faces / len(normals)
                
                if overhang_ratio < 0.2:  # Less than 20% overhangs
                    print_score += 10
        except:
            pass
        
        return min(100, max(0, print_score))

    def _get_quality_grade(self, radar_score: float) -> str:
        """Convert radar score to letter grade"""
        if radar_score >= 95:
            return "A+"
        elif radar_score >= 90:
            return "A"
        elif radar_score >= 85:
            return "B+"
        elif radar_score >= 80:
            return "B"
        elif radar_score >= 75:
            return "C+"
        elif radar_score >= 70:
            return "C"
        elif radar_score >= 60:
            return "D"
        else:
            return "F"

    def _mock_analysis(self) -> Dict:
        """Mock analysis when 3D libraries not available"""
        return {
            "file_path": "mock_analysis",
            "file_size_mb": 1.5,
            "vertex_count": 3000,
            "face_count": 1500,
            "volume": 2.5,
            "surface_area": 15.0,
            "is_watertight": True,
            "dimensions": [50, 30, 40],
            "aspect_ratio": 1.67,
            "shape_complexity_score": 75,
            "dog_likeness_score": 85,
            "mesh_quality_score": 90,
            "printability_score": 88,
            "radar_score": 84.5,
            "quality_grade": "B+",
            "mock_mode": True
        }

def quality_gate_check(stl_path: str, min_score: float = 90) -> Tuple[bool, Dict]:
    """Quality gate check for CI/CD pipeline"""
    
    print(f"🔍 Running Quality Gate Check")
    print(f"   File: {stl_path}")
    print(f"   Minimum Score: {min_score}")
    print("-" * 60)
    
    analyzer = STLQualityAnalyzer()
    analysis = analyzer.analyze_stl_file(stl_path)
    
    if "error" in analysis:
        print(f"❌ Analysis Failed: {analysis['error']}")
        return False, analysis
    
    radar_score = analysis.get("radar_score", 0)
    quality_grade = analysis.get("quality_grade", "F")
    
    # Print detailed results
    print(f"📊 Quality Analysis Results:")
    print(f"   Radar Score: {radar_score}/100 (Grade: {quality_grade})")
    print(f"   Shape Complexity: {analysis.get('shape_complexity_score', 0)}/100")
    print(f"   Dog-likeness: {analysis.get('dog_likeness_score', 0)}/100")
    print(f"   Mesh Quality: {analysis.get('mesh_quality_score', 0)}/100")
    print(f"   Printability: {analysis.get('printability_score', 0)}/100")
    
    print(f"\n📏 Technical Metrics:")
    print(f"   Vertices: {analysis.get('vertex_count', 0):,}")
    print(f"   Faces: {analysis.get('face_count', 0):,}")
    print(f"   Volume: {analysis.get('volume', 0):.2f}")
    print(f"   Watertight: {analysis.get('is_watertight', False)}")
    print(f"   Dimensions: {analysis.get('dimensions', [0,0,0])}")
    
    # Gate decision
    passed = radar_score >= min_score
    
    if passed:
        print(f"\n✅ QUALITY GATE PASSED")
        print(f"   Score {radar_score} meets minimum threshold {min_score}")
    else:
        print(f"\n❌ QUALITY GATE FAILED")
        print(f"   Score {radar_score} below minimum threshold {min_score}")
        print(f"   🔧 Recommendations:")
        
        if analysis.get('dog_likeness_score', 0) < 80:
            print(f"      - Improve dog-specific feature detection")
        if analysis.get('mesh_quality_score', 0) < 80:
            print(f"      - Fix mesh quality issues (watertight, degenerates)")
        if analysis.get('shape_complexity_score', 0) < 70:
            print(f"      - Increase geometric detail and complexity")
        if analysis.get('printability_score', 0) < 80:
            print(f"      - Address 3D printing constraints")
    
    return passed, analysis

def batch_quality_analysis(directory: str, output_file: str = None):
    """Run quality analysis on multiple STL files"""
    
    stl_files = list(Path(directory).glob("*.stl"))
    
    if not stl_files:
        print(f"❌ No STL files found in {directory}")
        return
    
    print(f"📊 Batch Quality Analysis")
    print(f"   Directory: {directory}")
    print(f"   Files: {len(stl_files)}")
    print("-" * 60)
    
    analyzer = STLQualityAnalyzer()
    results = []
    
    for stl_file in stl_files:
        print(f"\n🔍 Analyzing {stl_file.name}...")
        analysis = analyzer.analyze_stl_file(str(stl_file))
        analysis["filename"] = stl_file.name
        results.append(analysis)
        
        if "error" not in analysis:
            score = analysis.get("radar_score", 0)
            grade = analysis.get("quality_grade", "F")
            print(f"   Score: {score}/100 (Grade: {grade})")
    
    # Summary statistics
    valid_results = [r for r in results if "error" not in r]
    if valid_results:
        scores = [r["radar_score"] for r in valid_results]
        avg_score = np.mean(scores)
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        print(f"\n📈 Summary Statistics:")
        print(f"   Average Score: {avg_score:.1f}")
        print(f"   Min Score: {min_score:.1f}")
        print(f"   Max Score: {max_score:.1f}")
        print(f"   Files above 90: {sum(s >= 90 for s in scores)}/{len(scores)}")
    
    # Save detailed results
    if output_file:
        report = {
            "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "directory": directory,
            "total_files": len(stl_files),
            "valid_analyses": len(valid_results),
            "summary": {
                "avg_score": avg_score if valid_results else 0,
                "min_score": min_score if valid_results else 0,
                "max_score": max_score if valid_results else 0,
                "high_quality_count": sum(s >= 90 for s in scores) if valid_results else 0
            },
            "detailed_results": results
        }
        
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="PetPlantr Quality Gate")
    parser.add_argument("--stl_path", type=str, help="Path to STL file for single analysis")
    parser.add_argument("--min_score", type=float, default=90, help="Minimum radar score")
    parser.add_argument("--batch_dir", type=str, help="Directory for batch analysis")
    parser.add_argument("--output", type=str, help="Output file for results")
    parser.add_argument("--ci", action="store_true", help="CI mode (exit with error code)")
    
    args = parser.parse_args()
    
    if args.stl_path:
        # Single file analysis
        passed, analysis = quality_gate_check(args.stl_path, args.min_score)
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(analysis, f, indent=2)
        
        if args.ci and not passed:
            sys.exit(1)  # Fail CI pipeline
            
    elif args.batch_dir:
        # Batch analysis
        batch_quality_analysis(args.batch_dir, args.output)
        
    else:
        # Demo analysis
        print("🎪 PetPlantr Quality Gate Demo")
        print("=" * 60)
        
        # Look for any STL files in current directory
        stl_files = list(Path(".").glob("*.stl"))
        
        if stl_files:
            print(f"Found {len(stl_files)} STL files for demo analysis:")
            for stl_file in stl_files[:3]:  # Analyze first 3 files
                print(f"\n" + "="*60)
                passed, analysis = quality_gate_check(str(stl_file))
        else:
            print("No STL files found for demo.")
            print("\nUsage examples:")
            print("  python quality_gate.py --stl_path model.stl --min_score 90")
            print("  python quality_gate.py --batch_dir outputs/ --output report.json")
            print("  python quality_gate.py --stl_path model.stl --ci  # For CI/CD")

if __name__ == "__main__":
    main()
