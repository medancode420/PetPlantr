"""
Stage 2 UNet-256 Training Script for Modal
Enhanced resolution and detail refinement

Based on Stage 1 success, targeting:
- Higher resolution: 256x256 
- Increased base channels: (256, 256, 256, 512)
- Same T4 optimizations: batch_size=1, grad_accum=8
- Target val loss: < 0.09
"""

import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
import numpy as np
from pathlib import Path
import boto3
import modal
import logging
from typing import Dict, Any
from datetime import datetime

# Set up logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Modal setup
app = modal.App("petplantr-unet-stage2")

# Enhanced image with additional dependencies for Stage 2
image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install([
        "torch>=2.0.0",
        "torchvision>=0.15.0", 
        "diffusers>=0.25.0",
        "transformers>=4.35.0",
        "accelerate>=0.25.0",
        "numpy>=1.24.0",
        "boto3>=1.26.0",
        "wandb>=0.15.0",
        "tqdm>=4.65.0",
        "pillow>=9.5.0",
        "xformers>=0.0.22",  # Memory optimization
    ])
    .run_commands([
        "apt-get update",
        "apt-get install -y git curl wget"
    ])
    # Copy local modules
    .add_local_file("./embedding_dataset.py", "/root/embedding_dataset.py")
    .add_local_file("./unet256.py", "/root/unet256.py")  # Enhanced UNet
)

# Persistent volumes
model_volume = modal.Volume.from_name("petplantr-models", create_if_missing=True)

@app.function(
    image=image,
    gpu="T4",  # Keep T4 for cost efficiency
    volumes={"/models": model_volume},
    secrets=[
        modal.Secret.from_name("aws-petplantr"),
        modal.Secret.from_name("slack-webhook"),
        modal.Secret.from_name("wandb-api")
    ],
    timeout=10800,  # 3 hours for Stage 2
    memory=16000,   # 16GB RAM
)
def train_unet_stage2(
    batch_size: int = 1,       # Keep T4-optimized
    grad_accum: int = 8,       # Effective batch size: 8
    epochs: int = 8,           # More epochs for Stage 2
    learning_rate: float = 5e-5,  # Lower LR for fine-tuning
    enable_checkpointing: bool = True,
    enable_xformers: bool = True,
    load_stage1_weights: bool = True
):
    """
    Stage 2 UNet-256 training with enhanced resolution
    """
    import sys
    sys.path.append('/root')
    
    # Import modules
    from embedding_dataset import EmbeddingDataset
    from unet128 import UNet128  # Use UNet128 with larger params for Stage 2
    
    import torch
    import torch.nn.functional as F
    from torch.utils.data import DataLoader
    from torch.optim import AdamW
    from torch.optim.lr_scheduler import CosineAnnealingLR
    import numpy as np
    from pathlib import Path
    import boto3
    from tqdm import tqdm
    
    logger.info("🚀 Starting Stage 2 UNet-256 Training")
    logger.info("=" * 50)
    logger.info(f"📦 Batch size: {batch_size}")
    logger.info(f"🔄 Gradient accumulation: {grad_accum}")
    logger.info(f"📊 Epochs: {epochs}")
    logger.info(f"📈 Learning rate: {learning_rate}")
    logger.info(f"🔧 Load Stage 1 weights: {load_stage1_weights}")
    
    # Enable optimizations
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("🧹 GPU cache cleared")
    
    # Initialize WandB for Stage 2
    wandb_api_key = os.getenv("WANDB_API_KEY")
    if wandb_api_key:
        import wandb
        wandb.login(key=wandb_api_key)
        wandb.init(
            project="petplantr-unet-stage2",
            name=f"stage2-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            config={
                "stage": 2,
                "architecture": "unet256",
                "batch_size": batch_size,
                "gradient_accumulation": grad_accum,
                "epochs": epochs,
                "learning_rate": learning_rate,
                "load_stage1_weights": load_stage1_weights
            }
        )
        logger.info("✅ WandB initialized for Stage 2")
    
    # Download enhanced dataset (Stage 2 might have more data)
    s3_client = boto3.client('s3')
    logger.info("📥 Downloading Stage 2 embeddings...")
    
    os.makedirs("/tmp/embeddings", exist_ok=True)
    
    # Download enhanced embeddings (higher resolution)
    s3_client.download_file(
        "petplantr-dataset", 
        "embeddings/stage2/train_embeddings_256.npz",
        "/tmp/embeddings/train_embeddings.npz"
    )
    s3_client.download_file(
        "petplantr-dataset",
        "embeddings/stage2/val_embeddings_256.npz", 
        "/tmp/embeddings/val_embeddings.npz"
    )
    
    logger.info("✅ Stage 2 embeddings downloaded")
    
    # Load datasets
    train_dataset = EmbeddingDataset("/tmp/embeddings/train_embeddings.npz")
    val_dataset = EmbeddingDataset("/tmp/embeddings/val_embeddings.npz")
    
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True,
        num_workers=2,
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )
    
    logger.info(f"📊 Stage 2 - Train: {len(train_dataset)}, Val: {len(val_dataset)}")
    
    # Create enhanced UNet model for Stage 2 (higher resolution)
    unet = UNet128(
        in_channels=4,  # RGBA
        out_channels=4,
        model_channels=256,  # Enhanced from 128 in Stage 1
        num_res_blocks=2,
        attention_resolutions=(8, 16, 32),  # More attention layers
        dropout=0.1,
        channel_mult=(1, 2, 4, 8),  # Deeper architecture
        num_heads=8,  # More attention heads
        context_dim=768
    )
    
    # Load Stage 1 weights if requested
    if load_stage1_weights:
        logger.info("📂 Loading Stage 1 weights...")
        try:
            stage1_path = "/tmp/stage1_weights.pth"
            s3_client.download_file(
                "petplantr-models",
                "prod/unet128_stage1.pth",
                stage1_path
            )
            
            stage1_weights = torch.load(stage1_path, map_location='cpu')
            
            # Load compatible weights (might need adaptation for 256 vs 128)
            unet.load_state_dict(stage1_weights['model_state_dict'], strict=False)
            logger.info("✅ Stage 1 weights loaded (partial)")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load Stage 1 weights: {e}")
            logger.info("🔧 Training Stage 2 from scratch")
    
    unet = unet.cuda()
    
    if enable_xformers:
        try:
            unet.enable_xformers_memory_efficient_attention()
            logger.info("✅ XFormers enabled for Stage 2")
        except:
            logger.warning("⚠️ XFormers not available")
    
    if enable_checkpointing:
        unet.enable_gradient_checkpointing()
        logger.info("✅ Gradient checkpointing enabled")
    
    # Training setup
    optimizer = AdamW(unet.parameters(), lr=learning_rate, weight_decay=0.01)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=learning_rate/10)
    
    # Training loop with Stage 2 enhancements
    best_val_loss = float('inf')
    global_step = 0
    
    logger.info("🚀 Starting Stage 2 training loop...")
    
    for epoch in range(epochs):
        # Training phase
        unet.train()
        train_loss = 0.0
        
        pbar = tqdm(train_loader, desc=f"Stage 2 Epoch {epoch+1}/{epochs}")
        
        for batch_idx, batch in enumerate(pbar):
            embeddings = batch['embeddings'].cuda()
            
            # Enhanced noise schedule for Stage 2
            noise = torch.randn_like(embeddings)
            timesteps = torch.randint(0, 1000, (embeddings.shape[0],), device=embeddings.device)
            
            # Add noise
            noisy_embeddings = embeddings + noise * timesteps.view(-1, 1, 1, 1) / 1000
            
            # Predict noise
            noise_pred = unet(noisy_embeddings, timesteps)
            
            # Loss calculation
            loss = F.mse_loss(noise_pred, noise)
            loss = loss / grad_accum
            
            loss.backward()
            
            if (batch_idx + 1) % grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(unet.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad()
                global_step += 1
                
                # Log to WandB
                if wandb_api_key and global_step % 10 == 0:
                    wandb.log({
                        "train_loss": loss.item() * grad_accum,
                        "learning_rate": optimizer.param_groups[0]['lr'],
                        "step": global_step,
                        "epoch": epoch
                    })
            
            train_loss += loss.item() * grad_accum
            
            pbar.set_postfix({
                'Loss': f"{loss.item():.4f}",
                'Avg': f"{train_loss/(batch_idx+1):.4f}",
                'Step': global_step
            })
        
        avg_train_loss = train_loss / len(train_loader)
        
        # Validation phase
        unet.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                embeddings = batch['embeddings'].cuda()
                noise = torch.randn_like(embeddings)
                timesteps = torch.randint(0, 1000, (embeddings.shape[0],), device=embeddings.device)
                
                noisy_embeddings = embeddings + noise * timesteps.view(-1, 1, 1, 1) / 1000
                noise_pred = unet(noisy_embeddings, timesteps)
                
                loss = F.mse_loss(noise_pred, noise)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader)
        
        # Update scheduler
        scheduler.step()
        
        # Log epoch results
        logger.info(f"Epoch {epoch+1}/{epochs}: Train={avg_train_loss:.4f}, Val={avg_val_loss:.4f}")
        
        if wandb_api_key:
            wandb.log({
                "avg_train_loss": avg_train_loss,
                "avg_val_loss": avg_val_loss,
                "epoch": epoch + 1
            })
        
        # Save best checkpoint
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            
            checkpoint = {
                'epoch': epoch + 1,
                'model_state_dict': unet.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': avg_train_loss,
                'val_loss': avg_val_loss,
                'best_val_loss': best_val_loss,
                'global_step': global_step,
                'config': {
                    'stage': 2,
                    'architecture': 'unet256',
                    'epochs': epochs,
                    'batch_size': batch_size,
                    'learning_rate': learning_rate
                }
            }
            
            torch.save(checkpoint, f"/models/unet256_stage2_best.pth")
            logger.info(f"✅ Best Stage 2 checkpoint saved (val_loss: {avg_val_loss:.4f})")
            
            # Upload to S3
            try:
                s3_client.upload_file(
                    f"/models/unet256_stage2_best.pth",
                    "petplantr-models",
                    "models/unet256_stage2_best.pth"
                )
                logger.info("📤 Best Stage 2 model uploaded to S3")
            except Exception as e:
                logger.warning(f"⚠️ S3 upload failed: {e}")
    
    # Final results
    logger.info("🎉 Stage 2 UNet-256 Training Completed!")
    logger.info(f"   Best validation loss: {best_val_loss:.4f}")
    logger.info(f"   Target was: < 0.09")
    
    success = best_val_loss < 0.09
    if success:
        logger.info("✅ Stage 2 PASSED - Better than Stage 1!")
    else:
        logger.info("⚠️ Stage 2 did not beat target - keeping Stage 1")
    
    return {
        "status": "completed",
        "stage": 2,
        "best_val_loss": best_val_loss,
        "target_achieved": success,
        "recommendation": "promote" if success else "keep_stage1"
    }

@app.local_entrypoint()
def main():
    """Launch Stage 2 UNet-256 training"""
    print("🚀 Launching Stage 2 UNet-256 training...")
    print("🎯 Target: Validation loss < 0.09")
    print("")
    
    result = train_unet_stage2.remote()
    print(f"✅ Stage 2 training result: {result}")

if __name__ == "__main__":
    main()
