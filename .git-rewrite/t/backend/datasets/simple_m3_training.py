"""
PetPlantr Simple M3 Max Training
Simplified approach focusing on CLIP feature extraction and basic training

This version avoids complex UNet operations and focuses on getting a working model
"""

import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from transformers import CLIPVisionModel, CLIPImageProcessor
from PIL import Image
import boto3
from pathlib import Path
import logging
from datetime import datetime
from tqdm import tqdm
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplePetDataset(Dataset):
    """Simplified dataset for M3 Max training"""
    
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
        
        # Simple transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),  # CLIP standard size
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # CLIP processor
        self.processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        
        # Load and process image
        image = Image.open(img_path).convert('RGB')
        
        # For our simple model
        pixel_values = self.transform(image)
        
        # For CLIP
        clip_inputs = self.processor(images=image, return_tensors="pt")
        clip_pixel_values = clip_inputs["pixel_values"].squeeze(0)
        
        return {
            "pixel_values": pixel_values,
            "clip_pixel_values": clip_pixel_values,
            "image_path": str(img_path)
        }

class SimpleFeatureExtractor(nn.Module):
    """Simple feature extraction model for pets"""
    
    def __init__(self, input_dim=768, hidden_dim=512, output_dim=256):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, x):
        return self.encoder(x)

class SimpleM3Pipeline:
    """Simplified training pipeline for M3 Max"""
    
    def __init__(self, 
                 data_dir: str,
                 output_dir: str = "./models",
                 batch_size: int = 8,
                 learning_rate: float = 1e-4,
                 num_epochs: int = 10):
        
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        
        # Use MPS for M3 Max
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
            logger.info("🍎 Using Apple M3 Max MPS acceleration")
        else:
            self.device = torch.device("cpu")
            logger.info("⚠️  MPS not available, using CPU")
        
        self._setup_models()
        self._setup_data()
    
    def _setup_models(self):
        """Initialize models"""
        logger.info("🧠 Loading models...")
        
        # CLIP vision encoder (frozen)
        self.clip_model = CLIPVisionModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_model.eval()
        self.clip_model.requires_grad_(False)
        self.clip_model.to(self.device)
        
        # Simple feature extractor (trainable)
        self.feature_extractor = SimpleFeatureExtractor()
        self.feature_extractor.to(self.device)
        
        # Optimizer
        self.optimizer = torch.optim.AdamW(
            self.feature_extractor.parameters(),
            lr=self.learning_rate,
            weight_decay=0.01
        )
        
        # Loss function (simple reconstruction loss)
        self.criterion = nn.MSELoss()
        
        logger.info(f"✅ Models loaded to {self.device}")
    
    def _setup_data(self):
        """Setup data loaders"""
        # Training dataset
        train_dataset = SimplePetDataset(str(self.data_dir), "train")
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=2
        )
        
        # Validation dataset
        val_dataset = SimplePetDataset(str(self.data_dir), "val")
        self.val_loader = DataLoader(
            val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=2
        )
        
        logger.info(f"📊 Train: {len(train_dataset)}, Val: {len(val_dataset)}")
    
    def train_epoch(self, epoch: int):
        """Train one epoch"""
        self.feature_extractor.train()
        total_loss = 0
        
        progress_bar = tqdm(self.train_loader, desc=f"Epoch {epoch+1}/{self.num_epochs}")
        
        for step, batch in enumerate(progress_bar):
            try:
                # Move to device
                clip_pixel_values = batch["clip_pixel_values"].to(self.device)
                
                # Get CLIP features
                with torch.no_grad():
                    clip_features = self.clip_model(clip_pixel_values).pooler_output
                
                # Extract features with our model
                extracted_features = self.feature_extractor(clip_features)
                
                # Simple reconstruction loss (try to reconstruct CLIP features)
                target_features = clip_features[:, :extracted_features.shape[1]]  # Truncate to match
                loss = self.criterion(extracted_features, target_features)
                
                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.feature_extractor.parameters(), max_norm=1.0)
                self.optimizer.step()
                
                total_loss += loss.item()
                progress_bar.set_postfix({"loss": f"{loss.item():.4f}"})
                
                # Memory cleanup
                if step % 5 == 0 and self.device.type == "mps":
                    torch.mps.empty_cache()
                    
            except Exception as e:
                logger.error(f"Error at step {step}: {e}")
                continue
        
        avg_loss = total_loss / len(self.train_loader)
        logger.info(f"📈 Epoch {epoch+1} - Average Loss: {avg_loss:.4f}")
        return avg_loss
    
    def validate(self):
        """Run validation"""
        self.feature_extractor.eval()
        total_loss = 0
        
        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc="Validation"):
                try:
                    clip_pixel_values = batch["clip_pixel_values"].to(self.device)
                    
                    # Get CLIP features
                    clip_features = self.clip_model(clip_pixel_values).pooler_output
                    
                    # Extract features
                    extracted_features = self.feature_extractor(clip_features)
                    
                    # Compute loss
                    target_features = clip_features[:, :extracted_features.shape[1]]
                    loss = self.criterion(extracted_features, target_features)
                    total_loss += loss.item()
                    
                except Exception as e:
                    logger.error(f"Validation error: {e}")
                    continue
        
        avg_loss = total_loss / len(self.val_loader) if len(self.val_loader) > 0 else 0
        logger.info(f"🧪 Validation Loss: {avg_loss:.4f}")
        return avg_loss
    
    def save_model(self, epoch: int, loss: float):
        """Save model checkpoint"""
        checkpoint = {
            "epoch": epoch,
            "feature_extractor_state_dict": self.feature_extractor.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "loss": loss,
            "timestamp": datetime.now().isoformat()
        }
        
        checkpoint_path = self.output_dir / f"simple_m3_backbone_epoch_{epoch+1}.pt"
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"💾 Model saved: {checkpoint_path}")
        
        return checkpoint_path
    
    def train(self):
        """Main training loop"""
        logger.info("🚀 Starting Simple M3 Max training...")
        logger.info(f"🖥️  Device: {self.device}")
        logger.info(f"📊 Batch size: {self.batch_size}")
        logger.info(f"🔄 Epochs: {self.num_epochs}")
        
        best_val_loss = float('inf')
        best_path = None
        
        for epoch in range(self.num_epochs):
            # Train
            train_loss = self.train_epoch(epoch)
            
            # Validate
            val_loss = self.validate()
            
            # Save checkpoint
            current_path = self.save_model(epoch, val_loss)
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_path = current_path
                logger.info(f"🏆 New best model! Loss: {val_loss:.4f}")
        
        logger.info("✅ Training completed!")
        return best_path

def download_dataset_local():
    """Download dataset from S3 to local storage"""
    logger.info("📥 Downloading dataset from S3...")
    
    # Create local data directory
    data_dir = Path("./data/oxford_simple")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup S3 client
    s3 = boto3.client('s3')
    bucket = "petplantr-dataset"
    
    # Download training images
    train_dir = data_dir / "train"
    train_dir.mkdir(exist_ok=True)
    
    try:
        train_objects = s3.list_objects_v2(
            Bucket=bucket,
            Prefix="public/oxford_v37/training/"
        )
        
        if 'Contents' in train_objects:
            for obj in tqdm(train_objects['Contents'], desc="Downloading training images"):
                if obj['Key'].endswith('.jpg'):
                    local_path = train_dir / Path(obj['Key']).name
                    if not local_path.exists():  # Skip if already downloaded
                        s3.download_file(bucket, obj['Key'], str(local_path))
    except Exception as e:
        logger.error(f"Error downloading training images: {e}")
    
    # Download validation images
    val_dir = data_dir / "val"
    val_dir.mkdir(exist_ok=True)
    
    try:
        val_objects = s3.list_objects_v2(
            Bucket=bucket,
            Prefix="public/oxford_v37/validation/"
        )
        
        if 'Contents' in val_objects:
            for obj in tqdm(val_objects['Contents'], desc="Downloading validation images"):
                if obj['Key'].endswith('.jpg'):
                    local_path = val_dir / Path(obj['Key']).name
                    if not local_path.exists():  # Skip if already downloaded
                        s3.download_file(bucket, obj['Key'], str(local_path))
    except Exception as e:
        logger.error(f"Error downloading validation images: {e}")
    
    logger.info(f"✅ Dataset downloaded to {data_dir}")
    return str(data_dir)

def main():
    """Main training function"""
    print("🍎 PetPlantr Simple M3 Max Training")
    print("=" * 42)
    
    # Download dataset
    data_dir = download_dataset_local()
    
    # Initialize training pipeline
    pipeline = SimpleM3Pipeline(
        data_dir=data_dir,
        batch_size=8,
        learning_rate=1e-4,
        num_epochs=10
    )
    
    # Train model
    best_model_path = pipeline.train()
    
    print(f"🎉 Training completed! Best model: {best_model_path}")

if __name__ == "__main__":
    main()
