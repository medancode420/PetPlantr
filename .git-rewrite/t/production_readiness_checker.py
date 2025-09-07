#!/usr/bin/env python3
"""
Production Readiness Checker for PetPlantr Pipeline
Comprehensive quality control for 3D printing production
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import numpy as np
from enhanced_stl_analyzer import analyze_stl_quality

class ProductionReadinessChecker:
    """
    Comprehensive production readiness validation for STL files
    """
    
    def __init__(self):
        # Production quality thresholds
        self.thresholds = {
            'min_overall_score': 70,
            'min_geometry_score': 60,
            'min_topology_score': 80,
            'min_printability_score': 70,
            'min_volume_mm3': 30000,      # Must have reasonable volume
            'max_volume_mm3': 2000000,    # Must fit on printer
            'min_height_mm': 20,          # Must be printable size
            'max_height_mm': 250,         # Must fit printer build volume
            'min_width_mm': 30,           # Must be reasonable size
            'min_depth_mm': 30,           # Must be reasonable size
            'max_triangle_quality': 8.0,  # Triangle aspect ratio limit
            'min_face_count': 20,         # Must have enough detail
            'max_face_count': 200000,     # Must not be too complex
            'min_normal_consistency': 0.85,  # Normal vector consistency
            'max_degenerate_ratio': 0.02, # Max percentage of degenerate triangles
            'must_be_watertight': True,    # Critical for 3D printing
            'planter_ratio_tolerance': 2.5  # How far from ideal (1.0) planter shape can be
        }
        
        # Failure reasons categorization
        self.failure_categories = {
            'CRITICAL': [],     # Must fix before production
            'WARNING': [],      # Should fix but may proceed
            'INFO': []          # Nice to fix but not blocking
        }
    
    def check_production_readiness(self, stl_file_path):
        """
        Comprehensive production readiness check
        """
        print(f"🔍 Production Readiness Check: {Path(stl_file_path).name}")
        print("="*80)
        
        try:
            # Get quality analysis
            quality_report, mesh_obj = analyze_stl_quality(stl_file_path)
            
            # Initialize results
            results = {
                'file_path': str(stl_file_path),
                'timestamp': datetime.now().isoformat(),
                'production_ready': True,
                'overall_grade': 'A',
                'checks_passed': 0,
                'total_checks': 0,
                'critical_failures': [],
                'warnings': [],
                'info_notes': [],
                'quality_report': quality_report
            }
            
            # Run all checks
            self._check_overall_quality(quality_report, results)
            self._check_geometry_constraints(quality_report, results)
            self._check_mesh_quality(quality_report, results)
            self._check_printability(quality_report, results)
            self._check_planter_characteristics(quality_report, results)
            self._check_file_properties(stl_file_path, results)
            
            # Calculate grade
            results['overall_grade'] = self._calculate_grade(results)
            
            # Final determination
            results['production_ready'] = len(results['critical_failures']) == 0
            
            return results
            
        except Exception as e:
            return {
                'file_path': str(stl_file_path),
                'timestamp': datetime.now().isoformat(),
                'production_ready': False,
                'overall_grade': 'F',
                'error': str(e),
                'critical_failures': [f"Analysis failed: {e}"]
            }
    
    def _check_overall_quality(self, quality_report, results):
        """Check overall quality scores"""
        scores = quality_report['quality_scores']
        
        # Overall score check
        if scores['overall'] >= self.thresholds['min_overall_score']:
            results['checks_passed'] += 1
            results['info_notes'].append(f"✅ Overall quality excellent: {scores['overall']}/100")
        else:
            results['critical_failures'].append(f"❌ Overall quality too low: {scores['overall']}/100 (min: {self.thresholds['min_overall_score']})")
        results['total_checks'] += 1
        
        # Individual score checks
        if scores['geometry'] >= self.thresholds['min_geometry_score']:
            results['checks_passed'] += 1
        else:
            results['warnings'].append(f"⚠️ Geometry score low: {scores['geometry']}/100")
        results['total_checks'] += 1
        
        if scores['topology'] >= self.thresholds['min_topology_score']:
            results['checks_passed'] += 1
        else:
            results['critical_failures'].append(f"❌ Topology score too low: {scores['topology']}/100")
        results['total_checks'] += 1
        
        if scores['printability'] >= self.thresholds['min_printability_score']:
            results['checks_passed'] += 1
        else:
            results['warnings'].append(f"⚠️ Printability score low: {scores['printability']}/100")
        results['total_checks'] += 1
    
    def _check_geometry_constraints(self, quality_report, results):
        """Check geometric constraints for production"""
        geometry = quality_report['geometry']
        dims = geometry['dimensions_mm']
        
        # Volume checks
        volume = geometry['volume_mm3']
        if self.thresholds['min_volume_mm3'] <= volume <= self.thresholds['max_volume_mm3']:
            results['checks_passed'] += 1
            results['info_notes'].append(f"✅ Volume acceptable: {volume:.0f} mm³")
        else:
            if volume < self.thresholds['min_volume_mm3']:
                results['warnings'].append(f"⚠️ Volume too small: {volume:.0f} mm³ (min: {self.thresholds['min_volume_mm3']})")
            else:
                results['critical_failures'].append(f"❌ Volume too large: {volume:.0f} mm³ (max: {self.thresholds['max_volume_mm3']})")
        results['total_checks'] += 1
        
        # Dimension checks
        height = dims['height']
        if self.thresholds['min_height_mm'] <= height <= self.thresholds['max_height_mm']:
            results['checks_passed'] += 1
        else:
            if height < self.thresholds['min_height_mm']:
                results['warnings'].append(f"⚠️ Height too small: {height:.1f} mm")
            else:
                results['critical_failures'].append(f"❌ Height too large for printer: {height:.1f} mm")
        results['total_checks'] += 1
        
        width = dims['width']
        if width >= self.thresholds['min_width_mm']:
            results['checks_passed'] += 1
        else:
            results['warnings'].append(f"⚠️ Width too small: {width:.1f} mm")
        results['total_checks'] += 1
        
        depth = dims['depth']
        if depth >= self.thresholds['min_depth_mm']:
            results['checks_passed'] += 1
        else:
            results['warnings'].append(f"⚠️ Depth too small: {depth:.1f} mm")
        results['total_checks'] += 1
    
    def _check_mesh_quality(self, quality_report, results):
        """Check mesh quality for 3D printing"""
        mesh = quality_report['mesh_quality']
        
        # Watertight check (CRITICAL)
        if mesh['is_watertight'] == 'True' or mesh['is_watertight'] == True:
            results['checks_passed'] += 1
            results['info_notes'].append("✅ Mesh is watertight")
        else:
            results['critical_failures'].append("❌ Mesh is NOT watertight - will not print correctly")
        results['total_checks'] += 1
        
        # Face count checks
        face_count = mesh['face_count']
        if self.thresholds['min_face_count'] <= face_count <= self.thresholds['max_face_count']:
            results['checks_passed'] += 1
            results['info_notes'].append(f"✅ Face count good: {face_count:,}")
        else:
            if face_count < self.thresholds['min_face_count']:
                results['warnings'].append(f"⚠️ Face count too low: {face_count} (may lack detail)")
            else:
                results['warnings'].append(f"⚠️ Face count very high: {face_count:,} (may slow printing)")
        results['total_checks'] += 1
        
        # Triangle quality
        triangle_quality = mesh['avg_triangle_quality']
        if triangle_quality <= self.thresholds['max_triangle_quality']:
            results['checks_passed'] += 1
        else:
            results['warnings'].append(f"⚠️ Poor triangle quality: {triangle_quality:.2f} (stretched triangles)")
        results['total_checks'] += 1
        
        # Normal consistency
        normal_consistency = mesh['normal_consistency']
        if normal_consistency >= self.thresholds['min_normal_consistency']:
            results['checks_passed'] += 1
        else:
            results['warnings'].append(f"⚠️ Inconsistent normals: {normal_consistency:.1%}")
        results['total_checks'] += 1
        
        # Degenerate triangles
        degenerate_ratio = mesh['degenerate_triangles'] / face_count if face_count > 0 else 0
        if degenerate_ratio <= self.thresholds['max_degenerate_ratio']:
            results['checks_passed'] += 1
        else:
            results['warnings'].append(f"⚠️ Too many degenerate triangles: {mesh['degenerate_triangles']} ({degenerate_ratio:.1%})")
        results['total_checks'] += 1
    
    def _check_printability(self, quality_report, results):
        """Check 3D printing specific requirements"""
        geometry = quality_report['geometry']
        dims = geometry['dimensions_mm']
        
        # Check for thin walls (basic heuristic)
        surface_area = geometry['surface_area_mm2']
        volume = geometry['volume_mm3']
        
        if volume > 0:
            wall_thickness_estimate = volume / surface_area
            if wall_thickness_estimate >= 2.0:  # At least 2mm effective thickness
                results['checks_passed'] += 1
                results['info_notes'].append(f"✅ Estimated wall thickness adequate: {wall_thickness_estimate:.1f}mm")
            else:
                results['warnings'].append(f"⚠️ May have thin walls: {wall_thickness_estimate:.1f}mm estimated thickness")
        else:
            results['warnings'].append("⚠️ Cannot estimate wall thickness (zero volume)")
        results['total_checks'] += 1
        
        # Check aspect ratio for stability
        height = dims['height']
        base_size = max(dims['width'], dims['depth'])
        if base_size > 0:
            aspect_ratio = height / base_size
            if aspect_ratio <= 3.0:  # Not too tall and narrow
                results['checks_passed'] += 1
            else:
                results['warnings'].append(f"⚠️ High aspect ratio may be unstable: {aspect_ratio:.1f}")
        results['total_checks'] += 1
    
    def _check_planter_characteristics(self, quality_report, results):
        """Check planter-specific requirements"""
        planter = quality_report['planter_analysis']
        
        # Planter shape check
        if planter['is_planter_like']:
            results['checks_passed'] += 1
            results['info_notes'].append("✅ Has planter-like shape")
        else:
            results['warnings'].append("⚠️ Does not have typical planter shape")
        results['total_checks'] += 1
        
        # Planter ratio check
        ratio = planter['planter_ratio']
        if abs(ratio - 1.0) <= self.thresholds['planter_ratio_tolerance']:
            results['checks_passed'] += 1
        else:
            results['info_notes'].append(f"📝 Planter ratio: {ratio:.2f} (ideal: 1.0)")
        results['total_checks'] += 1
    
    def _check_file_properties(self, stl_file_path, results):
        """Check file-level properties"""
        file_path = Path(stl_file_path)
        
        # File exists and is readable
        if file_path.exists() and file_path.is_file():
            results['checks_passed'] += 1
            results['info_notes'].append("✅ File exists and readable")
        else:
            results['critical_failures'].append("❌ File not found or not readable")
        results['total_checks'] += 1
        
        # File size check
        if file_path.exists():
            file_size_mb = file_path.stat().st_size / (1024*1024)
            if 0.01 <= file_size_mb <= 100:  # Reasonable file size
                results['checks_passed'] += 1
                results['info_notes'].append(f"✅ File size reasonable: {file_size_mb:.2f} MB")
            else:
                if file_size_mb < 0.01:
                    results['warnings'].append(f"⚠️ File very small: {file_size_mb:.3f} MB")
                else:
                    results['warnings'].append(f"⚠️ File very large: {file_size_mb:.1f} MB")
        results['total_checks'] += 1
    
    def _calculate_grade(self, results):
        """Calculate letter grade based on pass rate and failures"""
        if results['total_checks'] == 0:
            return 'F'
        
        pass_rate = results['checks_passed'] / results['total_checks']
        critical_count = len(results['critical_failures'])
        warning_count = len(results['warnings'])
        
        # Critical failures = automatic F
        if critical_count > 0:
            return 'F'
        
        # Grade based on pass rate and warnings
        if pass_rate >= 0.95 and warning_count == 0:
            return 'A+'
        elif pass_rate >= 0.90 and warning_count <= 1:
            return 'A'
        elif pass_rate >= 0.85 and warning_count <= 2:
            return 'A-'
        elif pass_rate >= 0.80 and warning_count <= 3:
            return 'B+'
        elif pass_rate >= 0.75:
            return 'B'
        elif pass_rate >= 0.70:
            return 'B-'
        elif pass_rate >= 0.65:
            return 'C+'
        elif pass_rate >= 0.60:
            return 'C'
        elif pass_rate >= 0.50:
            return 'D'
        else:
            return 'F'
    
    def print_production_report(self, results):
        """Print detailed production readiness report"""
        print("\n" + "="*100)
        print("🏭 PETPLANTR PRODUCTION READINESS REPORT")
        print("="*100)
        
        # Header info
        print(f"\n📁 FILE: {Path(results['file_path']).name}")
        print(f"⏰ TIMESTAMP: {results['timestamp']}")
        
        # Overall status
        if results['production_ready']:
            status_emoji = "✅"
            status_text = "READY FOR PRODUCTION"
        else:
            status_emoji = "❌"
            status_text = "NOT READY FOR PRODUCTION"
        
        grade = results['overall_grade']
        if grade in ['A+', 'A', 'A-']:
            grade_emoji = "🏆"
        elif grade in ['B+', 'B', 'B-']:
            grade_emoji = "🥇"
        elif grade in ['C+', 'C']:
            grade_emoji = "🥈"
        elif grade == 'D':
            grade_emoji = "🥉"
        else:
            grade_emoji = "❌"
        
        print(f"\n{status_emoji} STATUS: {status_text}")
        print(f"{grade_emoji} GRADE: {grade}")
        
        if 'checks_passed' in results and 'total_checks' in results:
            pass_rate = results['checks_passed'] / results['total_checks'] * 100
            print(f"📊 PASS RATE: {results['checks_passed']}/{results['total_checks']} ({pass_rate:.1f}%)")
        
        # Critical failures
        if results['critical_failures']:
            print(f"\n🚨 CRITICAL ISSUES (MUST FIX):")
            for failure in results['critical_failures']:
                print(f"   {failure}")
        
        # Warnings
        if results['warnings']:
            print(f"\n⚠️ WARNINGS (SHOULD FIX):")
            for warning in results['warnings']:
                print(f"   {warning}")
        
        # Info notes
        if results['info_notes']:
            print(f"\n✅ PASSED CHECKS:")
            for note in results['info_notes']:
                print(f"   {note}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if results['production_ready']:
            print("   🎉 This model is ready for production 3D printing!")
            print("   📋 Proceed with printing using standard PLA/PETG settings")
            if results['warnings']:
                print("   🔧 Consider addressing warnings for optimal quality")
        else:
            print("   🔧 Address critical issues before production")
            if results['critical_failures']:
                if any("watertight" in failure.lower() for failure in results['critical_failures']):
                    print("   🔧 Fix mesh watertightness using mesh repair tools")
                if any("volume" in failure.lower() for failure in results['critical_failures']):
                    print("   📏 Adjust model size to fit printer constraints")
        
        print("\n" + "="*100)

def main():
    if len(sys.argv) != 2:
        print("Usage: python production_readiness_checker.py <stl_file>")
        print("Example: python production_readiness_checker.py model.stl")
        sys.exit(1)
    
    stl_file = sys.argv[1]
    
    # Initialize checker
    checker = ProductionReadinessChecker()
    
    # Run check
    results = checker.check_production_readiness(stl_file)
    
    # Print report
    checker.print_production_report(results)
    
    # Save results
    output_path = Path(stl_file).parent / f"{Path(stl_file).stem}_production_readiness.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Production readiness report saved to: {output_path}")
    
    # Return appropriate exit code
    sys.exit(0 if results['production_ready'] else 1)

if __name__ == "__main__":
    main()
