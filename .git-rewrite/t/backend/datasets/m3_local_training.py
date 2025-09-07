"""
PetPlantr M3 Max Local Training Script
Optimized for Apple Silicon M3 Max with 128GB unified memory

Advantages:
- 128GB unified memory (vs 15.6GB VRAM on T4)
- Zero additional cost
- Instant debugging and iteration
- Native Apple Silicon PyTorch support

Usage: python m3_local_training.py
"""

import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from transformers import CLIPVisionModel, CLIPImageProcessor
from diffusers import UNet2DConditionModel, DDPMScheduler
from PIL import Image
import boto3
from pathlib import Path
import logging
from datetime import datetime
from tqdm import tqdm
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedPetDataset(Dataset):
    """Optimized dataset for M3 Max training"""
    
    def __init__(self, images_dir: str, split: str = "train"):
        self.images_dir = Path(images_dir)
        self.split = split
        
        # Load image paths
        self.image_paths = []
        split_dir = self.images_dir / split
        if split_dir.exists():
            for img_path in split_dir.glob("*.jpg"):
                self.image_paths.append(img_path)
        
        logger.info(f"Loaded {len(self.image_paths)} images for {split}")
        
        # Optimized transforms for M3 Max
        self.transform = transforms.Compose([
            transforms.Resize((512, 512)),  # Standard diffusion resolution
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5])  # Normalize to [-1, 1]
        ])
        
        # CLIP processor
        self.processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        
        # Load and process image
        image = Image.open(img_path).convert('RGB')
        
        # For UNet (RGBA with alpha channel)
        pixel_values = self.transform(image)
        # Add alpha channel (all ones for solid opacity)
        alpha_channel = torch.ones(1, pixel_values.shape[1], pixel_values.shape[2])
        pixel_values = torch.cat([pixel_values, alpha_channel], dim=0)
        
        # For CLIP encoder (RGB)
        clip_inputs = self.processor(images=image, return_tensors="pt")
        clip_pixel_values = clip_inputs["pixel_values"].squeeze(0)
        
        return {
            "pixel_values": pixel_values,
            "clip_pixel_values": clip_pixel_values,
            "image_path": str(img_path)
        }

class M3TrainingPipeline:
    """Optimized training pipeline for M3 Max"""
    
    def __init__(self, 
                 data_dir: str,
                 output_dir: str = "./models",
                 batch_size: int = 4,  # Reduced batch size for stability
                 learning_rate: float = 1e-5,  # Lower learning rate for stability
                 num_epochs: int = 3):  # Fewer epochs for faster iteration
        
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Training config optimized for M3 Max
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        
        # Use MPS (Metal Performance Shaders) for M3 Max
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
            logger.info("🍎 Using Apple M3 Max MPS acceleration")
        else:
            self.device = torch.device("cpu")
            logger.info("⚠️  MPS not available, using CPU")
        
        self._setup_models()
        self._setup_data()
    
    def _setup_models(self):
        """Initialize models optimized for M3 Max"""
        logger.info("🧠 Loading models...")
        
        # Vision encoder (frozen)
        self.vision_encoder = CLIPVisionModel.from_pretrained("openai/clip-vit-base-patch32")
        self.vision_encoder.eval()
        self.vision_encoder.requires_grad_(False)
        self.vision_encoder.to(self.device)
        
        # UNet for denoising (trainable)
        self.unet = UNet2DConditionModel.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            subfolder="unet",
            torch_dtype=torch.float32  # Use float32 for M3 Max
        )
        self.unet.to(self.device)
        
        # Noise scheduler
        self.scheduler = DDPMScheduler.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            subfolder="scheduler"
        )
        
        # Optimizer optimized for Apple Silicon
        self.optimizer = optim.AdamW(
            self.unet.parameters(),
            lr=self.learning_rate,
            weight_decay=0.01,
            eps=1e-8
        )
        
        logger.info(f"✅ Models loaded to {self.device}")
    
    def _setup_data(self):
        """Setup data loaders"""
        # Training dataset
        train_dataset = OptimizedPetDataset(str(self.data_dir), "train")
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=2,  # Reduced workers to avoid memory issues
            pin_memory=False  # Not needed for MPS
        )
        
        # Validation dataset
        val_dataset = OptimizedPetDataset(str(self.data_dir), "val")
        self.val_loader = DataLoader(
            val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=2,
            pin_memory=False
        )
        
        logger.info(f"📊 Train: {len(train_dataset)}, Val: {len(val_dataset)}")
    
    def train_epoch(self, epoch: int):
        """Train one epoch"""
        self.unet.train()
        total_loss = 0
        
        progress_bar = tqdm(self.train_loader, desc=f"Epoch {epoch+1}/{self.num_epochs}")
        
        for step, batch in enumerate(progress_bar):
            try:
                # Move to device
                pixel_values = batch["pixel_values"].to(self.device)
                clip_pixel_values = batch["clip_pixel_values"].to(self.device)
                
                # Get image embeddings from CLIP
                with torch.no_grad():
                    image_embeddings = self.vision_encoder(clip_pixel_values).last_hidden_state
                
                # Add noise to images
                noise = torch.randn_like(pixel_values)
                timesteps = torch.randint(
                    0, self.scheduler.config.num_train_timesteps, 
                    (pixel_values.shape[0],), 
                    device=self.device
                )
                noisy_images = self.scheduler.add_noise(pixel_values, noise, timesteps)
                
                # Predict noise
                noise_pred = self.unet(
                    noisy_images,
                    timesteps,
                    encoder_hidden_states=image_embeddings
                ).sample
                
                # Compute loss
                loss = nn.functional.mse_loss(noise_pred, noise)
                
                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                
                # Gradient clipping for stability
                torch.nn.utils.clip_grad_norm_(self.unet.parameters(), max_norm=1.0)
                
                self.optimizer.step()
                
                total_loss += loss.item()
                progress_bar.set_postfix({"loss": f"{loss.item():.4f}"})
                
                # Memory cleanup every few steps
                if step % 5 == 0:
                    if self.device.type == "mps":
                        torch.mps.empty_cache()
                        
            except RuntimeError as e:
                logger.error(f"Runtime error at step {step}: {e}")
                # Skip this batch and continue
                continue
        
        avg_loss = total_loss / len(self.train_loader)
        logger.info(f"📈 Epoch {epoch+1} - Average Loss: {avg_loss:.4f}")
        return avg_loss
    
    def validate(self):
        """Run validation"""
        self.unet.eval()
        total_loss = 0
        
        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc="Validation"):
                pixel_values = batch["pixel_values"].to(self.device)
                clip_pixel_values = batch["clip_pixel_values"].to(self.device)
                
                # Get image embeddings
                image_embeddings = self.vision_encoder(clip_pixel_values).last_hidden_state
                
                # Add noise and predict
                noise = torch.randn_like(pixel_values)
                timesteps = torch.randint(
                    0, self.scheduler.config.num_train_timesteps,
                    (pixel_values.shape[0],),
                    device=self.device
                )
                noisy_images = self.scheduler.add_noise(pixel_values, noise, timesteps)
                
                noise_pred = self.unet(
                    noisy_images,
                    timesteps,
                    encoder_hidden_states=image_embeddings
                ).sample
                
                loss = nn.functional.mse_loss(noise_pred, noise)
                total_loss += loss.item()
        
        avg_loss = total_loss / len(self.val_loader)
        logger.info(f"🧪 Validation Loss: {avg_loss:.4f}")
        return avg_loss
    
    def save_model(self, epoch: int, loss: float):
        """Save model checkpoint"""
        checkpoint = {
            "epoch": epoch,
            "unet_state_dict": self.unet.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "loss": loss,
            "timestamp": datetime.now().isoformat()
        }
        
        checkpoint_path = self.output_dir / f"m3_backbone_epoch_{epoch+1}.pt"
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"💾 Model saved: {checkpoint_path}")
        
        return checkpoint_path
    
    def train(self):
        """Main training loop"""
        logger.info("🚀 Starting M3 Max training...")
        logger.info(f"🖥️  Device: {self.device}")
        logger.info(f"📊 Batch size: {self.batch_size}")
        logger.info(f"🔄 Epochs: {self.num_epochs}")
        
        best_val_loss = float('inf')
        
        for epoch in range(self.num_epochs):
            # Train
            train_loss = self.train_epoch(epoch)
            
            # Validate
            val_loss = self.validate()
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_path = self.save_model(epoch, val_loss)
                logger.info(f"🏆 New best model saved!")
        
        logger.info("✅ Training completed!")
        return best_path

def download_dataset_local():
    """Download dataset from S3 to local storage"""
    logger.info("📥 Downloading dataset from S3...")
    
    # Create local data directory
    data_dir = Path("./data/oxford_local")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup S3 client
    s3 = boto3.client('s3')
    bucket = "petplantr-dataset"
    
    # Download training images
    train_dir = data_dir / "train"
    train_dir.mkdir(exist_ok=True)
    
    # List and download training images
    train_objects = s3.list_objects_v2(
        Bucket=bucket,
        Prefix="public/oxford_v37/training/"
    )
    
    if 'Contents' in train_objects:
        for obj in tqdm(train_objects['Contents'], desc="Downloading training images"):
            if obj['Key'].endswith('.jpg'):
                local_path = train_dir / Path(obj['Key']).name
                s3.download_file(bucket, obj['Key'], str(local_path))
    
    # Download validation images
    val_dir = data_dir / "val"
    val_dir.mkdir(exist_ok=True)
    
    val_objects = s3.list_objects_v2(
        Bucket=bucket,
        Prefix="public/oxford_v37/validation/"
    )
    
    if 'Contents' in val_objects:
        for obj in tqdm(val_objects['Contents'], desc="Downloading validation images"):
            if obj['Key'].endswith('.jpg'):
                local_path = val_dir / Path(obj['Key']).name
                s3.download_file(bucket, obj['Key'], str(local_path))
    
    logger.info(f"✅ Dataset downloaded to {data_dir}")
    return str(data_dir)

def main():
    """Main training function"""
    print("🍎 PetPlantr M3 Max Local Training")
    print("=" * 40)
    
    # Download dataset
    data_dir = download_dataset_local()
    
    # Initialize training pipeline
    pipeline = M3TrainingPipeline(
        data_dir=data_dir,
        batch_size=16,  # Larger batch size for M3 Max
        learning_rate=1e-4,
        num_epochs=5
    )
    
    # Train model
    best_model_path = pipeline.train()
    
    print(f"🎉 Training completed! Best model: {best_model_path}")

if __name__ == "__main__":
    main()
