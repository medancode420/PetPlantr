# PetPlantr AI/ML Modeling Pipeline Architecture

## Pipeline Overview

The PetPlantr modeling pipeline transforms pet photos into 3D printable planters through a 6-stage process optimized for high-fidelity facial features and printable geometry.

## Stage Configuration

### A. Feature Extraction
**Tool**: Vision Transformer (ViT) backbone fine-tuned on pet faces
**Purpose**: Extract robust facial features that distinguish breed characteristics

```yaml
feature_extraction:
  model: "vit_base_patch16_224"
  backbone: "vision_transformer"
  fine_tuning:
    layers_unfrozen: "last_2_layers"
    loss_function: "arcface_loss"
    margin: 0.5
    scale: 64
  training:
    learning_rate: 2e-5
    batch_size: 32
    epochs: 15
    optimizer: "adamw"
  augmentation:
    brightness: 0.2
    contrast: 0.2
    saturation: 0.1
    horizontal_flip: 0.5
```

### B. Depth/Normal Estimation  
**Tool**: DINOv2 + MiDaS ensemble
**Purpose**: Generate accurate depth maps and surface normals for 3D reconstruction

```yaml
depth_normal_estimation:
  models:
    primary: "dinov2_vitb14"
    depth: "midas_dpt_large"
    ensemble_weight: 0.7
  preprocessing:
    resize: [384, 384]
    normalization: "imagenet"
  postprocessing:
    gaussian_blur: 1.5
    edge_preservation: true
    fur_edge_enhancement: true
  output:
    depth_resolution: [512, 512]
    normal_format: "world_space"
```

### C. Multi-view Mesh Reconstruction
**Tool**: Shape-MVD fine-tune
**Purpose**: Reconstruct 3D mesh from multiple viewpoints

```yaml
mesh_reconstruction:
  model: "shape_mvd"
  training_data:
    multi_view_images: 150
    minimum_pets: 30
    views_per_pet: 4-6
  training:
    epochs: 20
    learning_rate: 1e-4
    batch_size: 8
    scheduler: "cosine_annealing"
  augmentation:
    horizontal_flip: true
    rotation_degrees: [-15, 15]
    color_jitter: false  # Preserve color accuracy
  reconstruction:
    voxel_resolution: 256
    mesh_simplification: true
    smoothing_iterations: 3
```

### D. Planter Boolean & Cavity
**Tool**: OpenSCAD or MeshLab script
**Purpose**: Create printable planter geometry with drainage

```yaml
planter_geometry:
  tools: ["openscad", "meshlab"]
  cavity:
    cylinder_diameter: "configurable"  # User-selectable
    depth_ratio: 0.8  # 80% of total height
    drainage_hole: 8mm
  shell:
    wall_thickness: 2mm
    offset_method: "preserve_facial_geometry"
    minimum_thickness: 1.5mm
  base:
    flat_bottom: true
    stability_margin: 5mm
    feet_count: 4  # Optional stability feet
```

### E. Mesh Cleanup
**Tool**: Instant-Meshes → MeshLab
**Purpose**: Optimize mesh for 3D printing

```yaml
mesh_cleanup:
  target_faces: 180000  # Maximum for reasonable file size
  tools:
    primary: "instant_meshes"
    secondary: "meshlab"
  operations:
    - "remove_isolated_pieces"
    - "remove_duplicate_vertices"
    - "fix_non_manifold_edges"
    - "smooth_laplacian"
  validation:
    manifold_check: true
    watertight_check: true
    minimum_wall_thickness: 0.8mm
```

### F. Texture/Marking (Optional)
**Tool**: Vertex color bake → bump map
**Purpose**: Add surface detail for resin prints

```yaml
texture_marking:
  enabled: false  # Optional feature
  vertex_coloring:
    bake_resolution: 2048
    color_space: "srgb"
  bump_mapping:
    height_scale: 0.05mm
    noise_type: "perlin"
    frequency: 20
  surface_detail:
    layer_line_masking: true
    procedural_noise: 0.05mm
    fur_texture_simulation: true
```

## Pipeline Integration

### Compute Requirements
```yaml
infrastructure:
  gpu_instances:
    feature_extraction: "g4dn.xlarge"  # 1x T4 GPU
    depth_estimation: "g4dn.2xlarge"  # 1x T4 GPU, more RAM
    mesh_reconstruction: "p3.2xlarge" # 1x V100 GPU
  cpu_instances:
    geometry_processing: "c5.4xlarge"  # 16 vCPU for OpenSCAD
    mesh_cleanup: "c5.2xlarge"        # 8 vCPU for MeshLab
  storage:
    input_images: "s3://petplantr-uploads-{stage}"
    intermediate: "s3://petplantr-processing-{stage}"
    output_stl: "s3://petplantr-stl-ready-{stage}"
```

### Processing Timeline
```yaml
performance_targets:
  feature_extraction: "30 seconds"
  depth_estimation: "45 seconds"
  mesh_reconstruction: "3-4 minutes"
  boolean_operations: "30 seconds"
  mesh_cleanup: "45 seconds"
  texture_baking: "60 seconds"  # If enabled
  total_pipeline: "6-8 minutes"
```

### Quality Metrics
```yaml
quality_assurance:
  mesh_validation:
    manifold_ratio: ">95%"
    face_count: "<180k"
    volume_check: "positive"
  feature_preservation:
    facial_landmark_accuracy: ">90%"
    breed_characteristic_retention: ">85%"
  printability:
    minimum_feature_size: "0.4mm"
    overhang_angle: "<45°"
    support_requirement: "minimal"
```

## Model Deployment Strategy

### Training Infrastructure
- **Feature Extraction**: Fine-tune ViT on curated pet face dataset
- **Depth Estimation**: Combine pre-trained DINOv2 + MiDaS-DPT-Large
- **Shape-MVD**: Train on multi-view pet dataset with breed diversity

### Production Deployment
- **Model Serving**: TorchServe or ONNX Runtime
- **Batch Processing**: AWS Batch for compute-intensive stages
- **Real-time Monitoring**: Track processing times and quality metrics

### Version Control
- **Model Versioning**: MLflow or Weights & Biases
- **Pipeline Versioning**: Git-based with configuration management
- **A/B Testing**: Compare model versions on quality metrics

## Next Steps for Implementation

1. **Data Collection**: Gather diverse pet photos for training
2. **Model Training**: Fine-tune each stage with quality metrics
3. **Pipeline Integration**: Connect to existing Step Functions workflow
4. **Quality Testing**: Validate output against printing requirements
5. **Performance Optimization**: Optimize for 6-8 minute total processing time
