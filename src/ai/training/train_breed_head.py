#!/usr/bin/env python3
"""
PetPlantr CLIP+DPT Training Pipeline
Story 1.4: Retrain CLIP+DPT pipeline with full set
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from PIL import Image
import albumentations as A
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, accuracy_score
import logging
import argparse
import json
from tqdm import tqdm
import wandb
from datetime import datetime

from src.ai.models.clip_breed import CLIPBreedDetector

logger = logging.getLogger(__name__)

class BreedDataset(Dataset):
    """Dataset for breed classification training"""

    def __init__(self, manifest_path: str, image_dir: str, transform=None, breed_to_idx=None):
        self.manifest_path = Path(manifest_path)
        self.image_dir = Path(image_dir)
        self.transform = transform

        # Load manifest
        self.manifest = pd.read_csv(self.manifest_path)

        # Create breed mapping
        if breed_to_idx is None:
            unique_breeds = sorted(self.manifest['breed'].unique())
            self.breed_to_idx = {breed: idx for idx, breed in enumerate(unique_breeds)}
        else:
            self.breed_to_idx = breed_to_idx

        self.idx_to_breed = {v: k for k, v in self.breed_to_idx.items()}

        logger.info(f"Loaded dataset with {len(self.manifest)} images, {len(self.breed_to_idx)} breeds")

    def __len__(self):
        return len(self.manifest)

    def __getitem__(self, idx):
        row = self.manifest.iloc[idx]
        image_path = self.image_dir / row['filename']
        breed = row['breed']

        # Load image
        image = Image.open(image_path).convert('RGB')

        # Apply transforms
        if self.transform:
            image_np = np.array(image)
            transformed = self.transform(image=image_np)
            image = Image.fromarray((transformed['image'] * 255).astype(np.uint8))

        # Convert to tensor
        if isinstance(image, Image.Image):
            image = torch.from_numpy(np.array(image)).permute(2, 0, 1).float() / 255.0

        label = self.breed_to_idx[breed]

        return image, label

def get_transforms(augment: bool = True):
    """Get data augmentation transforms"""
    if augment:
        return A.Compose([
            A.Resize(224, 224),
            A.HorizontalFlip(p=0.5),
            A.Rotate(limit=15, p=0.5),
            A.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.05, p=0.5),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    else:
        return A.Compose([
            A.Resize(224, 224),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

def train_epoch(model, dataloader, optimizer, criterion, device, scaler=None):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for images, labels in tqdm(dataloader, desc="Training"):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()

        with torch.cuda.amp.autocast(enabled=scaler is not None):
            outputs = model(images)
            loss = criterion(outputs['combined_logits'], labels)

        if scaler:
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            optimizer.step()

        total_loss += loss.item()
        _, predicted = outputs['combined_logits'].max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    accuracy = 100. * correct / total
    avg_loss = total_loss / len(dataloader)

    return avg_loss, accuracy

def validate(model, dataloader, criterion, device):
    """Validate model"""
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for images, labels in tqdm(dataloader, desc="Validating"):
            images, labels = images.to(device), labels.to(device)

            outputs = model(images)
            loss = criterion(outputs['combined_logits'], labels)

            total_loss += loss.item()
            _, predicted = outputs['combined_logits'].max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    accuracy = 100. * correct / total
    avg_loss = total_loss / len(dataloader)
    f1 = f1_score(all_labels, all_preds, average='weighted')

    return avg_loss, accuracy, f1

def main():
    parser = argparse.ArgumentParser(description="Train CLIP+DPT breed detection model")
    parser.add_argument("--manifest", default="data/manifest.csv", help="Dataset manifest")
    parser.add_argument("--image-dir", default="data/raw", help="Image directory")
    parser.add_argument("--output-dir", default="models/v1.3", help="Output directory")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--val-split", type=float, default=0.2, help="Validation split")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--wandb", action="store_true", help="Use Weights & Biases")
    parser.add_argument("--resume", help="Resume from checkpoint")

    args = parser.parse_args()

    # Set random seed
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Setup W&B if requested
    if args.wandb:
        wandb.init(project="petplantr-breed-detection", name=f"v1.3-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        wandb.config.update(args)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    logger.info("Loading dataset...")
    full_dataset = BreedDataset(args.manifest, args.image_dir)

    # Handle small datasets
    if len(full_dataset) < 5:
        logger.warning(f"Small dataset ({len(full_dataset)} samples). Using all data for training, no validation.")
        train_dataset = full_dataset
        val_dataset = full_dataset  # Use same data for validation (not ideal but necessary)
    else:
        # Split dataset
        train_indices, val_indices = train_test_split(
            range(len(full_dataset)),
            test_size=args.val_split,
            stratify=[full_dataset.manifest.iloc[i]['breed'] for i in range(len(full_dataset))],
            random_state=args.seed
        )

        # Create subset datasets
        train_dataset = torch.utils.data.Subset(full_dataset, train_indices)
        val_dataset = torch.utils.data.Subset(full_dataset, val_indices)

    # Apply transforms
    if hasattr(train_dataset, 'dataset'):
        # It's a subset
        train_dataset.dataset.transform = get_transforms(augment=True)
        val_dataset.dataset.transform = get_transforms(augment=False)
    else:
        # It's the full dataset
        train_dataset.transform = get_transforms(augment=True)
        val_dataset.transform = get_transforms(augment=False)

    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)

    # Create model
    num_breeds = len(full_dataset.breed_to_idx)
    model = CLIPBreedDetector(num_breeds=num_breeds)
    model.to(device)

    # Setup optimizer and loss
    optimizer = optim.AdamW(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler() if torch.cuda.is_available() else None

    # Resume from checkpoint if provided
    start_epoch = 0
    if args.resume:
        checkpoint = torch.load(args.resume)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        logger.info(f"Resumed from epoch {start_epoch}")

    # Training loop
    best_f1 = 0.0
    for epoch in range(start_epoch, args.epochs):
        logger.info(f"Epoch {epoch+1}/{args.epochs}")

        # Train
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, device, scaler)

        # Validate
        val_loss, val_acc, val_f1 = validate(model, val_loader, criterion, device)

        logger.info(".2f")
        logger.info(".2f")

        # Log to W&B
        if args.wandb:
            wandb.log({
                'epoch': epoch,
                'train_loss': train_loss,
                'train_acc': train_acc,
                'val_loss': val_loss,
                'val_acc': val_acc,
                'val_f1': val_f1
            })

        # Save best model
        if val_f1 > best_f1:
            best_f1 = val_f1
            model.save_model(output_dir / "best_model", list(full_dataset.breed_to_idx.keys()))
            logger.info(".2f")

        # Save checkpoint
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_f1': val_f1,
            'best_f1': best_f1
        }
        torch.save(checkpoint, output_dir / f"checkpoint_epoch_{epoch}.pth")

    # Save final model
    model.save_model(output_dir / "final_model", list(full_dataset.breed_to_idx.keys()))

    logger.info("Training completed!")
    logger.info(".2f")
    logger.info(f"Model saved to {output_dir}")

if __name__ == "__main__":
    main()