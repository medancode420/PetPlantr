#!/usr/bin/env python3
"""
PetPlantr Feature Extraction Service
Vision Transformer + ArcFace for pet facial feature extraction

This service:
1. Downloads pet photos from S3
2. Extracts facial features using fine-tuned ViT
3. Applies ArcFace loss for metric learning
4. Uploads feature vectors to S3
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
import cv2
import boto3
from transformers import ViTImageProcessor, ViTForImageClassification
import timm
from fastapi import FastAPI, HTTPException
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
s3_client = boto3.client('s3', region_name='us-east-1')
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')

# Initialize FastAPI app
app = FastAPI(title="PetPlantr Feature Extraction", version="1.0.0")

class PetFeatureExtractor:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        self.model = None
        self.processor = None
        self.arcface_model = None
        
    async def load_models(self):
        """Load the fine-tuned ViT and ArcFace models"""
        try:
            # Load model weights path from Secrets Manager
            weights_path = await self._get_model_weights_path()
            
            # Load fine-tuned ViT model
            logger.info("Loading fine-tuned ViT model...")
            self.processor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
            
            # Load from local cache or download from S3
            model_local_path = "/app/cache/vit_pet_features.pth"
            if not os.path.exists(model_local_path):
                await self._download_model_from_s3(weights_path, model_local_path)
            
            # Initialize model architecture
            self.model = ViTForImageClassification.from_pretrained(
                'google/vit-base-patch16-224',
                num_labels=512,  # Feature vector dimension
                ignore_mismatched_sizes=True
            )
            
            # Load fine-tuned weights
            checkpoint = torch.load(model_local_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            # Load ArcFace model for metric learning
            logger.info("Loading ArcFace model...")
            self.arcface_model = self._create_arcface_model()
            
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    async def _get_model_weights_path(self) -> str:
        """Get model weights path from Secrets Manager"""
        try:
            response = secrets_client.get_secret_value(
                SecretId='petplantr/models/vit-feature-extraction'
            )
            return response['SecretString']
        except Exception as e:
            logger.error(f"Failed to get model weights path: {e}")
            # Fallback to default path
            return "s3://petplantr-models-prod/vit-feature-extraction/latest.pth"
    
    async def _download_model_from_s3(self, s3_path: str, local_path: str):
        """Download model weights from S3"""
        try:
            # Parse S3 path
            path_parts = s3_path.replace('s3://', '').split('/', 1)
            bucket = path_parts[0]
            key = path_parts[1]
            
            logger.info(f"Downloading model from {s3_path}...")
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            s3_client.download_file(bucket, key, local_path)
            logger.info("Model downloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to download model from S3: {e}")
            raise
    
    def _create_arcface_model(self):
        """Create ArcFace model for metric learning"""
        import insightface
        
        # Initialize ArcFace model
        model = insightface.app.FaceAnalysis()
        model.prepare(ctx_id=0)  # Use GPU
        return model
    
    async def process_photos(self, order_id: str, photo_urls: List[str]) -> Dict[str, Any]:
        """
        Process pet photos and extract features
        
        Args:
            order_id: Unique order identifier
            photo_urls: List of S3 URLs for pet photos
            
        Returns:
            Dictionary containing extracted features and metadata
        """
        try:
            logger.info(f"Processing {len(photo_urls)} photos for order {order_id}")
            
            all_features = []
            photo_metadata = []
            
            for i, photo_url in enumerate(photo_urls):
                # Download and preprocess image
                image = await self._download_and_preprocess_image(photo_url)
                
                # Extract ViT features
                vit_features = await self._extract_vit_features(image)
                
                # Extract ArcFace features (if face detected)
                arcface_features = await self._extract_arcface_features(image)
                
                # Combine features
                combined_features = self._combine_features(vit_features, arcface_features)
                
                all_features.append(combined_features)
                photo_metadata.append({
                    'photo_index': i,
                    'photo_url': photo_url,
                    'has_face': arcface_features is not None,
                    'feature_quality': self._assess_feature_quality(combined_features)
                })
            
            # Aggregate features across all photos
            aggregated_features = self._aggregate_features(all_features)
            
            # Predict breed and confidence
            breed_prediction = await self._predict_breed(aggregated_features)
            
            result = {
                'order_id': order_id,
                'extracted_features': aggregated_features.tolist(),
                'breed_prediction': breed_prediction['breed'],
                'breed_confidence': breed_prediction['confidence'],
                'photo_metadata': photo_metadata,
                'feature_dimensions': len(aggregated_features),
                'processing_timestamp': asyncio.get_event_loop().time()
            }
            
            logger.info(f"Feature extraction completed for order {order_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process photos for order {order_id}: {e}")
            raise
    
    async def _download_and_preprocess_image(self, photo_url: str) -> np.ndarray:
        """Download image from S3 and preprocess"""
        try:
            # Parse S3 URL
            if photo_url.startswith('s3://'):
                path_parts = photo_url.replace('s3://', '').split('/', 1)
                bucket = path_parts[0]
                key = path_parts[1]
                
                # Download to memory
                response = s3_client.get_object(Bucket=bucket, Key=key)
                image_data = response['Body'].read()
                
                # Load image
                image = Image.open(io.BytesIO(image_data))
                image = image.convert('RGB')
                
                # Convert to numpy array
                image_np = np.array(image)
                
                return image_np
            else:
                raise ValueError(f"Unsupported photo URL format: {photo_url}")
                
        except Exception as e:
            logger.error(f"Failed to download and preprocess image {photo_url}: {e}")
            raise
    
    async def _extract_vit_features(self, image: np.ndarray) -> torch.Tensor:
        """Extract features using fine-tuned ViT"""
        try:
            # Convert to PIL Image for processor
            pil_image = Image.fromarray(image)
            
            # Preprocess image
            inputs = self.processor(pil_image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Extract features
            with torch.no_grad():
                outputs = self.model(**inputs)
                features = outputs.logits  # Shape: [1, 512]
                
                # L2 normalize features
                features = F.normalize(features, p=2, dim=1)
                
            return features.squeeze(0)  # Shape: [512]
            
        except Exception as e:
            logger.error(f"Failed to extract ViT features: {e}")
            raise
    
    async def _extract_arcface_features(self, image: np.ndarray) -> torch.Tensor:
        """Extract ArcFace features if face is detected"""
        try:
            # Convert BGR to RGB (insightface expects BGR)
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Detect faces
            faces = self.arcface_model.get(image_bgr)
            
            if len(faces) > 0:
                # Use the largest face
                largest_face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
                
                # Extract embedding
                embedding = largest_face.embedding
                
                # Convert to tensor and normalize
                embedding_tensor = torch.from_numpy(embedding).float()
                embedding_tensor = F.normalize(embedding_tensor, p=2, dim=0)
                
                return embedding_tensor
            else:
                logger.warning("No face detected in image")
                return None
                
        except Exception as e:
            logger.error(f"Failed to extract ArcFace features: {e}")
            return None
    
    def _combine_features(self, vit_features: torch.Tensor, arcface_features: torch.Tensor = None) -> torch.Tensor:
        """Combine ViT and ArcFace features"""
        if arcface_features is not None:
            # Concatenate features
            combined = torch.cat([vit_features, arcface_features], dim=0)
        else:
            # Use only ViT features, pad with zeros
            zeros = torch.zeros(512, device=vit_features.device)  # ArcFace embedding size
            combined = torch.cat([vit_features, zeros], dim=0)
        
        # Final normalization
        combined = F.normalize(combined, p=2, dim=0)
        return combined
    
    def _aggregate_features(self, feature_list: List[torch.Tensor]) -> torch.Tensor:
        """Aggregate features across multiple photos"""
        if len(feature_list) == 1:
            return feature_list[0]
        
        # Stack and take mean
        stacked = torch.stack(feature_list)
        aggregated = torch.mean(stacked, dim=0)
        
        # Normalize again
        aggregated = F.normalize(aggregated, p=2, dim=0)
        return aggregated
    
    async def _predict_breed(self, features: torch.Tensor) -> Dict[str, Any]:
        """Predict breed from extracted features"""
        # TODO: Implement breed classification model
        # For now, return mock prediction
        return {
            'breed': 'golden_retriever',
            'confidence': 0.85
        }
    
    def _assess_feature_quality(self, features: torch.Tensor) -> float:
        """Assess quality of extracted features"""
        # Simple quality metric based on feature magnitude distribution
        magnitude = torch.norm(features)
        quality = min(1.0, magnitude.item() / 10.0)  # Normalize to [0, 1]
        return quality

# Global extractor instance
feature_extractor = PetFeatureExtractor()

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    await feature_extractor.load_models()

@app.post("/extract-features")
async def extract_features(request: Dict[str, Any]):
    """Extract features from pet photos"""
    try:
        order_id = request.get('order_id')
        photo_urls = request.get('photo_urls', [])
        
        if not order_id or not photo_urls:
            raise HTTPException(status_code=400, detail="Missing order_id or photo_urls")
        
        # Process photos
        result = await feature_extractor.process_photos(order_id, photo_urls)
        
        # Upload result to S3
        output_key = f"{order_id}/features.json"
        s3_client.put_object(
            Bucket='petplantr-processing-dev',
            Key=output_key,
            Body=json.dumps(result),
            ContentType='application/json'
        )
        
        return {
            'success': True,
            'order_id': order_id,
            'output_path': f"s3://petplantr-processing-dev/{output_key}",
            'features_extracted': len(photo_urls),
            'breed_prediction': result['breed_prediction']
        }
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'feature-extraction',
        'gpu_available': torch.cuda.is_available(),
        'model_loaded': feature_extractor.model is not None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
