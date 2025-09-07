#!/usr/bin/env python3
"""
Ultimate Dog Planter Generator
Creates perfect breed-specific dog planters with anatomical accuracy
"""
import cv2
import numpy as np
import trimesh
from pathlib import Path
import json
import time
import argparse

class UltimateDogPlanterGenerator:
    def __init__(self):
        # Comprehensive breed database with precise anatomical parameters
        self.breed_database = {
            'golden_retriever': {
                'name': 'Golden Retriever',
                'head': {
                    'width_ratio': 0.8, 'length_ratio': 0.9, 'height_ratio': 0.8,
                    'muzzle_length': 0.6, 'forehead_slope': 0.3
                },
                'ears': {'type': 'floppy', 'size': 0.6, 'position': 0.7},
                'body': {
                    'length': 1.2, 'width': 0.7, 'height': 0.8,
                    'chest_depth': 0.9, 'waist_taper': 0.8
                },
                'legs': {'front_length': 0.4, 'back_length': 0.35, 'thickness': 0.08},
                'tail': {'length': 0.6, 'curve': 0.3, 'thickness': 0.05},
                'sitting_pose': {'back_angle': 20, 'front_straight': True}
            },
            'german_shepherd': {
                'name': 'German Shepherd',
                'head': {
                    'width_ratio': 0.7, 'length_ratio': 1.0, 'height_ratio': 0.85,
                    'muzzle_length': 0.7, 'forehead_slope': 0.2
                },
                'ears': {'type': 'erect', 'size': 0.4, 'position': 0.8},
                'body': {
                    'length': 1.3, 'width': 0.6, 'height': 0.9,
                    'chest_depth': 0.95, 'waist_taper': 0.7
                },
                'legs': {'front_length': 0.45, 'back_length': 0.4, 'thickness': 0.09},
                'tail': {'length': 0.7, 'curve': 0.2, 'thickness': 0.06},
                'sitting_pose': {'back_angle': 15, 'front_straight': True}
            },
            'pug': {
                'name': 'Pug',
                'head': {
                    'width_ratio': 1.0, 'length_ratio': 0.7, 'height_ratio': 0.9,
                    'muzzle_length': 0.2, 'forehead_slope': 0.6
                },
                'ears': {'type': 'small_fold', 'size': 0.2, 'position': 0.8},
                'body': {
                    'length': 0.9, 'width': 0.8, 'height': 0.7,
                    'chest_depth': 0.8, 'waist_taper': 0.9
                },
                'legs': {'front_length': 0.3, 'back_length': 0.25, 'thickness': 0.07},
                'tail': {'length': 0.4, 'curve': 0.8, 'thickness': 0.04},
                'sitting_pose': {'back_angle': 25, 'front_straight': True}
            },
            'labrador': {
                'name': 'Labrador',
                'head': {
                    'width_ratio': 0.85, 'length_ratio': 0.85, 'height_ratio': 0.8,
                    'muzzle_length': 0.5, 'forehead_slope': 0.25
                },
                'ears': {'type': 'hanging', 'size': 0.5, 'position': 0.7},
                'body': {
                    'length': 1.15, 'width': 0.75, 'height': 0.8,
                    'chest_depth': 0.9, 'waist_taper': 0.8
                },
                'legs': {'front_length': 0.4, 'back_length': 0.35, 'thickness': 0.08},
                'tail': {'length': 0.6, 'curve': 0.2, 'thickness': 0.05},
                'sitting_pose': {'back_angle': 18, 'front_straight': True}
            },
            'beagle': {
                'name': 'Beagle',
                'head': {
                    'width_ratio': 0.75, 'length_ratio': 0.8, 'height_ratio': 0.75,
                    'muzzle_length': 0.5, 'forehead_slope': 0.3
                },
                'ears': {'type': 'long_hanging', 'size': 0.7, 'position': 0.6},
                'body': {
                    'length': 1.0, 'width': 0.7, 'height': 0.75,
                    'chest_depth': 0.85, 'waist_taper': 0.8
                },
                'legs': {'front_length': 0.35, 'back_length': 0.3, 'thickness': 0.07},
                'tail': {'length': 0.5, 'curve': 0.4, 'thickness': 0.04},
                'sitting_pose': {'back_angle': 22, 'front_straight': True}
            }
        }
        
        print("🏆 Ultimate Dog Planter Generator initialized")
        print(f"   Available breeds: {', '.join(self.breed_database.keys())}")

    def generate_ultimate_planter(self, breed_name, pet_name=None, size_mm=120):
        """
        Generate the ultimate breed-specific dog planter
        """
        print(f"\n🎯 Generating ultimate {breed_name} planter")
        
        # Get breed parameters
        if breed_name not in self.breed_database:
            print(f"⚠️ Breed '{breed_name}' not in database, using closest match")
            breed_name = self._find_closest_breed(breed_name)
        
        breed_params = self.breed_database[breed_name]
        base_scale = size_mm
        
        print(f"📐 Using {breed_params['name']} parameters, base size: {size_mm}mm")
        
        # Create anatomically perfect head
        head_mesh = self._create_perfect_head(breed_params['head'], base_scale)
        
        # Create breed-specific ears
        ear_meshes = self._create_perfect_ears(breed_params['ears'], breed_params['head'], base_scale)
        
        # Create proportional body
        body_mesh = self._create_perfect_body(breed_params['body'], base_scale)
        
        # Create sitting pose legs
        leg_meshes = self._create_sitting_legs(breed_params['legs'], breed_params['sitting_pose'], base_scale)
        
        # Create characteristic tail
        tail_mesh = self._create_perfect_tail(breed_params['tail'], base_scale)
        
        # Assemble the complete dog
        complete_dog = self._assemble_perfect_dog(
            head_mesh, ear_meshes, body_mesh, leg_meshes, tail_mesh, breed_params
        )
        
        # Add premium planter features
        planter_mesh = self._add_premium_planter_features(complete_dog, breed_params)
        
        # Final perfection pass
        final_mesh = self._perfection_finishing(planter_mesh, breed_name)
        
        # Save with quality metadata
        timestamp = int(time.time())
        output_path = f"generated_models/ultimate_{breed_name}_{pet_name or 'planter'}_{timestamp}.stl"
        final_mesh.export(output_path)
        
        # Create quality report
        self._create_quality_report(final_mesh, breed_params, output_path)
        
        print(f"🏆 Ultimate {breed_name} planter complete: {output_path}")
        return output_path

    def _find_closest_breed(self, breed_name):
        """Find the closest breed match"""
        breed_lower = breed_name.lower()
        
        # Direct matches
        for key in self.breed_database.keys():
            if key in breed_lower or breed_lower in key:
                return key
        
        # Keyword matches
        if 'retriever' in breed_lower or 'golden' in breed_lower:
            return 'golden_retriever'
        elif 'shepherd' in breed_lower or 'german' in breed_lower:
            return 'german_shepherd'
        elif 'lab' in breed_lower:
            return 'labrador'
        elif 'pug' in breed_lower:
            return 'pug'
        elif 'beagle' in breed_lower:
            return 'beagle'
        
        # Default to golden retriever
        return 'golden_retriever'

    def _create_perfect_head(self, head_params, base_scale):
        """Create anatomically perfect breed-specific head"""
        print("   Creating perfect head...")
        
        # Calculate precise dimensions
        width = base_scale * head_params['width_ratio']
        length = base_scale * head_params['length_ratio'] 
        height = base_scale * head_params['height_ratio']
        
        # Create base head shape
        head = trimesh.creation.icosphere(subdivisions=4, radius=1.0)
        
        # Apply breed-specific proportions
        vertices = head.vertices
        vertices[:, 0] *= width/2    # X width
        vertices[:, 1] *= height/2   # Y height
        vertices[:, 2] *= length/2   # Z length
        
        # Create breed-specific muzzle
        muzzle_length = length * head_params['muzzle_length']
        forehead_slope = head_params['forehead_slope']
        
        for i, vertex in enumerate(vertices):
            x, y, z = vertex
            
            # Front muzzle area (positive Z)
            if z > 0:
                distance_factor = z / (length/2)
                
                # Muzzle tapering
                if distance_factor > 0.3:  # Muzzle region
                    muzzle_factor = (distance_factor - 0.3) / 0.7
                    
                    # Taper width and height
                    width_scale = 1.0 - muzzle_factor * 0.4
                    height_scale = 1.0 - muzzle_factor * 0.3
                    
                    vertices[i][0] *= width_scale
                    vertices[i][1] *= height_scale
                    
                    # Extend muzzle
                    vertices[i][2] += muzzle_factor * muzzle_length * 0.3
            
            # Forehead slope
            if z < 0 and y > 0:  # Back of head, top
                slope_factor = (-z / (length/2)) * (y / (height/2))
                vertices[i][1] += slope_factor * forehead_slope * height * 0.2
        
        head.vertices = vertices
        return head

    def _create_perfect_ears(self, ear_params, head_params, base_scale):
        """Create breed-specific perfect ears"""
        print(f"   Creating {ear_params['type']} ears...")
        
        ear_size = ear_params['size']
        ear_position = ear_params['position']
        head_width = base_scale * head_params['width_ratio']
        head_height = base_scale * head_params['height_ratio']
        
        ears = []
        
        if ear_params['type'] == 'floppy':
            # Golden Retriever style floppy ears
            for side in [-1, 1]:
                ear = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
                
                # Scale to ear proportions
                ear_width = head_width * 0.15 * ear_size
                ear_length = head_height * 0.5 * ear_size
                ear_thickness = head_width * 0.04
                
                ear.vertices[:, 0] *= ear_width
                ear.vertices[:, 1] *= ear_length
                ear.vertices[:, 2] *= ear_thickness
                
                # Position on head
                ear.apply_translation([
                    side * head_width * 0.35,
                    head_height * ear_position * 0.2,
                    0
                ])
                
                # Rotate for hanging position
                ear.apply_transform(trimesh.transformations.rotation_matrix(
                    np.radians(30 * side), [0, 0, 1]
                ))
                
                ears.append(ear)
                
        elif ear_params['type'] == 'erect':
            # German Shepherd style erect ears
            for side in [-1, 1]:
                ear = trimesh.creation.cone(radius=head_width * 0.08 * ear_size, 
                                         height=head_height * 0.35 * ear_size)
                
                # Position on top of head
                ear.apply_translation([
                    side * head_width * 0.25,
                    head_height * ear_position * 0.3,
                    0
                ])
                
                ears.append(ear)
                
        elif ear_params['type'] == 'small_fold':
            # Pug style small folded ears
            for side in [-1, 1]:
                ear = trimesh.creation.icosphere(subdivisions=1, radius=1.0)
                
                ear_width = head_width * 0.08 * ear_size
                ear_height = head_height * 0.15 * ear_size
                ear_thickness = head_width * 0.03
                
                ear.vertices[:, 0] *= ear_width
                ear.vertices[:, 1] *= ear_height
                ear.vertices[:, 2] *= ear_thickness
                
                ear.apply_translation([
                    side * head_width * 0.3,
                    head_height * ear_position * 0.2,
                    head_width * 0.1
                ])
                
                ears.append(ear)
                
        elif ear_params['type'] in ['hanging', 'long_hanging']:
            # Labrador/Beagle style hanging ears
            ear_length_mult = 0.6 if ear_params['type'] == 'hanging' else 0.8
            
            for side in [-1, 1]:
                ear = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
                
                ear_width = head_width * 0.12 * ear_size
                ear_length = head_height * ear_length_mult * ear_size
                ear_thickness = head_width * 0.03
                
                ear.vertices[:, 0] *= ear_width
                ear.vertices[:, 1] *= ear_length
                ear.vertices[:, 2] *= ear_thickness
                
                ear.apply_translation([
                    side * head_width * 0.32,
                    head_height * ear_position * 0.1,
                    head_width * 0.05
                ])
                
                # Slight forward hang
                ear.apply_transform(trimesh.transformations.rotation_matrix(
                    np.radians(15), [1, 0, 0]
                ))
                
                ears.append(ear)
        
        return ears

    def _create_perfect_body(self, body_params, base_scale):
        """Create perfectly proportioned body"""
        print("   Creating perfect body...")
        
        # Body dimensions
        length = base_scale * body_params['length']
        width = base_scale * body_params['width']
        height = base_scale * body_params['height']
        
        # Create base body
        body = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
        
        # Apply proportions
        vertices = body.vertices
        vertices[:, 0] *= width/2
        vertices[:, 1] *= height/2
        vertices[:, 2] *= length/2
        
        # Add chest depth and waist taper
        chest_depth = body_params['chest_depth']
        waist_taper = body_params['waist_taper']
        
        for i, vertex in enumerate(vertices):
            x, y, z = vertex
            
            # Front chest area (positive Z)
            if z > 0:
                chest_factor = z / (length/2)
                vertices[i][0] *= (1.0 + chest_factor * (chest_depth - 1.0))
                vertices[i][1] *= (1.0 + chest_factor * 0.1)
            
            # Waist taper (negative Z)
            else:
                waist_factor = abs(z) / (length/2)
                vertices[i][0] *= (1.0 - waist_factor * (1.0 - waist_taper))
        
        body.vertices = vertices
        return body

    def _create_sitting_legs(self, leg_params, pose_params, base_scale):
        """Create legs in perfect sitting position"""
        print("   Creating sitting legs...")
        
        front_length = base_scale * leg_params['front_length']
        back_length = base_scale * leg_params['back_length']
        thickness = base_scale * leg_params['thickness']
        
        legs = []
        
        # Front legs (straight down in sitting pose)
        for side in [-1, 1]:
            leg = trimesh.creation.cylinder(radius=thickness, height=front_length)
            
            # Position at front of body
            leg.apply_translation([
                side * base_scale * 0.2,
                -front_length/2,
                base_scale * 0.3
            ])
            
            legs.append(leg)
        
        # Back legs (folded in sitting pose)
        back_angle = np.radians(pose_params['back_angle'])
        
        for side in [-1, 1]:
            # Upper leg (thigh)
            upper_leg = trimesh.creation.cylinder(radius=thickness*1.2, height=back_length*0.6)
            
            # Rotate for sitting angle
            upper_leg.apply_transform(trimesh.transformations.rotation_matrix(
                back_angle, [1, 0, 0]
            ))
            
            upper_leg.apply_translation([
                side * base_scale * 0.15,
                -back_length*0.15,
                -base_scale * 0.15
            ])
            
            # Lower leg (shin, folded under)
            lower_leg = trimesh.creation.cylinder(radius=thickness, height=back_length*0.4)
            
            lower_leg.apply_transform(trimesh.transformations.rotation_matrix(
                -back_angle*1.5, [1, 0, 0]
            ))
            
            lower_leg.apply_translation([
                side * base_scale * 0.15,
                -back_length*0.25,
                -base_scale * 0.05
            ])
            
            legs.extend([upper_leg, lower_leg])
        
        return legs

    def _create_perfect_tail(self, tail_params, base_scale):
        """Create breed-characteristic tail"""
        print("   Creating perfect tail...")
        
        tail_length = base_scale * tail_params['length']
        tail_curve = tail_params['curve']
        tail_thickness = base_scale * tail_params['thickness']
        
        # Create curved tail with multiple segments
        segments = 6
        segment_length = tail_length / segments
        
        tail_parts = []
        current_pos = np.array([0, 0, -base_scale * 0.35])
        current_angle = np.pi/8  # Starting angle
        
        for i in range(segments):
            # Tapering thickness
            segment_thickness = tail_thickness * (1.0 - i * 0.15)
            segment = trimesh.creation.cylinder(radius=segment_thickness, height=segment_length)
            
            # Rotate and position
            rotation = trimesh.transformations.rotation_matrix(current_angle, [1, 0, 0])
            segment.apply_transform(rotation)
            segment.apply_translation(current_pos)
            
            tail_parts.append(segment)
            
            # Update for next segment
            direction = np.array([0, np.sin(current_angle), np.cos(current_angle)])
            current_pos += direction * segment_length
            current_angle += tail_curve * np.pi / segments
        
        # Combine tail segments
        tail = trimesh.util.concatenate(tail_parts) if tail_parts else trimesh.creation.box([1,1,1])
        return tail

    def _assemble_perfect_dog(self, head, ears, body, legs, tail, breed_params):
        """Assemble all parts into perfect dog"""
        print("   Assembling perfect dog...")
        
        # Position head on body
        body_bounds = body.bounds
        head_offset = [0, body_bounds[1][1] * 0.7, body_bounds[1][2] * 0.5]
        head.apply_translation(head_offset)
        
        # Position ears on head
        for ear in ears:
            ear.apply_translation(head_offset)
        
        # Combine all parts
        all_parts = [head, body, tail] + ears + legs
        combined = trimesh.util.concatenate(all_parts)
        
        # Ensure proper sitting position (base at Y=0)
        bounds = combined.bounds
        combined.apply_translation([0, -bounds[0][1], 0])
        
        return combined

    def _add_premium_planter_features(self, mesh, breed_params):
        """Add premium planter features"""
        print("   Adding premium planter features...")
        
        bounds = mesh.bounds
        height = bounds[1][1] - bounds[0][1]
        center_x = (bounds[1][0] + bounds[0][0]) / 2
        center_z = (bounds[1][2] + bounds[0][2]) / 2
        
        # Premium cavity parameters
        cavity_depth = height * 0.45  # Deep cavity
        cavity_radius = min(bounds[1][0] - bounds[0][0], bounds[1][2] - bounds[0][2]) * 0.3
        rim_height = 3.0  # Premium rim
        
        vertices = mesh.vertices.copy()
        top_y = bounds[1][1]
        
        for i, vertex in enumerate(vertices):
            x, y, z = vertex
            
            dist_from_center = np.sqrt((x - center_x)**2 + (z - center_z)**2)
            
            # Create luxury planting cavity
            if y > top_y - cavity_depth * 1.1:
                if dist_from_center < cavity_radius:
                    # Smooth cavity with premium finish
                    depth_factor = (y - (top_y - cavity_depth)) / cavity_depth
                    radial_factor = 1.0 - (dist_from_center / cavity_radius)
                    
                    # Luxury cavity profile
                    cavity_profile = 0.5 * (1 + np.cos(np.pi * radial_factor))
                    depression = cavity_depth * depth_factor * cavity_profile
                    
                    vertices[i][1] = y - depression
                    
                elif dist_from_center < cavity_radius + rim_height:
                    # Premium rim
                    rim_factor = 1.0 - ((dist_from_center - cavity_radius) / rim_height)
                    if y > top_y - rim_height and rim_factor > 0:
                        vertices[i][1] = min(y + rim_height * rim_factor, top_y + rim_height)
        
        mesh.vertices = vertices
        
        # Add drainage system
        self._add_drainage_system(mesh)
        
        return mesh

    def _add_drainage_system(self, mesh):
        """Add sophisticated drainage system"""
        bounds = mesh.bounds
        bottom_y = bounds[0][1]
        center_x = (bounds[1][0] + bounds[0][0]) / 2
        center_z = (bounds[1][2] + bounds[0][2]) / 2
        
        # Multiple small drainage holes
        hole_positions = [
            (center_x, center_z),
            (center_x + 12, center_z + 8),
            (center_x - 12, center_z + 8),
            (center_x + 8, center_z - 12),
            (center_x - 8, center_z - 12)
        ]
        
        vertices = mesh.vertices
        hole_radius = 2.5
        hole_depth = 4.0
        
        for hole_x, hole_z in hole_positions:
            for i, vertex in enumerate(vertices):
                x, y, z = vertex
                
                if y < bottom_y + hole_depth:
                    dist = np.sqrt((x - hole_x)**2 + (z - hole_z)**2)
                    
                    if dist < hole_radius:
                        hole_factor = 1.0 - (dist / hole_radius)
                        depression = hole_depth * hole_factor * 0.6
                        vertices[i][1] = max(y - depression, bottom_y - 1.0)

    def _perfection_finishing(self, mesh, breed_name):
        """Final perfection pass"""
        print("   Applying perfection finishing...")
        
        # Ensure watertightness
        if not mesh.is_watertight:
            mesh.fill_holes()
        
        # Premium smoothing
        mesh = self._premium_smoothing(mesh)
        
        # Perfect size for printing
        bounds = mesh.bounds
        current_size = bounds[1] - bounds[0]
        max_dim = max(current_size)
        
        if max_dim > 140:  # Perfect printing size
            scale = 140 / max_dim
            mesh.apply_scale(scale)
        
        return mesh

    def _premium_smoothing(self, mesh, iterations=3):
        """Premium quality smoothing"""
        original_volume = mesh.volume if mesh.is_watertight else 0
        
        for i in range(iterations):
            vertex_neighbors = mesh.vertex_neighbors
            new_vertices = mesh.vertices.copy()
            
            for v_idx, neighbors in enumerate(vertex_neighbors):
                if len(neighbors) > 0:
                    neighbor_avg = np.mean(mesh.vertices[neighbors], axis=0)
                    # Premium smoothing factor
                    new_vertices[v_idx] = mesh.vertices[v_idx] * 0.8 + neighbor_avg * 0.2
            
            mesh.vertices = new_vertices
            
            # Volume preservation
            if original_volume > 0 and mesh.is_watertight:
                new_volume = mesh.volume
                if new_volume > 0:
                    scale_factor = (original_volume / new_volume) ** (1/3)
                    if 0.95 <= scale_factor <= 1.05:
                        mesh.apply_scale(scale_factor)
        
        return mesh

    def _create_quality_report(self, mesh, breed_params, output_path):
        """Create comprehensive quality report"""
        report = {
            "breed": breed_params['name'],
            "generation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "file_path": output_path,
            "mesh_stats": {
                "vertices": len(mesh.vertices),
                "faces": len(mesh.faces),
                "volume_mm3": float(mesh.volume) if mesh.is_watertight else 0,
                "surface_area_mm2": float(mesh.area),
                "watertight": bool(mesh.is_watertight)
            },
            "dimensions_mm": {
                "width": float(mesh.bounds[1][0] - mesh.bounds[0][0]),
                "height": float(mesh.bounds[1][1] - mesh.bounds[0][1]),
                "depth": float(mesh.bounds[1][2] - mesh.bounds[0][2])
            },
            "quality_score": self._calculate_quality_score(mesh)
        }
        
        # Save report
        report_path = output_path.replace('.stl', '_quality_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Quality report saved: {report_path}")
        print(f"🏆 Quality score: {report['quality_score']}/100")

    def _calculate_quality_score(self, mesh):
        """Calculate overall quality score"""
        score = 100
        
        # Watertightness (critical)
        if not mesh.is_watertight:
            score -= 30
        
        # Vertex/face ratio (efficiency)
        if len(mesh.faces) > 0:
            vertex_face_ratio = len(mesh.vertices) / len(mesh.faces)
            if vertex_face_ratio > 1.0:  # Too many vertices
                score -= 10
        
        # Size check
        bounds = mesh.bounds
        max_dim = max(bounds[1] - bounds[0])
        if max_dim < 50 or max_dim > 200:  # Size issues
            score -= 15
        
        # Volume check
        if mesh.is_watertight and mesh.volume < 100000:  # Too small volume
            score -= 10
        
        return max(0, score)

def generate_breed_collection():
    """Generate a collection of different breed planters"""
    generator = UltimateDogPlanterGenerator()
    
    breeds_to_generate = ['golden_retriever', 'german_shepherd', 'pug', 'labrador', 'beagle']
    results = []
    
    print("🏆 Generating Ultimate Breed Collection")
    print("="*50)
    
    for breed in breeds_to_generate:
        try:
            result = generator.generate_ultimate_planter(breed, f"Ultimate{breed.title()}")
            results.append(result)
            print(f"✅ {breed} complete")
        except Exception as e:
            print(f"❌ {breed} failed: {e}")
    
    print(f"\n🎉 Collection complete: {len(results)} ultimate planters generated")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate ultimate breed-specific dog planters')
    parser.add_argument('--breed', type=str, default='golden_retriever', 
                       help='Breed to generate (golden_retriever, german_shepherd, pug, labrador, beagle)')
    parser.add_argument('--name', type=str, default=None, help='Pet name for the planter')
    parser.add_argument('--size', type=int, default=120, help='Base size in mm')
    parser.add_argument('--collection', action='store_true', help='Generate entire breed collection')
    
    args = parser.parse_args()
    
    if args.collection:
        generate_breed_collection()
    else:
        generator = UltimateDogPlanterGenerator()
        result = generator.generate_ultimate_planter(args.breed, args.name, args.size)
        print(f"\n🏆 Ultimate planter generation complete!")
        print(f"📁 Output: {result}")
