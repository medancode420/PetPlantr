#!/usr/bin/env python3
"""
Enable mock breed detection for testing
"""
import sys
import os
sys.path.insert(0, '.')

from src.services import breed_detection as svc

# Mock the model info to show it's loaded
original_get_model_info = svc.get_model_info
def mock_get_model_info():
    return {
        'loaded': True,
        'model_version': 'mock-v1.0',
        'device': 'cpu',
        'num_breeds': 14
    }
svc.get_model_info = mock_get_model_info

# Mock the predict function
original_predict = svc.predict
async def mock_predict(image=None, confidence_threshold=0.8, top_k=5):
    return {
        'predicted_breed': 'Golden Retriever',
        'confidence': 0.92,
        'top_predictions': [
            {'Golden Retriever': 0.92},
            {'Labrador Retriever': 0.85},
            {'German Shepherd': 0.78}
        ],
        'is_high_confidence': True,
        'model_version': 'mock-v1.0'
    }
svc.predict = mock_predict

print('✅ Mock breed detection service enabled')
