# Animal3D Multi-View Extractor

Extracts canonical multi-view pet images from the **Animal3D dataset** (ICCV 2023) for PetPlantr training pipeline.

## Overview

The Animal3D dataset contains up to 40 camera views per pet identity. This tool extracts exactly 5 canonical views needed for multi-view 3D reconstruction:

- **View 0**: Front view
- **View 1**: Left profile  
- **View 2**: Right profile
- **View 3**: Rear view
- **View 4**: Top view

## Installation

```bash
# Install required dependency
pip install pillow

# Make script executable
chmod +x extract_animal3d_views.py
```

## Usage

### Basic Usage
```bash
python extract_animal3d_views.py --src_dir data/animal3d
```

### Advanced Usage
```bash
python extract_animal3d_views.py \
    --src_dir /path/to/animal3d \
    --dst_dir data/proprietary_raw \
    --limit 10 \
    --min_resolution 1500
```

### Arguments
- `--src_dir`: Root path to Animal3D dataset (required)
- `--dst_dir`: Output directory (default: `data/proprietary_raw`)
- `--limit`: Max identities per species (optional)
- `--min_resolution`: Min pixels on shortest side (default: 1500)

## Expected Input Structure

```
data/animal3d/
├── dog/
│   ├── identity_001/
│   │   ├── view_0.jpg    # front
│   │   ├── view_1.jpg    # left
│   │   ├── view_2.jpg    # right
│   │   ├── view_3.jpg    # rear
│   │   ├── view_4.jpg    # top
│   │   └── view_5.jpg... # (other views, ignored)
│   └── identity_002/
│       └── ...
└── cat/
    ├── identity_001/
    └── ...
```

## Output Structure

```
data/proprietary_raw/
├── dog_001/
│   ├── front.jpg
│   ├── left.jpg
│   ├── right.jpg
│   ├── back.jpg
│   └── top.jpg
├── dog_002/
│   └── ...
├── cat_001/
│   ├── front.jpg
│   ├── left.jpg
│   ├── right.jpg
│   ├── back.jpg
│   └── top.jpg
└── cat_002/
    └── ...
```

## Quality Filters

The extractor automatically filters identities based on:

1. **Completeness**: All 5 required views must exist
2. **Resolution**: Each image must be ≥1500px on shortest side
3. **Readability**: Images must be valid JPEG files

Identities failing any filter are skipped and reported.

## Example Output

```
🚀 Animal3D Multi-View Extractor
   Source: data/animal3d
   Destination: data/proprietary_raw
   Min resolution: 1500px

🔍 Processing dog identities: 150 found
   ✅ identity_001 → dog_001 (5 views)
   ⚠️  identity_002: Missing view_4.jpg
   ✅ identity_003 → dog_002 (5 views)
   ⚠️  identity_004: view_0.jpg below 1500px
   ...

🔍 Processing cat identities: 120 found
   ✅ identity_001 → cat_001 (5 views)
   ✅ identity_002 → cat_002 (5 views)
   ...

============================================================
📊 EXTRACTION SUMMARY
============================================================
Species      | Kept     | Skipped  | Total   
------------------------------------------------------------
dog          | 23       | 127      | 150     
cat          | 18       | 102      | 120     
------------------------------------------------------------
TOTAL        | 41       | 229      | 270     

🎯 Result: 41 identities with complete high-resolution view sets
✅ SUCCESS: Sufficient identities extracted for training
📁 Output directory: data/proprietary_raw
```

## Integration with PetPlantr

After extraction, the output is ready for PetPlantr preprocessing:

```bash
# 1. Extract Animal3D views
python extract_animal3d_views.py --src_dir data/animal3d --limit 15

# 2. Preprocess for training
python scripts/preprocess_proprietary.py

# 3. Upload to S3
bash scripts/process_and_upload.sh

# 4. Launch Stage 2 training
modal run train_unet_stage2.py --env BATCH=1,GRAD_ACCUM=8,EPOCHS=5
```

## Error Handling

- **Exit code 0**: Success (≥5 identities extracted)
- **Exit code 1**: Failure (<5 identities or other errors)
- **Warnings**: Logged for skipped identities with reasons

## Dataset Citation

```bibtex
@inproceedings{xu2023animal3d,
  title={Animal3D: A Comprehensive Dataset of 3D Animal Pose and Shape},
  author={Xu, Jiacong and Zhang, Yi and Chang, Jiawei and Ma, Ke and Stam, Jos and Metaxas, Dimitris N and Zhao, Jian},
  booktitle={Proceedings of the IEEE/CVF International Conference on Computer Vision},
  year={2023}
}
```

**License**: CC BY-NC-SA 4.0  
**Dataset URL**: https://animal3d.github.io/

## Troubleshooting

### Common Issues

1. **"Invalid Animal3D structure"**
   - Ensure `dog/` and `cat/` subdirectories exist in source
   - Check that identity folders contain `view_*.jpg` files

2. **"Pillow is required"**
   - Install with: `pip install pillow`

3. **"Less than 5 identities extracted"**
   - Lower `--min_resolution` (try 1024 or 800)
   - Remove `--limit` to process all identities
   - Check dataset completeness

### Performance Tips

- Use `--limit` for faster testing (e.g., `--limit 5` per species)
- Higher `--min_resolution` = better quality but fewer results
- Script processes ~10 identities/second on modern hardware

---

*Ready to extract high-quality multi-view pet data for advanced 3D reconstruction training!* 🐕🐱
