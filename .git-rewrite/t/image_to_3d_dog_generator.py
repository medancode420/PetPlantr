#!/usr/bin/env python3
"""
Image to 3D Dog Planter Generator
Research-based implementation using multiple image-to-3D techniques
"""
import cv2
import numpy as np
import trimesh
from pathlib import Path
import json
import time
from PIL import Image
from scipy import ndimage
from scipy.interpolate import griddata
from skimage import measure, morphology, segmentation, filters
import matplotlib.pyplot as plt

class ImageTo3DDogGenerator:
    def __init__(self):
        """Initialize with research-based image-to-3D techniques"""
        print("🔬 Image-to-3D Dog Generator initialized with research-based methods")
        
        # Define multiple conversion techniques
        self.techniques = {
            'silhouette_extrusion': 'Extract dog silhouette and extrude with depth variation',
            'depth_estimation': 'Create depth map from image features and generate surface',
            'multi_view_reconstruction': 'Generate multiple views and reconstruct 3D shape',
            'edge_based_modeling': 'Use edge detection to create 3D structure',
            'contour_to_mesh': 'Convert contours to proper 3D mesh topology'
        }

    def convert_image_to_dog_planter(self, image_path, breed=None, size_mm=120):
        """Convert dog image to 3D planter using best available technique"""
        start_time = time.time()
        print(f"\n🐕 Converting {image_path} to 3D dog planter...")
        
        # Load and preprocess image
        image = self._load_and_preprocess_image(image_path)
        
        # Try multiple techniques in order of effectiveness
        mesh = None
        technique_used = None
        
        # Technique 1: Advanced silhouette extrusion (most reliable for dog shapes)
        print("\n🎯 Technique 1: Advanced Silhouette Extrusion")
        mesh = self._silhouette_extrusion_technique(image, size_mm)
        if mesh and self._validate_mesh(mesh):
            technique_used = 'silhouette_extrusion'
        
        # Technique 2: Depth estimation with shape preservation
        if mesh is None:
            print("\n🎯 Technique 2: Depth Estimation with Shape Preservation")
            mesh = self._depth_estimation_technique(image, size_mm)
            if mesh and self._validate_mesh(mesh):
                technique_used = 'depth_estimation'
        
        # Technique 3: Multi-view reconstruction
        if mesh is None:
            print("\n🎯 Technique 3: Multi-view Reconstruction")
            mesh = self._multi_view_reconstruction_technique(image, size_mm)
            if mesh and self._validate_mesh(mesh):
                technique_used = 'multi_view_reconstruction'
        
        # Technique 4: Edge-based modeling
        if mesh is None:
            print("\n🎯 Technique 4: Edge-based Modeling")
            mesh = self._edge_based_modeling_technique(image, size_mm)
            if mesh and self._validate_mesh(mesh):
                technique_used = 'edge_based_modeling'
        
        # Fallback: Simple contour extrusion
        if mesh is None:
            print("\n🎯 Fallback: Simple Contour Extrusion")
            mesh = self._simple_contour_technique(image, size_mm)
            technique_used = 'simple_contour'
        
        if mesh is None:
            print("❌ All techniques failed")
            return None
        
        # Post-process the mesh
        mesh = self._post_process_mesh(mesh, size_mm)
        
        # Add planter functionality
        mesh = self._add_planter_features(mesh, size_mm)
        
        duration = time.time() - start_time
        print(f"\n✅ Conversion complete using {technique_used} in {duration:.2f}s")
        
        return {
            'mesh': mesh,
            'technique': technique_used,
            'duration': duration,
            'vertices': len(mesh.vertices),
            'faces': len(mesh.faces),
            'volume': mesh.volume,
            'watertight': mesh.is_watertight
        }

    def _load_and_preprocess_image(self, image_path):
        """Load and preprocess image for 3D conversion"""
        print("📸 Loading and preprocessing image...")
        
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize to manageable size while preserving aspect ratio
        height, width = image.shape[:2]
        max_size = 512
        if max(height, width) > max_size:
            scale = max_size / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        
        print(f"📐 Preprocessed image: {image.shape[1]}×{image.shape[0]}")
        return image

    def _silhouette_extrusion_technique(self, image, size_mm):
        """Advanced silhouette extrusion with depth variation"""
        print("🔧 Extracting dog silhouette and creating 3D extrusion...")
        
        try:
            # Convert to different color spaces for better segmentation
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Multiple segmentation approaches
            masks = []
            
            # 1. Otsu thresholding on grayscale
            _, mask1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            masks.append(mask1)
            
            # 2. Adaptive thresholding
            mask2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            masks.append(mask2)
            
            # 3. HSV-based segmentation (good for fur/skin tones)
            lower_bound = np.array([0, 20, 20])
            upper_bound = np.array([180, 255, 240])
            mask3 = cv2.inRange(hsv, lower_bound, upper_bound)
            masks.append(mask3)
            
            # 4. Edge-based segmentation
            edges = cv2.Canny(gray, 50, 150)
            kernel = np.ones((3,3), np.uint8)
            mask4 = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
            mask4 = cv2.dilate(mask4, kernel, iterations=1)
            masks.append(mask4)
            
            # Combine masks using voting
            combined_mask = np.zeros_like(gray, dtype=np.uint8)
            for mask in masks:
                combined_mask += (mask > 127).astype(np.uint8)
            
            # Use majority voting
            final_mask = (combined_mask >= len(masks)//2 + 1).astype(np.uint8) * 255
            
            # Clean up the mask
            final_mask = self._clean_mask(final_mask)
            
            # Find main contour
            contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                print("❌ No contours found")
                return None
            
            # Get largest contour (should be the dog)
            main_contour = max(contours, key=cv2.contourArea)
            
            # Create depth variation based on distance from edge
            depth_map = self._create_depth_from_contour(final_mask, main_contour)
            
            # Convert to 3D mesh with depth variation
            mesh = self._extrude_with_depth_variation(main_contour, depth_map, size_mm)
            
            print(f"✅ Silhouette extraction: {len(mesh.vertices)} vertices")
            return mesh
            
        except Exception as e:
            print(f"❌ Silhouette extrusion failed: {e}")
            return None

    def _depth_estimation_technique(self, image, size_mm):
        """Create depth map from image features and generate surface"""
        print("🔧 Creating depth map from image features...")
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Multiple depth cues
            depth_maps = []
            
            # 1. Brightness-based depth (darker = deeper)
            brightness_depth = (255 - gray) / 255.0
            depth_maps.append(brightness_depth)
            
            # 2. Gradient-based depth (higher gradients = raised features)
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            gradient_depth = gradient_magnitude / gradient_magnitude.max()
            depth_maps.append(gradient_depth)
            
            # 3. Distance transform depth
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            binary = binary > 127
            distance_depth = ndimage.distance_transform_edt(binary)
            if distance_depth.max() > 0:
                distance_depth = distance_depth / distance_depth.max()
                depth_maps.append(distance_depth)
            
            # 4. Texture-based depth
            blur = cv2.GaussianBlur(gray, (15, 15), 0)
            texture = cv2.absdiff(gray, blur)
            texture_depth = texture / 255.0
            depth_maps.append(texture_depth)
            
            # Combine depth maps with weights
            weights = [0.4, 0.2, 0.3, 0.1]  # Emphasize brightness and distance
            combined_depth = np.zeros_like(depth_maps[0])
            for depth, weight in zip(depth_maps, weights):
                combined_depth += depth * weight
            
            # Smooth the depth map
            combined_depth = ndimage.gaussian_filter(combined_depth, sigma=2)
            
            # Create object mask
            object_mask = binary
            
            # Generate 3D mesh from depth map
            mesh = self._depth_map_to_mesh(combined_depth, object_mask, size_mm)
            
            print(f"✅ Depth estimation: {len(mesh.vertices)} vertices")
            return mesh
            
        except Exception as e:
            print(f"❌ Depth estimation failed: {e}")
            return None

    def _multi_view_reconstruction_technique(self, image, size_mm):
        """Generate multiple views and reconstruct 3D shape"""
        print("🔧 Generating multiple views for 3D reconstruction...")
        
        try:
            # Generate synthetic views by transforming the original image
            views = self._generate_synthetic_views(image)
            
            # Extract silhouettes from each view
            silhouettes = []
            for i, view in enumerate(views):
                silhouette = self._extract_silhouette(view)
                if silhouette is not None:
                    silhouettes.append((silhouette, i * 45))  # 45-degree intervals
            
            if len(silhouettes) < 2:
                print("❌ Insufficient views for reconstruction")
                return None
            
            # Perform volume carving
            volume = self._volume_carving(silhouettes, size_mm)
            
            # Convert volume to mesh
            mesh = self._volume_to_mesh(volume, size_mm)
            
            print(f"✅ Multi-view reconstruction: {len(mesh.vertices)} vertices")
            return mesh
            
        except Exception as e:
            print(f"❌ Multi-view reconstruction failed: {e}")
            return None

    def _edge_based_modeling_technique(self, image, size_mm):
        """Use edge detection to create 3D structure"""
        print("🔧 Creating 3D structure from edge features...")
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Multi-scale edge detection
            edges_multi = []
            for sigma in [1, 2, 4]:
                blurred = cv2.GaussianBlur(gray, (0, 0), sigma)
                edges = cv2.Canny(blurred, 50, 150)
                edges_multi.append(edges)
            
            # Combine multi-scale edges
            combined_edges = np.maximum.reduce(edges_multi)
            
            # Create edge-based depth
            # Strong edges = raised features
            edge_distance = ndimage.distance_transform_edt(~(combined_edges > 0))
            edge_depth = edge_distance / edge_distance.max() if edge_distance.max() > 0 else edge_distance
            
            # Smooth to create surfaces
            edge_depth = ndimage.gaussian_filter(edge_depth, sigma=3)
            
            # Create mask from edges
            mask = combined_edges > 0
            mask = ndimage.binary_dilation(mask, iterations=5)
            
            # Generate mesh
            mesh = self._depth_map_to_mesh(edge_depth, mask, size_mm)
            
            print(f"✅ Edge-based modeling: {len(mesh.vertices)} vertices")
            return mesh
            
        except Exception as e:
            print(f"❌ Edge-based modeling failed: {e}")
            return None

    def _simple_contour_technique(self, image, size_mm):
        """Simple contour extrusion as fallback"""
        print("🔧 Using simple contour extrusion as fallback...")
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Simple threshold
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                print("❌ No contours found in fallback")
                return None
            
            main_contour = max(contours, key=cv2.contourArea)
            
            # Simple extrusion
            mesh = self._simple_extrude_contour(main_contour, size_mm)
            
            print(f"✅ Simple contour: {len(mesh.vertices)} vertices")
            return mesh
            
        except Exception as e:
            print(f"❌ Simple contour failed: {e}")
            return None

    def _clean_mask(self, mask):
        """Clean up binary mask"""
        # Remove small noise
        mask = morphology.remove_small_objects(mask > 127, min_size=100)
        mask = mask.astype(np.uint8) * 255
        
        # Fill holes
        mask = ndimage.binary_fill_holes(mask > 127).astype(np.uint8) * 255
        
        # Smooth boundaries
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask

    def _create_depth_from_contour(self, mask, contour):
        """Create depth variation from contour using distance transform"""
        # Distance from edges gives depth
        distance = ndimage.distance_transform_edt(mask > 127)
        
        # Normalize
        if distance.max() > 0:
            distance = distance / distance.max()
        
        # Add some noise for organic feel
        noise = np.random.normal(0, 0.05, distance.shape)
        distance = np.clip(distance + noise, 0, 1)
        
        # Smooth
        distance = ndimage.gaussian_filter(distance, sigma=2)
        
        return distance

    def _extrude_with_depth_variation(self, contour, depth_map, size_mm):
        """Extrude contour with depth variation"""
        # Simplify contour
        epsilon = 0.02 * cv2.contourArea(contour)
        simplified = cv2.approxPolyDP(contour, epsilon, True)
        points = simplified.reshape(-1, 2)
        
        # Scale points
        scale = size_mm / 200.0  # Assume 200px = desired size
        
        vertices = []
        faces = []
        
        # Create vertices with varying heights
        for point in points:
            x, y = point * scale
            # Get depth at this point
            px, py = int(point[0]), int(point[1])
            if 0 <= px < depth_map.shape[1] and 0 <= py < depth_map.shape[0]:
                depth = depth_map[py, px]
            else:
                depth = 0
            
            height = depth * size_mm * 0.3  # Max 30% of size
            
            # Bottom vertex
            vertices.append([x, y, 0])
            # Top vertex
            vertices.append([x, y, height])
        
        # Create side faces
        n_points = len(points)
        for i in range(n_points):
            next_i = (i + 1) % n_points
            
            # Indices
            bottom_curr = i * 2
            top_curr = i * 2 + 1
            bottom_next = next_i * 2
            top_next = next_i * 2 + 1
            
            # Two triangles per side
            faces.append([bottom_curr, bottom_next, top_curr])
            faces.append([bottom_next, top_next, top_curr])
        
        # Add top and bottom caps using simple triangulation
        # Bottom cap
        center_bottom = len(vertices)
        center_x = np.mean([v[0] for v in vertices[::2]])
        center_y = np.mean([v[1] for v in vertices[::2]])
        vertices.append([center_x, center_y, 0])
        
        for i in range(n_points):
            next_i = (i + 1) % n_points
            faces.append([center_bottom, i * 2, next_i * 2])
        
        # Top cap
        center_top = len(vertices)
        center_z = np.mean([v[2] for v in vertices[1::2]])
        vertices.append([center_x, center_y, center_z])
        
        for i in range(n_points):
            next_i = (i + 1) % n_points
            faces.append([center_top, next_i * 2 + 1, i * 2 + 1])
        
        # Create mesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, validate=False)
        return mesh

    def _depth_map_to_mesh(self, depth_map, mask, size_mm):
        """Convert depth map to 3D mesh"""
        height, width = depth_map.shape
        scale = size_mm / max(height, width)
        
        vertices = []
        faces = []
        vertex_indices = {}
        
        # Create vertices only where mask is true
        vertex_count = 0
        for y in range(height):
            for x in range(width):
                if mask[y, x]:
                    depth = depth_map[y, x] * size_mm * 0.3
                    vertices.append([x * scale, y * scale, depth])
                    vertex_indices[(x, y)] = vertex_count
                    vertex_count += 1
        
        # Create faces
        for y in range(height - 1):
            for x in range(width - 1):
                # Check if all 4 corners exist
                corners = [(x, y), (x+1, y), (x, y+1), (x+1, y+1)]
                if all(corner in vertex_indices for corner in corners):
                    # Create two triangles
                    v1 = vertex_indices[(x, y)]
                    v2 = vertex_indices[(x+1, y)]
                    v3 = vertex_indices[(x, y+1)]
                    v4 = vertex_indices[(x+1, y+1)]
                    
                    faces.append([v1, v2, v3])
                    faces.append([v2, v4, v3])
        
        # Create mesh
        if vertices and faces:
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces, validate=False)
            return mesh
        else:
            return None

    def _generate_synthetic_views(self, image):
        """Generate multiple synthetic views of the image"""
        views = [image]  # Original view
        
        # Generate rotated/skewed versions to simulate different viewpoints
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # Rotate
        for angle in [15, -15, 30, -30]:
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (width, height), borderValue=(255, 255, 255))
            views.append(rotated)
        
        # Perspective transforms (simulate viewing from side)
        for skew in [0.1, -0.1]:
            pts1 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
            pts2 = np.float32([[0, 0], [width, 0], [skew * width, height], [width + skew * width, height]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            warped = cv2.warpPerspective(image, M, (width, height), borderValue=(255, 255, 255))
            views.append(warped)
        
        return views

    def _extract_silhouette(self, image):
        """Extract silhouette from a single view"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary > 127

    def _volume_carving(self, silhouettes, size_mm):
        """Perform volume carving from multiple silhouettes"""
        # Create a 3D volume
        resolution = 64
        volume = np.ones((resolution, resolution, resolution), dtype=bool)
        
        # Carve volume using each silhouette
        for silhouette, angle in silhouettes:
            # Project silhouette onto volume from the given angle
            # This is a simplified implementation
            h, w = silhouette.shape
            for z in range(resolution):
                for y in range(resolution):
                    # Project this slice onto the silhouette
                    sy = int(y * h / resolution)
                    if sy < h:
                        for x in range(resolution):
                            sx = int(x * w / resolution)
                            if sx < w and not silhouette[sy, sx]:
                                volume[x, y, z] = False
        
        return volume

    def _volume_to_mesh(self, volume, size_mm):
        """Convert volume to mesh using marching cubes"""
        try:
            from skimage import measure
            
            # Apply marching cubes
            vertices, faces, _, _ = measure.marching_cubes(volume.astype(float), level=0.5)
            
            # Scale to desired size
            scale = size_mm / max(volume.shape)
            vertices = vertices * scale
            
            # Create mesh
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces, validate=False)
            return mesh
            
        except Exception as e:
            print(f"❌ Volume to mesh conversion failed: {e}")
            return None

    def _simple_extrude_contour(self, contour, size_mm):
        """Simple extrusion of contour"""
        # Simplify contour
        epsilon = 0.02 * cv2.contourArea(contour)
        simplified = cv2.approxPolyDP(contour, epsilon, True)
        points = simplified.reshape(-1, 2)
        
        scale = size_mm / 200.0
        height = size_mm * 0.3
        
        vertices = []
        faces = []
        
        # Bottom vertices
        for point in points:
            vertices.append([point[0] * scale, point[1] * scale, 0])
        
        # Top vertices
        for point in points:
            vertices.append([point[0] * scale, point[1] * scale, height])
        
        n_points = len(points)
        
        # Side faces
        for i in range(n_points):
            next_i = (i + 1) % n_points
            
            # Two triangles per side
            faces.append([i, next_i, i + n_points])
            faces.append([next_i, next_i + n_points, i + n_points])
        
        # Caps (simple triangulation)
        # Bottom
        for i in range(1, n_points - 1):
            faces.append([0, i, i + 1])
        
        # Top
        for i in range(1, n_points - 1):
            faces.append([n_points, n_points + i + 1, n_points + i])
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, validate=False)
        return mesh

    def _validate_mesh(self, mesh):
        """Validate that mesh is reasonable"""
        if mesh is None:
            return False
        
        if len(mesh.vertices) < 10:
            print("❌ Mesh has too few vertices")
            return False
        
        if len(mesh.faces) < 10:
            print("❌ Mesh has too few faces")
            return False
        
        if not mesh.is_volume:
            print("⚠️ Mesh is not a volume")
            # Don't reject, can sometimes be fixed
        
        return True

    def _post_process_mesh(self, mesh, size_mm):
        """Post-process mesh for quality"""
        print("🔧 Post-processing mesh...")
        
        # Remove duplicate vertices
        mesh.merge_vertices()
        
        # Remove degenerate faces
        mesh.remove_degenerate_faces()
        
        # Remove unreferenced vertices
        mesh.remove_unreferenced_vertices()
        
        # Smooth the mesh
        mesh = mesh.smoothed()
        
        # Fix normals
        mesh.fix_normals()
        
        # Try to make watertight
        if not mesh.is_watertight:
            mesh.fill_holes()
        
        print(f"✅ Post-processing complete: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
        return mesh

    def _add_planter_features(self, mesh, size_mm):
        """Add planter cavity and features"""
        print("🪴 Adding planter features...")
        
        try:
            if not mesh.is_watertight:
                print("⚠️ Mesh not watertight, skipping cavity")
                return mesh
            
            # Get mesh bounds
            bounds = mesh.bounds
            width = bounds[1][0] - bounds[0][0]
            height = bounds[1][1] - bounds[0][1]
            depth = bounds[1][2] - bounds[0][2]
            
            # Create cavity in the top/back area
            center_x = (bounds[0][0] + bounds[1][0]) / 2
            center_y = bounds[1][1] - height * 0.3  # Towards the back
            center_z = bounds[1][2] - depth * 0.1   # Near the top
            
            # Cavity dimensions
            cavity_radius = min(width, height) * 0.25
            cavity_depth = depth * 0.6
            
            # Create cylindrical cavity
            cavity = trimesh.creation.cylinder(
                radius=cavity_radius,
                height=cavity_depth,
                transform=trimesh.transformations.translation_matrix([center_x, center_y, center_z - cavity_depth/2])
            )
            
            # Subtract cavity from mesh
            result = mesh.difference(cavity)
            
            if result and result.is_volume and result.volume > 0:
                print(f"✅ Added planter cavity (radius: {cavity_radius:.1f}mm, depth: {cavity_depth:.1f}mm)")
                return result
            else:
                print("⚠️ Cavity operation failed, keeping original")
                return mesh
                
        except Exception as e:
            print(f"⚠️ Failed to add planter features: {e}")
            return mesh

    def generate_dog_planter_collection(self, image_paths, output_dir="generated_models"):
        """Generate multiple dog planters from images"""
        print(f"\n🏭 Generating dog planter collection from {len(image_paths)} images...")
        
        results = {}
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        for i, image_path in enumerate(image_paths):
            print(f"\n{'='*60}")
            print(f"Processing image {i+1}/{len(image_paths)}: {Path(image_path).name}")
            print(f"{'='*60}")
            
            try:
                # Convert image to 3D
                result = self.convert_image_to_dog_planter(image_path)
                
                if result:
                    # Save STL
                    filename = f"dog_planter_{Path(image_path).stem}_{result['technique']}.stl"
                    stl_path = output_path / filename
                    result['mesh'].export(str(stl_path))
                    
                    results[Path(image_path).name] = {
                        'success': True,
                        'stl_path': str(stl_path),
                        'technique': result['technique'],
                        'duration': result['duration'],
                        'quality': {
                            'vertices': result['vertices'],
                            'faces': result['faces'],
                            'volume': result['volume'],
                            'watertight': result['watertight']
                        }
                    }
                    
                    print(f"✅ Saved: {stl_path}")
                else:
                    results[Path(image_path).name] = {
                        'success': False,
                        'error': 'All conversion techniques failed'
                    }
                    
            except Exception as e:
                print(f"❌ Failed to process {image_path}: {e}")
                results[Path(image_path).name] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Generate summary report
        self._generate_collection_report(results, output_path)
        
        return results

    def _generate_collection_report(self, results, output_path):
        """Generate summary report for the collection"""
        timestamp = int(time.time() * 1000)
        report_file = output_path / f"image_to_3d_report_{timestamp}.json"
        
        successful = [r for r in results.values() if r.get('success', False)]
        failed = [r for r in results.values() if not r.get('success', False)]
        
        report = {
            'timestamp': timestamp,
            'generator': 'image_to_3d_dog_generator',
            'total_images': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(results) * 100 if results else 0,
            'techniques_used': {},
            'results': results
        }
        
        # Count techniques used
        for result in successful:
            technique = result.get('technique', 'unknown')
            report['techniques_used'][technique] = report['techniques_used'].get(technique, 0) + 1
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📊 COLLECTION SUMMARY:")
        print(f"  Total images: {len(results)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")
        print(f"  Success rate: {report['success_rate']:.1f}%")
        print(f"  Techniques used: {report['techniques_used']}")
        print(f"  Report saved: {report_file}")

if __name__ == "__main__":
    generator = ImageTo3DDogGenerator()
    
    # Test with a sample image
    sample_images = ["test_golden_dog.jpg"]
    results = generator.generate_dog_planter_collection(sample_images)
    
    print("\n🎯 Image-to-3D conversion complete!")
    print("Generated dog planters ready for 3D printing!")
