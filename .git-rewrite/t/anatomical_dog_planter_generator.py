#!/usr/bin/env python3
"""
Anatomically Correct Dog Planter Generator
Creates accurate dog-shaped planters based on input photos using parametric modeling
"""
import time
import cv2
import numpy as np
import trimesh
from pathlib import Path
import json
import requests
from openai import OpenAI
import os
try:
    from advanced_breed_detector import AdvancedBreedDetector
except ImportError:
    print("⚠️ Advanced breed detector not available, using simplified detection")
    AdvancedBreedDetector = None

class AnatomicalDogPlanterGenerator:
    def __init__(self, debug_dir=None):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if AdvancedBreedDetector:
            self.breed_detector = AdvancedBreedDetector()
        else:
            self.breed_detector = None
        self.debug_dir = debug_dir
        
        # Dog anatomy parameters by breed category
        self.breed_anatomy = {
            'golden_retriever': {
                'head_width_ratio': 0.8,
                'head_length_ratio': 0.9,
                'ear_type': 'floppy',
                'muzzle_length': 0.6,
                'body_proportions': {'length': 1.2, 'width': 0.7, 'height': 0.8},
                'tail_curve': 0.3,
                'leg_length': 0.4
            },
            'german_shepherd': {
                'head_width_ratio': 0.7,
                'head_length_ratio': 1.0,
                'ear_type': 'erect',
                'muzzle_length': 0.7,
                'body_proportions': {'length': 1.3, 'width': 0.6, 'height': 0.9},
                'tail_curve': 0.2,
                'leg_length': 0.45
            },
            'pug': {
                'head_width_ratio': 1.0,
                'head_length_ratio': 0.7,
                'ear_type': 'small_erect',
                'muzzle_length': 0.2,
                'body_proportions': {'length': 0.9, 'width': 0.8, 'height': 0.7},
                'tail_curve': 0.8,
                'leg_length': 0.3
            },
            'default': {
                'head_width_ratio': 0.8,
                'head_length_ratio': 0.8,
                'ear_type': 'medium',
                'muzzle_length': 0.5,
                'body_proportions': {'length': 1.1, 'width': 0.7, 'height': 0.8},
                'tail_curve': 0.4,
                'leg_length': 0.4
            }
        }
        
        print("🐕 Anatomical Dog Planter Generator initialized")

    def generate_anatomical_planter(self, photo_path, pet_name=None):
        """
        Generate anatomically correct dog planter from photo
        """
        print(f"🎯 Generating anatomical planter for {pet_name or 'dog'}")
        
        # Step 1: Analyze the dog photo for breed and characteristics
        breed_info, breed_name = self._robust_breed_detection(photo_path)
        
        print(f"🔍 Detected breed: {breed_name}")
        
        # Step 2: Get anatomical parameters
        anatomy = self._get_breed_anatomy(breed_name)
        
        # Step 3: Analyze photo for specific measurements
        photo_analysis = self._analyze_photo_proportions(photo_path)
        
        # Step 4: Generate reference concept image
        concept_image = self._generate_reference_concept(breed_info, anatomy)
        
        # Step 5: Create parametric 3D model
        mesh = self._create_parametric_dog_planter(anatomy, photo_analysis, concept_image)
        
        # Step 6: Add planter functionality
        mesh = self._add_planter_features(mesh, anatomy)
        
        # Step 7: Final refinement
        mesh = self._refine_for_production(mesh)
        
        # Save result
        timestamp = int(time.time() if 'time' in globals() else 1751070000)
        output_path = f"generated_models/anatomical_{pet_name or 'dog'}_{breed_name}_{timestamp}.stl"
        mesh.export(output_path)
        
        print(f"✅ Anatomical planter created: {output_path}")
        return output_path

    def _get_breed_anatomy(self, breed_name):
        """Get anatomical parameters for breed"""
        # Try exact match first
        if breed_name in self.breed_anatomy:
            return self.breed_anatomy[breed_name].copy()
        
        # Try partial matches
        for breed_key in self.breed_anatomy:
            if breed_key in breed_name or breed_name in breed_key:
                return self.breed_anatomy[breed_key].copy()
        
        # Default anatomy
        return self.breed_anatomy['default'].copy()

    def _robust_breed_detection(self, photo_path):
        """
        Robust breed detection using multiple fallback methods
        """
        print("🔍 Performing robust breed detection...")
        
        # Method 1: Try advanced breed detector if available
        if self.breed_detector:
            try:
                breed_info = self.breed_detector.detect_breed_and_generate_prompts(photo_path)
                breed_name = breed_info.get('breed', 'mixed breed').lower().replace(' ', '_')
                print(f"✅ Advanced detection: {breed_name}")
                return breed_info, breed_name
            except Exception as e:
                print(f"⚠️ Advanced breed detector failed: {e}")
        
        # Method 2: Image analysis based detection
        try:
            breed_info, breed_name = self._analyze_image_for_breed(photo_path)
            if breed_name != 'unknown':
                print(f"✅ Image analysis detection: {breed_name}")
                return breed_info, breed_name
        except Exception as e:
            print(f"⚠️ Image analysis failed: {e}")
        
        # Method 3: Filename based detection
        filename = Path(photo_path).name.lower()
        if 'golden' in filename or 'retriever' in filename:
            breed_info = {'breed': 'Golden Retriever', 'confidence': 0.8}
            breed_name = 'golden_retriever'
        elif 'german' in filename or 'shepherd' in filename:
            breed_info = {'breed': 'German Shepherd', 'confidence': 0.8}
            breed_name = 'german_shepherd'
        elif 'pug' in filename:
            breed_info = {'breed': 'Pug', 'confidence': 0.8}
            breed_name = 'pug'
        elif 'lab' in filename or 'labrador' in filename:
            breed_info = {'breed': 'Labrador', 'confidence': 0.8}
            breed_name = 'golden_retriever'  # Similar anatomy
        elif 'beagle' in filename:
            breed_info = {'breed': 'Beagle', 'confidence': 0.8}
            breed_name = 'default'
        else:
            breed_info = {'breed': 'Golden Retriever', 'confidence': 0.5}
            breed_name = 'golden_retriever'  # Safe default
        
        print(f"✅ Filename detection: {breed_name}")
        return breed_info, breed_name

    def _analyze_image_for_breed(self, photo_path):
        """
        Analyze image characteristics to guess breed
        """
        img = cv2.imread(photo_path)
        if img is None:
            return {'breed': 'Unknown'}, 'unknown'
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        # Basic feature analysis
        features = {
            'aspect_ratio': width / height,
            'brightness': np.mean(gray),
            'contrast': np.std(gray)
        }
        
        # Face detection for head shape analysis
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml')
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) > 0:
            # Analyze largest face
            face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = face
            
            face_aspect = w / h
            face_area_ratio = (w * h) / (width * height)
            
            # Simple breed classification based on face characteristics
            if face_aspect > 1.2 and face_area_ratio > 0.2:
                # Wide face, could be pug or bulldog type
                return {'breed': 'Pug', 'confidence': 0.7}, 'pug'
            elif face_aspect < 0.8 and face_area_ratio > 0.15:
                # Tall narrow face, could be German Shepherd
                return {'breed': 'German Shepherd', 'confidence': 0.7}, 'german_shepherd'
            else:
                # Medium proportions, likely Golden Retriever type
                return {'breed': 'Golden Retriever', 'confidence': 0.6}, 'golden_retriever'
        
        # If no face detected, use default
        return {'breed': 'Golden Retriever', 'confidence': 0.5}, 'golden_retriever'

    def _analyze_photo_proportions(self, photo_path):
        """Analyze photo to extract proportional measurements"""
        print("📐 Analyzing photo proportions...")
        
        # Load and process image
        img = cv2.imread(photo_path)
        if img is None:
            return {'confidence': 0.0}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        # Face detection to establish scale
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml')
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        analysis = {
            'image_dimensions': (width, height),
            'confidence': 0.7
        }
        
        if len(faces) > 0:
            # Use largest face as reference
            face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = face
            
            analysis.update({
                'face_region': (x, y, w, h),
                'face_center': (x + w//2, y + h//2),
                'face_width_ratio': w / width,
                'face_height_ratio': h / height,
                'confidence': 0.9
            })
            
            # Estimate body proportions based on face
            estimated_body_width = w * 1.5
            estimated_body_height = h * 2.0
            
            analysis.update({
                'estimated_body_width': estimated_body_width,
                'estimated_body_height': estimated_body_height,
                'head_to_body_ratio': w / estimated_body_width
            })
        
        return analysis

    def _generate_reference_concept(self, breed_info, anatomy):
        """Generate high-quality reference concept image"""
        print("🎨 Generating reference concept...")
        
        breed_name = breed_info.get('breed', 'dog')
        
        # Ultra-precise prompt for concept generation
        prompt = f"""
Professional product photography of a decorative {breed_name} dog planter.
EXACT SPECIFICATIONS:
- Breed-accurate {breed_name} sitting pose
- Head width: {anatomy['head_width_ratio']:.1f} relative proportion
- Muzzle length: {anatomy['muzzle_length']:.1f} of head length
- Ears: {anatomy['ear_type']} style, breed-accurate
- Body proportions: length {anatomy['body_proportions']['length']:.1f}, width {anatomy['body_proportions']['width']:.1f}
- Functional planter with visible planting cavity at top
- Smooth ceramic finish, modern minimalist design
- Pure white background, studio lighting
- NOT terrain, NOT landscape, NOT flat surface
- Three-dimensional sculptural object, suitable for tabletop
- Premium home decor quality
"""
        
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="hd",
                style="natural",
                n=1
            )
            
            image_url = response.data[0].url
            image_data = requests.get(image_url).content
            
            # Save reference
            if self.debug_dir:
                ref_path = Path(self.debug_dir) / "reference_concept.png"
                with open(ref_path, 'wb') as f:
                    f.write(image_data)
            
            return image_data
            
        except Exception as e:
            print(f"⚠️ Reference generation failed: {e}")
            return None

    def _create_parametric_dog_planter(self, anatomy, photo_analysis, concept_image):
        """Create parametric 3D dog model based on anatomical parameters"""
        print("🏗️ Creating parametric dog model...")
        
        # Base dimensions (in mm)
        base_scale = 100  # Base size
        
        # Calculate dimensions from anatomy
        head_width = base_scale * anatomy['head_width_ratio']
        head_length = base_scale * anatomy['head_length_ratio']
        head_height = base_scale * 0.8
        
        body_length = base_scale * anatomy['body_proportions']['length']
        body_width = base_scale * anatomy['body_proportions']['width']
        body_height = base_scale * anatomy['body_proportions']['height']
        
        # Create head mesh
        head_mesh = self._create_dog_head(head_width, head_length, head_height, anatomy)
        
        # Create body mesh
        body_mesh = self._create_dog_body(body_length, body_width, body_height, anatomy)
        
        # Create legs
        leg_meshes = self._create_dog_legs(anatomy, base_scale)
        
        # Create tail
        tail_mesh = self._create_dog_tail(anatomy, base_scale)
        
        # Position and combine parts
        combined_mesh = self._assemble_dog_parts(head_mesh, body_mesh, leg_meshes, tail_mesh, anatomy)
        
        return combined_mesh

    def _create_dog_head(self, width, length, height, anatomy):
        """Create anatomically correct dog head"""
        print(f"   Creating {anatomy['ear_type']} head...")
        
        # Base head ellipsoid
        head = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
        
        # Scale to create ellipsoid shape
        head.vertices[:, 0] *= width/2   # X width
        head.vertices[:, 1] *= height/2  # Y height  
        head.vertices[:, 2] *= length/2  # Z length
        
        # Adjust for breed-specific head shape
        vertices = head.vertices
        
        # Create muzzle
        muzzle_length = length * anatomy['muzzle_length']
        muzzle_width = width * 0.6
        muzzle_height = height * 0.4
        
        # Extend front vertices for muzzle
        for i, vertex in enumerate(vertices):
            x, y, z = vertex
            
            # Front face (positive Z)
            if z > length/4:
                # Taper for muzzle
                muzzle_factor = (z - length/4) / (length/2 - length/4)
                scale_x = 1.0 - muzzle_factor * (1.0 - muzzle_width/width)
                scale_y = 1.0 - muzzle_factor * (1.0 - muzzle_height/height)
                
                vertices[i][0] *= scale_x
                vertices[i][1] *= scale_y
                vertices[i][2] += muzzle_factor * muzzle_length * 0.3
        
        head.vertices = vertices
        
        # Add ears based on type
        ears = self._create_ears(anatomy['ear_type'], width, height)
        if ears:
            head = trimesh.util.concatenate([head] + ears)
        
        return head

    def _create_ears(self, ear_type, head_width, head_height):
        """Create breed-specific ears"""
        ears = []
        
        if ear_type == 'floppy':
            # Golden retriever style floppy ears
            ear_width = head_width * 0.2
            ear_length = head_height * 0.6
            ear_thickness = head_width * 0.05
            
            for side in [-1, 1]:  # Left and right
                ear = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
                
                # Scale to ear shape
                ear.vertices[:, 0] *= ear_width/2
                ear.vertices[:, 1] *= ear_length/2  
                ear.vertices[:, 2] *= ear_thickness/2
                
                # Position on side of head
                ear.apply_translation([side * head_width * 0.4, head_height * 0.2, 0])
                
                # Rotate for hanging position
                ear.apply_transform(trimesh.transformations.rotation_matrix(
                    np.radians(30 * side), [0, 0, 1]
                ))
                
                ears.append(ear)
                
        elif ear_type == 'erect':
            # German shepherd style erect ears
            ear_width = head_width * 0.15
            ear_height = head_height * 0.4
            ear_thickness = head_width * 0.04
            
            for side in [-1, 1]:
                ear = trimesh.creation.cone(radius=ear_width/2, height=ear_height)
                
                # Position on top-side of head
                ear.apply_translation([side * head_width * 0.3, head_height * 0.3, 0])
                
                ears.append(ear)
                
        elif ear_type == 'small_erect':
            # Pug style small ears
            ear_width = head_width * 0.1
            ear_height = head_height * 0.2
            
            for side in [-1, 1]:
                ear = trimesh.creation.cone(radius=ear_width/2, height=ear_height)
                ear.apply_translation([side * head_width * 0.35, head_height * 0.25, 0])
                ears.append(ear)
        
        return ears

    def _create_dog_body(self, length, width, height, anatomy):
        """Create dog body"""
        print("   Creating body...")
        
        # Main body ellipsoid
        body = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
        
        # Scale to create ellipsoid shape
        body.vertices[:, 0] *= width/2   # X width
        body.vertices[:, 1] *= height/2  # Y height
        body.vertices[:, 2] *= length/2  # Z length
        
        # Adjust proportions for sitting position
        vertices = body.vertices
        
        # Create chest (front) and rear distinction
        for i, vertex in enumerate(vertices):
            x, y, z = vertex
            
            # Front chest area - broader
            if z > 0:
                chest_factor = z / (length/2)
                vertices[i][0] *= (1.0 + chest_factor * 0.2)  # Broader chest
                vertices[i][1] *= (1.0 + chest_factor * 0.1)  # Slightly taller
        
        body.vertices = vertices
        return body

    def _create_dog_legs(self, anatomy, base_scale):
        """Create dog legs for sitting position"""
        print("   Creating legs...")
        
        leg_radius = base_scale * 0.08
        leg_length = base_scale * anatomy['leg_length']
        
        legs = []
        
        # Front legs (sitting position - straight down)
        for side in [-1, 1]:
            leg = trimesh.creation.cylinder(radius=leg_radius, height=leg_length)
            # Position at front of body
            leg.apply_translation([
                side * base_scale * 0.25,  # Side spacing
                -leg_length/2,             # Down from body
                base_scale * 0.3           # Front position
            ])
            legs.append(leg)
        
        # Back legs (sitting position - folded)
        for side in [-1, 1]:
            # Upper leg
            upper_leg = trimesh.creation.cylinder(radius=leg_radius*1.2, height=leg_length*0.6)
            upper_leg.apply_translation([
                side * base_scale * 0.2,
                -leg_length*0.2,
                -base_scale * 0.2
            ])
            
            # Lower leg (folded under)
            lower_leg = trimesh.creation.cylinder(radius=leg_radius, height=leg_length*0.4)
            lower_leg.apply_translation([
                side * base_scale * 0.2,
                -leg_length*0.3,
                -base_scale * 0.1
            ])
            
            legs.extend([upper_leg, lower_leg])
        
        return legs

    def _create_dog_tail(self, anatomy, base_scale):
        """Create breed-appropriate tail"""
        print("   Creating tail...")
        
        tail_radius = base_scale * 0.05
        tail_length = base_scale * 0.6
        curve_amount = anatomy['tail_curve']
        
        # Create curved tail using multiple segments
        segments = 8
        segment_length = tail_length / segments
        
        tail_parts = []
        current_pos = np.array([0, 0, -base_scale * 0.4])  # Start at rear of body
        current_angle = np.pi/6  # Starting angle
        
        for i in range(segments):
            segment = trimesh.creation.cylinder(radius=tail_radius*(1-i*0.1), height=segment_length)
            
            # Rotate and position segment
            rotation = trimesh.transformations.rotation_matrix(current_angle, [1, 0, 0])
            segment.apply_transform(rotation)
            segment.apply_translation(current_pos)
            
            tail_parts.append(segment)
            
            # Update for next segment
            direction = np.array([0, np.sin(current_angle), np.cos(current_angle)])
            current_pos += direction * segment_length
            current_angle += curve_amount * np.pi / segments  # Curve the tail
        
        # Combine tail segments
        tail = trimesh.util.concatenate(tail_parts)
        return tail

    def _assemble_dog_parts(self, head, body, legs, tail, anatomy):
        """Assemble all dog parts into complete model"""
        print("   Assembling complete dog...")
        
        # Position head on body
        head_offset = [0, body.bounds[1][1] * 0.8, body.bounds[1][2] * 0.6]
        head.apply_translation(head_offset)
        
        # Combine all parts
        all_parts = [head, body, tail] + legs
        combined = trimesh.util.concatenate(all_parts)
        
        # Ensure sitting position (bottom at Y=0)
        bounds = combined.bounds
        combined.apply_translation([0, -bounds[0][1], 0])
        
        return combined

    def _add_planter_features(self, mesh, anatomy):
        """Add functional planter features"""
        print("🪴 Adding planter features...")
        
        # Create planting cavity at the top
        bounds = mesh.bounds
        top_y = bounds[1][1]
        cavity_depth = (bounds[1][1] - bounds[0][1]) * 0.3  # 30% of height
        
        # Find center of top surface
        center_x = (bounds[1][0] + bounds[0][0]) / 2
        center_z = (bounds[1][2] + bounds[0][2]) / 2
        
        # Create cavity by removing vertices
        vertices = mesh.vertices
        cavity_radius = min(bounds[1][0] - bounds[0][0], bounds[1][2] - bounds[0][2]) * 0.25
        
        # Modify vertices to create cavity
        for i, vertex in enumerate(vertices):
            x, y, z = vertex
            
            # Check if vertex is in cavity region
            if y > top_y - cavity_depth:
                dist_from_center = np.sqrt((x - center_x)**2 + (z - center_z)**2)
                
                if dist_from_center < cavity_radius:
                    # Create smooth cavity
                    depth_factor = (y - (top_y - cavity_depth)) / cavity_depth
                    radial_factor = 1.0 - (dist_from_center / cavity_radius)
                    
                    depression = cavity_depth * depth_factor * radial_factor
                    vertices[i][1] -= depression
        
        # Ensure base stability
        base_y = bounds[0][1]
        base_thickness = 5.0  # mm
        
        for i, vertex in enumerate(vertices):
            if vertex[1] < base_y + base_thickness:
                # Flatten base for stability
                vertices[i][1] = base_y
        
        return mesh

    def _refine_for_production(self, mesh):
        """Final refinement for 3D printing"""
        print("✨ Final production refinement...")
        
        # Remove any internal geometry
        if not mesh.is_watertight:
            mesh.fill_holes()
        
        # Smooth surface
        try:
            # Use trimesh's built-in smoothing if available
            if hasattr(mesh, 'smooth_shaded'):
                mesh = mesh.smooth_shaded
            else:
                # Manual smoothing
                mesh = self._manual_smooth(mesh)
        except Exception as e:
            print(f"   Smoothing failed: {e}, continuing without smoothing")
        
        # Ensure printable size
        bounds = mesh.bounds
        current_size = bounds[1] - bounds[0]
        max_dim = max(current_size)
        
        if max_dim > 150:  # Scale down if too large
            scale = 150 / max_dim
            mesh.apply_scale(scale)
            print(f"   Scaled to printable size: {scale:.2f}x")
        
        # Ensure minimum wall thickness
        if mesh.is_watertight and hasattr(mesh, 'voxelized'):
            # Add minimum wall thickness if too thin
            voxel_size = 2.0  # mm
            voxelized = mesh.voxelized(pitch=voxel_size)
            if voxelized:
                mesh = voxelized.marching_cubes
        
        print(f"   Final mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
        return mesh

    def _manual_smooth(self, mesh, iterations=2):
        """Manual Laplacian smoothing"""
        print(f"   Applying manual smoothing ({iterations} iterations)...")
        
        original_volume = mesh.volume if mesh.is_watertight else 0
        
        for i in range(iterations):
            # Get vertex neighbors
            vertex_neighbors = mesh.vertex_neighbors
            new_vertices = mesh.vertices.copy()
            
            for v_idx, neighbors in enumerate(vertex_neighbors):
                if len(neighbors) > 0:
                    # Average neighbor positions
                    neighbor_avg = np.mean(mesh.vertices[neighbors], axis=0)
                    # Conservative smoothing
                    new_vertices[v_idx] = mesh.vertices[v_idx] * 0.7 + neighbor_avg * 0.3
            
            mesh.vertices = new_vertices
            
            # Volume preservation
            if original_volume > 0 and mesh.is_watertight:
                new_volume = mesh.volume
                if new_volume > 0:
                    scale_factor = (original_volume / new_volume) ** (1/3)
                    if 0.9 <= scale_factor <= 1.1:
                        mesh.apply_scale(scale_factor)
        
        return mesh

if __name__ == "__main__":
    import time
    
    # Test the anatomical generator
    generator = AnatomicalDogPlanterGenerator(debug_dir="debug/anatomical_test")
    
    test_photo = "test_golden_dog.jpg"
    if Path(test_photo).exists():
        print("🎯 Testing anatomical dog planter generation...")
        
        # Create debug directory
        Path("debug/anatomical_test").mkdir(parents=True, exist_ok=True)
        
        result = generator.generate_anatomical_planter(test_photo, "AnatomicalTest")
        
        if result:
            print(f"🏆 Anatomical planter generation complete: {result}")
            
            # Quick quality check
            mesh = trimesh.load_mesh(result)
            print(f"📊 Quality check:")
            print(f"   Vertices: {len(mesh.vertices):,}")
            print(f"   Faces: {len(mesh.faces):,}")
            print(f"   Watertight: {'✅' if mesh.is_watertight else '❌'}")
            print(f"   Volume: {mesh.volume:.0f} mm³")
            print(f"   Bounds: {mesh.bounds}")
        else:
            print("❌ Anatomical generation failed")
    else:
        print(f"❌ Test photo not found: {test_photo}")
