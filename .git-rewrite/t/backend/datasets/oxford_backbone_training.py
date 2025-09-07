"""
PetPlantr Oxford-Only Backbone Pre-training on Modal
Streamlined training script for immediate backbone training

Cost: ~$0.60 for 45 minutes on T4 GPU
Output: s3://petplantr-models/backbone/oxford_pretrain.pt
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import modal
import boto3

# Modal app configuration
app = modal.App("petplantr-oxford-backbone")

# Cost-effective T4 GPU for backbone training
gpu_config = "T4"

# Lightweight Docker image
image = (modal.Image.debian_slim()
    .pip_install([
        "torch>=2.1.0",
        "torchvision>=0.16.0",
        "diffusers>=0.28.0",
        "transformers>=4.40.0", 
        "accelerate>=0.30.0",
        "huggingface_hub>=0.22.0",
        "opencv-python==4.9.0.80",
        "pillow==10.2.0",
        "numpy==1.26.3",
        "boto3==1.34.1",
        "tqdm>=4.65.0"
    ])
    .apt_install(["wget", "curl"])
)

# Persistent volume for model weights
volume = modal.Volume.from_name("petplantr-models", create_if_missing=True)

@app.function(
    image=image,
    gpu=gpu_config,
    volumes={"/models": volume},
    timeout=3600,  # 1 hour timeout
    memory=16384,   # 16GB RAM
    secrets=[modal.Secret.from_name("aws-petplantr")]
)
def train_oxford_backbone(
    s3_bucket: str = "petplantr-dataset",
    s3_prefix: str = "public/oxford_v37",
    output_bucket: str = "petplantr-models",
    epochs: int = 5,
    batch_size: int = 2,  # Aggressive reduction to 2 for memory efficiency
    learning_rate: float = 1e-4
):
    """Train backbone model on Oxford-IIIT enhanced dataset"""
    
    # Import dependencies inside Modal function
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import Dataset, DataLoader
    from torch.optim import AdamW
    from torch.optim.lr_scheduler import CosineAnnealingLR
    from torch.utils.checkpoint import checkpoint
    from transformers import CLIPImageProcessor, CLIPVisionModel
    from diffusers import UNet2DConditionModel, DDPMScheduler
    from PIL import Image
    import logging
    from tqdm import tqdm
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Oxford Backbone Pre-training")
    logger.info("=" * 50)
    logger.info(f"📊 Dataset: S3://{s3_bucket}/{s3_prefix}")
    logger.info(f"🖥️  GPU: {torch.cuda.get_device_name()}")
    logger.info(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
    logger.info(f"📦 Batch size: {batch_size} (optimized for T4)")
    
    # Enable memory optimization for T4 GPU
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    
    # Clear GPU cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("🧹 GPU cache cleared")
    
    # Download dataset from S3
    logger.info("📥 Downloading Oxford dataset from S3...")
    s3_client = boto3.client('s3')
    
    # Create local dataset directory
    os.makedirs("/tmp/oxford/training", exist_ok=True)
    os.makedirs("/tmp/oxford/validation", exist_ok=True)
    os.makedirs("/tmp/oxford/metadata", exist_ok=True)
    
    # Download training images
    response = s3_client.list_objects_v2(
        Bucket=s3_bucket,
        Prefix=f"{s3_prefix}/training/"
    )
    
    train_files = []
    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.jpg'):
            local_path = f"/tmp/oxford/training/{Path(obj['Key']).name}"
            s3_client.download_file(s3_bucket, obj['Key'], local_path)
            train_files.append(local_path)
    
    # Download validation images
    response = s3_client.list_objects_v2(
        Bucket=s3_bucket,
        Prefix=f"{s3_prefix}/validation/"
    )
    
    val_files = []
    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.jpg'):
            local_path = f"/tmp/oxford/validation/{Path(obj['Key']).name}"
            s3_client.download_file(s3_bucket, obj['Key'], local_path)
            val_files.append(local_path)
    
    logger.info(f"✅ Downloaded {len(train_files)} training, {len(val_files)} validation images")
    
    # Simple dataset class
    class OxfordDataset(Dataset):
        def __init__(self, image_files, transform=None):
            self.image_files = image_files
            self.processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
        def __len__(self):
            return len(self.image_files)
            
        def __getitem__(self, idx):
            img_path = self.image_files[idx]
            
            # Load and process image
            image = Image.open(img_path).convert('RGB')
            
            # CLIP preprocessing
            inputs = self.processor(images=image, return_tensors="pt")
            pixel_values = inputs.pixel_values.squeeze(0)
            
            # Extract breed from filename
            filename = Path(img_path).name
            breed = filename.split('_')[2] if len(filename.split('_')) > 2 else "unknown"
            
            return {
                'pixel_values': pixel_values,
                'breed': breed,
                'filename': filename
            }
    
    # Create datasets
    train_dataset = OxfordDataset(train_files)
    val_dataset = OxfordDataset(val_files)
    
    # Data loaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True,
        num_workers=2,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size // 2,  # Smaller batch for validation to save memory
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )
    
    logger.info(f"📊 Loaders: {len(train_loader)} train, {len(val_loader)} val batches")
    
    # Load pre-trained models
    logger.info("🔧 Loading pre-trained models...")
    
    # CLIP vision encoder
    vision_encoder = CLIPVisionModel.from_pretrained("openai/clip-vit-base-patch32")
    vision_encoder = vision_encoder.cuda()
    vision_encoder.eval()
    
    # UNet backbone for 3D reconstruction
    unet = UNet2DConditionModel.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        subfolder="unet"
    )
    unet = unet.cuda()
    
    # 🔧 MEMORY OPTIMIZATION: Enable gradient checkpointing (-30% VRAM)
    unet.enable_gradient_checkpointing()
    logger.info("✅ Gradient checkpointing enabled for UNet")
    
    # Noise scheduler
    scheduler = DDPMScheduler.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        subfolder="scheduler"
    )
    
    logger.info("✅ Models loaded successfully")
    
    # Optimizer
    optimizer = AdamW(unet.parameters(), lr=learning_rate, weight_decay=0.01)
    lr_scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=learning_rate/10)
    
    # Training loop
    logger.info("🚀 Starting backbone training...")
    
    best_val_loss = float('inf')
    
    # Gradient accumulation to simulate larger batch size
    accumulation_steps = 4  # Effective batch size = 8 * 4 = 32
    logger.info(f"📊 Gradient accumulation: {accumulation_steps} steps (effective batch size: {batch_size * accumulation_steps})")
    
    for epoch in range(epochs):
        # Training phase
        unet.train()
        train_loss = 0.0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
        
        for batch_idx, batch in enumerate(pbar):
            pixel_values = batch['pixel_values'].cuda()
            
            # Encode images to latent space
            with torch.no_grad():
                vision_outputs = vision_encoder(pixel_values=pixel_values)
                image_embeddings = vision_outputs.last_hidden_state
            
            # Convert RGB to RGBA for UNet (add alpha channel)
            if pixel_values.shape[1] == 3:  # RGB
                alpha_channel = torch.ones(pixel_values.shape[0], 1, pixel_values.shape[2], pixel_values.shape[3], 
                                         device=pixel_values.device, dtype=pixel_values.dtype)
                rgba_images = torch.cat([pixel_values, alpha_channel], dim=1)
            else:
                rgba_images = pixel_values
            
            # Add noise for denoising training (use RGBA images, not embeddings)
            noise = torch.randn_like(rgba_images)
            timesteps = torch.randint(0, scheduler.config.num_train_timesteps, 
                                    (pixel_values.shape[0],), device=pixel_values.device)
            
            noisy_images = scheduler.add_noise(rgba_images, noise, timesteps)
            
            # Predict noise (use RGBA images as input, embeddings as conditioning)
            noise_pred = unet(
                sample=noisy_images,
                timestep=timesteps,
                encoder_hidden_states=image_embeddings
            ).sample
            
            # Calculate loss
            loss = F.mse_loss(noise_pred, noise)
            
            # Scale loss for gradient accumulation
            loss = loss / accumulation_steps
            
            # Backward pass
            loss.backward()
            
            # Gradient accumulation
            if (batch_idx + 1) % accumulation_steps == 0:
                torch.nn.utils.clip_grad_norm_(unet.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad()
                
                # Clear GPU cache periodically
                if (batch_idx + 1) % (accumulation_steps * 4) == 0:
                    torch.cuda.empty_cache()
            
            train_loss += loss.item() * accumulation_steps  # Un-scale for logging
            
            # Update progress bar
            pbar.set_postfix({
                'Loss': f"{loss.item():.4f}",
                'Avg': f"{train_loss/(batch_idx+1):.4f}",
                'LR': f"{optimizer.param_groups[0]['lr']:.2e}"
            })
        
        # Final gradient step if needed
        if len(train_loader) % accumulation_steps != 0:
            torch.nn.utils.clip_grad_norm_(unet.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad()
        
        avg_train_loss = train_loss / len(train_loader)
        
        # Clear GPU cache after training phase
        torch.cuda.empty_cache()
        
        # Validation phase
        unet.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                pixel_values = batch['pixel_values'].cuda()
                
                vision_outputs = vision_encoder(pixel_values=pixel_values)
                image_embeddings = vision_outputs.last_hidden_state
                
                # Convert RGB to RGBA for UNet (add alpha channel)
                if pixel_values.shape[1] == 3:  # RGB
                    alpha_channel = torch.ones(pixel_values.shape[0], 1, pixel_values.shape[2], pixel_values.shape[3], 
                                             device=pixel_values.device, dtype=pixel_values.dtype)
                    rgba_images = torch.cat([pixel_values, alpha_channel], dim=1)
                else:
                    rgba_images = pixel_values
                
                noise = torch.randn_like(rgba_images)
                timesteps = torch.randint(0, scheduler.config.num_train_timesteps,
                                        (pixel_values.shape[0],), device=pixel_values.device)
                
                noisy_images = scheduler.add_noise(rgba_images, noise, timesteps)
                noise_pred = unet(
                    sample=noisy_images,
                    timestep=timesteps,
                    encoder_hidden_states=image_embeddings
                ).sample
                
                loss = F.mse_loss(noise_pred, noise)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader)
        
        # Update learning rate
        lr_scheduler.step()
        
        # Log epoch results
        logger.info(f"Epoch {epoch+1}/{epochs}: Train={avg_train_loss:.4f}, Val={avg_val_loss:.4f}")
        
        # Save checkpoint if best validation loss
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            
            checkpoint = {
                'epoch': epoch + 1,
                'unet_state_dict': unet.state_dict(),
                'vision_encoder_state_dict': vision_encoder.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': avg_train_loss,
                'val_loss': avg_val_loss,
                'config': {
                    'model_type': 'oxford_backbone',
                    'epochs': epochs,
                    'batch_size': batch_size,
                    'learning_rate': learning_rate,
                    'dataset_size': len(train_files),
                    'validation_size': len(val_files)
                }
            }
            
            torch.save(checkpoint, f"/models/oxford_pretrain_best.pt")
            logger.info(f"✅ Best checkpoint saved at epoch {epoch+1}")
    
    # Save final model
    final_checkpoint = {
        'epoch': epochs,
        'unet_state_dict': unet.state_dict(),
        'vision_encoder_state_dict': vision_encoder.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'train_loss': avg_train_loss,
        'val_loss': avg_val_loss,
        'config': {
            'model_type': 'oxford_backbone',
            'epochs': epochs,
            'batch_size': batch_size,
            'learning_rate': learning_rate,
            'dataset_size': len(train_files),
            'validation_size': len(val_files)
        }
    }
    
    torch.save(final_checkpoint, f"/models/oxford_pretrain.pt")
    logger.info("✅ Final backbone saved")
    
    # Upload to S3
    try:
        # Upload best model
        s3_client.upload_file(
            "/models/oxford_pretrain_best.pt",
            output_bucket,
            "backbone/oxford_pretrain_best.pt"
        )
        
        # Upload final model
        s3_client.upload_file(
            "/models/oxford_pretrain.pt", 
            output_bucket,
            "backbone/oxford_pretrain.pt"
        )
        
        logger.info("✅ Backbone models uploaded to S3")
        logger.info(f"📍 Location: s3://{output_bucket}/backbone/oxford_pretrain.pt")
        
    except Exception as e:
        logger.warning(f"⚠️ S3 upload failed: {e}")
    
    logger.info("🎉 Oxford Backbone Pre-training Completed!")
    logger.info(f"   Final train loss: {avg_train_loss:.4f}")
    logger.info(f"   Final val loss: {avg_val_loss:.4f}")
    logger.info(f"   Best val loss: {best_val_loss:.4f}")
    
    return {
        "status": "success",
        "final_train_loss": avg_train_loss,
        "final_val_loss": avg_val_loss,
        "best_val_loss": best_val_loss,
        "epochs_completed": epochs,
        "model_s3_path": f"s3://{output_bucket}/backbone/oxford_pretrain.pt"
    }

@app.local_entrypoint()
def start_oxford_training():
    """Start Oxford backbone pre-training"""
    
    print("🚀 Starting Oxford Backbone Pre-training")
    print("=" * 50)
    print("📊 Dataset: 150 images (113 train, 37 val)")
    print("🏷️  Breeds: 37 (cats & dogs)")
    print("🖥️  GPU: T4 (cost-effective)")
    print("💰 Estimated Cost: ~$0.60")
    print("⏱️  Duration: ~45 minutes")
    print("")
    print("🎯 Output: s3://petplantr-models/backbone/oxford_pretrain.pt")
    print("")
    
    # Start training
    result = train_oxford_backbone.remote()
    print(f"✅ Training result: {result}")

if __name__ == "__main__":
    start_oxford_training()
