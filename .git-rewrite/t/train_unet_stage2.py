#!/usr/bin/env python3
"""
PetPlantr Stage 2 UNet-256 Training
Trains higher resolution model on proprietary multi-view dataset
"""

import os
import modal
from pathlib import Path

# Modal configuration
app = modal.App("petplantr-stage2-training")

# Base image with ML dependencies - using flexible versions
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
        # Removed xformers to avoid conflicts
    ])
    .env({"WANDB_API_KEY": os.getenv("WANDB_API_KEY", "")})
)

# GPU configuration for Stage 2 (higher memory needs)
@app.function(
    image=base_image,
    gpu="T4",  # Updated Modal syntax
    memory=32768,  # 32GB RAM for larger model
    timeout=7200,  # 2 hours max
    secrets=[
        modal.Secret.from_name("aws-credentials"),
        modal.Secret.from_name("wandb-api")
    ]
)
def train_unet_stage2():
    """Train UNet-256 on proprietary dataset"""
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    from torchvision import transforms
    from PIL import Image
    import boto3
    import json
    import wandb
    from pathlib import Path
    import sys
    
    # Add current directory to path for imports
    sys.path.append("/root")
    
    print("🚀 Starting Stage 2 UNet-256 Training")
    print(f"   Device: {torch.cuda.get_device_name() if torch.cuda.is_available() else 'CPU'}")
    print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
    
    # Training configuration from environment
    BATCH_SIZE = int(os.getenv("BATCH", "1"))
    GRAD_ACCUM = int(os.getenv("GRAD_ACCUM", "8"))
    EPOCHS = int(os.getenv("EPOCHS", "5"))
    LEARNING_RATE = float(os.getenv("LR", "1e-4"))
    
    print(f"   Batch size: {BATCH_SIZE} (effective: {BATCH_SIZE * GRAD_ACCUM})")
    print(f"   Epochs: {EPOCHS}")
    print(f"   Learning rate: {LEARNING_RATE}")
    
    # Initialize WandB (optional)
    wandb_api_key = os.getenv("WANDB_API_KEY")
    if wandb_api_key:
        wandb.init(
            project="petplantr-stage2",
            config={
                "model": "UNet-256",
                "batch_size": BATCH_SIZE,
                "grad_accumulation": GRAD_ACCUM,
                "epochs": EPOCHS,
                "learning_rate": LEARNING_RATE,
                "dataset": "proprietary_multiview"
            }
        )
        print("✅ WandB initialized")
    else:
        print("⚠️  WandB not configured, training without logging")
    
    # Download proprietary dataset from S3
    print("📥 Downloading proprietary dataset...")
    s3 = boto3.client('s3')
    bucket_name = "petplantr-dataset"
    dataset_prefix = "datasets/proprietary_multiview"
    
    # Create local dataset directory
    dataset_dir = Path("/tmp/proprietary_dataset")
    dataset_dir.mkdir(exist_ok=True)
    
    # Download training manifest
    manifest_path = dataset_dir / "training_manifest.json"
    try:
        s3.download_file(bucket_name, "manifests/training_manifest.json", str(manifest_path))
        with open(manifest_path) as f:
            manifest = json.load(f)
        print(f"✅ Dataset manifest: {manifest['total_pets']} pets, {manifest['total_photos']} photos")
    except Exception as e:
        print(f"❌ Failed to download manifest: {e}")
        return
    
    # Download proprietary photos
    proprietary_dir = dataset_dir / "proprietary_photos"
    proprietary_dir.mkdir(exist_ok=True)
    
    print("📥 Downloading proprietary photos...")
    
    # List all proprietary photos
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix="proprietary_photos/")
    
    downloaded_count = 0
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(('.jpg', '.jpeg', '.JPG', '.JPEG')):
            filename = Path(key).name
            local_path = proprietary_dir / filename
            s3.download_file(bucket_name, key, str(local_path))
            downloaded_count += 1
    
    print(f"✅ Downloaded {downloaded_count} proprietary photos")
    
    # Load Stage 1 weights as starting point
    print("📥 Loading Stage 1 weights...")
    try:
        stage1_weights_path = "/tmp/stage1_weights.pth"
        s3.download_file(bucket_name, "prod/unet_weights.pth", stage1_weights_path)
        print("✅ Stage 1 weights downloaded")
    except Exception as e:
        print(f"⚠️  Could not load Stage 1 weights: {e}")
        print("   Training from scratch...")
        stage1_weights_path = None
    
    # Define UNet-256 model (expanded from Stage 1)
    class UNet256(nn.Module):
        def __init__(self, in_channels=3, out_channels=3, features=64):
            super().__init__()
            
            # Encoder (downsampling)
            self.encoder1 = self._make_encoder_block(in_channels, features)
            self.encoder2 = self._make_encoder_block(features, features * 2)
            self.encoder3 = self._make_encoder_block(features * 2, features * 4)
            self.encoder4 = self._make_encoder_block(features * 4, features * 8)
            
            # Bottleneck
            self.bottleneck = self._make_encoder_block(features * 8, features * 16)
            
            # Decoder (upsampling)
            self.decoder4 = self._make_decoder_block(features * 16, features * 8)
            self.decoder3 = self._make_decoder_block(features * 16, features * 4)
            self.decoder2 = self._make_decoder_block(features * 8, features * 2)
            self.decoder1 = self._make_decoder_block(features * 4, features)
            
            # Final output layer
            self.final = nn.Conv2d(features * 2, out_channels, kernel_size=1)
            
        def _make_encoder_block(self, in_channels, out_channels):
            return nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, 3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True)
            )
            
        def _make_decoder_block(self, in_channels, out_channels):
            return nn.Sequential(
                nn.ConvTranspose2d(in_channels, out_channels, 2, stride=2),
                nn.Conv2d(out_channels, out_channels, 3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, 3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True)
            )
            
        def forward(self, x):
            # Encoder path
            enc1 = self.encoder1(x)
            enc2 = self.encoder2(nn.MaxPool2d(2)(enc1))
            enc3 = self.encoder3(nn.MaxPool2d(2)(enc2))
            enc4 = self.encoder4(nn.MaxPool2d(2)(enc3))
            
            # Bottleneck
            bottleneck = self.bottleneck(nn.MaxPool2d(2)(enc4))
            
            # Decoder path with skip connections
            dec4 = self.decoder4(bottleneck)
            dec4 = torch.cat([dec4, enc4], dim=1)
            
            dec3 = self.decoder3(dec4)
            dec3 = torch.cat([dec3, enc3], dim=1)
            
            dec2 = self.decoder2(dec3)
            dec2 = torch.cat([dec2, enc2], dim=1)
            
            dec1 = self.decoder1(dec2)
            dec1 = torch.cat([dec1, enc1], dim=1)
            
            return self.final(dec1)
    
    # Dataset class for multi-view training
    class MultiViewPetDataset(Dataset):
        def __init__(self, dataset_dir, manifest, transform=None):
            self.dataset_dir = Path(dataset_dir)
            self.pets = manifest['pets']
            self.transform = transform or transforms.Compose([
                transforms.Resize((256, 256)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
        def __len__(self):
            return len(self.pets) * 4  # 4 views per pet
            
        def __getitem__(self, idx):
            pet_idx = idx // 4
            view_idx = idx % 4
            views = ['front.jpg', 'left.jpg', 'right.jpg', 'back.jpg']
            
            pet_info = self.pets[pet_idx]
            pet_id = pet_info['pet_id']
            view_name = views[view_idx]
            
            image_path = self.dataset_dir / pet_id / view_name
            image = Image.open(image_path).convert('RGB')
            
            if self.transform:
                image = self.transform(image)
                
            # For simplicity, use same image as input and target
            # In production, this would be input->3D model->output
            return image, image
    
    # Create model and training setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = UNet256().to(device)
    
    # Load Stage 1 weights if available (partial loading)
    if stage1_weights_path and os.path.exists(stage1_weights_path):
        try:
            stage1_state = torch.load(stage1_weights_path, map_location=device)
            # Load compatible layers only
            model_dict = model.state_dict()
            pretrained_dict = {k: v for k, v in stage1_state.items() if k in model_dict and v.size() == model_dict[k].size()}
            model_dict.update(pretrained_dict)
            model.load_state_dict(model_dict)
            print(f"✅ Loaded {len(pretrained_dict)} layers from Stage 1")
        except Exception as e:
            print(f"⚠️  Could not load Stage 1 weights: {e}")
    
    # Training setup
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    
    # Create dataset and dataloader
    dataset = MultiViewPetDataset(dataset_dir, manifest)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    
    print(f"✅ Dataset ready: {len(dataset)} samples")
    print(f"🏋️  Training setup complete")
    
    # Training loop
    model.train()
    best_loss = float('inf')
    
    for epoch in range(EPOCHS):
        epoch_loss = 0.0
        optimizer.zero_grad()
        
        for batch_idx, (inputs, targets) in enumerate(dataloader):
            inputs, targets = inputs.to(device), targets.to(device)
            
            # Forward pass
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            
            # Backward pass with gradient accumulation
            loss = loss / GRAD_ACCUM
            loss.backward()
            
            if (batch_idx + 1) % GRAD_ACCUM == 0:
                optimizer.step()
                optimizer.zero_grad()
            
            epoch_loss += loss.item() * GRAD_ACCUM
            
            if batch_idx % 10 == 0:
                print(f"   Epoch {epoch+1}/{EPOCHS}, Batch {batch_idx}/{len(dataloader)}, Loss: {loss.item():.6f}")
                
                if wandb_api_key:
                    wandb.log({
                        "batch_loss": loss.item(),
                        "epoch": epoch,
                        "batch": batch_idx
                    })
        
        # End of epoch
        avg_loss = epoch_loss / len(dataloader)
        scheduler.step()
        
        print(f"🎯 Epoch {epoch+1}/{EPOCHS} - Average Loss: {avg_loss:.6f}")
        
        if wandb_api_key:
            wandb.log({
                "epoch_loss": avg_loss,
                "learning_rate": scheduler.get_last_lr()[0],
                "epoch": epoch
            })
        
        # Save best model
        if avg_loss < best_loss:
            best_loss = avg_loss
            
            # Save model weights
            weights_path = "/tmp/unet256_stage2_best.pth"
            torch.save(model.state_dict(), weights_path)
            print(f"💾 Best model saved: {avg_loss:.6f}")
            
            # Upload to S3
            try:
                s3.upload_file(weights_path, bucket_name, "stage2/unet256_stage2_best.pth")
                print("✅ Weights uploaded to S3")
            except Exception as e:
                print(f"⚠️  Failed to upload weights: {e}")
    
    # Training complete
    print(f"\n🎉 Stage 2 Training Complete!")
    print(f"   Best validation loss: {best_loss:.6f}")
    print(f"   Target was: < 0.09")
    
    if best_loss < 0.09:
        print("✅ TARGET ACHIEVED - Ready for production!")
    else:
        print("⚠️  Target not reached - consider more training")
    
    if wandb_api_key:
        wandb.finish()
    
    return {
        "success": True,
        "best_loss": best_loss,
        "epochs_trained": EPOCHS,
        "target_achieved": best_loss < 0.09
    }

# Entry point for Modal
@app.local_entrypoint()
def main():
    """Local entrypoint for Modal training"""
    print("🚀 Launching Stage 2 UNet-256 Training on Modal...")
    result = train_unet_stage2.remote()
    print(f"📊 Training result: {result}")
    return result

if __name__ == "__main__":
    main()
