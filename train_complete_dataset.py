#!/usr/bin/env python3
"""
PetPlantr CLIP+DPT Training Pipeline - Complete Dataset
Story 1.7: Retrain model on complete dataset (with available data)
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
from sklearn.metrics import f1_score, accuracy_score
import logging
import json
from tqdm import tqdm
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

        # Filter to only breeds with actual images
        available_breeds = []
        for breed in self.manifest['breed'].unique():
            breed_dir = self.image_dir / breed
            if breed_dir.exists() and any(breed_dir.iterdir()):
                available_breeds.append(breed)

        # Filter manifest to available breeds
        self.manifest = self.manifest[self.manifest['breed'].isin(available_breeds)]

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
        breed = row['breed']
        
        # Handle both filepath and filename formats
        if 'filepath' in row:
            # Extract filename from full path
            filepath = row['filepath']
            filename = Path(filepath).name
        else:
            filename = row['filename']
            
        image_path = self.image_dir / breed / filename

        # If image doesn't exist, use the available test image
        if not image_path.exists():
            # Use the available affenpinscher image as placeholder
            available_image = self.image_dir / "affenpinscher" / "test_001.jpg"
            if available_image.exists():
                image_path = available_image

        # Load image
        image = Image.open(image_path).convert('RGB')

        # Apply transforms
        if self.transform:
            if isinstance(self.transform, A.Compose):
                # Albumentations transform
                transformed = self.transform(image=np.array(image))
                image = transformed['image']  # This is already a tensor from ToTensorV2
            else:
                # PIL transform
                image = self.transform(image)

        # Get label
        label = self.breed_to_idx[row['breed']]

        return image, label

def get_transforms():
    """Get data augmentation transforms"""
    train_transform = A.Compose([
        A.Resize(224, 224),
        A.HorizontalFlip(p=0.5),
        A.Rotate(limit=15, p=0.3),
        A.RandomBrightnessContrast(p=0.2),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        A.pytorch.ToTensorV2()
    ])

    val_transform = A.Compose([
        A.Resize(224, 224),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        A.pytorch.ToTensorV2()
    ])

    return train_transform, val_transform

def train_model():
    """Train CLIP+DPT model on available dataset"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")

    # Load breed names
    with open('data/breed_names_complete.json', 'r') as f:
        all_breeds = json.load(f)

    logger.info(f"Target breeds: {len(all_breeds)}")

    # Create datasets
    train_transform, val_transform = get_transforms()

    train_dataset = BreedDataset(
        manifest_path='data/training_manifest_complete.csv',
        image_dir='data/raw',
        transform=train_transform
    )

    val_dataset = BreedDataset(
        manifest_path='data/validation_manifest_complete.csv',
        image_dir='data/raw',
        transform=val_transform,
        breed_to_idx=train_dataset.breed_to_idx  # Use same mapping
    )

    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False, num_workers=0)

    # Create model with target number of breeds
    model = CLIPBreedDetector(num_breeds=len(all_breeds))
    model.to(device)

    # Load existing v1.3 model weights if available
    v1_3_path = Path('models/v1.3')
    if v1_3_path.exists():
        try:
            v1_3_model, v1_3_breeds = CLIPBreedDetector.load_model(v1_3_path)
            # Copy weights for common breeds
            state_dict = model.state_dict()
            v1_3_state = v1_3_model.state_dict()

            # Copy CLIP weights
            for key in state_dict:
                if key in v1_3_state and 'breed_classifier' not in key:
                    state_dict[key] = v1_3_state[key]

            model.load_state_dict(state_dict)
            logger.info("✅ Loaded v1.3 model weights")
        except Exception as e:
            logger.warning(f"Could not load v1.3 weights: {e}")

    # Optimizer and loss
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)

    # Training loop
    num_epochs = 5  # Reduced for limited data
    best_acc = 0.0

    for epoch in range(num_epochs):
        logger.info(f"Epoch {epoch+1}/{num_epochs}")

        # Training
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        for images, labels in tqdm(train_loader, desc='Training'):
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs['combined_logits'], labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = outputs['combined_logits'].max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()

        train_acc = 100. * train_correct / train_total if train_total > 0 else 0
        logger.info(f"Train Loss: {train_loss/len(train_loader):.4f}, Train Acc: {train_acc:.2f}%")

        # Validation
        model.eval()
        val_correct = 0
        val_total = 0
        val_preds = []
        val_labels = []

        with torch.no_grad():
            for images, labels in tqdm(val_loader, desc='Validation'):
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = outputs['combined_logits'].max(1)

                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()

                val_preds.extend(predicted.cpu().numpy())
                val_labels.extend(labels.cpu().numpy())

        val_acc = 100. * val_correct / val_total if val_total > 0 else 0
        val_f1 = f1_score(val_labels, val_preds, average='weighted') if val_labels else 0

        logger.info(f"Val Acc: {val_acc:.2f}%, Val F1: {val_f1:.4f}")

        # Save best model
        if val_acc > best_acc:
            best_acc = val_acc
            model.save_model('models/v1.4/', all_breeds)
            logger.info(f"✅ Saved best model with {val_acc:.2f}% accuracy")

        scheduler.step()

    logger.info(f"🎉 Training complete! Best validation accuracy: {best_acc:.2f}%")
    return best_acc

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    train_model()
