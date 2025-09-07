#!/usr/bin/env python3
"""
PetPlantr Stage 2 UNet-256 Training - Simplified for Proprietary Photos Only
Trains higher resolution model on real proprietary dog photos
"""

import os
import modal
from pathlib import Path

# Modal configuration
app = modal.App("petplantr-stage2-simple")

# Base image with ML dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install(["git", "wget", "curl"])
    .pip_install([
        "torch>=2.0.0,<2.2.0",
        "torchvision>=0.15.0,<0.17.0", 
        "transformers>=4.30.0,<4.36.0",
        "diffusers>=0.20.0,<0.25.0",
        "accelerate>=0.20.0,<0.25.0",
        "wandb>=0.15.0",
        "pillow>=10.0.0",
        "numpy>=1.24.0,<1.25.0",
        "boto3>=1.34.0",
    ])
    .env({"WANDB_API_KEY": os.getenv("WANDB_API_KEY", "")})
)

# GPU configuration for Stage 2
@app.function(
    image=base_image,
    gpu="T4",
    memory=32768,  # 32GB RAM
    timeout=7200,  # 2 hours max
    secrets=[
        modal.Secret.from_name("aws-credentials"),
        modal.Secret.from_name("wandb-api")
    ]
)
def train_unet_stage2_simple():
    """Train UNet-256 on proprietary dataset only"""
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    from torchvision import transforms
    from PIL import Image
    import wandb
    import boto3
    import json
    import random
    from pathlib import Path
    import time
    from datetime import datetime
    
    # Initialize WandB
    wandb.init(
        project="petplantr-stage2",
        name="unet256_proprietary_only",
        config={
            "architecture": "UNet-256",
            "dataset": "proprietary_photos_only",
            "batch_size": 2,
            "learning_rate": 0.0001,
            "epochs": 5,
            "image_size": 256
        }
    )
    print("✅ WandB initialized")
    
    # Download proprietary photos directly
    print("📥 Downloading proprietary photos...")
    s3 = boto3.client('s3')
    bucket_name = "petplantr-dataset"
    
    dataset_dir = Path("/tmp/proprietary_photos")
    dataset_dir.mkdir(exist_ok=True)
    
    # Download all proprietary photos
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix="proprietary_photos/")
    
    photo_paths = []
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(('.jpg', '.jpeg', '.JPG', '.JPEG')):
            filename = Path(key).name
            local_path = dataset_dir / filename
            s3.download_file(bucket_name, key, str(local_path))
            photo_paths.append(local_path)
    
    print(f"✅ Downloaded {len(photo_paths)} proprietary photos")
    
    # Simple dataset class for proprietary photos
    class ProprietaryPhotoDataset(Dataset):
        def __init__(self, photo_paths, transform=None):
            self.photo_paths = photo_paths
            self.transform = transform
            
        def __len__(self):
            return len(self.photo_paths)
            
        def __getitem__(self, idx):
            image_path = self.photo_paths[idx]
            
            try:
                # Load image
                image = Image.open(image_path).convert('RGB')
                
                if self.transform:
                    image = self.transform(image)
                
                # For self-supervised learning, use the same image as input and target
                # In a real scenario, you'd have pairs of images or use different augmentations
                return image, image
                
            except Exception as e:
                print(f"Error loading {image_path}: {e}")
                # Return a random other image if this one fails
                alt_idx = random.randint(0, len(self.photo_paths) - 1)
                return self.__getitem__(alt_idx)
    
    # Define transforms
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Create dataset and dataloader
    dataset = ProprietaryPhotoDataset(photo_paths, transform=transform)
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True, num_workers=2)
    
    print(f"✅ Dataset ready: {len(dataset)} photos")
    
    # Simple UNet-256 model
    class SimpleUNet256(nn.Module):
        def __init__(self, in_channels=3, out_channels=3, features=64):
            super().__init__()
            
            # Encoder
            self.encoder1 = self._make_encoder_block(in_channels, features)
            self.encoder2 = self._make_encoder_block(features, features * 2)
            self.encoder3 = self._make_encoder_block(features * 2, features * 4)
            self.encoder4 = self._make_encoder_block(features * 4, features * 8)
            
            # Bottleneck
            self.bottleneck = self._make_encoder_block(features * 8, features * 16)
            
            # Decoder
            self.decoder4 = self._make_decoder_block(features * 16, features * 8)
            self.decoder3 = self._make_decoder_block(features * 8, features * 4)
            self.decoder2 = self._make_decoder_block(features * 4, features * 2)
            self.decoder1 = self._make_decoder_block(features * 2, features)
            
            # Final output
            self.final = nn.Conv2d(features, out_channels, kernel_size=1)
            
        def _make_encoder_block(self, in_channels, out_channels):
            return nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True)
            )
            
        def _make_decoder_block(self, in_channels, out_channels):
            return nn.Sequential(
                nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2),
                nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True)
            )
        
        def forward(self, x):
            # Encoder
            e1 = self.encoder1(x)
            e2 = self.encoder2(nn.MaxPool2d(2)(e1))
            e3 = self.encoder3(nn.MaxPool2d(2)(e2))
            e4 = self.encoder4(nn.MaxPool2d(2)(e3))
            
            # Bottleneck
            b = self.bottleneck(nn.MaxPool2d(2)(e4))
            
            # Decoder with skip connections
            d4 = self.decoder4(b) + e4
            d3 = self.decoder3(d4) + e3
            d2 = self.decoder2(d3) + e2
            d1 = self.decoder1(d2) + e1
            
            return torch.sigmoid(self.final(d1))
    
    # Initialize model, loss, and optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🔥 Using device: {device}")
    
    model = SimpleUNet256(in_channels=3, out_channels=3).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.0001)
    
    print("🏋️  Training setup complete")
    
    # Training loop
    model.train()
    total_batches = len(dataloader)
    
    for epoch in range(5):
        epoch_loss = 0.0
        epoch_start = time.time()
        
        for batch_idx, (inputs, targets) in enumerate(dataloader):
            inputs = inputs.to(device)
            targets = targets.to(device)
            
            # Forward pass
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
            # Log progress
            if batch_idx % 5 == 0:
                print(f"Epoch {epoch+1}/5, Batch {batch_idx+1}/{total_batches}, Loss: {loss.item():.6f}")
                wandb.log({
                    "batch_loss": loss.item(),
                    "epoch": epoch + 1,
                    "batch": batch_idx + 1
                })
        
        # Log epoch metrics
        avg_epoch_loss = epoch_loss / total_batches
        epoch_time = time.time() - epoch_start
        
        print(f"✅ Epoch {epoch+1}/5 complete - Avg Loss: {avg_epoch_loss:.6f}, Time: {epoch_time:.1f}s")
        
        wandb.log({
            "epoch_loss": avg_epoch_loss,
            "epoch_time": epoch_time,
            "epoch": epoch + 1
        })
    
    # Save model weights
    print("💾 Saving model weights...")
    weights_path = "/tmp/unet256_proprietary_weights.pth"
    torch.save(model.state_dict(), weights_path)
    
    # Upload to S3
    try:
        s3_weights_key = "models/unet256_stage2_proprietary.pth"
        s3.upload_file(weights_path, "petplantr-models", s3_weights_key)
        print(f"📤 Uploaded weights to s3://petplantr-models/{s3_weights_key}")
        
        wandb.log({"model_uploaded": True, "s3_key": s3_weights_key})
        
    except Exception as e:
        print(f"⚠️  Failed to upload weights: {e}")
        wandb.log({"model_uploaded": False, "upload_error": str(e)})
    
    print("🎉 Training completed successfully!")
    
    return {
        "status": "success",
        "epochs": 5,
        "total_photos": len(photo_paths),
        "final_loss": avg_epoch_loss,
        "model_path": s3_weights_key if 'e' not in locals() else None
    }

# Main function to run training
@app.local_entrypoint()
def main():
    print("🚀 Launching Stage 2 UNet-256 Training (Proprietary Photos Only)")
    result = train_unet_stage2_simple.remote()
    print(f"📊 Training result: {result}")

if __name__ == "__main__":
    main()
