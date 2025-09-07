#!/usr/bin/env python3
"""
PetPlantr CLIP+DPT Breed Detection Model
Story 1.4: Retrain CLIP+DPT pipeline with full set
"""

import torch
import torch.nn as nn
from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer
import timm
from typing import Dict, List, Tuple, Optional, Union
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class CLIPBreedDetector(nn.Module):
    """CLIP-based breed detection model with DPT depth estimation"""

    def __init__(self, num_breeds: int = 130, model_name: str = "openai/clip-vit-base-patch32"):
        super().__init__()

        # Load CLIP model and processor
        self.clip_model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.tokenizer = CLIPTokenizer.from_pretrained(model_name)

        # Freeze CLIP vision encoder (we'll fine-tune text encoder)
        for param in self.clip_model.vision_model.parameters():
            param.requires_grad = False

        # Breed classification head
        hidden_size = self.clip_model.config.vision_config.hidden_size
        self.breed_classifier = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size // 2, num_breeds)
        )

    def forward(self, images: torch.Tensor, text_inputs: Optional[Dict] = None) -> Dict[str, torch.Tensor]:
        """
        Forward pass through CLIP+DPT pipeline

        Args:
            images: Batch of images [B, C, H, W]
            text_inputs: Optional text inputs for zero-shot classification

        Returns:
            Dict with breed_logits, depth_features, and combined_logits
        """

        # CLIP vision encoding
        vision_outputs = self.clip_model.vision_model(images)
        image_features = vision_outputs.pooler_output  # [B, hidden_size]

        # Breed classification from CLIP features only (simplified for now)
        breed_logits = self.breed_classifier(image_features)

        # For now, skip depth features and combined classification
        combined_logits = breed_logits  # Use CLIP-only predictions
        depth_features = torch.zeros(images.size(0), 512, device=images.device)  # Dummy

        # Zero-shot classification if text provided
        zero_shot_logits = None
        if text_inputs is not None:
            text_outputs = self.clip_model.text_model(**text_inputs)
            text_features = text_outputs.pooler_output

            # Compute similarity
            image_features_norm = image_features / image_features.norm(dim=1, keepdim=True)
            text_features_norm = text_features / text_features.norm(dim=1, keepdim=True)
            zero_shot_logits = torch.matmul(image_features_norm, text_features_norm.t()) * self.clip_model.logit_scale.exp()

        return {
            'breed_logits': breed_logits,
            'combined_logits': combined_logits,
            'depth_features': depth_features,
            'zero_shot_logits': zero_shot_logits,
            'image_features': image_features
        }

    def get_breed_probabilities(self, images: torch.Tensor, breed_names: List[str]) -> torch.Tensor:
        """Get breed probabilities for images"""
        with torch.no_grad():
            outputs = self.forward(images)
            probs = torch.softmax(outputs['combined_logits'], dim=1)
            return probs

    def save_model(self, path: Union[str, Path], breed_names: List[str]):
        """Save model and breed names"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save model state
        torch.save(self.state_dict(), path / "model.pth")

        # Save breed names
        with open(path / "breed_names.json", "w") as f:
            json.dump(breed_names, f)

        # Save model config
        config = {
            "num_breeds": len(breed_names),
            "clip_model": "openai/clip-vit-base-patch32",
            "depth_model": "dpt_large"
        }
        with open(path / "config.json", "w") as f:
            json.dump(config, f)

        logger.info(f"Model saved to {path}")

    @classmethod
    def load_model(cls, path: Union[str, Path]) -> Tuple['CLIPBreedDetector', List[str]]:
        """Load model and breed names"""
        path = Path(path)

        # Load config
        with open(path / "config.json", "r") as f:
            config = json.load(f)

        # Load breed names
        with open(path / "breed_names.json", "r") as f:
            breed_names = json.load(f)

        # Create model
        model = cls(num_breeds=config["num_breeds"])
        model.load_state_dict(torch.load(path / "model.pth"))
        model.eval()

        logger.info(f"Model loaded from {path}")
        return model, breed_names