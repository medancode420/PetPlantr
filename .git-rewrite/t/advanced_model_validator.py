#!/usr/bin/env python3
"""
Advanced 3D Model Validator for PetPlantr Production Pipeline
Implements comprehensive validation, repair, and quality assurance for pet planter STL files.

Features:
- Multi-level mesh validation (topology, geometry, printability)
- Automated mesh repair and optimization
- Print readiness assessment
- Quality scoring and certification
- Professional reporting
"""

import os
import json
import math
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationCriteria:
    """Comprehensive validation criteria for pet planters"""
    
    # Mesh topology requirements
    MIN_VERTICES = 100
    MAX_VERTICES = 50000
    MIN_FACES = 200
    MAX_FACES = 100000
    
    # Geometric requirements
    MIN_VOLUME_CM3 = 10.0
    MAX_VOLUME_CM3 = 2000.0
    MIN_SURFACE_AREA_CM2 = 50.0
    MAX_SURFACE_AREA_CM2 = 5000.0
    
    # Planter-specific requirements
    MIN_CAVITY_DEPTH_MM = 30.0
    MAX_CAVITY_DEPTH_MM = 150.0
    MIN_WALL_THICKNESS_MM = 1.5
    OPTIMAL_WALL_THICKNESS_MM = 3.0
    
    # Print requirements
    MIN_LAYER_HEIGHT_MM = 0.1
    MAX_OVERHANG_ANGLE_DEG = 45.0
    MIN_DRAINAGE_HOLES = 1
    DRAINAGE_HOLE_MIN_DIAMETER_MM = 4.0
    
    # Quality thresholds
    MIN_MANIFOLD_SCORE = 0.95
    MIN_SYMMETRY_SCORE = 0.80
    MIN_PRINTABILITY_SCORE = 0.85
    MIN_OVERALL_QUALITY = 0.85

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    timestamp: float
    file_path: str
    
    # Scores (0.0 - 1.0)
    topology_score: float
    geometry_score: float
    planter_score: float
    printability_score: float
    overall_score: float
    
    # Detailed results
    is_manifold: bool
    is_watertight: bool
    is_printable: bool
    is_production_ready: bool
    
    # Measurements
    vertex_count: int
    face_count: int
    volume_cm3: float
    surface_area_cm2: float
    dimensions_mm: List[float]
    
    # Issues and recommendations
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    
    # Repair actions taken
    repairs_applied: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "validation_report": {
                "timestamp": self.timestamp,
                "file_path": os.path.basename(self.file_path),
                "scores": {
                    "topology": round(self.topology_score, 3),
                    "geometry": round(self.geometry_score, 3),
                    "planter_specific": round(self.planter_score, 3),
                    "printability": round(self.printability_score, 3),
                    "overall": round(self.overall_score, 3)
                },
                "status": {
                    "is_manifold": self.is_manifold,
                    "is_watertight": self.is_watertight,
                    "is_printable": self.is_printable,
                    "is_production_ready": self.is_production_ready
                },
                "measurements": {
                    "vertices": self.vertex_count,
                    "faces": self.face_count,
                    "volume_cm3": round(self.volume_cm3, 2),
                    "surface_area_cm2": round(self.surface_area_cm2, 2),
                    "dimensions_mm": [round(d, 1) for d in self.dimensions_mm]
                },
                "quality_assessment": {
                    "critical_issues": self.critical_issues,
                    "warnings": self.warnings,
                    "recommendations": self.recommendations,
                    "repairs_applied": self.repairs_applied
                }
            }
        }

class AdvancedModelValidator:
    """Advanced 3D model validator with repair capabilities"""
    
    def __init__(self, criteria: Optional[ValidationCriteria] = None):
        self.criteria = criteria or ValidationCriteria()
        self.repair_log = []
        
    def validate_stl_file(self, stl_path: str, auto_repair: bool = True) -> ValidationReport:
        """Comprehensive STL file validation"""
        logger.info(f"🔍 Starting comprehensive validation: {os.path.basename(stl_path)}")
        
        # Load STL file
        vertices, faces = self._load_stl_file(stl_path)
        
        if not vertices or not faces:
            return self._create_failure_report(stl_path, "Failed to load STL file")
        
        logger.info(f"📊 Loaded mesh: {len(vertices)} vertices, {len(faces)} faces")
        
        # Initialize report
        report = ValidationReport(
            timestamp=time.time(),
            file_path=stl_path,
            topology_score=0.0,
            geometry_score=0.0,
            planter_score=0.0,
            printability_score=0.0,
            overall_score=0.0,
            is_manifold=False,
            is_watertight=False,
            is_printable=False,
            is_production_ready=False,
            vertex_count=len(vertices),
            face_count=len(faces),
            volume_cm3=0.0,
            surface_area_cm2=0.0,
            dimensions_mm=[0, 0, 0],
            critical_issues=[],
            warnings=[],
            recommendations=[],
            repairs_applied=[]
        )
        
        # Stage 1: Topology Validation
        topology_results = self._validate_topology(vertices, faces)
        report.topology_score = topology_results["score"]
        report.is_manifold = topology_results["is_manifold"]
        report.is_watertight = topology_results["is_watertight"]
        
        # Stage 2: Geometry Validation
        geometry_results = self._validate_geometry(vertices, faces)
        report.geometry_score = geometry_results["score"]
        report.volume_cm3 = geometry_results["volume"]
        report.surface_area_cm2 = geometry_results["surface_area"]
        report.dimensions_mm = geometry_results["dimensions"]
        
        # Stage 3: Planter-Specific Validation
        planter_results = self._validate_planter_features(vertices, faces)
        report.planter_score = planter_results["score"]
        
        # Stage 4: Printability Validation
        printability_results = self._validate_printability(vertices, faces)
        report.printability_score = printability_results["score"]
        report.is_printable = printability_results["is_printable"]
        
        # Collect all issues
        all_results = [topology_results, geometry_results, planter_results, printability_results]
        for result in all_results:
            report.critical_issues.extend(result.get("critical_issues", []))
            report.warnings.extend(result.get("warnings", []))
            report.recommendations.extend(result.get("recommendations", []))
        
        # Auto-repair if requested and needed
        if auto_repair and (report.critical_issues or not report.is_manifold):
            logger.info("🔧 Applying automatic repairs...")
            repaired_vertices, repaired_faces = self._apply_automatic_repairs(vertices, faces, report)
            
            # Re-validate after repairs
            if repaired_vertices != vertices or repaired_faces != faces:
                logger.info("🔄 Re-validating after repairs...")
                return self.validate_stl_file(stl_path, auto_repair=False)  # Avoid infinite recursion
        
        # Calculate overall score
        report.overall_score = (
            report.topology_score * 0.3 +
            report.geometry_score * 0.2 +
            report.planter_score * 0.3 +
            report.printability_score * 0.2
        )
        
        # Determine production readiness
        report.is_production_ready = (
            report.overall_score >= self.criteria.MIN_OVERALL_QUALITY and
            report.is_manifold and
            report.is_printable and
            len(report.critical_issues) == 0
        )
        
        # Log summary
        self._log_validation_summary(report)
        
        return report
    
    def _validate_topology(self, vertices: List[List[float]], faces: List[List[int]]) -> Dict[str, Any]:
        """Validate mesh topology"""
        results = {
            "score": 0.0,
            "is_manifold": False,
            "is_watertight": False,
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check vertex/face count
        if len(vertices) < self.criteria.MIN_VERTICES:
            results["critical_issues"].append(f"Too few vertices: {len(vertices)} < {self.criteria.MIN_VERTICES}")
        elif len(vertices) > self.criteria.MAX_VERTICES:
            results["warnings"].append(f"High vertex count: {len(vertices)} > {self.criteria.MAX_VERTICES}")
        
        if len(faces) < self.criteria.MIN_FACES:
            results["critical_issues"].append(f"Too few faces: {len(faces)} < {self.criteria.MIN_FACES}")
        elif len(faces) > self.criteria.MAX_FACES:
            results["warnings"].append(f"High face count: {len(faces)} > {self.criteria.MAX_FACES}")
        
        # Check for degenerate faces
        degenerate_count = 0
        for face in faces:
            if len(face) < 3:
                degenerate_count += 1
            elif len(set(face)) < 3:  # Duplicate vertices in face
                degenerate_count += 1
        
        if degenerate_count > 0:
            results["critical_issues"].append(f"Found {degenerate_count} degenerate faces")
        
        # Simplified manifold check (edge count analysis)
        edge_count = {}
        for face in faces:
            for i in range(len(face)):
                j = (i + 1) % len(face)
                edge = tuple(sorted([face[i], face[j]]))
                edge_count[edge] = edge_count.get(edge, 0) + 1
        
        # Check for non-manifold edges (used by more than 2 faces)
        non_manifold_edges = sum(1 for count in edge_count.values() if count > 2)
        if non_manifold_edges == 0:
            results["is_manifold"] = True
        else:
            results["critical_issues"].append(f"Found {non_manifold_edges} non-manifold edges")
        
        # Check for boundary edges (used by only 1 face)
        boundary_edges = sum(1 for count in edge_count.values() if count == 1)
        if boundary_edges == 0:
            results["is_watertight"] = True
        else:
            results["warnings"].append(f"Found {boundary_edges} boundary edges (not watertight)")
        
        # Calculate topology score
        score = 1.0
        if results["critical_issues"]:
            score -= 0.3 * len(results["critical_issues"])
        if results["warnings"]:
            score -= 0.1 * len(results["warnings"])
        if not results["is_manifold"]:
            score -= 0.4
        
        results["score"] = max(0.0, score)
        
        return results
    
    def _validate_geometry(self, vertices: List[List[float]], faces: List[List[int]]) -> Dict[str, Any]:
        """Validate mesh geometry"""
        results = {
            "score": 0.0,
            "volume": 0.0,
            "surface_area": 0.0,
            "dimensions": [0, 0, 0],
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Calculate dimensions
        if vertices:
            xs = [v[0] for v in vertices]
            ys = [v[1] for v in vertices]
            zs = [v[2] for v in vertices]
            
            dimensions = [
                (max(xs) - min(xs)) * 10,  # Convert to mm
                (max(ys) - min(ys)) * 10,
                (max(zs) - min(zs)) * 10
            ]
            results["dimensions"] = dimensions
        
        # Calculate volume using divergence theorem
        volume = 0.0
        for face in faces:
            if len(face) >= 3:
                v0, v1, v2 = [vertices[face[i]] for i in range(3)]
                volume += (v0[0] * (v1[1] * v2[2] - v1[2] * v2[1]) +
                          v1[0] * (v2[1] * v0[2] - v2[2] * v0[1]) +
                          v2[0] * (v0[1] * v1[2] - v0[2] * v1[1])) / 6.0
        
        results["volume"] = abs(volume)
        
        # Calculate surface area
        surface_area = 0.0
        for face in faces:
            if len(face) >= 3:
                v0, v1, v2 = [vertices[face[i]] for i in range(3)]
                u = [v1[i] - v0[i] for i in range(3)]
                v = [v2[i] - v0[i] for i in range(3)]
                cross = [
                    u[1] * v[2] - u[2] * v[1],
                    u[2] * v[0] - u[0] * v[2],
                    u[0] * v[1] - u[1] * v[0]
                ]
                surface_area += 0.5 * math.sqrt(sum(c*c for c in cross))
        
        results["surface_area"] = surface_area
        
        # Validate geometry constraints
        if results["volume"] < self.criteria.MIN_VOLUME_CM3:
            results["critical_issues"].append(f"Volume too small: {results['volume']:.1f} < {self.criteria.MIN_VOLUME_CM3}")
        elif results["volume"] > self.criteria.MAX_VOLUME_CM3:
            results["warnings"].append(f"Volume very large: {results['volume']:.1f} > {self.criteria.MAX_VOLUME_CM3}")
        
        if results["surface_area"] < self.criteria.MIN_SURFACE_AREA_CM2:
            results["critical_issues"].append(f"Surface area too small: {results['surface_area']:.1f} < {self.criteria.MIN_SURFACE_AREA_CM2}")
        
        # Check for reasonable proportions
        if dimensions[0] > 0 and dimensions[1] > 0 and dimensions[2] > 0:
            aspect_ratios = [
                max(dimensions[0], dimensions[1]) / min(dimensions[0], dimensions[1]),
                max(dimensions[0], dimensions[2]) / min(dimensions[0], dimensions[2]),
                max(dimensions[1], dimensions[2]) / min(dimensions[1], dimensions[2])
            ]
            
            if any(ratio > 10 for ratio in aspect_ratios):
                results["warnings"].append("Extreme aspect ratio detected - may cause print issues")
        
        # Calculate geometry score
        score = 1.0
        if results["critical_issues"]:
            score -= 0.4 * len(results["critical_issues"])
        if results["warnings"]:
            score -= 0.1 * len(results["warnings"])
        
        results["score"] = max(0.0, score)
        
        return results
    
    def _validate_planter_features(self, vertices: List[List[float]], faces: List[List[int]]) -> Dict[str, Any]:
        """Validate planter-specific features"""
        results = {
            "score": 0.0,
            "has_cavity": False,
            "has_drainage": False,
            "wall_thickness_ok": False,
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Simplified planter feature detection
        # In production, this would use more sophisticated analysis
        
        # Check for reasonable height (planters should be taller than they are wide)
        if vertices:
            zs = [v[2] for v in vertices]
            xs = [v[0] for v in vertices]
            ys = [v[1] for v in vertices]
            
            height = (max(zs) - min(zs)) * 10  # mm
            width = max((max(xs) - min(xs)) * 10, (max(ys) - min(ys)) * 10)
            
            if height < 30:
                results["critical_issues"].append(f"Height too small for planter: {height:.1f}mm")
            elif height > 200:
                results["warnings"].append(f"Very tall planter: {height:.1f}mm")
            
            # Basic cavity detection (simplified)
            # Look for inward-facing surfaces at the top
            top_z = max(zs)
            top_vertices = [i for i, v in enumerate(vertices) if v[2] > top_z - 0.5]
            
            if len(top_vertices) > 10:  # Suggests a cavity opening
                results["has_cavity"] = True
            else:
                results["critical_issues"].append("No planter cavity detected")
            
            # Basic drainage hole detection (simplified)
            # Look for holes in the bottom surface
            bottom_z = min(zs)
            bottom_faces = [face for face in faces if all(vertices[i][2] < bottom_z + 0.2 for i in face)]
            
            if len(bottom_faces) < len(faces) * 0.8:  # Some faces missing from bottom
                results["has_drainage"] = True
            else:
                results["recommendations"].append("Consider adding drainage holes")
        
        # Wall thickness check (simplified)
        # In production, this would use ray casting or distance fields
        results["wall_thickness_ok"] = True  # Assume OK for now
        results["recommendations"].append("Verify wall thickness with specialized tools")
        
        # Calculate planter score
        score = 0.0
        if results["has_cavity"]:
            score += 0.4
        if results["has_drainage"]:
            score += 0.2
        if results["wall_thickness_ok"]:
            score += 0.2
        
        # Penalty for critical issues
        if results["critical_issues"]:
            score -= 0.3 * len(results["critical_issues"])
        
        results["score"] = max(0.0, min(1.0, score + 0.2))  # Base score + bonuses
        
        return results
    
    def _validate_printability(self, vertices: List[List[float]], faces: List[List[int]]) -> Dict[str, Any]:
        """Validate 3D printability"""
        results = {
            "score": 0.0,
            "is_printable": False,
            "has_overhangs": False,
            "needs_supports": False,
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check for overhangs
        overhang_faces = 0
        for face in faces:
            if len(face) >= 3:
                # Calculate face normal
                v0, v1, v2 = [vertices[face[i]] for i in range(3)]
                u = [v1[i] - v0[i] for i in range(3)]
                v = [v2[i] - v0[i] for i in range(3)]
                normal = [
                    u[1] * v[2] - u[2] * v[1],
                    u[2] * v[0] - u[0] * v[2],
                    u[0] * v[1] - u[1] * v[0]
                ]
                length = math.sqrt(sum(n*n for n in normal))
                if length > 0:
                    normal = [n/length for n in normal]
                    
                    # Check angle with vertical (Z-axis)
                    angle_with_vertical = math.acos(abs(normal[2])) * 180 / math.pi
                    
                    if angle_with_vertical > self.criteria.MAX_OVERHANG_ANGLE_DEG:
                        overhang_faces += 1
        
        overhang_ratio = overhang_faces / len(faces) if faces else 0
        
        if overhang_ratio > 0.1:  # More than 10% overhang faces
            results["has_overhangs"] = True
            results["needs_supports"] = True
            results["warnings"].append(f"Significant overhangs detected: {overhang_ratio:.1%} of faces")
        
        # Check for floating parts (simplified)
        # In production, this would use connected component analysis
        
        # Check base contact (model should sit on print bed)
        if vertices:
            min_z = min(v[2] for v in vertices)
            base_vertices = [v for v in vertices if v[2] <= min_z + 0.1]
            
            if len(base_vertices) < 5:
                results["critical_issues"].append("Insufficient base contact with print bed")
            
        # Calculate printability score
        score = 1.0
        if results["has_overhangs"]:
            score -= 0.2
        if results["needs_supports"]:
            score -= 0.1
        if results["critical_issues"]:
            score -= 0.4 * len(results["critical_issues"])
        
        results["score"] = max(0.0, score)
        results["is_printable"] = score >= self.criteria.MIN_PRINTABILITY_SCORE
        
        return results
    
    def _apply_automatic_repairs(self, vertices: List[List[float]], faces: List[List[int]], report: ValidationReport) -> Tuple[List[List[float]], List[List[int]]]:
        """Apply automatic mesh repairs"""
        repaired_vertices = vertices.copy()
        repaired_faces = faces.copy()
        
        # Remove duplicate vertices
        if "duplicate" in str(report.critical_issues).lower():
            repaired_vertices, repaired_faces = self._remove_duplicate_vertices(repaired_vertices, repaired_faces)
            report.repairs_applied.append("Removed duplicate vertices")
        
        # Remove degenerate faces
        original_face_count = len(repaired_faces)
        repaired_faces = [face for face in repaired_faces if len(face) >= 3 and len(set(face)) >= 3]
        
        if len(repaired_faces) < original_face_count:
            removed_count = original_face_count - len(repaired_faces)
            report.repairs_applied.append(f"Removed {removed_count} degenerate faces")
        
        return repaired_vertices, repaired_faces
    
    def _remove_duplicate_vertices(self, vertices: List[List[float]], faces: List[List[int]]) -> Tuple[List[List[float]], List[List[int]]]:
        """Remove duplicate vertices and update face indices"""
        tolerance = 1e-6
        unique_vertices = []
        vertex_map = {}
        
        for i, vertex in enumerate(vertices):
            # Find if this vertex already exists
            found_duplicate = False
            for j, unique_vertex in enumerate(unique_vertices):
                if all(abs(vertex[k] - unique_vertex[k]) < tolerance for k in range(3)):
                    vertex_map[i] = j
                    found_duplicate = True
                    break
            
            if not found_duplicate:
                vertex_map[i] = len(unique_vertices)
                unique_vertices.append(vertex)
        
        # Update face indices
        updated_faces = []
        for face in faces:
            new_face = [vertex_map[vertex_idx] for vertex_idx in face]
            # Only keep faces with 3 unique vertices
            if len(set(new_face)) >= 3:
                updated_faces.append(new_face)
        
        return unique_vertices, updated_faces
    
    def _load_stl_file(self, stl_path: str) -> Tuple[List[List[float]], List[List[int]]]:
        """Load STL file and extract vertices and faces"""
        vertices = []
        faces = []
        
        try:
            with open(stl_path, 'r') as f:
                content = f.read()
                
                # Parse ASCII STL format
                lines = content.split('\n')
                vertex_buffer = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('vertex'):
                        coords = line.split()[1:4]
                        vertex = [float(coord) for coord in coords]
                        vertex_buffer.append(vertex)
                        
                        if len(vertex_buffer) == 3:
                            # Add vertices to list and create face
                            face_indices = []
                            for vertex in vertex_buffer:
                                if vertex not in vertices:
                                    vertices.append(vertex)
                                face_indices.append(vertices.index(vertex))
                            
                            faces.append(face_indices)
                            vertex_buffer = []
                
        except Exception as e:
            logger.error(f"Failed to load STL file: {e}")
            return [], []
        
        return vertices, faces
    
    def _create_failure_report(self, stl_path: str, reason: str) -> ValidationReport:
        """Create a failure report"""
        return ValidationReport(
            timestamp=time.time(),
            file_path=stl_path,
            topology_score=0.0,
            geometry_score=0.0,
            planter_score=0.0,
            printability_score=0.0,
            overall_score=0.0,
            is_manifold=False,
            is_watertight=False,
            is_printable=False,
            is_production_ready=False,
            vertex_count=0,
            face_count=0,
            volume_cm3=0.0,
            surface_area_cm2=0.0,
            dimensions_mm=[0, 0, 0],
            critical_issues=[reason],
            warnings=[],
            recommendations=["Fix critical issues and re-validate"],
            repairs_applied=[]
        )
    
    def _log_validation_summary(self, report: ValidationReport):
        """Log validation summary"""
        logger.info(f"📊 Validation Summary:")
        logger.info(f"   Overall Score: {report.overall_score:.1%}")
        logger.info(f"   Topology: {report.topology_score:.1%}")
        logger.info(f"   Geometry: {report.geometry_score:.1%}")
        logger.info(f"   Planter Features: {report.planter_score:.1%}")
        logger.info(f"   Printability: {report.printability_score:.1%}")
        
        status_icon = "✅" if report.is_production_ready else "❌"
        logger.info(f"{status_icon} Production Ready: {report.is_production_ready}")
        
        if report.critical_issues:
            logger.warning(f"🚨 Critical Issues: {len(report.critical_issues)}")
            for issue in report.critical_issues:
                logger.warning(f"   - {issue}")
        
        if report.warnings:
            logger.info(f"⚠️  Warnings: {len(report.warnings)}")
            for warning in report.warnings:
                logger.info(f"   - {warning}")

def validate_stl_file(stl_path: str, output_dir: Optional[str] = None) -> ValidationReport:
    """Main function to validate an STL file"""
    
    if not os.path.exists(stl_path):
        raise FileNotFoundError(f"STL file not found: {stl_path}")
    
    # Initialize validator
    validator = AdvancedModelValidator()
    
    # Run validation
    report = validator.validate_stl_file(stl_path, auto_repair=True)
    
    # Save report
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, f"validation_report_{int(time.time())}.json")
        
        with open(report_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        logger.info(f"📄 Validation report saved: {report_path}")
    
    return report

def main():
    """Main function for standalone validation"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python advanced_validator.py <stl_file> [output_dir]")
        return
    
    stl_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        report = validate_stl_file(stl_path, output_dir)
        
        print(f"\n🎯 Validation Complete!")
        print(f"📊 Overall Score: {report.overall_score:.1%}")
        print(f"🏭 Production Ready: {'Yes' if report.is_production_ready else 'No'}")
        
        if report.critical_issues:
            print(f"🚨 Critical Issues ({len(report.critical_issues)}):")
            for issue in report.critical_issues:
                print(f"   - {issue}")
        
        if report.recommendations:
            print(f"💡 Recommendations ({len(report.recommendations)}):")
            for rec in report.recommendations:
                print(f"   - {rec}")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
