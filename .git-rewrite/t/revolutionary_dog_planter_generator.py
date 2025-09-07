#!/usr/bin/env python3
"""
Revolutionary Dog-Like Planter Generator
Uses real dog anatomy and pose reference to create truly dog-like planters
"""
import cv2
import numpy as np
import trimesh
from pathlib import Path
import json
import time
from scipy.spatial.distance import cdist
from scipy.interpolate import splprep, splev

class RevolutionaryDogPlanterGenerator:
    def __init__(self):
        # Real dog anatomy key points and proportions
        self.dog_anatomy_keypoints = {
            'golden_retriever': {
                'head_profile': {
                    'skull_curve': [(0, 0.9), (0.2, 1.0), (0.4, 0.95), (0.6, 0.8)],
                    'muzzle_line': [(0.6, 0.8), (0.8, 0.6), (1.0, 0.4)],
                    'lower_jaw': [(1.0, 0.4), (0.8, 0.3), (0.6, 0.35), (0.4, 0.4)]
                },
                'body_profile': {
                    'back_line': [(0, 0.8), (0.3, 0.85), (0.7, 0.8), (1.0, 0.75)],
                    'chest_line': [(0, 0.6), (0.2, 0.5), (0.4, 0.45)],
                    'belly_line': [(0.4, 0.45), (0.7, 0.4), (1.0, 0.45)]
                },
                'sitting_pose': {
                    'front_legs': [
                        [(0.25, 0.45), (0.25, 0.2), (0.25, 0)],  # Left front
                        [(0.35, 0.45), (0.35, 0.2), (0.35, 0)]   # Right front
                    ],
                    'back_legs': [
                        [(0.65, 0.6), (0.6, 0.3), (0.7, 0.1)],   # Left back (folded)
                        [(0.75, 0.6), (0.7, 0.3), (0.8, 0.1)]    # Right back (folded)
                    ]
                },
                'ears': {
                    'type': 'floppy',
                    'attachment_points': [(0.15, 0.9), (0.25, 0.9)],
                    'ear_curves': [
                        [(0.15, 0.9), (0.1, 0.7), (0.12, 0.5), (0.18, 0.6)],
                        [(0.25, 0.9), (0.3, 0.7), (0.28, 0.5), (0.22, 0.6)]
                    ]
                },
                'tail': {
                    'attachment': (0.95, 0.7),
                    'curve': [(0.95, 0.7), (1.1, 0.8), (1.2, 0.9), (1.15, 1.0)]
                }
            }
        }
        
        print("🔥 Revolutionary Dog-Like Planter Generator initialized")

    def generate_dog_like_planter(self, breed='golden_retriever', pet_name=None, size_mm=120):
        """
        Generate a truly dog-like planter using anatomical references
        """
        print(f"\n🐕 Generating dog-like {breed} planter")
        
        # Get anatomical keypoints
        anatomy = self.dog_anatomy_keypoints.get(breed, self.dog_anatomy_keypoints['golden_retriever'])
        
        # Create dog-like mesh using anatomical references
        dog_mesh = self._create_anatomical_dog_mesh(anatomy, size_mm)
        
        # Add realistic dog features
        dog_mesh = self._add_realistic_dog_features(dog_mesh, anatomy)
        
        # Convert to functional planter while preserving dog-like appearance
        planter_mesh = self._convert_to_dog_planter(dog_mesh, anatomy)
        
        # Final dog-like refinement
        final_mesh = self._dog_like_refinement(planter_mesh, breed)
        
        # Save result
        timestamp = int(time.time())
        output_path = f"generated_models/doglike_{breed}_{pet_name or 'planter'}_{timestamp}.stl"
        final_mesh.export(output_path)
        
        print(f"🐕 Dog-like {breed} planter complete: {output_path}")
        return output_path

    def _create_anatomical_dog_mesh(self, anatomy, size_mm):
        """
        Create mesh from anatomical keypoints using spline interpolation
        """
        print("   Creating anatomical dog mesh from keypoints...")
        
        # Extract profile curves
        head_profile = self._create_smooth_curve_from_keypoints(anatomy['head_profile'])
        body_profile = self._create_smooth_curve_from_keypoints(anatomy['body_profile'])
        
        # Create 3D mesh by revolving and extruding profiles
        head_mesh = self._profile_to_3d_head(head_profile, size_mm)
        body_mesh = self._profile_to_3d_body(body_profile, size_mm)
        
        # Add legs using anatomical positioning
        leg_meshes = self._create_anatomical_legs(anatomy['sitting_pose'], size_mm)
        
        # Add realistic ears
        ear_meshes = self._create_realistic_ears(anatomy['ears'], size_mm)
        
        # Add tail
        tail_mesh = self._create_curved_tail(anatomy['tail'], size_mm)
        
        # Combine all parts
        all_parts = [head_mesh, body_mesh, tail_mesh] + leg_meshes + ear_meshes
        combined_mesh = trimesh.util.concatenate([mesh for mesh in all_parts if mesh is not None])
        
        return combined_mesh

    def _create_smooth_curve_from_keypoints(self, profile_dict):
        """
        Create smooth curves from anatomical keypoints
        """
        curves = {}
        
        for curve_name, points in profile_dict.items():
            if len(points) >= 3:
                # Convert to numpy array
                points_array = np.array(points)
                
                # Create smooth spline
                try:
                    tck, u = splprep([points_array[:, 0], points_array[:, 1]], s=0.1, k=3)
                    u_new = np.linspace(0, 1, 50)
                    smooth_curve = splev(u_new, tck)
                    curves[curve_name] = np.column_stack(smooth_curve)
                except:
                    # Fallback to original points
                    curves[curve_name] = points_array
            else:
                curves[curve_name] = np.array(points)
        
        return curves

    def _profile_to_3d_head(self, head_profile, size_mm):
        """
        Convert 2D head profile to 3D dog head
        """
        print("     Creating 3D dog head from profile...")
        
        # Combine skull and muzzle curves
        skull_points = head_profile.get('skull_curve', np.array([[0, 0.8]]))
        muzzle_points = head_profile.get('muzzle_line', np.array([[0.8, 0.6]]))
        jaw_points = head_profile.get('lower_jaw', np.array([[0.8, 0.4]]))
        
        # Create complete head outline
        if len(skull_points) > 0 and len(muzzle_points) > 0:
            head_outline = np.vstack([skull_points, muzzle_points])
            if len(jaw_points) > 0:
                # Add lower jaw (reversed to close the shape)
                head_outline = np.vstack([head_outline, jaw_points[::-1]])
        else:
            # Fallback head shape
            head_outline = np.array([
                [0, 0.9], [0.3, 1.0], [0.6, 0.8], [1.0, 0.4],
                [0.8, 0.3], [0.4, 0.35], [0, 0.5]
            ])
        
        # Scale to actual size
        head_outline[:, 0] *= size_mm * 0.6  # Width
        head_outline[:, 1] *= size_mm * 0.5  # Height
        
        # Create 3D head by revolution and extrusion
        head_mesh = self._revolve_profile_to_head(head_outline, size_mm)
        
        return head_mesh

    def _revolve_profile_to_head(self, profile, size_mm):
        """
        Create 3D head by revolving 2D profile
        """
        # Create vertices by revolving profile
        angles = np.linspace(0, 2*np.pi, 16)  # 16 segments around
        vertices = []
        faces = []
        
        for i, (x, y) in enumerate(profile):
            for j, angle in enumerate(angles):
                # Convert to cylindrical coordinates, then to cartesian
                radius = x * 0.7  # Head width factor
                z = x
                x_3d = radius * np.cos(angle)
                y_3d = y
                z_3d = radius * np.sin(angle)
                
                vertices.append([x_3d, y_3d, z_3d])
        
        vertices = np.array(vertices)
        
        # Create faces (simplified triangulation)
        n_profile = len(profile)
        n_angles = len(angles)
        
        for i in range(n_profile - 1):
            for j in range(n_angles):
                # Current quad vertices
                v1 = i * n_angles + j
                v2 = i * n_angles + (j + 1) % n_angles
                v3 = (i + 1) * n_angles + (j + 1) % n_angles
                v4 = (i + 1) * n_angles + j
                
                # Two triangles per quad
                faces.append([v1, v2, v3])
                faces.append([v1, v3, v4])
        
        if len(vertices) > 0 and len(faces) > 0:
            return trimesh.Trimesh(vertices=vertices, faces=faces)
        else:
            # Fallback: simple ellipsoid
            return trimesh.creation.icosphere(subdivisions=2, radius=size_mm*0.3)

    def _profile_to_3d_body(self, body_profile, size_mm):
        """
        Convert 2D body profile to 3D dog body
        """
        print("     Creating 3D dog body from profile...")
        
        # Get body curves
        back_line = body_profile.get('back_line', np.array([[0, 0.8], [1, 0.7]]))
        chest_line = body_profile.get('chest_line', np.array([[0, 0.6], [0.4, 0.4]]))
        belly_line = body_profile.get('belly_line', np.array([[0.4, 0.4], [1, 0.4]]))
        
        # Create body outline
        if len(chest_line) > 0 and len(belly_line) > 0:
            body_outline = np.vstack([back_line, belly_line[::-1]])
        else:
            # Fallback body shape
            body_outline = np.array([
                [0, 0.8], [0.5, 0.85], [1.0, 0.75],
                [1.0, 0.4], [0.5, 0.35], [0, 0.5]
            ])
        
        # Scale to size
        body_outline[:, 0] *= size_mm * 1.2  # Length
        body_outline[:, 1] *= size_mm * 0.6  # Height
        
        # Create 3D body by extrusion with varying width
        body_mesh = self._extrude_body_profile(body_outline, size_mm)
        
        return body_mesh

    def _extrude_body_profile(self, profile, size_mm):
        """
        Extrude body profile with dog-like width variation
        """
        # Create 3D body by extruding profile with width variation
        width_profile = size_mm * 0.5  # Base width
        
        vertices = []
        faces = []
        
        # Create vertices along width (Z direction)
        z_positions = np.linspace(-width_profile/2, width_profile/2, 8)
        
        for z in z_positions:
            # Width varies along body length (narrower at ends)
            for x, y in profile:
                length_factor = abs(x) / (size_mm * 1.2) if size_mm > 0 else 0
                width_scale = 1.0 - 0.3 * length_factor  # Taper towards ends
                scaled_z = z * width_scale
                vertices.append([x, y, scaled_z])
        
        vertices = np.array(vertices)
        
        # Create faces (simplified)
        n_profile = len(profile)
        n_z = len(z_positions)
        
        for i in range(n_z - 1):
            for j in range(n_profile):
                v1 = i * n_profile + j
                v2 = i * n_profile + (j + 1) % n_profile
                v3 = (i + 1) * n_profile + (j + 1) % n_profile
                v4 = (i + 1) * n_profile + j
                
                faces.append([v1, v2, v3])
                faces.append([v1, v3, v4])
        
        if len(vertices) > 0 and len(faces) > 0:
            return trimesh.Trimesh(vertices=vertices, faces=faces)
        else:
            # Fallback: elongated ellipsoid
            body = trimesh.creation.icosphere(subdivisions=2, radius=size_mm*0.4)
            body.vertices[:, 0] *= 1.5  # Elongate
            return body

    def _create_anatomical_legs(self, sitting_pose, size_mm):
        """
        Create anatomically correct sitting dog legs
        """
        print("     Creating anatomical sitting legs...")
        
        legs = []
        leg_radius = size_mm * 0.06
        
        # Front legs (straight down)
        for leg_points in sitting_pose.get('front_legs', []):
            if len(leg_points) >= 2:
                leg_path = np.array(leg_points) * size_mm
                leg_mesh = self._create_leg_from_path(leg_path, leg_radius)
                if leg_mesh:
                    legs.append(leg_mesh)
        
        # Back legs (folded sitting position)
        for leg_points in sitting_pose.get('back_legs', []):
            if len(leg_points) >= 2:
                leg_path = np.array(leg_points) * size_mm
                leg_mesh = self._create_leg_from_path(leg_path, leg_radius * 1.2)
                if leg_mesh:
                    legs.append(leg_mesh)
        
        return legs

    def _create_leg_from_path(self, path_points, radius):
        """
        Create leg mesh following a 3D path
        """
        if len(path_points) < 2:
            return None
        
        # Convert 2D path to 3D
        path_3d = np.zeros((len(path_points), 3))
        path_3d[:, :2] = path_points
        
        # Create cylinder segments along path
        segments = []
        for i in range(len(path_3d) - 1):
            start = path_3d[i]
            end = path_3d[i + 1]
            
            # Create cylinder segment
            direction = end - start
            length = np.linalg.norm(direction)
            
            if length > 0:
                segment = trimesh.creation.cylinder(radius=radius, height=length)
                
                # Orient cylinder along path
                if not np.allclose(direction, [0, 0, length]):
                    # Calculate rotation to align with direction
                    z_axis = np.array([0, 0, 1])
                    direction_norm = direction / length
                    
                    if not np.allclose(direction_norm, z_axis):
                        rotation_axis = np.cross(z_axis, direction_norm)
                        if np.linalg.norm(rotation_axis) > 1e-6:
                            rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
                            angle = np.arccos(np.clip(np.dot(z_axis, direction_norm), -1, 1))
                            rotation_matrix = trimesh.transformations.rotation_matrix(angle, rotation_axis)
                            segment.apply_transform(rotation_matrix)
                
                # Position segment
                center = (start + end) / 2
                segment.apply_translation(center)
                segments.append(segment)
        
        if segments:
            return trimesh.util.concatenate(segments)
        return None

    def _create_realistic_ears(self, ear_config, size_mm):
        """
        Create realistic dog ears
        """
        print("     Creating realistic ears...")
        
        ears = []
        ear_type = ear_config.get('type', 'floppy')
        
        if ear_type == 'floppy':
            # Create floppy Golden Retriever ears
            for ear_curve in ear_config.get('ear_curves', []):
                if len(ear_curve) >= 3:
                    ear_points = np.array(ear_curve) * size_mm
                    ear_mesh = self._create_floppy_ear(ear_points, size_mm)
                    if ear_mesh:
                        ears.append(ear_mesh)
        
        return ears

    def _create_floppy_ear(self, ear_curve, size_mm):
        """
        Create a floppy ear from curve points
        """
        if len(ear_curve) < 3:
            return None
        
        # Create ear surface by extruding curve
        ear_thickness = size_mm * 0.02
        
        vertices = []
        faces = []
        
        # Create two sides of the ear
        for side in [-1, 1]:
            for point in ear_curve:
                x, y = point
                z = side * ear_thickness / 2
                vertices.append([x, y, z])
        
        vertices = np.array(vertices)
        
        # Create faces connecting the two sides
        n_points = len(ear_curve)
        for i in range(n_points - 1):
            # Connect corresponding points on both sides
            v1 = i  # Left side
            v2 = i + 1
            v3 = i + n_points  # Right side
            v4 = i + 1 + n_points
            
            # Two triangles per quad
            faces.append([v1, v2, v3])
            faces.append([v2, v4, v3])
        
        if len(vertices) > 0 and len(faces) > 0:
            return trimesh.Trimesh(vertices=vertices, faces=faces)
        return None

    def _create_curved_tail(self, tail_config, size_mm):
        """
        Create curved dog tail
        """
        print("     Creating curved tail...")
        
        tail_curve = tail_config.get('curve', [(0.95, 0.7), (1.2, 0.9)])
        if len(tail_curve) < 2:
            return None
        
        # Convert to 3D path
        tail_path = np.array(tail_curve) * size_mm
        tail_radius = size_mm * 0.04
        
        # Create tail as tapered tube
        tail_mesh = self._create_leg_from_path(tail_path, tail_radius)
        
        return tail_mesh

    def _add_realistic_dog_features(self, mesh, anatomy):
        """
        Add realistic dog features like facial details
        """
        print("   Adding realistic dog features...")
        
        # For now, return the mesh as-is
        # Future: Add nose, eyes, facial features
        return mesh

    def _convert_to_dog_planter(self, dog_mesh, anatomy):
        """
        Convert dog mesh to functional planter while preserving dog-like appearance
        """
        print("   Converting to functional planter...")
        
        if dog_mesh is None:
            return trimesh.creation.box([100, 100, 100])
        
        # Ensure base is flat and stable
        bounds = dog_mesh.bounds
        base_y = bounds[0][1]
        
        # Flatten base
        vertices = dog_mesh.vertices
        for i, vertex in enumerate(vertices):
            if vertex[1] < base_y + 2:  # Bottom 2mm
                vertices[i][1] = base_y
        
        # Add planting cavity while preserving dog shape
        top_y = bounds[1][1]
        height = top_y - base_y
        cavity_depth = height * 0.3
        
        center_x = (bounds[1][0] + bounds[0][0]) / 2
        center_z = (bounds[1][2] + bounds[0][2]) / 2
        cavity_radius = min(bounds[1][0] - bounds[0][0], bounds[1][2] - bounds[0][2]) * 0.25
        
        # Create cavity
        for i, vertex in enumerate(vertices):
            x, y, z = vertex
            
            if y > top_y - cavity_depth:
                dist_from_center = np.sqrt((x - center_x)**2 + (z - center_z)**2)
                
                if dist_from_center < cavity_radius:
                    depth_factor = (y - (top_y - cavity_depth)) / cavity_depth
                    radial_factor = 1.0 - (dist_from_center / cavity_radius)
                    
                    cavity_profile = 0.5 * (1 + np.cos(np.pi * radial_factor))
                    depression = cavity_depth * depth_factor * cavity_profile * 0.7
                    
                    vertices[i][1] = y - depression
        
        dog_mesh.vertices = vertices
        
        # Ensure watertightness
        if not dog_mesh.is_watertight:
            dog_mesh.fill_holes()
        
        return dog_mesh

    def _dog_like_refinement(self, mesh, breed):
        """
        Final refinement to enhance dog-like appearance
        """
        print("   Final dog-like refinement...")
        
        # Smoothing that preserves features
        mesh = self._feature_preserving_smooth(mesh)
        
        # Size optimization
        bounds = mesh.bounds
        current_size = bounds[1] - bounds[0]
        max_dim = max(current_size)
        
        if max_dim > 140:
            scale = 140 / max_dim
            mesh.apply_scale(scale)
        
        return mesh

    def _feature_preserving_smooth(self, mesh, iterations=2):
        """
        Smooth mesh while preserving dog-like features
        """
        original_volume = mesh.volume if mesh.is_watertight else 0
        
        for i in range(iterations):
            vertex_neighbors = mesh.vertex_neighbors
            new_vertices = mesh.vertices.copy()
            
            for v_idx, neighbors in enumerate(vertex_neighbors):
                if len(neighbors) > 0:
                    neighbor_avg = np.mean(mesh.vertices[neighbors], axis=0)
                    # Light smoothing to preserve features
                    new_vertices[v_idx] = mesh.vertices[v_idx] * 0.85 + neighbor_avg * 0.15
            
            mesh.vertices = new_vertices
            
            # Volume preservation
            if original_volume > 0 and mesh.is_watertight:
                new_volume = mesh.volume
                if new_volume > 0:
                    scale_factor = (original_volume / new_volume) ** (1/3)
                    if 0.95 <= scale_factor <= 1.05:
                        mesh.apply_scale(scale_factor)
        
        return mesh

def test_dog_like_generation():
    """
    Test the revolutionary dog-like planter generation
    """
    generator = RevolutionaryDogPlanterGenerator()
    
    print("🔥 Testing revolutionary dog-like planter generation...")
    
    result = generator.generate_dog_like_planter('golden_retriever', 'DogLikeTest', 120)
    
    if result:
        print(f"🐕 Dog-like planter generation complete: {result}")
        
        # Quick analysis
        mesh = trimesh.load_mesh(result)
        print(f"📊 Analysis:")
        print(f"   Vertices: {len(mesh.vertices):,}")
        print(f"   Faces: {len(mesh.faces):,}")
        print(f"   Watertight: {'✅' if mesh.is_watertight else '❌'}")
        print(f"   Volume: {mesh.volume:.0f} mm³")
        
        return result
    else:
        print("❌ Dog-like generation failed")
        return None

if __name__ == "__main__":
    test_dog_like_generation()
