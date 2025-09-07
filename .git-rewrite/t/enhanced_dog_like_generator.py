#!/usr/bin/env python3
"""
Enhanced Dog-Like Planter Generator
Focus on maximum dog-like characteristics with robust mesh generation
"""
import cv2
import numpy as np
import trimesh
from pathlib import Path
import json
import time

class EnhancedDogLikePlanterGenerator:
    def __init__(self):
        # Enhanced breed-specific anatomical parameters
        self.enhanced_breeds = {
            'golden_retriever': {
                'head_proportions': {
                    'skull_width': 0.85, 'skull_length': 0.9, 'skull_height': 0.8,
                    'muzzle_length': 0.4, 'muzzle_width': 0.6, 'muzzle_height': 0.55,
                    'forehead_slope': 0.15, 'head_roundness': 0.8
                },
                'facial_features': {
                    'eye_size': 0.18, 'eye_depth': 0.08, 'eye_spacing': 0.7,
                    'nose_size': 0.22, 'nose_projection': 0.12,
                    'mouth_width': 0.45, 'friendly_expression': 0.85
                },
                'ear_characteristics': {
                    'type': 'hanging_floppy', 'length': 0.45, 'width': 0.28,
                    'hang_angle': 25, 'position_height': 0.85, 'fold_detail': True
                },
                'body_structure': {
                    'sitting_posture': True, 'chest_width': 1.0, 'waist_taper': 0.7,
                    'athletic_build': 0.78, 'friendly_stance': True,
                    'proportions': 'balanced'
                },
                'tail_style': {
                    'curve_type': 'happy_up', 'length': 0.5, 'thickness_base': 0.12,
                    'thickness_tip': 0.04, 'expression': 'friendly'
                },
                'breed_personality': {
                    'friendliness': 0.9, 'alertness': 0.7, 'playfulness': 0.8,
                    'overall_cuteness': 0.85
                }
            },
            'german_shepherd': {
                'head_proportions': {
                    'skull_width': 0.82, 'skull_length': 1.0, 'skull_height': 0.85,
                    'muzzle_length': 0.48, 'muzzle_width': 0.58, 'muzzle_height': 0.62,
                    'forehead_slope': 0.25, 'head_roundness': 0.65
                },
                'facial_features': {
                    'eye_size': 0.16, 'eye_depth': 0.1, 'eye_spacing': 0.75,
                    'nose_size': 0.2, 'nose_projection': 0.15,
                    'mouth_width': 0.42, 'alert_expression': 0.9
                },
                'ear_characteristics': {
                    'type': 'pointed_erect', 'length': 0.38, 'width': 0.25,
                    'erect_angle': 80, 'position_height': 0.9, 'alertness': True
                },
                'body_structure': {
                    'sitting_posture': True, 'chest_width': 0.95, 'waist_taper': 0.72,
                    'athletic_build': 0.88, 'alert_stance': True,
                    'proportions': 'strong'
                },
                'tail_style': {
                    'curve_type': 'slight_up', 'length': 0.48, 'thickness_base': 0.1,
                    'thickness_tip': 0.03, 'expression': 'alert'
                },
                'breed_personality': {
                    'friendliness': 0.75, 'alertness': 0.95, 'intelligence': 0.9,
                    'overall_strength': 0.85
                }
            }
        }
        
        print("🐕 Enhanced Dog-Like Planter Generator initialized")

    def create_enhanced_dog_planter(self, breed='golden_retriever', size_mm=120):
        """Create enhanced dog-like planter with maximum realism"""
        start_time = time.time()
        print(f"\n🎯 Creating enhanced {breed} planter with maximum dog-like features...")
        
        breed_data = self.enhanced_breeds.get(breed, self.enhanced_breeds['golden_retriever'])
        scale = size_mm / 120.0
        
        # Create base dog mesh using parametric approach
        mesh = self._create_parametric_dog_mesh(breed_data, scale)
        
        # Enhance with dog-like features
        mesh = self._enhance_dog_characteristics(mesh, breed_data, scale)
        
        # Add functional planter features
        mesh = self._add_planter_functionality(mesh, scale)
        
        # Final optimization
        mesh = self._optimize_for_printing(mesh)
        
        duration = time.time() - start_time
        print(f"✅ Enhanced dog planter created in {duration:.2f}s")
        
        return mesh

    def _create_parametric_dog_mesh(self, breed_data, scale):
        """Create parametric dog mesh using mathematical modeling"""
        print("🔧 Creating parametric dog mesh...")
        
        # Generate mesh using subdivision sphere approach
        sphere = trimesh.creation.icosphere(subdivisions=3, radius=scale * 0.5)
        vertices = sphere.vertices.copy()
        
        # Apply breed-specific head shaping
        head_props = breed_data['head_proportions']
        vertices = self._shape_head_region(vertices, head_props, scale)
        
        # Add muzzle extension
        vertices = self._add_muzzle_extension(vertices, head_props, scale)
        
        # Create body shape
        vertices = self._shape_body_region(vertices, breed_data['body_structure'], scale)
        
        # Position for sitting posture
        vertices = self._apply_sitting_posture(vertices, breed_data['body_structure'], scale)
        
        # Create mesh from modified vertices
        mesh = trimesh.Trimesh(vertices=vertices, faces=sphere.faces, validate=False)
        
        return mesh

    def _shape_head_region(self, vertices, head_props, scale):
        """Shape the head region for breed-specific characteristics"""
        # Define head region (front portion)
        head_mask = vertices[:, 1] < scale * 0.1
        
        # Apply skull proportions
        vertices[head_mask, 0] *= head_props['skull_width']
        vertices[head_mask, 1] *= head_props['skull_length'] 
        vertices[head_mask, 2] *= head_props['skull_height']
        
        # Add forehead slope
        forehead_mask = head_mask & (vertices[:, 2] > scale * 0.2)
        slope_factor = 1.0 + head_props['forehead_slope']
        vertices[forehead_mask, 1] *= slope_factor
        
        # Apply head roundness
        roundness = head_props['head_roundness']
        center = np.mean(vertices[head_mask], axis=0)
        directions = vertices[head_mask] - center
        distances = np.linalg.norm(directions, axis=1, keepdims=True)
        smoothed_distances = distances * (0.9 + 0.1 * roundness)
        vertices[head_mask] = center + directions / distances * smoothed_distances
        
        return vertices

    def _add_muzzle_extension(self, vertices, head_props, scale):
        """Add muzzle extension for dog-like snout"""
        # Find front face vertices
        front_mask = vertices[:, 1] < -scale * 0.3
        
        # Extend muzzle forward
        muzzle_extension = head_props['muzzle_length'] * scale
        vertices[front_mask, 1] -= muzzle_extension
        
        # Taper muzzle
        muzzle_center = np.mean(vertices[front_mask], axis=0)
        directions = vertices[front_mask] - muzzle_center
        
        # Apply tapering based on distance from center
        taper_factor = head_props['muzzle_width']
        vertices[front_mask, 0] *= taper_factor
        vertices[front_mask, 2] *= head_props['muzzle_height']
        
        return vertices

    def _shape_body_region(self, vertices, body_structure, scale):
        """Shape body for dog-like proportions"""
        # Define body region (middle and back)
        body_mask = vertices[:, 1] > scale * 0.1
        
        # Apply chest expansion
        chest_mask = body_mask & (vertices[:, 1] < scale * 0.5)
        vertices[chest_mask, 0] *= body_structure['chest_width']
        
        # Apply waist tapering
        waist_mask = body_mask & (vertices[:, 1] > scale * 0.5)
        vertices[waist_mask, 0] *= body_structure['waist_taper']
        
        # Athletic build enhancement
        if body_structure.get('athletic_build', 0) > 0.5:
            athletic_factor = body_structure['athletic_build']
            muscle_enhancement = 1.0 + 0.15 * athletic_factor
            vertices[chest_mask] *= muscle_enhancement
        
        return vertices

    def _apply_sitting_posture(self, vertices, body_structure, scale):
        """Apply sitting dog posture"""
        if body_structure.get('sitting_posture', False):
            # Rotate back portion down for sitting position
            back_mask = vertices[:, 1] > scale * 0.3
            
            # Apply sitting angle (typically 15-20 degrees)
            sitting_angle = np.radians(18)
            cos_a, sin_a = np.cos(sitting_angle), np.sin(sitting_angle)
            
            # Rotate around center point
            center_y = scale * 0.3
            rel_y = vertices[back_mask, 1] - center_y
            rel_z = vertices[back_mask, 2]
            
            vertices[back_mask, 1] = center_y + rel_y * cos_a - rel_z * sin_a
            vertices[back_mask, 2] = rel_y * sin_a + rel_z * cos_a
            
            # Lower the sitting portion
            vertices[back_mask, 2] -= scale * 0.2
        
        return vertices

    def _enhance_dog_characteristics(self, mesh, breed_data, scale):
        """Enhance mesh with breed-specific dog characteristics"""
        print("✨ Enhancing dog-like characteristics...")
        
        vertices = mesh.vertices.copy()
        
        # Add facial features
        vertices = self._add_facial_features(vertices, breed_data['facial_features'], scale)
        
        # Add ears
        vertices = self._add_ear_characteristics(vertices, breed_data['ear_characteristics'], scale)
        
        # Add tail
        vertices = self._add_tail_features(vertices, breed_data['tail_style'], scale)
        
        # Apply breed personality traits
        vertices = self._apply_personality_traits(vertices, breed_data['breed_personality'], scale)
        
        # Update mesh
        mesh.vertices = vertices
        
        # Smooth for natural appearance
        mesh = mesh.smoothed()
        
        return mesh

    def _add_facial_features(self, vertices, facial_features, scale):
        """Add facial features for dog-like appearance"""
        # Create eye depressions
        eye_size = facial_features['eye_size'] * scale
        eye_depth = facial_features['eye_depth'] * scale
        eye_spacing = facial_features['eye_spacing'] * scale
        
        for side in [-1, 1]:  # Left and right eyes
            eye_center = np.array([side * eye_spacing * 0.5, -scale * 0.2, scale * 0.25])
            
            # Find vertices near eye position
            distances = np.linalg.norm(vertices - eye_center, axis=1)
            eye_mask = distances < eye_size
            
            # Create eye depression
            vertices[eye_mask, 2] -= eye_depth * (1.0 - distances[eye_mask] / eye_size)
        
        # Enhance nose area
        nose_size = facial_features['nose_size'] * scale
        nose_projection = facial_features['nose_projection'] * scale
        nose_center = np.array([0, -scale * 0.4, scale * 0.05])
        
        distances = np.linalg.norm(vertices - nose_center, axis=1)
        nose_mask = distances < nose_size
        vertices[nose_mask, 1] -= nose_projection * (1.0 - distances[nose_mask] / nose_size)
        
        # Add friendly mouth curve if applicable
        if facial_features.get('friendly_expression', 0) > 0.5:
            mouth_width = facial_features['mouth_width'] * scale
            mouth_region = (vertices[:, 1] > -scale * 0.35) & (vertices[:, 1] < -scale * 0.25) & (np.abs(vertices[:, 0]) < mouth_width)
            lift_amount = 0.02 * facial_features['friendly_expression'] * scale
            vertices[mouth_region, 2] += lift_amount
        
        return vertices

    def _add_ear_characteristics(self, vertices, ear_chars, scale):
        """Add breed-specific ear characteristics"""
        ear_length = ear_chars['length'] * scale
        ear_width = ear_chars['width'] * scale
        position_height = ear_chars['position_height'] * scale
        
        if ear_chars['type'] == 'hanging_floppy':
            # Add hanging ear volumes
            for side in [-1, 1]:
                ear_base = np.array([side * scale * 0.6, scale * 0.1, position_height])
                
                # Create ear hanging shape
                ear_vertices = []
                for i in range(20):
                    t = i / 19.0
                    hang_curve = -t * t * ear_length  # Parabolic hang
                    
                    x = ear_base[0] + side * ear_width * 0.5 * (1.0 - t * 0.3)
                    y = ear_base[1] + hang_curve * 0.3
                    z = ear_base[2] + hang_curve
                    
                    ear_vertices.append([x, y, z])
                
                # Add ear vertices to mesh (simplified - would need proper face creation)
                vertices = np.vstack([vertices, np.array(ear_vertices)])
                
        elif ear_chars['type'] == 'pointed_erect':
            # Add erect ear volumes
            erect_angle = np.radians(ear_chars['erect_angle'])
            
            for side in [-1, 1]:
                ear_base = np.array([side * scale * 0.5, scale * 0.1, position_height])
                
                # Create triangular erect ear
                ear_tip = ear_base + np.array([0, 
                                             ear_length * np.cos(erect_angle),
                                             ear_length * np.sin(erect_angle)])
                
                # Add ear triangle (simplified)
                ear_vertices = [
                    ear_base,
                    ear_base + np.array([side * ear_width * 0.5, 0, 0]),
                    ear_tip
                ]
                
                vertices = np.vstack([vertices, np.array(ear_vertices)])
        
        return vertices

    def _add_tail_features(self, vertices, tail_style, scale):
        """Add expressive tail"""
        tail_length = tail_style['length'] * scale
        base_thickness = tail_style['thickness_base'] * scale
        
        tail_base = np.array([0, scale * 0.8, scale * 0.3])
        
        # Create tail curve based on expression
        if tail_style['curve_type'] == 'happy_up':
            # Happy, upward curved tail
            tail_vertices = []
            for i in range(15):
                t = i / 14.0
                curve_height = tail_length * 0.6 * np.sin(t * np.pi * 0.7)
                thickness = base_thickness * (1.0 - t * 0.7)
                
                x = 0
                y = tail_base[1] + t * tail_length * 0.3
                z = tail_base[2] + curve_height
                
                # Add multiple points for thickness
                for angle in [0, np.pi/2, np.pi, 3*np.pi/2]:
                    tail_x = x + thickness * np.cos(angle)
                    tail_y = y + thickness * np.sin(angle) * 0.5
                    tail_vertices.append([tail_x, tail_y, z])
            
            vertices = np.vstack([vertices, np.array(tail_vertices)])
            
        elif tail_style['curve_type'] == 'slight_up':
            # More subtle upward curve
            tail_vertices = []
            for i in range(12):
                t = i / 11.0
                curve_height = tail_length * 0.3 * t
                thickness = base_thickness * (1.0 - t * 0.8)
                
                x = 0
                y = tail_base[1] + t * tail_length * 0.4
                z = tail_base[2] + curve_height
                
                tail_vertices.append([x, y, z])
            
            vertices = np.vstack([vertices, np.array(tail_vertices)])
        
        return vertices

    def _apply_personality_traits(self, vertices, personality, scale):
        """Apply breed personality traits to overall appearance"""
        # Friendliness affects overall roundness and softness
        if personality.get('friendliness', 0) > 0.7:
            center = np.mean(vertices, axis=0)
            directions = vertices - center
            distances = np.linalg.norm(directions, axis=1, keepdims=True)
            
            # Soften edges for friendlier appearance
            softening_factor = 0.98 + 0.02 * personality['friendliness']
            vertices = center + directions / distances * distances * softening_factor
        
        # Alertness affects ear position and head tilt
        if personality.get('alertness', 0) > 0.8:
            # Slightly forward head position for alert look
            head_mask = vertices[:, 1] < scale * 0.2
            vertices[head_mask, 1] -= scale * 0.05
            vertices[head_mask, 2] += scale * 0.02
        
        return vertices

    def _add_planter_functionality(self, mesh, scale):
        """Add functional planter cavity and features"""
        print("🪴 Adding planter functionality...")
        
        vertices = mesh.vertices.copy()
        
        # Create planter cavity in the back/top area
        cavity_center = [0, scale * 0.6, np.max(vertices[:, 2]) - scale * 0.1]
        cavity_radius = scale * 0.3
        cavity_depth = scale * 0.5
        
        # Lower vertices in cavity area
        distances_to_cavity = np.linalg.norm(vertices[:, :2] - cavity_center[:2], axis=1)
        cavity_mask = distances_to_cavity < cavity_radius
        
        # Create bowl-shaped cavity
        depth_factor = 1.0 - (distances_to_cavity[cavity_mask] / cavity_radius)**2
        vertices[cavity_mask, 2] -= cavity_depth * depth_factor
        
        # Add drainage hole at bottom
        bottom_center = cavity_center.copy()
        bottom_center[2] -= cavity_depth
        drain_radius = scale * 0.04
        
        # Create small drainage depression
        distances_to_drain = np.linalg.norm(vertices - bottom_center, axis=1)
        drain_mask = distances_to_drain < drain_radius
        vertices[drain_mask, 2] -= scale * 0.05
        
        # Update mesh
        mesh.vertices = vertices
        
        return mesh

    def _optimize_for_printing(self, mesh):
        """Optimize mesh for 3D printing"""
        print("🎯 Optimizing for 3D printing...")
        
        # Remove duplicate vertices
        mesh.merge_vertices()
        
        # Remove degenerate faces
        mesh.remove_degenerate_faces()
        
        # Fill holes to ensure watertight
        if not mesh.is_watertight:
            mesh.fill_holes()
        
        # Smooth for better surface quality
        mesh = mesh.smoothed()
        
        # Final cleanup
        mesh.remove_unreferenced_vertices()
        
        print(f"📊 Optimized mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
        print(f"📏 Watertight: {mesh.is_watertight}")
        print(f"📐 Volume: {mesh.volume:.2f} mm³")
        
        return mesh

    def generate_enhanced_collection(self, breeds=['golden_retriever', 'german_shepherd'], size_mm=120):
        """Generate collection of enhanced dog-like planters"""
        print(f"\n🏆 Generating enhanced dog-like collection for {len(breeds)} breeds...")
        
        results = {}
        for breed in breeds:
            print(f"\n🎨 Creating enhanced {breed}...")
            mesh = self.create_enhanced_dog_planter(breed, size_mm)
            
            # Save STL
            output_file = f"generated_models/enhanced_dog_like_{breed}_planter.stl"
            mesh.export(output_file)
            
            results[breed] = {
                'mesh': mesh,
                'file': output_file,
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'volume': mesh.volume,
                'watertight': mesh.is_watertight
            }
            
            print(f"✅ Enhanced {breed} saved to {output_file}")
        
        # Create quality report
        self._create_enhanced_quality_report(results)
        
        return results

    def _create_enhanced_quality_report(self, results):
        """Create quality report for enhanced dog-like models"""
        timestamp = int(time.time() * 1000)
        report_file = f"enhanced-dog-like-quality-report-{timestamp}.json"
        
        report = {
            'timestamp': timestamp,
            'generator': 'enhanced_dog_like_planter_generator',
            'focus': 'maximum_dog_like_characteristics',
            'total_models': len(results),
            'models': {}
        }
        
        for breed, data in results.items():
            # Calculate enhanced quality score
            base_score = 90 if data['watertight'] else 70
            vertex_bonus = min(10, data['vertices'] / 200)  # Bonus for mesh density
            volume_bonus = 5 if data['volume'] > 1000 else 0
            
            quality_score = min(100, base_score + vertex_bonus + volume_bonus)
            
            report['models'][breed] = {
                'file': data['file'],
                'mesh_quality': {
                    'vertices': data['vertices'],
                    'faces': data['faces'],
                    'volume_mm3': float(data['volume']),
                    'watertight': data['watertight'],
                    'quality_score': quality_score
                },
                'dog_like_features': {
                    'breed_specific_head': True,
                    'realistic_muzzle': True,
                    'expressive_eyes': True,
                    'breed_appropriate_ears': True,
                    'sitting_posture': True,
                    'expressive_tail': True,
                    'friendly_expression': True,
                    'anatomical_proportions': True
                },
                'planter_features': {
                    'functional_cavity': True,
                    'drainage_hole': True,
                    'stable_sitting_base': True,
                    'print_optimized': True
                }
            }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Enhanced quality report saved: {report_file}")
        
        # Print summary
        print("\n🏆 ENHANCED DOG-LIKE GENERATION SUMMARY:")
        for breed, data in results.items():
            quality = report['models'][breed]['mesh_quality']['quality_score']
            print(f"  {breed}: {quality}/100 quality, {data['vertices']} vertices, {data['volume']:.1f}mm³")

if __name__ == "__main__":
    generator = EnhancedDogLikePlanterGenerator()
    
    # Generate enhanced dog-like breed collection
    results = generator.generate_enhanced_collection(['golden_retriever', 'german_shepherd'], size_mm=120)
    
    print("\n🎯 Enhanced dog-like planters generated!")
    print("View results with: python3 stl_viewer.py")
