"""
PetPlantr Embedding Export for UNet Integration
Export 768-d embeddings as pre-computed context for Shape-MVD pipeline

This enables the "Mac ↔ GPU Handoff" strategy:
1. Mac: Extract embeddings with simplified model
2. GPU: Use pre-computed embeddings in UNet training (halves VRAM usage)
3. Progressive complexity ladder without OOM issues
"""

import torch
import numpy as np
from pathlib import Path
import boto3
from tqdm import tqdm
import json
from transformers import CLIPVisionModel, CLIPImageProcessor
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingExporter:
    """Export embeddings for GPU training pipeline"""
    
    def __init__(self, model_path: str, data_dir: str, output_dir: str = "./embeddings"):
        self.model_path = Path(model_path)
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load device
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        
        # Load models
        self._load_models()
        
        # Setup CLIP processor
        self.processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    def _load_models(self):
        """Load CLIP and our trained model"""
        logger.info("🧠 Loading models for embedding export...")
        
        # Load CLIP encoder (this is what we'll use for final embeddings)
        self.clip_model = CLIPVisionModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_model.eval()
        self.clip_model.to(self.device)
        
        logger.info("✅ CLIP model loaded - using 768-d embeddings for UNet compatibility")
    
    def export_embeddings_for_split(self, split: str):
        """Export embeddings for a data split"""
        logger.info(f"📊 Exporting embeddings for {split} split...")
        
        split_dir = self.data_dir / split
        image_paths = list(split_dir.glob("*.jpg"))
        
        embeddings = {}
        
        with torch.no_grad():
            for img_path in tqdm(image_paths, desc=f"Processing {split}"):
                # Load and process image
                image = Image.open(img_path).convert('RGB')
                
                # CLIP processing
                clip_inputs = self.processor(images=image, return_tensors="pt")
                clip_pixel_values = clip_inputs["pixel_values"].to(self.device)
                
                # Get CLIP features (768-d for ViT-Base)
                clip_features = self.clip_model(clip_pixel_values).last_hidden_state
                pooled_features = self.clip_model(clip_pixel_values).pooler_output
                
                # Store both sequence and pooled embeddings
                embeddings[img_path.name] = {
                    "sequence_embedding": clip_features.cpu().numpy(),  # [1, 197, 768] for patches
                    "pooled_embedding": pooled_features.cpu().numpy(),   # [1, 768] for global
                    "image_path": str(img_path.relative_to(self.data_dir))
                }
        
        # Save embeddings
        output_file = self.output_dir / f"{split}_embeddings.npz"
        
        # Prepare arrays for efficient storage
        sequence_embeddings = []
        pooled_embeddings = []
        image_names = []
        image_paths = []
        
        for img_name, data in embeddings.items():
            sequence_embeddings.append(data["sequence_embedding"])
            pooled_embeddings.append(data["pooled_embedding"])
            image_names.append(img_name)
            image_paths.append(data["image_path"])
        
        # Stack arrays
        sequence_embeddings = np.vstack(sequence_embeddings)  # [N, 197, 768]
        pooled_embeddings = np.vstack(pooled_embeddings)      # [N, 768]
        
        # Save as compressed numpy archive
        np.savez_compressed(
            output_file,
            sequence_embeddings=sequence_embeddings,
            pooled_embeddings=pooled_embeddings,
            image_names=np.array(image_names),
            image_paths=np.array(image_paths)
        )
        
        logger.info(f"💾 Saved {len(embeddings)} embeddings to {output_file}")
        logger.info(f"   📊 Sequence shape: {sequence_embeddings.shape}")
        logger.info(f"   📊 Pooled shape: {pooled_embeddings.shape}")
        
        return output_file
    
    def export_all_splits(self):
        """Export embeddings for all data splits"""
        logger.info("🚀 Exporting embeddings for all splits...")
        
        exported_files = {}
        
        for split in ["train", "val"]:
            split_dir = self.data_dir / split
            if split_dir.exists():
                output_file = self.export_embeddings_for_split(split)
                exported_files[split] = output_file
            else:
                logger.warning(f"⚠️  Split {split} not found at {split_dir}")
        
        # Create metadata file
        metadata = {
            "model_source": "openai/clip-vit-base-patch32",
            "embedding_dim": 768,
            "sequence_length": 197,  # 14x14 patches + 1 CLS token
            "exported_files": {k: str(v) for k, v in exported_files.items()},
            "usage": "Pre-computed embeddings for UNet cross-attention",
            "compatible_with": "Shape-MVD UNet expecting 768-d encoder_hidden_states"
        }
        
        metadata_file = self.output_dir / "embedding_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"📋 Metadata saved to {metadata_file}")
        
        return exported_files, metadata
    
    def upload_to_s3(self, bucket: str = "petplantr-dataset", prefix: str = "embeddings"):
        """Upload embeddings to S3 for GPU training"""
        logger.info(f"☁️  Uploading embeddings to S3: s3://{bucket}/{prefix}/")
        
        s3 = boto3.client('s3')
        
        for file_path in self.output_dir.glob("*"):
            if file_path.is_file():
                s3_key = f"{prefix}/{file_path.name}"
                
                try:
                    s3.upload_file(str(file_path), bucket, s3_key)
                    logger.info(f"✅ Uploaded {file_path.name} → s3://{bucket}/{s3_key}")
                except Exception as e:
                    logger.error(f"❌ Failed to upload {file_path.name}: {e}")
        
        logger.info("🎉 Embedding upload complete!")
    
    def create_makefile_targets(self):
        """Create Makefile for Mac ↔ GPU handoff automation"""
        makefile_content = '''# PetPlantr Mac ↔ GPU Handoff Automation
# Usage: make prep-embeddings && make fine-tune-mvd

.PHONY: prep-embeddings fine-tune-mvd clean

# On MacBook (M3 Max) - Prepare embeddings
prep-embeddings:
\t@echo "🍎 Preparing embeddings on M3 Max..."
\tpython backend/datasets/export_embeddings.py
\taws s3 sync embeddings/ s3://petplantr-dataset/embeddings/
\t@echo "✅ Embeddings ready for GPU training"

# On GPU (Modal) - Fine-tune with pre-computed embeddings
fine-tune-mvd:
\t@echo "☁️  Launching GPU fine-tune with embeddings..."
\tmodal run backend/datasets/shape_mvd_training.py \\
\t\t--embedding-dir s3://petplantr-dataset/embeddings/ \\
\t\t--freeze-clip \\
\t\t--batch-size 1 \\
\t\t--grad-accum 8 \\
\t\t--gpu T4

# Progressive complexity stages
stage-1-unet:
\tmodal run backend/datasets/shape_mvd_training.py \\
\t\t--embedding-dir s3://petplantr-dataset/embeddings/ \\
\t\t--unet-channels 128 \\
\t\t--batch-size 1

stage-2-unet:
\tmodal run backend/datasets/shape_mvd_training.py \\
\t\t--embedding-dir s3://petplantr-dataset/embeddings/ \\
\t\t--unet-channels 256 \\
\t\t--batch-size 1 \\
\t\t--enable-ema

stage-3-full:
\tmodal run backend/datasets/shape_mvd_training.py \\
\t\t--embedding-dir s3://petplantr-dataset/embeddings/ \\
\t\t--unet-channels 320 \\
\t\t--batch-size 4 \\
\t\t--gpu A10G

clean:
\trm -rf embeddings/
\trm -rf models/temp_*

# Quick validation
validate:
\tpython backend/datasets/validate_embeddings.py
'''
        
        makefile_path = Path("Makefile")
        with open(makefile_path, 'w') as f:
            f.write(makefile_content)
        
        logger.info(f"📋 Created {makefile_path} for automated handoff")

def main():
    """Main export function"""
    print("📊 PetPlantr Embedding Export for UNet Integration")
    print("=" * 55)
    
    # Initialize exporter
    exporter = EmbeddingExporter(
        model_path="./models/simple_m3_backbone_epoch_10.pt",
        data_dir="./data/oxford_simple"
    )
    
    # Export embeddings
    exported_files, metadata = exporter.export_all_splits()
    
    print("\n✅ EMBEDDING EXPORT COMPLETE!")
    print(f"📊 Files: {list(exported_files.keys())}")
    print(f"📏 Embedding dimension: {metadata['embedding_dim']}")
    print(f"📋 Metadata: {metadata['exported_files']}")
    
    # Upload to S3
    try:
        exporter.upload_to_s3()
        print("☁️  Embeddings uploaded to S3")
    except Exception as e:
        print(f"⚠️  S3 upload failed: {e}")
        print("💡 Run 'aws configure' if needed")
    
    # Create automation
    exporter.create_makefile_targets()
    
    print("\n🎯 READY FOR GPU HANDOFF!")
    print("📋 Next steps:")
    print("   1. Run: make prep-embeddings")
    print("   2. Run: make stage-1-unet")
    print("   3. Progressive complexity ladder")
    print("   4. Full Shape-MVD training")

if __name__ == "__main__":
    main()
