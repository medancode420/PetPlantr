#!/usr/bin/env python3
"""
PetPlantr Stage 2 UNet-256 Training - Fixed Version
Trains directly on proprietary photos without complex manifest dependencies
"""

import os
import modal
from pathlib import Path

# Modal configuration
app = modal.App("petplantr-stage2-training-fixed")

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

@app.function(
    image=base_image,
    gpu="T4",
    memory=16384,  # 16GB RAM
    timeout=3600,  # 1 hour max
    secrets=[
        modal.Secret.from_name("aws-credentials"),
        modal.Secret.from_name("wandb-api")
    ]
)
def train_unet_stage2_fixed():
    """Train UNet-256 on proprietary dataset with simplified approach"""
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    from torchvision import transforms
    from PIL import Image
    import boto3
    import json
    import wandb
    import numpy as np
    from pathlib import Path
    import random

    print("🚀 Starting Stage 2 UNet-256 Training")
    print(f"   Device: {torch.cuda.get_device_name()}")
    print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Training configuration
    config = {
        'batch_size': 2,
        'learning_rate': 0.0001,
        'epochs': 5,
        'image_size': 256,
        'model_name': 'unet256_stage2'
    }
    
    print(f"   Batch size: {config['batch_size']}")
    print(f"   Epochs: {config['epochs']}")
    print(f"   Learning rate: {config['learning_rate']}")
    
    # Initialize WandB
    try:
        wandb.init(
            project="petplantr-stage2",
            config=config,
            name=f"unet256_fixed_{config['epochs']}epochs"
        )
        print("✅ WandB initialized")
    except Exception as e:
        print(f"⚠️  WandB failed: {e}")
    
    # Download dataset
    print("📥 Downloading proprietary dataset...")
    s3 = boto3.client('s3')
    bucket_name = "petplantr-dataset"
    
    dataset_dir = Path("/tmp/proprietary_dataset")
    dataset_dir.mkdir(exist_ok=True)
    
    # Download all proprietary photos
    photos_dir = dataset_dir / "photos"
    photos_dir.mkdir(exist_ok=True)
    
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix="proprietary_photos/")
    
    downloaded_photos = []
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(('.jpg', '.jpeg', '.JPG', '.JPEG')):
            filename = Path(key).name
            local_path = photos_dir / filename
            s3.download_file(bucket_name, key, str(local_path))
            downloaded_photos.append(str(local_path))
    
    print(f"✅ Downloaded {len(downloaded_photos)} proprietary photos")
    
    # Simple Dataset class for single images
    class SimplePhotoDataset(Dataset):
        def __init__(self, photo_paths, transform=None):
            self.photo_paths = photo_paths
            self.transform = transform
            
        def __len__(self):
            return len(self.photo_paths)
            
        def __getitem__(self, idx):
            img_path = self.photo_paths[idx]
            
            try:
                image = Image.open(img_path).convert('RGB')
                
                if self.transform:
                    image = self.transform(image)
                
                # For autoencoder training, input and target are the same
                return image, image
                
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                # Return a dummy tensor if image fails to load
                dummy = torch.zeros(3, 256, 256)
                return dummy, dummy
    
    # Data transforms
    transform = transforms.Compose([
        transforms.Resize((config['image_size'], config['image_size'])),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Create dataset and dataloader
    dataset = SimplePhotoDataset(downloaded_photos, transform=transform)
    dataloader = DataLoader(dataset, batch_size=config['batch_size'], shuffle=True, num_workers=0)
    
    print(f"✅ Dataset ready: {len(dataset)} samples")
    
    # Define simplified UNet-256 model
    class UNet256Simple(nn.Module):
        def __init__(self, in_channels=3, out_channels=3):
            super().__init__()
            
            # Encoder
            self.enc1 = self._conv_block(in_channels, 64)
            self.enc2 = self._conv_block(64, 128)
            self.enc3 = self._conv_block(128, 256)
            self.enc4 = self._conv_block(256, 512)
            
            # Bottleneck
            self.bottleneck = self._conv_block(512, 1024)
            
            # Decoder
            self.upconv4 = nn.ConvTranspose2d(1024, 512, 2, stride=2)
            self.dec4 = self._conv_block(1024, 512)
            
            self.upconv3 = nn.ConvTranspose2d(512, 256, 2, stride=2)
            self.dec3 = self._conv_block(512, 256)
            
            self.upconv2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
            self.dec2 = self._conv_block(256, 128)
            
            self.upconv1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
            self.dec1 = self._conv_block(128, 64)
            
            # Final layer
            self.final = nn.Conv2d(64, out_channels, 1)
            
        def _conv_block(self, in_ch, out_ch):
            return nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 3, padding=1),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_ch, out_ch, 3, padding=1),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True)
            )
            
        def forward(self, x):
            # Encoder
            enc1 = self.enc1(x)
            enc2 = self.enc2(nn.MaxPool2d(2)(enc1))
            enc3 = self.enc3(nn.MaxPool2d(2)(enc2))
            enc4 = self.enc4(nn.MaxPool2d(2)(enc3))
            
            # Bottleneck
            bottleneck = self.bottleneck(nn.MaxPool2d(2)(enc4))
            
            # Decoder with skip connections
            up4 = self.upconv4(bottleneck)
            merge4 = torch.cat([up4, enc4], dim=1)
            dec4 = self.dec4(merge4)
            
            up3 = self.upconv3(dec4)
            merge3 = torch.cat([up3, enc3], dim=1)
            dec3 = self.dec3(merge3)
            
            up2 = self.upconv2(dec3)
            merge2 = torch.cat([up2, enc2], dim=1)
            dec2 = self.dec2(merge2)
            
            up1 = self.upconv1(dec2)
            merge1 = torch.cat([up1, enc1], dim=1)
            dec1 = self.dec1(merge1)
            
            output = self.final(dec1)
            return torch.tanh(output)  # Output in [-1, 1] range
    
    # Initialize model
    model = UNet256Simple().to(device)
    criterion = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=config['learning_rate'], weight_decay=0.01)
    
    print("🏋️  Training setup complete")
    
    # Training loop
    model.train()
    total_loss = 0
    
    for epoch in range(config['epochs']):
        epoch_loss = 0
        
        for batch_idx, (inputs, targets) in enumerate(dataloader):
            inputs, targets = inputs.to(device), targets.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            total_loss += loss.item()
            
            if batch_idx % 5 == 0:
                print(f"Epoch {epoch+1}/{config['epochs']}, Batch {batch_idx}, Loss: {loss.item():.4f}")
                
                try:
                    wandb.log({
                        "epoch": epoch + 1,
                        "batch": batch_idx,
                        "loss": loss.item(),
                        "learning_rate": config['learning_rate']
                    })
                except:
                    pass
        
        avg_epoch_loss = epoch_loss / len(dataloader)
        print(f"✅ Epoch {epoch+1} complete - Average Loss: {avg_epoch_loss:.4f}")
        
        try:
            wandb.log({
                "epoch": epoch + 1,
                "epoch_loss": avg_epoch_loss
            })
        except:
            pass
    
    # Save model weights
    final_weights_path = "/tmp/unet256_stage2_final.pth"
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'config': config,
        'total_loss': total_loss,
        'epochs_trained': config['epochs']
    }, final_weights_path)
    
    print("💾 Model weights saved")
    
    # Upload to S3
    try:
        models_bucket = "petplantr-models"
        s3_key = f"models/unet256_stage2_final.pth"
        
        s3.upload_file(final_weights_path, models_bucket, s3_key)
        print(f"☁️  Weights uploaded to s3://{models_bucket}/{s3_key}")
        
        # Also upload as 'best' version
        s3_key_best = f"models/unet256_stage2_best.pth"
        s3.upload_file(final_weights_path, models_bucket, s3_key_best)
        print(f"☁️  Best weights uploaded to s3://{models_bucket}/{s3_key_best}")
        
    except Exception as e:
        print(f"⚠️  S3 upload failed: {e}")
    
    try:
        wandb.finish()
    except:
        pass
    
    print("🎉 Stage 2 training completed successfully!")
    
    return {
        "status": "success",
        "epochs": config['epochs'],
        "final_loss": total_loss / (len(dataloader) * config['epochs']),
        "model_path": f"s3://{models_bucket}/{s3_key}",
        "photos_trained": len(downloaded_photos)
    }

@app.local_entrypoint()
def main():
    print("🚀 Launching Stage 2 UNet-256 Training on Modal...")
    result = train_unet_stage2_fixed.remote()
    print(f"📊 Training result: {result}")

if __name__ == "__main__":
    main()
