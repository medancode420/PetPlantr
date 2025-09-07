#!/usr/bin/env python3
"""
Advanced Planter Shape Optimizer for PetPlantr Pipeline
Analyzes and suggests improvements for non-planter-like models
"""
import sys
import numpy as np
import json
from pathlib import Path
from enhanced_stl_analyzer import analyze_stl_quality
from stl import mesh

class PlanterShapeOptimizer:
    """
    Advanced planter shape analysis and optimization recommendations
    """
    
    def __init__(self):
        # Ideal planter characteristics
        self.ideal_metrics = {
            'opening_ratio': {'min': 0.9, 'max': 1.8, 'ideal': 1.2},
            'shape_stability': {'min': 0.5, 'ideal': 0.8},
            'taper_ratio': {'min': 0.3, 'max': 0.9, 'ideal': 0.6},
            'volume_distribution': {'max': 0.7, 'ideal': 0.3},
            'aspect_ratio': {'min': 0.4, 'max': 2.0, 'ideal': 1.0},
            'planter_ratio': {'min': 0.8, 'max': 1.8, 'ideal': 1.1},
            'cavity_depth_ratio': {'min': 0.6, 'ideal': 0.8}  # Depth of planting cavity
        }
    
    def analyze_planter_deficiencies(self, stl_file_path):
        """
        Comprehensive analysis of planter shape deficiencies with specific recommendations
        """
        print(f"🔍 Analyzing planter shape: {Path(stl_file_path).name}")
        
        # Get enhanced quality analysis
        quality_report, mesh_obj = analyze_stl_quality(stl_file_path)
        planter_analysis = quality_report['planter_analysis']
        geometry = quality_report['geometry']
        
        # Initialize results
        results = {
            'file_path': str(stl_file_path),
            'current_metrics': planter_analysis,
            'deficiencies': [],
            'recommendations': [],
            'optimization_priority': [],
            'estimated_improvement_potential': 0,
            'current_planter_score': planter_analysis['planter_confidence'],
            'potential_planter_score': 0
        }
        
        # Analyze each characteristic
        self._analyze_opening_characteristics(planter_analysis, geometry, results)
        self._analyze_shape_stability(planter_analysis, results)
        self._analyze_proportions(planter_analysis, geometry, results)
        self._analyze_volume_distribution(planter_analysis, results)
        self._analyze_cavity_characteristics(mesh_obj, geometry, results)
        
        # Calculate potential improvement
        results['potential_planter_score'] = min(100, results['current_planter_score'] + results['estimated_improvement_potential'])
        
        # Prioritize recommendations
        self._prioritize_recommendations(results)
        
        return results
    
    def _analyze_opening_characteristics(self, planter_analysis, geometry, results):
        """Analyze opening and tapering characteristics"""
        opening_ratio = planter_analysis['opening_ratio']
        taper_ratio = planter_analysis['taper_ratio']
        
        issues = []
        recommendations = []
        potential_gain = 0
        
        # Opening ratio analysis
        if opening_ratio < self.ideal_metrics['opening_ratio']['min']:
            severity = "HIGH" if opening_ratio < 0.7 else "MEDIUM"
            issues.append(f"Opening too narrow (ratio: {opening_ratio:.2f})")
            recommendations.append({
                'type': 'geometry_modification',
                'severity': severity,
                'description': 'Widen the top opening of the planter',
                'specific_action': f'Increase top cross-section by {((self.ideal_metrics["opening_ratio"]["ideal"] / opening_ratio) - 1) * 100:.0f}%',
                'expected_gain': 15 if severity == "HIGH" else 10
            })
            potential_gain += 15 if severity == "HIGH" else 10
            
        elif opening_ratio > self.ideal_metrics['opening_ratio']['max']:
            severity = "MEDIUM" if opening_ratio < 3.0 else "HIGH"
            issues.append(f"Opening too wide (ratio: {opening_ratio:.2f})")
            recommendations.append({
                'type': 'geometry_modification',
                'severity': severity,
                'description': 'Narrow the top opening or strengthen the base',
                'specific_action': f'Reduce top opening by {((opening_ratio / self.ideal_metrics["opening_ratio"]["ideal"]) - 1) * 100:.0f}% or increase base size',
                'expected_gain': 10 if severity == "HIGH" else 5
            })
            potential_gain += 10 if severity == "HIGH" else 5
        
        # Taper ratio analysis
        if taper_ratio < self.ideal_metrics['taper_ratio']['min']:
            severity = "HIGH" if taper_ratio < 0.1 else "MEDIUM"
            issues.append(f"Extreme tapering (ratio: {taper_ratio:.2f})")
            recommendations.append({
                'type': 'shape_modification',
                'severity': severity,
                'description': 'Reduce extreme tapering for better planter stability',
                'specific_action': 'Gradually increase width from narrowest to widest section',
                'expected_gain': 20 if severity == "HIGH" else 15
            })
            potential_gain += 20 if severity == "HIGH" else 15
        
        elif taper_ratio > self.ideal_metrics['taper_ratio']['max']:
            issues.append(f"Insufficient tapering (ratio: {taper_ratio:.2f})")
            recommendations.append({
                'type': 'shape_modification',
                'severity': 'LOW',
                'description': 'Add subtle tapering for more planter-like appearance',
                'specific_action': 'Create gentle taper from bottom to top',
                'expected_gain': 5
            })
            potential_gain += 5
        
        results['deficiencies'].extend(issues)
        results['recommendations'].extend(recommendations)
        results['estimated_improvement_potential'] += potential_gain
    
    def _analyze_shape_stability(self, planter_analysis, results):
        """Analyze shape smoothness and stability"""
        stability = planter_analysis['shape_stability']
        
        if stability < self.ideal_metrics['shape_stability']['min']:
            severity = "HIGH" if stability < 0.3 else "MEDIUM"
            results['deficiencies'].append(f"Erratic shape transitions (stability: {stability:.2f})")
            results['recommendations'].append({
                'type': 'mesh_optimization',
                'severity': severity,
                'description': 'Smooth shape transitions between height levels',
                'specific_action': 'Apply mesh smoothing or remeshing with gradual transitions',
                'expected_gain': 15 if severity == "HIGH" else 10
            })
            results['estimated_improvement_potential'] += 15 if severity == "HIGH" else 10
    
    def _analyze_proportions(self, planter_analysis, geometry, results):
        """Analyze dimensional proportions"""
        dims = geometry['dimensions_mm']
        max_horizontal = max(dims['width'], dims['depth'])
        aspect_ratio = dims['height'] / max_horizontal if max_horizontal > 0 else 0
        
        issues = []
        recommendations = []
        potential_gain = 0
        
        if aspect_ratio < self.ideal_metrics['aspect_ratio']['min']:
            severity = "MEDIUM" if aspect_ratio < 0.2 else "LOW"
            issues.append(f"Too wide/short (aspect ratio: {aspect_ratio:.2f})")
            recommendations.append({
                'type': 'scaling',
                'severity': severity,
                'description': 'Increase height or reduce width for better proportions',
                'specific_action': f'Scale height by {(self.ideal_metrics["aspect_ratio"]["ideal"] / aspect_ratio):.1f}x',
                'expected_gain': 10 if severity == "MEDIUM" else 5
            })
            potential_gain += 10 if severity == "MEDIUM" else 5
            
        elif aspect_ratio > self.ideal_metrics['aspect_ratio']['max']:
            severity = "MEDIUM" if aspect_ratio > 3.0 else "LOW"
            issues.append(f"Too tall/narrow (aspect ratio: {aspect_ratio:.2f})")
            recommendations.append({
                'type': 'scaling',
                'severity': severity,
                'description': 'Reduce height or increase width for stability',
                'specific_action': f'Scale height by {(self.ideal_metrics["aspect_ratio"]["ideal"] / aspect_ratio):.1f}x',
                'expected_gain': 10 if severity == "MEDIUM" else 5
            })
            potential_gain += 10 if severity == "MEDIUM" else 5
        
        # Planter ratio analysis
        planter_ratio = planter_analysis['planter_ratio']
        if not (self.ideal_metrics['planter_ratio']['min'] <= planter_ratio <= self.ideal_metrics['planter_ratio']['max']):
            if planter_ratio < self.ideal_metrics['planter_ratio']['min']:
                issues.append(f"Bottom wider than top (ratio: {planter_ratio:.2f})")
                recommendations.append({
                    'type': 'shape_inversion',
                    'severity': 'HIGH',
                    'description': 'Invert shape - planters should be wider at top',
                    'specific_action': 'Redesign with larger top opening than bottom',
                    'expected_gain': 25
                })
                potential_gain += 25
            else:
                issues.append(f"Extremely top-heavy (ratio: {planter_ratio:.2f})")
                recommendations.append({
                    'type': 'stability_improvement',
                    'severity': 'MEDIUM',
                    'description': 'Strengthen base for stability',
                    'specific_action': 'Increase bottom cross-section for stability',
                    'expected_gain': 15
                })
                potential_gain += 15
        
        results['deficiencies'].extend(issues)
        results['recommendations'].extend(recommendations)
        results['estimated_improvement_potential'] += potential_gain
    
    def _analyze_volume_distribution(self, planter_analysis, results):
        """Analyze volume consistency throughout height"""
        vol_dist = planter_analysis['volume_distribution']
        
        if vol_dist > self.ideal_metrics['volume_distribution']['max']:
            severity = "MEDIUM" if vol_dist > 1.0 else "LOW"
            results['deficiencies'].append(f"Inconsistent volume distribution ({vol_dist:.2f})")
            results['recommendations'].append({
                'type': 'volume_optimization',
                'severity': severity,
                'description': 'Create more consistent volume throughout height',
                'specific_action': 'Smooth volume transitions between sections',
                'expected_gain': 10 if severity == "MEDIUM" else 5
            })
            results['estimated_improvement_potential'] += 10 if severity == "MEDIUM" else 5
    
    def _analyze_cavity_characteristics(self, mesh_obj, geometry, results):
        """Analyze planting cavity characteristics"""
        # Estimate cavity depth and opening
        vertices = mesh_obj.vectors.reshape(-1, 3)
        dims = geometry['dimensions_mm']
        
        # Calculate approximate cavity metrics
        volume = geometry['volume_mm3']
        bbox_volume = dims['width'] * dims['height'] * dims['depth']
        cavity_ratio = 1 - (volume / bbox_volume) if bbox_volume > 0 else 0
        
        issues = []
        recommendations = []
        potential_gain = 0
        
        if cavity_ratio < 0.3:  # Less than 30% hollow
            severity = "HIGH" if cavity_ratio < 0.1 else "MEDIUM"
            issues.append(f"Insufficient planting cavity (hollow ratio: {cavity_ratio:.2f})")
            recommendations.append({
                'type': 'cavity_creation',
                'severity': severity,
                'description': 'Create deeper planting cavity',
                'specific_action': f'Hollow out {((0.6 - cavity_ratio) * 100):.0f}% more volume for soil',
                'expected_gain': 20 if severity == "HIGH" else 15
            })
            potential_gain += 20 if severity == "HIGH" else 15
        
        # Check for drainage considerations
        if cavity_ratio > 0.2:  # Has some cavity
            recommendations.append({
                'type': 'functional_improvement',
                'severity': 'LOW',
                'description': 'Add drainage hole at bottom',
                'specific_action': 'Create 5-8mm drainage hole in base',
                'expected_gain': 5
            })
            potential_gain += 5
        
        results['deficiencies'].extend(issues)
        results['recommendations'].extend(recommendations)
        results['estimated_improvement_potential'] += potential_gain
    
    def _prioritize_recommendations(self, results):
        """Prioritize recommendations by impact and severity"""
        recommendations = results['recommendations']
        
        # Sort by expected gain (descending) and severity
        severity_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        
        sorted_recs = sorted(recommendations, 
                           key=lambda x: (severity_order.get(x['severity'], 0), x['expected_gain']), 
                           reverse=True)
        
        # Create priority list
        high_priority = [r for r in sorted_recs if r['severity'] == 'HIGH']
        medium_priority = [r for r in sorted_recs if r['severity'] == 'MEDIUM']
        low_priority = [r for r in sorted_recs if r['severity'] == 'LOW']
        
        results['optimization_priority'] = {
            'immediate_fixes': high_priority,
            'important_improvements': medium_priority,
            'nice_to_have': low_priority
        }
    
    def generate_optimization_report(self, results):
        """Generate comprehensive optimization report"""
        print("\n" + "="*100)
        print("🛠️ PLANTER SHAPE OPTIMIZATION REPORT")
        print("="*100)
        
        current_score = results['current_planter_score']
        potential_score = results['potential_planter_score']
        improvement = potential_score - current_score
        
        print(f"\n📊 OPTIMIZATION POTENTIAL:")
        print(f"   • Current Planter Score: {current_score:.1f}/100")
        print(f"   • Potential Score After Optimization: {potential_score:.1f}/100")
        print(f"   • Estimated Improvement: +{improvement:.1f} points")
        
        if results['deficiencies']:
            print(f"\n🚨 IDENTIFIED DEFICIENCIES:")
            for i, deficiency in enumerate(results['deficiencies'], 1):
                print(f"   {i}. {deficiency}")
        
        # Priority recommendations
        priority = results['optimization_priority']
        
        if priority['immediate_fixes']:
            print(f"\n🔥 IMMEDIATE FIXES (High Priority):")
            for i, rec in enumerate(priority['immediate_fixes'], 1):
                print(f"   {i}. {rec['description']}")
                print(f"      → {rec['specific_action']}")
                print(f"      → Expected gain: +{rec['expected_gain']} points")
        
        if priority['important_improvements']:
            print(f"\n⚡ IMPORTANT IMPROVEMENTS (Medium Priority):")
            for i, rec in enumerate(priority['important_improvements'], 1):
                print(f"   {i}. {rec['description']}")
                print(f"      → {rec['specific_action']}")
                print(f"      → Expected gain: +{rec['expected_gain']} points")
        
        if priority['nice_to_have']:
            print(f"\n✨ NICE-TO-HAVE (Low Priority):")
            for i, rec in enumerate(priority['nice_to_have'], 1):
                print(f"   {i}. {rec['description']}")
                print(f"      → {rec['specific_action']}")
                print(f"      → Expected gain: +{rec['expected_gain']} points")
        
        # Overall assessment
        print(f"\n🎯 OPTIMIZATION STRATEGY:")
        if improvement > 30:
            print("   🚀 Major transformation recommended - significant planter potential")
        elif improvement > 15:
            print("   🔧 Moderate improvements needed - good planter potential")
        elif improvement > 5:
            print("   ✨ Minor refinements needed - already planter-like")
        else:
            print("   ✅ Model is already well-optimized for planter use")
        
        if current_score < 30:
            print("   💡 Consider fundamental redesign for planter functionality")
        elif current_score < 50:
            print("   🔄 Focus on shape modifications and proportions")
        elif current_score < 70:
            print("   🎨 Fine-tune details for optimal planter characteristics")
        
        print("="*100)
    
    def save_optimization_report(self, results, output_path):
        """Save detailed optimization report to JSON"""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Optimization report saved to: {output_path}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python planter_shape_optimizer.py <stl_file>")
        print("Example: python planter_shape_optimizer.py model.stl")
        sys.exit(1)
    
    stl_file = sys.argv[1]
    
    if not Path(stl_file).exists():
        print(f"❌ File not found: {stl_file}")
        sys.exit(1)
    
    # Initialize optimizer
    optimizer = PlanterShapeOptimizer()
    
    try:
        # Analyze planter deficiencies
        results = optimizer.analyze_planter_deficiencies(stl_file)
        
        # Generate report
        optimizer.generate_optimization_report(results)
        
        # Save detailed results
        output_path = Path(stl_file).parent / f"{Path(stl_file).stem}_planter_optimization.json"
        optimizer.save_optimization_report(results, output_path)
        
    except Exception as e:
        print(f"❌ Error during optimization analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
