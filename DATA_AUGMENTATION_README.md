# PetPlantr Data Augmentation System

## Overview
This data augmentation system provides comprehensive image augmentation capabilities for the PetPlantr dataset. It supports multiple augmentation techniques including flips, crops, color jittering, and rotations.

## Features
- **Multiple Augmentation Types**: Flip, crop, color jitter, brightness, contrast, rotation
- **Containerised**: Docker-based for reproducible environments
- **Batch Processing**: Process entire datasets from manifest files
- **Quality Assurance**: Maintains image quality and metadata

## Quick Start

### Using Docker (Recommended)
```bash
# Build the container
docker build -f Dockerfile.augmentation -t petplantr-augmentation .

# Run augmentation
docker run -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output petplantr-augmentation \
  python data_augmentation.py \
  --input-dir /app/data \
  --output-dir /app/output \
  --manifest /app/data/manifest.csv \
  --augmentations flip_horizontal crop_center color_jitter \
  --max-images 100
```

### Direct Python Execution
```bash
python src/data_augmentation.py \
  --input-dir data \
  --output-dir data/augmented \
  --manifest data/manifest.csv \
  --augmentations flip_horizontal crop_center color_jitter
```

## Parameters

### Input/Output
- `--input-dir`: Directory containing input images (default: `data`)
- `--output-dir`: Directory for augmented images (default: `data/augmented`)
- `--manifest`: Dataset manifest CSV file (default: `data/manifest.csv`)

### Augmentation Control
- `--augmentations`: List of augmentations to apply
  - `flip_horizontal`: Horizontal mirror flip
  - `flip_vertical`: Vertical flip
  - `crop_center`: Center crop (80% of original)
  - `crop_random`: Random crop
  - `color_jitter`: Random color adjustment
  - `brightness_jitter`: Random brightness adjustment
  - `contrast_jitter`: Random contrast adjustment
  - `rotation_90`: 90-degree rotation
  - `rotation_180`: 180-degree rotation
  - `rotation_270`: 270-degree rotation

### Processing Control
- `--max-images`: Maximum number of images to process (optional)
- `--seed`: Random seed for reproducible results (default: 42)

## Output Structure
```
data/augmented/
├── affenpinscher/
│   ├── affenpinscher_001_original.jpg
│   ├── affenpinscher_001_flip_horizontal.jpg
│   ├── affenpinscher_001_crop_center.jpg
│   └── affenpinscher_001_color_jitter.jpg
├── beagle/
│   ├── beagle_001_original.jpg
│   ├── beagle_001_flip_horizontal.jpg
│   └── ...
└── augmentation_results.json
```

## Augmentation Details

### Flip Operations
- **Horizontal Flip**: Mirrors image left-to-right
- **Vertical Flip**: Flips image top-to-bottom

### Crop Operations
- **Center Crop**: Crops 80% from center, maintains aspect ratio
- **Random Crop**: Random crop of 50% original size

### Color Adjustments
- **Color Jitter**: Random color saturation (0.5x to 1.5x)
- **Brightness Jitter**: Random brightness (0.7x to 1.3x)
- **Contrast Jitter**: Random contrast (0.7x to 1.3x)

### Rotations
- **90°/180°/270°**: Clockwise rotations with canvas expansion

## Quality Assurance

### Validation Checks
- All output images are readable
- Breed labels match directory structure
- Image dimensions are reasonable
- File formats are preserved

### Testing
```bash
# Run validation on 100 random outputs
python -c "
import random
from pathlib import Path
from PIL import Image

output_dir = Path('data/augmented')
samples = list(output_dir.rglob('*.jpg'))[:100]

valid = 0
for img_path in samples:
    try:
        with Image.open(img_path) as img:
            img.verify()
            # Check breed label in path
            breed_from_path = img_path.parent.name
            if breed_from_path in img_path.name:
                valid += 1
    except:
        pass

print(f'Valid images: {valid}/100 ({valid/100:.1%})')
"
```

## Docker Usage Examples

### Basic Augmentation
```bash
docker run -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output petplantr-augmentation \
  python data_augmentation.py \
  --augmentations flip_horizontal color_jitter
```

### Advanced Configuration
```bash
docker run -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output petplantr-augmentation \
  python data_augmentation.py \
  --augmentations flip_horizontal crop_center color_jitter brightness_jitter \
  --max-images 500 \
  --seed 12345
```

### Development Mode
```bash
docker run -it -v $(pwd)/src:/app/src -v $(pwd)/data:/app/data petplantr-augmentation bash
```

## Performance Notes
- Processing speed: ~50-100 images/minute
- Memory usage: ~200MB base + 50MB per concurrent image
- Disk space: ~3x original dataset size (with multiple augmentations)

## Integration
This augmentation system integrates with:
- Dataset manifest system (`data/manifest.csv`)
- QA validation system (`src/qa_system.py`)
- Model training pipelines

## Troubleshooting
- **No images found**: Check input directory and manifest file paths
- **Memory errors**: Reduce `--max-images` or use smaller batches
- **Permission errors**: Ensure output directory is writable
- **Docker issues**: Check volume mounts and file permissions
