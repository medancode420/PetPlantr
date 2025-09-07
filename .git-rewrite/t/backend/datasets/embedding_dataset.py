"""
PetPlantr Embedding Dataset - Lookup Table Loader
Load pre-computed 768-d embeddings without CLIP on GPU

Each .npz contains:
  - 'sequence_embeddings': (n, 50, 768) CLIP patch embeddings  
  - 'pooled_embeddings': (n, 768) Global image embeddings
  - 'image_names': Image filenames
  - 'image_paths': Relative paths
"""

import numpy as np
import torch
from pathlib import Path
from torch.utils.data import Dataset
import logging

logger = logging.getLogger(__name__)

class EmbeddingDataset(Dataset):
    """
    Dataset that loads pre-computed embeddings and generates synthetic latents
    for Stage 1 UNet training without requiring actual VAE encoding
    """
    
    def __init__(self, root: str, split: str = "train"):
        self.root = Path(root)
        self.split = split
        
        # Load the embedding file for this split
        embedding_file = self.root / f"{split}_embeddings.npz"
        
        if not embedding_file.exists():
            raise FileNotFoundError(f"Embedding file not found: {embedding_file}")
        
        logger.info(f"Loading embeddings from {embedding_file}")
        data = np.load(embedding_file)
        
        # Extract embeddings and metadata
        self.sequence_embeddings = data['sequence_embeddings']  # (N, 50, 768)
        self.pooled_embeddings = data['pooled_embeddings']      # (N, 768)
        self.image_names = data['image_names']
        self.image_paths = data['image_paths']
        
        logger.info(f"Loaded {len(self.pooled_embeddings)} samples")
        logger.info(f"Sequence shape: {self.sequence_embeddings.shape}")
        logger.info(f"Pooled shape: {self.pooled_embeddings.shape}")
    
    def __len__(self):
        return len(self.pooled_embeddings)
    
    def __getitem__(self, idx):
        # Get pre-computed embeddings
        sequence_embed = self.sequence_embeddings[idx]  # (50, 768)
        pooled_embed = self.pooled_embeddings[idx]      # (768,)
        
        # Generate synthetic latents for Stage 1 training
        # In a real pipeline, these would come from VAE encoding
        # For now, we'll create random latents with some structure
        latent = self._generate_synthetic_latent(pooled_embed)
        
        return {
            "latent": latent.astype(np.float32),           # (4, 64, 64)
            "embed": pooled_embed.astype(np.float32),      # (768,) - for cross-attention
            "sequence_embed": sequence_embed.astype(np.float32), # (50, 768) - if needed
            "image_name": self.image_names[idx]
        }
    
    def _generate_synthetic_latent(self, embed):
        """
        Generate synthetic VAE latents based on embedding
        This is a placeholder for Stage 1 - in production, use real VAE encoding
        """
        # Use embedding to seed random generation for consistency
        seed = int(np.sum(embed * 1000)) % 2**31
        rng = np.random.RandomState(seed)
        
        # Generate 4-channel latent (typical VAE latent space)
        # Standard VAE latents are typically in range [-1, 1] with some structure
        latent = rng.normal(0, 0.18, (4, 64, 64))  # Standard VAE scale
        
        # Add some spatial structure based on embedding features
        # This gives the UNet something meaningful to learn from
        spatial_bias = embed[:16].reshape(4, 4)  # Use first 16 dims for spatial bias
        for c in range(4):
            for i in range(4):
                for j in range(4):
                    latent[c, i*16:(i+1)*16, j*16:(j+1)*16] += spatial_bias[i, j] * 0.1
        
        return latent

class ProductionEmbeddingDataset(Dataset):
    """
    Production version that loads actual VAE latents + embeddings
    Use this when you have real VAE-encoded latents
    """
    
    def __init__(self, embedding_root: str, latent_root: str, split: str = "train"):
        self.embedding_root = Path(embedding_root)
        self.latent_root = Path(latent_root)
        self.split = split
        
        # Load embeddings
        embedding_file = self.embedding_root / f"{split}_embeddings.npz"
        embed_data = np.load(embedding_file)
        self.embeddings = embed_data['pooled_embeddings']
        self.image_names = embed_data['image_names']
        
        # Load latents (when available)
        latent_files = sorted((Path(latent_root) / split).glob("*.npz"))
        self.latent_files = latent_files
        
        logger.info(f"Production dataset: {len(self.embeddings)} embeddings, {len(latent_files)} latent files")
    
    def __len__(self):
        return len(self.embeddings)
    
    def __getitem__(self, idx):
        # Load embedding
        embed = self.embeddings[idx]
        
        # Load corresponding latent
        if idx < len(self.latent_files):
            latent_data = np.load(self.latent_files[idx])
            latent = latent_data['latent']
        else:
            # Fallback to synthetic if latent not available
            latent = self._generate_synthetic_latent(embed)
        
        return {
            "latent": latent.astype(np.float32),
            "embed": embed.astype(np.float32),
            "image_name": self.image_names[idx]
        }
    
    def _generate_synthetic_latent(self, embed):
        """Same as base class"""
        seed = int(np.sum(embed * 1000)) % 2**31
        rng = np.random.RandomState(seed)
        latent = rng.normal(0, 0.18, (4, 64, 64))
        
        spatial_bias = embed[:16].reshape(4, 4)
        for c in range(4):
            for i in range(4):
                for j in range(4):
                    latent[c, i*16:(i+1)*16, j*16:(j+1)*16] += spatial_bias[i, j] * 0.1
        
        return latent
