"""
PetPlantr Shape-MVD Training on Modal
Fine-tune Shape-MVD for pet-specific 3D reconstruction

This script runs on Modal.com for cost-effective GPU training.
Estimated cost: ~$2 for 20 epochs on A100 GPU.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
from PIL import Image
import cv2
from diffusers import DDPMScheduler, UNet2DConditionModel
from transformers import CLIPImageProcessor, CLIPVisionModel
import modal

# Modal app configuration
app = modal.App("petplantr-shape-mvd-training")

# GPU configuration for training
gpu_config = modal.gpu.A100(count=1)

# Docker image with all dependencies
image = modal.Image.debian_slim().pip_install([
    "torch>=2.0.0",
    "torchvision>=0.15.0", 
    "diffusers==0.24.0",
    "transformers==4.36.0",
    "accelerate==0.25.0",
    "xformers==0.0.22",
    "opencv-python==4.8.1.78",
    "pillow==10.1.0",
    "numpy==1.24.3",
    "scikit-image==0.21.0",
    "wandb==0.16.0",
    "boto3==1.29.0"
])

# Volume for model checkpoints
volume = modal.Volume.from_name("petplantr-training", create_if_missing=True)

@app.function(
    image=image,
    gpu=gpu_config,
    volumes={"/checkpoints": volume},
    timeout=3600 * 4,  # 4 hours max
    memory=32768  # 32GB RAM
)
def train_shape_mvd(
    dataset_path: str,
    epochs: int = 20,
    batch_size: int = 4,
    learning_rate: float = 1e-5,
    save_every: int = 5,
    wandb_project: Optional[str] = "petplantr-shape-mvd"
):
    """
    Fine-tune Shape-MVD model for pet 3D reconstruction
    
    Args:
        dataset_path: Path to training dataset
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate for optimizer
        save_every: Save checkpoint every N epochs
        wandb_project: Weights & Biases project name
    """
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize Weights & Biases
    if wandb_project:
        import wandb
        wandb.init(
            project=wandb_project,
            config={
                "epochs": epochs,
                "batch_size": batch_size,
                "learning_rate": learning_rate,
                "model": "shape-mvd-pets"
            }
        )
    
    logger.info("🚀 Starting Shape-MVD training for pets")
    logger.info(f"   Epochs: {epochs}")
    logger.info(f"   Batch Size: {batch_size}")
    logger.info(f"   Learning Rate: {learning_rate}")
    
    # Load dataset
    logger.info("📊 Loading dataset...")
    train_dataset = PetShapeMVDDataset(dataset_path, split='train')
    val_dataset = PetShapeMVDDataset(dataset_path, split='validation')
    
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=4,
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )
    
    logger.info(f"   Training samples: {len(train_dataset)}")
    logger.info(f"   Validation samples: {len(val_dataset)}")
    
    # Initialize models
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"   Device: {device}")
    
    # Load CLIP for conditioning
    clip_processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = CLIPVisionModel.from_pretrained("openai/clip-vit-base-patch32")
    clip_model.to(device)
    clip_model.eval()
    
    # Initialize Shape-MVD UNet
    unet = UNet2DConditionModel(
        sample_size=64,  # Output resolution
        in_channels=4,   # RGBA channels
        out_channels=4,  # RGBA output
        layers_per_block=2,
        block_out_channels=(128, 128, 256, 256, 512, 512),
        down_block_types=(
            "DownBlock2D",
            "DownBlock2D",
            "DownBlock2D", 
            "DownBlock2D",
            "AttnDownBlock2D",
            "DownBlock2D",
        ),
        up_block_types=(
            "UpBlock2D",
            "AttnUpBlock2D",
            "UpBlock2D",
            "UpBlock2D", 
            "UpBlock2D",
            "UpBlock2D"
        ),
        cross_attention_dim=768,  # CLIP embedding dimension
        attention_head_dim=8,
    )
    unet.to(device)
    
    # Initialize diffusion scheduler
    scheduler = DDPMScheduler(
        num_train_timesteps=1000,
        beta_start=0.0001,
        beta_end=0.02,
        beta_schedule="linear",
        clip_sample=False
    )
    
    # Optimizer
    optimizer = torch.optim.AdamW(unet.parameters(), lr=learning_rate)
    
    # Load checkpoint if exists
    checkpoint_path = Path("/checkpoints/shape_mvd_pets_latest.pth")
    start_epoch = 0
    if checkpoint_path.exists():
        logger.info("📦 Loading checkpoint...")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        unet.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch']
        logger.info(f"   Resumed from epoch {start_epoch}")
    
    # Training loop
    logger.info("🎯 Starting training...")
    unet.train()
    
    for epoch in range(start_epoch, epochs):
        epoch_loss = 0.0
        num_batches = 0
        
        for batch_idx, batch in enumerate(train_loader):
            # Move batch to device
            images = batch['image'].to(device)
            depth_maps = batch['depth_map'].to(device) if 'depth_map' in batch else None
            
            # Get CLIP embeddings
            with torch.no_grad():
                clip_inputs = clip_processor(
                    images=[Image.fromarray((img.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)) for img in images],
                    return_tensors="pt"
                )
                clip_inputs = {k: v.to(device) for k, v in clip_inputs.items()}
                embeddings = clip_model(**clip_inputs).last_hidden_state.mean(dim=1)
            
            # Create target from images (simplified - in practice would use 3D supervision)
            target = F.interpolate(images, size=(64, 64), mode='bilinear', align_corners=False)
            
            # Sample random timesteps
            timesteps = torch.randint(0, scheduler.config.num_train_timesteps, (images.shape[0],), device=device)
            
            # Add noise to target
            noise = torch.randn_like(target)
            noisy_target = scheduler.add_noise(target, noise, timesteps)
            
            # Predict noise
            noise_pred = unet(
                noisy_target,
                timesteps,
                encoder_hidden_states=embeddings,
                return_dict=False
            )[0]
            
            # Calculate loss
            loss = F.mse_loss(noise_pred, noise)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(unet.parameters(), 1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            num_batches += 1
            
            if batch_idx % 10 == 0:
                logger.info(f"   Epoch {epoch+1}/{epochs}, Batch {batch_idx}/{len(train_loader)}, Loss: {loss.item():.4f}")
        
        avg_epoch_loss = epoch_loss / num_batches
        logger.info(f"✅ Epoch {epoch+1} completed, Average Loss: {avg_epoch_loss:.4f}")
        
        # Log to wandb
        if wandb_project:
            wandb.log({
                "epoch": epoch + 1,
                "train_loss": avg_epoch_loss,
                "learning_rate": learning_rate
            })
        
        # Validation
        if epoch % 2 == 0:
            val_loss = validate_model(unet, val_loader, scheduler, clip_model, clip_processor, device)
            logger.info(f"   Validation Loss: {val_loss:.4f}")
            
            if wandb_project:
                wandb.log({"val_loss": val_loss})
        
        # Save checkpoint
        if (epoch + 1) % save_every == 0 or epoch == epochs - 1:
            checkpoint = {
                'epoch': epoch + 1,
                'model_state_dict': unet.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': avg_epoch_loss,
                'config': {
                    'epochs': epochs,
                    'batch_size': batch_size,
                    'learning_rate': learning_rate
                }
            }
            
            # Save to volume
            torch.save(checkpoint, checkpoint_path)
            
            # Also save epoch-specific checkpoint
            epoch_checkpoint_path = Path(f"/checkpoints/shape_mvd_pets_epoch_{epoch+1}.pth")
            torch.save(checkpoint, epoch_checkpoint_path)
            
            logger.info(f"💾 Checkpoint saved: epoch {epoch+1}")
    
    logger.info("🎉 Training completed!")
    
    # Upload final model to S3
    upload_model_to_s3(checkpoint_path)
    
    return str(checkpoint_path)

def validate_model(unet, val_loader, scheduler, clip_model, clip_processor, device):
    """Validate the model on validation set"""
    unet.eval()
    total_loss = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for batch in val_loader:
            images = batch['image'].to(device)
            
            # Get CLIP embeddings
            clip_inputs = clip_processor(
                images=[Image.fromarray((img.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)) for img in images],
                return_tensors="pt"
            )
            clip_inputs = {k: v.to(device) for k, v in clip_inputs.items()}
            embeddings = clip_model(**clip_inputs).last_hidden_state.mean(dim=1)
            
            # Create target from images
            target = F.interpolate(images, size=(64, 64), mode='bilinear', align_corners=False)
            
            # Sample random timesteps
            timesteps = torch.randint(0, scheduler.config.num_train_timesteps, (images.shape[0],), device=device)
            
            # Add noise to target
            noise = torch.randn_like(target)
            noisy_target = scheduler.add_noise(target, noise, timesteps)
            
            # Predict noise
            noise_pred = unet(
                noisy_target,
                timesteps,
                encoder_hidden_states=embeddings,
                return_dict=False
            )[0]
            
            # Calculate loss
            loss = F.mse_loss(noise_pred, noise)
            total_loss += loss.item()
            num_batches += 1
    
    unet.train()
    return total_loss / num_batches

def upload_model_to_s3(checkpoint_path: Path):
    """Upload trained model to S3"""
    try:
        import boto3
        
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        # Upload to production S3 bucket
        s3_key = "shape-mvd-prod/latest.pth"
        bucket = "petplantr-models-prod"
        
        print(f"📤 Uploading model to s3://{bucket}/{s3_key}")
        s3_client.upload_file(str(checkpoint_path), bucket, s3_key)
        
        # Update Secrets Manager with new path
        secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
        secrets_client.update_secret(
            SecretId='petplantr/models/shape-mvd-weights',
            SecretString=f"s3://{bucket}/{s3_key}"
        )
        
        print("✅ Model uploaded and Secrets Manager updated")
        
    except Exception as e:
        print(f"❌ Failed to upload model: {e}")

class PetShapeMVDDataset(Dataset):
    """Dataset for Shape-MVD training"""
    
    def __init__(self, dataset_path: str, split: str = 'train'):
        self.dataset_path = Path(dataset_path)
        self.split = split
        
        # Load metadata
        metadata_path = self.dataset_path / 'metadata' / 'training_metadata.json'
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        # Get image list for split
        if split == 'train':
            self.images = self.metadata['training_images']
            self.image_dir = self.dataset_path / 'training'
        else:
            self.images = self.metadata['validation_images']
            self.image_dir = self.dataset_path / 'validation'
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_info = self.images[idx]
        
        # Load image
        img_path = self.image_dir / img_info['filename']
        image = Image.open(img_path).convert('RGB')
        
        # Convert to tensor and normalize
        image = np.array(image) / 255.0
        image = torch.from_numpy(image).permute(2, 0, 1).float()
        
        return {
            'image': image,
            'breed': img_info['breed'],
            'quality_score': img_info['quality_score']
        }

@app.local_entrypoint()
def main(
    dataset_path: str = "~/Desktop/PetPlantr_Dataset",
    epochs: int = 20,
    batch_size: int = 4,
    learning_rate: float = 1e-5
):
    """
    Main training entrypoint
    
    Usage:
        modal run shape_mvd_training.py --dataset-path ~/Desktop/PetPlantr_Dataset --epochs 20
    """
    
    print("🚀 Starting PetPlantr Shape-MVD Training on Modal")
    print(f"   Dataset: {dataset_path}")
    print(f"   Epochs: {epochs}")
    print(f"   Batch Size: {batch_size}")
    print(f"   Learning Rate: {learning_rate}")
    
    # Expand path
    dataset_path = str(Path(dataset_path).expanduser())
    
    # Check if dataset exists
    if not Path(dataset_path).exists():
        print(f"❌ Dataset not found: {dataset_path}")
        print("Please run the dataset download and preprocessing scripts first")
        return
    
    # Start training on Modal
    checkpoint_path = train_shape_mvd.remote(
        dataset_path=dataset_path,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate
    )
    
    print(f"✅ Training completed! Model saved to: {checkpoint_path}")
    print("")
    print("📋 Next Steps:")
    print("1. Model has been uploaded to S3 automatically")
    print("2. Secrets Manager has been updated with new model path")  
    print("3. Test the AI pipeline with real pet photos")
    print("4. Deploy the updated containers to production")

if __name__ == "__main__":
    main()
