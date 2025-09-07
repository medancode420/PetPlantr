#!/usr/bin/env python3
"""
PetPlantr QA System - Human Label Quality Assurance
Story 1.2: Human label QA pass (95% precision)
"""

from pathlib import Path
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import random
from PIL import Image
import io
import base64

# Optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None  # type: ignore
    PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None  # type: ignore
    NUMPY_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QASample:
    """QA sample for human review"""
    filename: str
    breed: str
    predicted_breed: str
    confidence: float
    image_data: str  # base64 encoded
    qa_status: str = "pending"  # pending, correct, incorrect
    human_label: Optional[str] = None
    reviewed_at: Optional[datetime] = None

class BreedQASystem:
    """Human QA system for breed classification validation"""

    def __init__(self, manifest_path: str = "data/manifest.csv", qa_data_path: str = "data/qa_samples.json"):
        self.manifest_path = Path(manifest_path)
        self.qa_data_path = Path(qa_data_path)
        self.qa_samples: Dict[str, QASample] = {}
        self.load_manifest()
        self.load_qa_data()

    def load_manifest(self):
        """Load dataset manifest"""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        if PANDAS_AVAILABLE:
            self.manifest_df = pd.read_csv(self.manifest_path)
            logger.info(f"Loaded {len(self.manifest_df)} images from manifest")
        else:
            # Fallback to CSV reading without pandas
            import csv
            self.manifest_data = []
            with open(self.manifest_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.manifest_data.append(row)
            logger.info(f"Loaded {len(self.manifest_data)} images from manifest (no pandas)")
            self.manifest_df = None  # type: ignore

    def load_qa_data(self):
        """Load existing QA data"""
        if self.qa_data_path.exists():
            with open(self.qa_data_path, 'r') as f:
                data = json.load(f)
                for key, sample_data in data.items():
                    sample_data['reviewed_at'] = datetime.fromisoformat(sample_data['reviewed_at']) if sample_data.get('reviewed_at') else None
                    self.qa_samples[key] = QASample(**sample_data)
            logger.info(f"Loaded {len(self.qa_samples)} existing QA samples")
        else:
            logger.info("No existing QA data found, starting fresh")

    def save_qa_data(self):
        """Save QA data to disk"""
        data = {}
        for key, sample in self.qa_samples.items():
            sample_dict = {
                'filename': sample.filename,
                'breed': sample.breed,
                'predicted_breed': sample.predicted_breed,
                'confidence': sample.confidence,
                'image_data': sample.image_data,
                'qa_status': sample.qa_status,
                'human_label': sample.human_label,
                'reviewed_at': sample.reviewed_at.isoformat() if sample.reviewed_at else None
            }
            data[key] = sample_dict

        self.qa_data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.qa_data_path, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_qa_samples(self, num_samples: int = 100, confidence_threshold: float = 0.8):
        """Generate QA samples for human review"""
        if not hasattr(self, 'manifest_data') or not self.manifest_data:
            logger.warning("No manifest data available for QA sample generation")
            return

        # Simple sampling without pandas/numpy
        candidates = self.manifest_data[:min(num_samples, len(self.manifest_data))]

        for row in candidates:
            filename = row['filename']
            if filename in self.qa_samples:
                continue

            actual_breed = row['breed']
            predicted_breed = actual_breed
            confidence = 0.95

            # Simulate some misclassifications
            if random.random() < 0.1:  # 10% misclassification rate
                # Simple breed selection from available breeds
                all_breeds = list(set(r['breed'] for r in self.manifest_data))
                other_breeds = [b for b in all_breeds if b != actual_breed]
                if other_breeds:
                    predicted_breed = random.choice(other_breeds)
                    confidence = random.uniform(0.6, 0.85)

            # Create mock image data
            image_data = f"data:image/jpeg;base64,{base64.b64encode(b'mock_image_data').decode()}"

            qa_sample = QASample(
                filename=filename,
                breed=actual_breed,
                predicted_breed=predicted_breed,
                confidence=confidence,
                image_data=image_data
            )

            self.qa_samples[filename] = qa_sample

        self.save_qa_data()
        logger.info(f"Generated {len(candidates)} QA samples")

    def get_pending_samples(self, limit: int = 10) -> List[QASample]:
        """Get pending QA samples for review"""
        pending = [s for s in self.qa_samples.values() if s.qa_status == "pending"]
        return pending[:limit]

    def submit_qa_review(self, filename: str, human_label: str, is_correct: bool):
        """Submit human QA review"""
        if filename not in self.qa_samples:
            raise ValueError(f"QA sample not found: {filename}")

        sample = self.qa_samples[filename]
        sample.human_label = human_label
        sample.qa_status = "correct" if is_correct else "incorrect"
        sample.reviewed_at = datetime.now()

        self.save_qa_data()
        logger.info(f"QA review submitted for {filename}: {'correct' if is_correct else 'incorrect'}")

    def calculate_precision(self) -> Dict[str, float]:
        """Calculate QA precision metrics"""
        reviewed_samples = [s for s in self.qa_samples.values() if s.qa_status in ["correct", "incorrect"]]

        if not reviewed_samples:
            return {"precision": 0.0, "total_reviewed": 0, "correct": 0, "incorrect": 0}

        correct = sum(1 for s in reviewed_samples if s.qa_status == "correct")
        total = len(reviewed_samples)

        precision = correct / total if total > 0 else 0.0

        return {
            "precision": precision,
            "total_reviewed": total,
            "correct": correct,
            "incorrect": total - correct
        }

    def generate_confusion_report(self) -> Dict[str, Any]:
        """Generate confusion matrix report"""
        reviewed_samples = [s for s in self.qa_samples.values() if s.qa_status in ["correct", "incorrect"]]

        confusion_matrix = {}
        mislabeled_samples = []

        for sample in reviewed_samples:
            pred = sample.predicted_breed
            actual = sample.breed

            if pred not in confusion_matrix:
                confusion_matrix[pred] = {}
            if actual not in confusion_matrix[pred]:
                confusion_matrix[pred][actual] = 0

            confusion_matrix[pred][actual] += 1

            if sample.qa_status == "incorrect":
                mislabeled_samples.append({
                    "filename": sample.filename,
                    "predicted": pred,
                    "actual": actual,
                    "confidence": sample.confidence
                })

        return {
            "confusion_matrix": confusion_matrix,
            "mislabeled_samples": mislabeled_samples,
            "total_mislabeled": len(mislabeled_samples),
            "generated_at": datetime.now().isoformat()
        }

    def export_qa_report(self, output_path: str = "reports/qa_report.json"):
        """Export comprehensive QA report"""
        precision_metrics = self.calculate_precision()
        confusion_report = self.generate_confusion_report()

        report = {
            "qa_metrics": precision_metrics,
            "confusion_analysis": confusion_report,
            "qa_status": "PASS" if precision_metrics["precision"] >= 0.95 else "FAIL",
            "target_precision": 0.95,
            "generated_at": datetime.now().isoformat()
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"QA report exported to {output_file}")
        return report

def main():
    """Main QA system entry point"""
    qa_system = BreedQASystem()

    # Generate QA samples if needed
    if len(qa_system.qa_samples) < 50:
        qa_system.generate_qa_samples(num_samples=100)

    # Export QA report
    report = qa_system.export_qa_report()

    print("🎯 QA System Status Report")
    print("=" * 50)
    print(f"Total QA Samples: {len(qa_system.qa_samples)}")
    print(f"Reviewed Samples: {report['qa_metrics']['total_reviewed']}")
    print(".2%")
    print(f"Status: {report['qa_status']}")
    print(f"Target: {report['target_precision']:.0%}")

    if report['qa_metrics']['total_reviewed'] > 0:
        print(f"Correct: {report['qa_metrics']['correct']}")
        print(f"Incorrect: {report['qa_metrics']['incorrect']}")

if __name__ == "__main__":
    main()
