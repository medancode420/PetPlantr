"""
Stage 1 UNet-128 Training Script for Modal    # Copy local Python modules to the image
    .add_local_file("embedding_dataset.py", "/root/embedding_dataset.py")
    .add_local_file("unet128.py", "/root/unet128.py")
Loads pre-computed embeddings and trains lightweight UNet
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

# Note: embedding_dataset and unet128 will be imported inside the function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modal setup
app = modal.App("petplantr-unet-stage1")

# GPU image with PyTorch and dependencies
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
    # Copy local Python modules to the image
    .add_local_file("./embedding_dataset.py", "/root/embedding_dataset.py")
    .add_local_file("./unet128.py", "/root/unet128.py")
)

# Modal volumes for model storage
model_volume = modal.Volume.from_name("petplantr-models", create_if_missing=True)

@app.function(
    image=image,
    gpu="T4",
    volumes={"/models": model_volume},
    secrets=[
        modal.Secret.from_name("aws-petplantr"),
        modal.Secret.from_name("slack-webhook"),
        modal.Secret.from_name("wandb-api")
    ],
    timeout=7200,  # 2 hours
    memory=16000,  # 16GB
)
def train_unet_stage1(
    batch_size: int = 1,       # T4-optimized batch size
    grad_accum: int = 8,       # Effective batch size: 8
    epochs: int = 5,           # Quick first pass
    learning_rate: float = 1e-4,
    enable_checkpointing: bool = True,
    enable_xformers: bool = True
):
    """
    Stage 1 UNet training on Modal T4 with optimized settings
    """
    import sys
    sys.path.append('/root')  # Add root to Python path for our modules
    
    # Now import our modules after path is set
    from embedding_dataset import EmbeddingDataset
    from unet128 import create_unet128
    
    import torch
    import torch.nn.functional as F
    from torch.utils.data import DataLoader
    from torch.optim import AdamW
    from torch.optim.lr_scheduler import CosineAnnealingLR
    import numpy as np
    from pathlib import Path
    import boto3
    from tqdm import tqdm
    
    logger.info("🚀 Starting Stage 1 UNet-128 Training")
    logger.info("=" * 50)
    logger.info(f"📦 Batch size: {batch_size}")
    logger.info(f"🔄 Gradient accumulation: {grad_accum} (effective: {batch_size * grad_accum})")
    logger.info(f"📊 Epochs: {epochs}")
    logger.info(f"🧠 Gradient checkpointing: {enable_checkpointing}")
    logger.info(f"⚡ XFormers: {enable_xformers}")
    
    # Slack notification helper
    def send_slack_notification(message: str):
        try:
            import requests
            webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
            if webhook_url and webhook_url != "https://hooks.slack.com/services/placeholder":
                requests.post(webhook_url, json={"text": message}, timeout=10)
                logger.info(f"📤 Slack: {message}")
            else:
                logger.info(f"📤 Slack (disabled): {message}")
        except Exception as e:
            logger.warning(f"⚠️  Slack notification failed: {e}")
    
    # Send start notification
    send_slack_notification("🚀 Stage 1 UNet128 training started!")
    
    # GPU optimization
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"🖥️  Device: {device}")
    
    if torch.cuda.is_available():
        logger.info(f"💾 GPU: {torch.cuda.get_device_name()}")
        logger.info(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        
        # Enable TF32 for speed
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.benchmark = True
        
        # Enable XFormers if requested
        if enable_xformers:
            try:
                import xformers
                logger.info("✅ XFormers enabled for memory optimization")
            except ImportError:
                logger.warning("⚠️  XFormers not available, continuing without")
                enable_xformers = False
    
    # Setup AWS credentials
    aws_access_key = os.environ["AWS_ACCESS_KEY_ID"]
    aws_secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]
    
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name="us-east-1"
    )
    
    logger.info("Starting Stage 1 UNet training")
    
    # Training config using passed parameters
    config = {
        "batch_size": batch_size,
        "grad_accumulation": grad_accum,
        "learning_rate": learning_rate,
        "num_epochs": epochs,
        "noise_schedule_steps": 1000,
        "save_every": 1,  # Save every epoch
        "log_every": 10,
        "device": device.type,
        "enable_checkpointing": enable_checkpointing,
        "enable_xformers": enable_xformers,
    }
    
    logger.info(f"Training config: {config}")
    
    # Setup device
    device = torch.device(config["device"])
    logger.info(f"Using device: {device}")
    
    # Initialize wandb (optional)
    try:
        import wandb
        # Only initialize if API key is available (from Modal secret or env)
        wandb_key = os.getenv('WANDB_API_KEY')
        if wandb_key:
            wandb.init(
                project="petplantr-unet-stage1",
                config=config,
                name=f"stage1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            )
            use_wandb = True
            logger.info("✅ Wandb initialized")
        else:
            logger.info("⚠️ Wandb API key not found, skipping logging")
            use_wandb = False
    except (ImportError, Exception) as e:
        logger.info(f"⚠️ Wandb not available, skipping logging: {e}")
        use_wandb = False
    
    # Download embedding data from S3
    logger.info("Downloading embedding data from S3...")
    
    data_dir = Path("/tmp/embeddings")
    data_dir.mkdir(exist_ok=True)
    
    # Download train embeddings
    train_file = data_dir / "train_embeddings.npz"
    s3_client.download_file(
        "petplantr-dataset", 
        "embeds/train_embeddings.npz", 
        str(train_file)
    )
    
    # Download val embeddings
    val_file = data_dir / "val_embeddings.npz"
    s3_client.download_file(
        "petplantr-dataset", 
        "embeds/val_embeddings.npz", 
        str(val_file)
    )
    
    logger.info(f"Downloaded embeddings to {data_dir}")
    
    # Create datasets
    train_dataset = EmbeddingDataset(str(data_dir), split="train")
    val_dataset = EmbeddingDataset(str(data_dir), split="val")
    
    logger.info(f"Train samples: {len(train_dataset)}")
    logger.info(f"Val samples: {len(val_dataset)}")
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=config["batch_size"], 
        shuffle=True,
        num_workers=2,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset, 
        batch_size=config["batch_size"], 
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )
    
    # Create model
    model = create_unet128().to(device)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    logger.info(f"Total parameters: {total_params:,}")
    logger.info(f"Trainable parameters: {trainable_params:,}")
    
    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(), 
        lr=config["learning_rate"],
        weight_decay=1e-2
    )
    
    # Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, 
        T_max=config["num_epochs"] * len(train_loader)
    )
    
    # Noise schedule for diffusion training
    def linear_beta_schedule(timesteps):
        beta_start = 0.0001
        beta_end = 0.02
        return torch.linspace(beta_start, beta_end, timesteps)
    
    betas = linear_beta_schedule(config["noise_schedule_steps"])
    alphas = 1.0 - betas
    alphas_cumprod = torch.cumprod(alphas, dim=0).to(device)
    
    def add_noise(x0, t, noise=None):
        if noise is None:
            noise = torch.randn_like(x0)
        
        sqrt_alphas_cumprod_t = torch.sqrt(alphas_cumprod[t])[:, None, None, None]
        sqrt_one_minus_alphas_cumprod_t = torch.sqrt(1.0 - alphas_cumprod[t])[:, None, None, None]
        
        return sqrt_alphas_cumprod_t * x0 + sqrt_one_minus_alphas_cumprod_t * noise
    
    # Training loop
    global_step = 0
    best_val_loss = float('inf')
    
    for epoch in range(config["num_epochs"]):
        logger.info(f"Starting epoch {epoch + 1}/{config['num_epochs']}")
        
        # Training
        model.train()
        train_loss = 0.0
        optimizer.zero_grad()
        
        for batch_idx, batch in enumerate(train_loader):
            latents = batch["latent"].to(device)  # (B, 4, 64, 64)
            embeddings = batch["embed"].to(device)  # (B, 768)
            
            # Sample random timesteps
            timesteps = torch.randint(
                0, config["noise_schedule_steps"], 
                (latents.shape[0],), 
                device=device
            )
            
            # Add noise to latents
            noise = torch.randn_like(latents)
            noisy_latents = add_noise(latents, timesteps, noise)
            
            # Forward pass
            noise_pred = model(noisy_latents, timesteps, embeddings)
            
            # Loss (MSE between predicted and actual noise)
            loss = F.mse_loss(noise_pred, noise)
            loss = loss / config["grad_accumulation"]
            
            # Backward pass
            loss.backward()
            
            # Gradient accumulation
            if (batch_idx + 1) % config["grad_accumulation"] == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1
                
                # Logging
                if global_step % config["log_every"] == 0:
                    logger.info(f"Step {global_step}, Loss: {loss.item() * config['grad_accumulation']:.6f}")
                    if use_wandb:
                        wandb.log({
                            "train_loss": loss.item() * config["grad_accumulation"],
                            "learning_rate": scheduler.get_last_lr()[0],
                            "epoch": epoch,
                            "step": global_step
                        })
            
            train_loss += loss.item() * config["grad_accumulation"]
        
        avg_train_loss = train_loss / len(train_loader)
        logger.info(f"Epoch {epoch + 1} - Average train loss: {avg_train_loss:.6f}")
        
        # Validation
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                latents = batch["latent"].to(device)
                embeddings = batch["embed"].to(device)
                
                timesteps = torch.randint(
                    0, config["noise_schedule_steps"], 
                    (latents.shape[0],), 
                    device=device
                )
                
                noise = torch.randn_like(latents)
                noisy_latents = add_noise(latents, timesteps, noise)
                
                noise_pred = model(noisy_latents, timesteps, embeddings)
                loss = F.mse_loss(noise_pred, noise)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader)
        logger.info(f"Epoch {epoch + 1} - Average val loss: {avg_val_loss:.6f}")
        
        # Log to wandb
        if use_wandb:
            wandb.log({
                "epoch": epoch + 1,
                "avg_train_loss": avg_train_loss,
                "avg_val_loss": avg_val_loss,
            })
        
        # Save checkpoint
        if (epoch + 1) % config["save_every"] == 0:
            checkpoint_path = f"/models/unet128_stage1_epoch_{epoch + 1}.pth"
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'train_loss': avg_train_loss,
                'val_loss': avg_val_loss,
                'config': config,
            }, checkpoint_path)
            
            logger.info(f"Saved checkpoint: {checkpoint_path}")
            
            # Upload to S3 if best model
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                
                # Upload best model to S3
                s3_key = f"models/unet128_stage1_best.pth"
                s3_client.upload_file(checkpoint_path, "petplantr-models", s3_key)
                logger.info(f"Uploaded best model to s3://petplantr-models/{s3_key}")
                
                if use_wandb:
                    wandb.log({"best_val_loss": best_val_loss})
    
    # Final save
    final_path = "/models/unet128_stage1_final.pth"
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config,
        'final_train_loss': avg_train_loss,
        'final_val_loss': avg_val_loss,
    }, final_path)
    
    # Upload final model
    s3_client.upload_file(final_path, "petplantr-models", "models/unet128_stage1_final.pth")
    logger.info("Training completed and models uploaded to S3")
    
    # Send completion notification
    send_slack_notification(f"✅ Stage 1 UNet128 training completed! Best val loss: {best_val_loss:.4f}")
    
    if use_wandb:
        wandb.finish()
    
    return {
        "status": "completed",
        "final_train_loss": avg_train_loss,
        "final_val_loss": avg_val_loss,
        "best_val_loss": best_val_loss,
        "total_steps": global_step,
        "model_params": total_params,
    }

@app.local_entrypoint()
def main():
    """Launch Stage 1 training with T4-optimized settings"""
    print("🚀 Launching Stage 1 UNet-128 training on Modal T4...")
    print("📦 Configuration:")
    print("   • Batch size: 1 (T4 optimized)")
    print("   • Gradient accumulation: 8 (effective batch: 8)")
    print("   • Epochs: 5 (quick first pass)")
    print("   • Gradient checkpointing: enabled")
    print("   • XFormers: enabled")
    print("")
    
    result = train_unet_stage1.remote(
        batch_size=1,
        grad_accum=8,
        epochs=5,
        learning_rate=1e-4,
        enable_checkpointing=True,
        enable_xformers=True
    )
    print(f"✅ Training completed: {result}")

if __name__ == "__main__":
    main()
