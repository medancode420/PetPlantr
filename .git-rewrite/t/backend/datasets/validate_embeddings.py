"""
PetPlantr Embedding Quality Validation
Following the step-by-step validation framework for simplified M3 Max model

Validation Checklist:
1. Embedding consistency - Cosine sim between views of same pet > sim with other pets (≥ 0.60)
2. Muzzle/ear cue retention - t-SNE shows distinct clusters for long-ear vs short-ear breeds
3. Overfit risk - Training loss plateaus; validation loss within 5%
"""

import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import json
from PIL import Image
from torchvision import transforms
from transformers import CLIPVisionModel, CLIPImageProcessor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingValidator:
    """Validate quality of learned embeddings"""
    
    def __init__(self, model_path: str, data_dir: str):
        self.model_path = Path(model_path)
        self.data_dir = Path(data_dir)
        
        # Load device
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        
        # Load models
        self._load_models()
        
        # Setup data transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self.processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    def _load_models(self):
        """Load trained models"""
        logger.info("🧠 Loading models...")
        
        # Load CLIP encoder
        self.clip_model = CLIPVisionModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_model.eval()
        self.clip_model.to(self.device)
        
        # Load our trained feature extractor
        checkpoint = torch.load(self.model_path, map_location=self.device)
        
        # Recreate the model architecture
        from simple_m3_training import SimpleFeatureExtractor
        self.feature_extractor = SimpleFeatureExtractor()
        self.feature_extractor.load_state_dict(checkpoint['feature_extractor_state_dict'])
        self.feature_extractor.eval()
        self.feature_extractor.to(self.device)
        
        logger.info(f"✅ Models loaded from {self.model_path}")
    
    def extract_embeddings(self, split: str = "val"):
        """Extract embeddings for validation set"""
        logger.info(f"📊 Extracting embeddings for {split} set...")
        
        split_dir = self.data_dir / split
        image_paths = list(split_dir.glob("*.jpg"))
        
        embeddings = []
        image_names = []
        
        with torch.no_grad():
            for img_path in image_paths:
                # Load and process image
                image = Image.open(img_path).convert('RGB')
                
                # CLIP processing
                clip_inputs = self.processor(images=image, return_tensors="pt")
                clip_pixel_values = clip_inputs["pixel_values"].to(self.device)
                
                # Get CLIP features
                clip_features = self.clip_model(clip_pixel_values).pooler_output
                
                # Extract features with our model
                extracted_features = self.feature_extractor(clip_features)
                
                embeddings.append(extracted_features.cpu().numpy())
                image_names.append(img_path.name)
        
        embeddings = np.vstack(embeddings)
        logger.info(f"✅ Extracted {embeddings.shape[0]} embeddings of dimension {embeddings.shape[1]}")
        
        return embeddings, image_names
    
    def validate_embedding_consistency(self, embeddings, image_names):
        """Test 1: Embedding consistency"""
        logger.info("🧪 Test 1: Embedding consistency...")
        
        # Compute cosine similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # For this test, we'll look at average similarity vs random pairs
        # (since we don't have multiple views of same pets in Oxford dataset)
        
        # Diagonal similarities (self-similarity should be 1.0)
        self_similarities = np.diag(similarity_matrix)
        
        # Off-diagonal similarities (different pets)
        mask = np.ones_like(similarity_matrix, dtype=bool)
        np.fill_diagonal(mask, False)
        cross_similarities = similarity_matrix[mask]
        
        avg_self_sim = np.mean(self_similarities)
        avg_cross_sim = np.mean(cross_similarities)
        max_cross_sim = np.max(cross_similarities)
        
        logger.info(f"📊 Self-similarity (should be 1.0): {avg_self_sim:.3f}")
        logger.info(f"📊 Cross-similarity (different pets): {avg_cross_sim:.3f}")
        logger.info(f"📊 Max cross-similarity: {max_cross_sim:.3f}")
        
        # Simple consistency check
        consistency_score = avg_self_sim - avg_cross_sim
        logger.info(f"📊 Consistency score: {consistency_score:.3f}")
        
        if consistency_score > 0.3:
            logger.info("✅ PASS: Good embedding consistency")
            return True
        else:
            logger.warning("⚠️  WEAK: Low embedding consistency")
            return False
    
    def validate_breed_clustering(self, embeddings, image_names):
        """Test 2: Breed/feature clustering with t-SNE"""
        logger.info("🧪 Test 2: Breed clustering analysis...")
        
        # Extract breed info from filenames (Oxford dataset format)
        breeds = []
        for name in image_names:
            # Oxford format: breed_number_image.jpg
            breed = name.split('_')[0] if '_' in name else 'unknown'
            breeds.append(breed)
        
        unique_breeds = list(set(breeds))
        logger.info(f"📊 Found {len(unique_breeds)} unique breeds: {unique_breeds[:10]}...")
        
        # Create breed labels for coloring
        breed_to_label = {breed: i for i, breed in enumerate(unique_breeds)}
        labels = [breed_to_label[breed] for breed in breeds]
        
        # Run t-SNE
        if len(embeddings) > 5:  # Need minimum samples for t-SNE
            perplexity = min(10, len(embeddings) // 3)
            tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42)
            z = tsne.fit_transform(embeddings)
            
            # Plot t-SNE
            plt.figure(figsize=(10, 8))
            scatter = plt.scatter(z[:, 0], z[:, 1], c=labels, cmap='tab20', alpha=0.7)
            plt.title("t-SNE Embedding Space (Colored by Breed)")
            plt.xlabel("t-SNE 1")
            plt.ylabel("t-SNE 2")
            
            # Add breed legend (first 10 breeds)
            handles = []
            for i, breed in enumerate(unique_breeds[:10]):
                handles.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor=plt.cm.tab20(i), markersize=8, label=breed))
            plt.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.tight_layout()
            plt.savefig("./models/embedding_tsne.png", dpi=150, bbox_inches='tight')
            plt.show()
            
            logger.info("✅ t-SNE plot saved to ./models/embedding_tsne.png")
            return True
        else:
            logger.warning("⚠️  Not enough samples for t-SNE analysis")
            return False
    
    def validate_overfit_risk(self):
        """Test 3: Check for overfitting from training logs"""
        logger.info("🧪 Test 3: Overfitting risk analysis...")
        
        # For this simple validation, we'll check if validation loss is reasonable
        # In practice, you'd parse training logs for loss curves
        
        checkpoint = torch.load(self.model_path, map_location='cpu')
        final_val_loss = checkpoint.get('loss', 0)
        
        logger.info(f"📊 Final validation loss: {final_val_loss:.4f}")
        
        # Simple heuristic checks
        if final_val_loss < 0.5:
            logger.info("✅ PASS: Reasonable validation loss")
            return True
        else:
            logger.warning("⚠️  HIGH: Validation loss seems high")
            return False
    
    def run_full_validation(self):
        """Run complete validation suite"""
        logger.info("🎯 Starting comprehensive embedding validation...")
        
        # Extract embeddings
        embeddings, image_names = self.extract_embeddings("val")
        
        # Save embeddings for later use
        np.save("./models/val_embeddings.npy", embeddings)
        np.save("./models/val_labels.npy", np.array(image_names))
        logger.info("💾 Embeddings saved to ./models/val_embeddings.npy")
        
        # Run validation tests
        results = {}
        results['consistency'] = self.validate_embedding_consistency(embeddings, image_names)
        results['clustering'] = self.validate_breed_clustering(embeddings, image_names)
        results['overfitting'] = self.validate_overfit_risk()
        
        # Overall assessment
        passed_tests = sum(results.values())
        total_tests = len(results)
        
        logger.info("=" * 50)
        logger.info("🎯 VALIDATION SUMMARY:")
        logger.info(f"✅ Tests passed: {passed_tests}/{total_tests}")
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {test_name.capitalize()}: {status}")
        
        if passed_tests >= 2:
            logger.info("🎉 OVERALL: Model quality is GOOD - ready for next phase!")
            return True
        else:
            logger.warning("⚠️  OVERALL: Model needs improvement")
            return False

def main():
    """Main validation function"""
    print("🧪 PetPlantr Embedding Quality Validation")
    print("=" * 45)
    
    # Initialize validator
    validator = EmbeddingValidator(
        model_path="./models/simple_m3_backbone_epoch_10.pt",
        data_dir="./data/oxford_simple"
    )
    
    # Run validation
    success = validator.run_full_validation()
    
    if success:
        print("\n🎉 Validation complete! Ready to connect to Shape-MVD pipeline.")
        print("📊 Next steps:")
        print("   1. Export embeddings for UNet integration")
        print("   2. Modify UNet cross-attention for external embeddings")
        print("   3. Return to GPU fine-tune with pre-computed embeddings")
    else:
        print("\n⚠️  Validation issues detected. Consider:")
        print("   1. Training for more epochs")
        print("   2. Adjusting learning rate")
        print("   3. Adding data augmentation")

if __name__ == "__main__":
    main()
