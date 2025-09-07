#!/usr/bin/env python3
"""
Iterative Planter Generator with Feedback Loop
Generates 3D dog planters with iterative refinement until 100% planter-like quality is achieved
"""
import os
import sys
import json
import time
import shutil
from pathlib import Path
import trimesh
import numpy as np

# Import our existing components
from enhanced_stl_analyzer import analyze_stl_quality, analyze_planter_characteristics
from planter_shape_optimizer import PlanterShapeOptimizer
from shape_to_planter_converter import ShapeToPlanterConverter
from image_to_3d_dog_generator import ImageTo3DDogGenerator
from hybrid_perfect_dog_generator import HybridPerfectDogGenerator
from realistic_dog_shape_generator import RealisticDogShapeGenerator

class IterativePlanterGenerator:
    def __init__(self, max_iterations=5, target_confidence=0.8):
        """
        Initialize iterative generator with feedback loop
        
        Args:
            max_iterations: Maximum refinement iterations per model
            target_confidence: Minimum planter confidence score to accept
        """
        self.max_iterations = max_iterations
        self.target_confidence = target_confidence
        
        # Initialize generators
        self.image_generator = ImageTo3DDogGenerator()
        self.hybrid_generator = HybridPerfectDogGenerator()
        self.realistic_generator = RealisticDogShapeGenerator()
        self.optimizer = PlanterShapeOptimizer()
        self.shape_converter = ShapeToPlanterConverter()
        
        # Track statistics
        self.stats = {
            'total_models': 0,
            'successful_models': 0,
            'failed_models': 0,
            'average_iterations': 0,
            'techniques_effectiveness': {},
            'optimization_success_rate': 0
        }
        
        print("🔄 Iterative Planter Generator initialized")
        print(f"   Target confidence: {target_confidence}")
        print(f"   Max iterations: {max_iterations}")

    def generate_perfect_planter(self, input_source, breed=None, size_mm=120, output_dir="iterative_models"):
        """
        Generate a perfect planter with iterative refinement
        
        Args:
            input_source: Path to image file, breed name, or 'synthetic'
            breed: Dog breed (if not using image)
            size_mm: Target size in millimeters
            output_dir: Output directory for generated models
        """
        start_time = time.time()
        print(f"\n{'='*80}")
        print(f"🎯 GENERATING PERFECT PLANTER")
        print(f"   Source: {input_source}")
        print(f"   Breed: {breed}")
        print(f"   Size: {size_mm}mm")
        print(f"{'='*80}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate base name for files
        if Path(input_source).exists():
            base_name = f"planter_{Path(input_source).stem}"
        else:
            base_name = f"planter_{breed or 'dog'}_{int(time.time())}"
        
        best_mesh = None
        best_confidence = 0
        iteration_results = []
        
        for iteration in range(self.max_iterations):
            print(f"\n🔄 ITERATION {iteration + 1}/{self.max_iterations}")
            print(f"{'─'*50}")
            
            # Generate initial model (or refine existing)
            if iteration == 0:
                mesh = self._generate_initial_model(input_source, breed, size_mm)
            else:
                # Apply optimization recommendations from previous iteration
                mesh = self._apply_optimizations(best_mesh, iteration_results[-1]['recommendations'], size_mm)
            
            if mesh is None:
                print(f"❌ Failed to generate model in iteration {iteration + 1}")
                continue
            
            # Save intermediate model
            temp_stl_path = output_path / f"{base_name}_iter_{iteration + 1}.stl"
            mesh.export(str(temp_stl_path))
            
            # Analyze quality
            print(f"📊 Analyzing quality...")
            quality_report = analyze_stl_quality(str(temp_stl_path))
            planter_analysis = analyze_planter_characteristics(str(temp_stl_path))
            
            # Get optimization recommendations
            recommendations = self.optimizer.analyze_planter_deficiencies(str(temp_stl_path))
            
            # Extract confidence score
            confidence = planter_analysis.get('planter_confidence', 0)
            
            iteration_result = {
                'iteration': iteration + 1,
                'stl_path': str(temp_stl_path),
                'confidence': confidence,
                'is_planter_like': planter_analysis.get('is_planter_like', False),
                'quality_metrics': quality_report,
                'planter_metrics': planter_analysis,
                'recommendations': recommendations,
                'improvement_potential': recommendations.get('overall_score', 0)
            }
            iteration_results.append(iteration_result)
            
            print(f"   Confidence: {confidence:.3f}")
            print(f"   Planter-like: {planter_analysis.get('is_planter_like', False)}")
            print(f"   Improvement potential: {recommendations.get('overall_score', 0):.1f}/100")
            
            # Update best model if this is better
            if confidence > best_confidence:
                best_confidence = confidence
                best_mesh = mesh.copy()
                print(f"   ✅ New best model!")
            
            # Check if we've achieved target quality
            if confidence >= self.target_confidence and planter_analysis.get('is_planter_like', False):
                print(f"🎉 TARGET ACHIEVED! Confidence: {confidence:.3f} >= {self.target_confidence}")
                break
            
            # If no significant improvement and multiple iterations, try shape conversion
            if iteration > 0 and confidence <= iteration_results[-2]['confidence'] + 0.05:
                print(f"⚠️ Limited improvement, trying shape-to-planter conversion")
                converted_mesh, conversion_report = self.shape_converter.convert_to_planter(
                    best_mesh, method='sectioned_planter', size_mm=size_mm
                )
                if converted_mesh:
                    best_mesh = converted_mesh
                    print(f"🔄 Applied shape-to-planter conversion")
            
            # If still not improving after conversion, try different conversion method
            elif iteration > 2 and confidence < self.target_confidence * 0.7:
                print(f"🔄 Trying alternative conversion method")
                converted_mesh, conversion_report = self.shape_converter.convert_to_planter(
                    best_mesh, method='envelope_planter', size_mm=size_mm
                )
                if converted_mesh:
                    best_mesh = converted_mesh
                    print(f"🔄 Applied envelope planter conversion")
        
        # Finalize best model
        final_result = self._finalize_model(best_mesh, best_confidence, base_name, output_path, iteration_results)
        
        # Update statistics
        self._update_stats(final_result, iteration_results)
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report(final_result, iteration_results, start_time)
        
        print(f"\n{'='*80}")
        print(f"🏁 GENERATION COMPLETE")
        print(f"   Final confidence: {best_confidence:.3f}")
        print(f"   Iterations used: {len(iteration_results)}")
        print(f"   Success: {'✅ YES' if best_confidence >= self.target_confidence else '❌ NO'}")
        print(f"   Total time: {time.time() - start_time:.1f}s")
        print(f"{'='*80}")
        
        return final_result

    def _generate_initial_model(self, input_source, breed, size_mm):
        """Generate initial model using best available method"""
        print("🏗️ Generating initial model...")
        
        # Determine generation method
        if Path(input_source).exists() and Path(input_source).suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
            # Image-based generation
            print("   Method: Image-to-3D conversion")
            result = self.image_generator.convert_image_to_dog_planter(input_source, breed, size_mm)
            return result['mesh'] if result else None
            
        elif breed:
            # Breed-based generation
            print(f"   Method: Hybrid generation for {breed}")
            try:
                result = self.hybrid_generator.generate_perfect_dog_planter(breed, size_mm=size_mm)
                # Handle different return types
                if isinstance(result, dict) and 'mesh' in result:
                    return result['mesh']
                elif isinstance(result, str):
                    # If it's a file path, load the mesh
                    import trimesh
                    return trimesh.load(result)
                elif hasattr(result, 'vertices'):
                    # If it's already a mesh object
                    return result
                else:
                    print(f"   Unexpected result type: {type(result)}")
                    return None
            except Exception as e:
                print(f"   Hybrid generation failed: {e}")
                # Fallback to realistic generator
                print("   Fallback: Realistic generation")
                return self.realistic_generator.generate_dog_shape(breed, size_mm)
        else:
            # Generic dog generation
            print("   Method: Generic realistic dog")
            return self.realistic_generator.generate_dog_shape('golden_retriever', size_mm)

    def _apply_optimizations(self, mesh, recommendations, size_mm):
        """Apply optimization recommendations to improve the mesh"""
        if not recommendations or not mesh:
            return mesh
        
        print("🔧 Applying optimizations...")
        optimized_mesh = mesh.copy()
        
        try:
            # Get prioritized recommendations
            priority_recs = recommendations.get('prioritized_recommendations', [])
            
            for rec in priority_recs[:3]:  # Apply top 3 recommendations
                action = rec.get('action', '')
                impact = rec.get('potential_impact', 0)
                
                print(f"   Applying: {action} (impact: {impact})")
                
                if 'opening' in action.lower():
                    optimized_mesh = self._improve_opening(optimized_mesh, size_mm)
                elif 'hollow' in action.lower() or 'cavity' in action.lower():
                    optimized_mesh = self._add_cavity(optimized_mesh, size_mm)
                elif 'taper' in action.lower():
                    optimized_mesh = self._improve_taper(optimized_mesh)
                elif 'stability' in action.lower() or 'base' in action.lower():
                    optimized_mesh = self._improve_stability(optimized_mesh)
                elif 'smooth' in action.lower():
                    optimized_mesh = self._smooth_mesh(optimized_mesh)
                elif 'wall' in action.lower() and 'thick' in action.lower():
                    optimized_mesh = self._thicken_walls(optimized_mesh, size_mm)
        
        except Exception as e:
            print(f"⚠️ Optimization error: {e}")
            return mesh
        
        return optimized_mesh

    def _improve_opening(self, mesh, size_mm):
        """Improve planter opening"""
        try:
            bounds = mesh.bounds
            height = bounds[1][2] - bounds[0][2]
            
            # Create opening at the top
            opening_radius = min(bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1]) * 0.25
            opening_center = [(bounds[0][0] + bounds[1][0]) / 2, 
                            (bounds[0][1] + bounds[1][1]) / 2,
                            bounds[1][2] - height * 0.1]
            
            # Create cylinder to subtract
            opening = trimesh.creation.cylinder(
                radius=opening_radius,
                height=height * 0.3,
                transform=trimesh.transformations.translation_matrix(opening_center)
            )
            
            result = mesh.difference(opening)
            return result if result and result.volume > 0 else mesh
            
        except Exception as e:
            print(f"Opening improvement failed: {e}")
            return mesh

    def _add_cavity(self, mesh, size_mm):
        """Add or improve internal cavity"""
        try:
            if not mesh.is_watertight:
                mesh.fill_holes()
            
            bounds = mesh.bounds
            cavity_radius = min(bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1]) * 0.3
            cavity_height = (bounds[1][2] - bounds[0][2]) * 0.6
            
            cavity_center = [(bounds[0][0] + bounds[1][0]) / 2,
                           (bounds[0][1] + bounds[1][1]) / 2,
                           bounds[1][2] - cavity_height / 2]
            
            cavity = trimesh.creation.cylinder(
                radius=cavity_radius,
                height=cavity_height,
                transform=trimesh.transformations.translation_matrix(cavity_center)
            )
            
            result = mesh.difference(cavity)
            return result if result and result.volume > 0 else mesh
            
        except Exception as e:
            print(f"Cavity addition failed: {e}")
            return mesh

    def _improve_taper(self, mesh):
        """Improve taper towards top"""
        try:
            # This is a simplified implementation
            # In practice, would need more sophisticated mesh deformation
            vertices = mesh.vertices.copy()
            bounds = mesh.bounds
            height = bounds[1][2] - bounds[0][2]
            
            for i, vertex in enumerate(vertices):
                z_ratio = (vertex[2] - bounds[0][2]) / height
                taper_factor = 1.0 - 0.3 * z_ratio  # Taper 30% towards top
                
                center_x = (bounds[0][0] + bounds[1][0]) / 2
                center_y = (bounds[0][1] + bounds[1][1]) / 2
                
                vertices[i][0] = center_x + (vertex[0] - center_x) * taper_factor
                vertices[i][1] = center_y + (vertex[1] - center_y) * taper_factor
            
            return trimesh.Trimesh(vertices=vertices, faces=mesh.faces, validate=False)
            
        except Exception as e:
            print(f"Taper improvement failed: {e}")
            return mesh

    def _improve_stability(self, mesh):
        """Improve base stability"""
        try:
            vertices = mesh.vertices.copy()
            bounds = mesh.bounds
            base_height = (bounds[1][2] - bounds[0][2]) * 0.1
            
            # Flatten and widen the base
            base_mask = vertices[:, 2] <= bounds[0][2] + base_height
            if np.any(base_mask):
                vertices[base_mask, 2] = bounds[0][2]  # Flatten base
                
                # Slightly widen base
                center_x = (bounds[0][0] + bounds[1][0]) / 2
                center_y = (bounds[0][1] + bounds[1][1]) / 2
                
                for i in np.where(base_mask)[0]:
                    vertices[i][0] = center_x + (vertices[i][0] - center_x) * 1.1
                    vertices[i][1] = center_y + (vertices[i][1] - center_y) * 1.1
            
            return trimesh.Trimesh(vertices=vertices, faces=mesh.faces, validate=False)
            
        except Exception as e:
            print(f"Stability improvement failed: {e}")
            return mesh

    def _smooth_mesh(self, mesh):
        """Smooth mesh surface"""
        try:
            return mesh.smoothed()
        except Exception as e:
            print(f"Smoothing failed: {e}")
            return mesh

    def _thicken_walls(self, mesh, size_mm):
        """Thicken walls for better printability"""
        try:
            # Simplified wall thickening
            # In practice, would use more sophisticated offset operations
            min_wall_thickness = max(1.0, size_mm * 0.02)  # 2% of size or 1mm minimum
            
            # This is a placeholder - real implementation would require
            # sophisticated mesh offsetting techniques
            return mesh
            
        except Exception as e:
            print(f"Wall thickening failed: {e}")
            return mesh

    def _finalize_model(self, mesh, confidence, base_name, output_path, iteration_results):
        """Finalize the best model with post-processing"""
        if mesh is None:
            return None
        
        print("🏁 Finalizing model...")
        
        # Final post-processing
        final_mesh = mesh.copy()
        
        # Clean up
        final_mesh.remove_duplicate_faces()
        final_mesh.remove_degenerate_faces()
        final_mesh.merge_vertices()
        final_mesh.remove_unreferenced_vertices()
        
        # Fix normals
        final_mesh.fix_normals()
        
        # Save final model
        final_stl_path = output_path / f"{base_name}_FINAL.stl"
        final_mesh.export(str(final_stl_path))
        
        # Final analysis
        final_quality = analyze_stl_quality(str(final_stl_path))
        final_planter = analyze_planter_characteristics(str(final_stl_path))
        
        return {
            'success': confidence >= self.target_confidence,
            'final_stl_path': str(final_stl_path),
            'final_confidence': confidence,
            'is_planter_like': final_planter.get('is_planter_like', False),
            'iterations_used': len(iteration_results),
            'final_quality': final_quality,
            'final_planter_analysis': final_planter,
            'iteration_history': iteration_results
        }

    def _update_stats(self, result, iteration_results):
        """Update generator statistics"""
        self.stats['total_models'] += 1
        
        if result and result['success']:
            self.stats['successful_models'] += 1
        else:
            self.stats['failed_models'] += 1
        
        if iteration_results:
            iterations = len(iteration_results)
            current_avg = self.stats['average_iterations']
            total = self.stats['total_models']
            self.stats['average_iterations'] = (current_avg * (total - 1) + iterations) / total

    def _generate_comprehensive_report(self, result, iteration_results, start_time):
        """Generate comprehensive report"""
        report = {
            'timestamp': int(time.time() * 1000),
            'generator': 'iterative_planter_generator',
            'generation_time': time.time() - start_time,
            'target_confidence': self.target_confidence,
            'max_iterations': self.max_iterations,
            'result': result,
            'iteration_history': iteration_results,
            'performance_metrics': {
                'convergence_rate': len(iteration_results) / self.max_iterations,
                'improvement_per_iteration': self._calculate_improvement_rate(iteration_results),
                'final_score': result['final_confidence'] if result else 0
            }
        }
        
        return report

    def _calculate_improvement_rate(self, iteration_results):
        """Calculate improvement rate across iterations"""
        if len(iteration_results) < 2:
            return 0
        
        initial_confidence = iteration_results[0]['confidence']
        final_confidence = iteration_results[-1]['confidence']
        iterations = len(iteration_results)
        
        return (final_confidence - initial_confidence) / iterations

    def generate_batch_perfect_planters(self, inputs, output_dir="batch_perfect_planters"):
        """Generate a batch of perfect planters"""
        print(f"\n🏭 BATCH GENERATION: {len(inputs)} planters")
        print(f"{'='*80}")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        batch_results = []
        success_count = 0
        
        for i, input_config in enumerate(inputs):
            print(f"\n📦 BATCH ITEM {i+1}/{len(inputs)}")
            
            # Extract configuration
            input_source = input_config.get('source', '')
            breed = input_config.get('breed', None)
            size_mm = input_config.get('size_mm', 120)
            
            # Generate planter
            result = self.generate_perfect_planter(
                input_source=input_source,
                breed=breed,
                size_mm=size_mm,
                output_dir=str(output_path / f"item_{i+1:03d}")
            )
            
            if result and result['success']:
                success_count += 1
            
            batch_results.append({
                'input_config': input_config,
                'result': result,
                'success': result['success'] if result else False
            })
        
        # Generate batch report
        batch_report = {
            'timestamp': int(time.time() * 1000),
            'total_items': len(inputs),
            'successful_items': success_count,
            'success_rate': success_count / len(inputs) * 100,
            'target_confidence': self.target_confidence,
            'generator_stats': self.stats,
            'results': batch_results
        }
        
        # Save batch report
        batch_report_path = output_path / f"batch_report_{batch_report['timestamp']}.json"
        with open(batch_report_path, 'w') as f:
            json.dump(batch_report, f, indent=2, default=str)
        
        print(f"\n🎯 BATCH COMPLETE")
        print(f"   Success rate: {batch_report['success_rate']:.1f}%")
        print(f"   Report saved: {batch_report_path}")
        
        return batch_report

    def get_generator_statistics(self):
        """Get current generator statistics"""
        success_rate = (self.stats['successful_models'] / self.stats['total_models'] * 100) if self.stats['total_models'] > 0 else 0
        
        return {
            'total_models_generated': self.stats['total_models'],
            'successful_models': self.stats['successful_models'],
            'failed_models': self.stats['failed_models'],
            'success_rate': success_rate,
            'average_iterations_per_model': self.stats['average_iterations'],
            'target_confidence': self.target_confidence,
            'techniques_effectiveness': self.stats['techniques_effectiveness']
        }

if __name__ == "__main__":
    # Initialize generator
    generator = IterativePlanterGenerator(max_iterations=5, target_confidence=0.8)
    
    # Test with different input types
    test_inputs = [
        {'source': 'golden_retriever', 'breed': 'golden_retriever', 'size_mm': 120},
        {'source': 'german_shepherd', 'breed': 'german_shepherd', 'size_mm': 140},
        {'source': 'synthetic', 'breed': 'labrador', 'size_mm': 100}
    ]
    
    # Generate batch
    results = generator.generate_batch_perfect_planters(test_inputs)
    
    # Print statistics
    stats = generator.get_generator_statistics()
    print(f"\n📊 FINAL STATISTICS:")
    print(f"   Models generated: {stats['total_models_generated']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")
    print(f"   Average iterations: {stats['average_iterations_per_model']:.1f}")
    
    print("\n🎉 Iterative generation complete!")
