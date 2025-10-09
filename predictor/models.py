"""
ML model wrapper for Virtual Memory Manager predictions.
Handles model loading, feature creation, and prediction logic.
"""

import numpy as np
import joblib
import json
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VMMPredictor:
    """ML model wrapper for Virtual Memory Manager page prediction."""
    
    def __init__(self, model_path: str = "model.pkl"):
        self.model = None
        self.metadata = None
        self.model_path = model_path
        self.is_loaded = False
        
    def load_model(self) -> bool:
        """Load the trained model and metadata."""
        try:
            # Load model
            self.model = joblib.load(self.model_path)
            
            # Load metadata
            metadata_path = self.model_path.replace('.pkl', '_metadata.json')
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            
            self.is_loaded = True
            logger.info(f"Model loaded successfully: {self.metadata['model_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def create_features(self, recent_accesses: List[int]) -> np.ndarray:
        """Create feature vector from recent access pattern."""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        window_size = self.metadata['window_size']
        page_range = self.metadata['page_range']
        
        # Pad or truncate to window size
        if len(recent_accesses) < window_size:
            # Pad with -1 (invalid page)
            padded_accesses = recent_accesses + [-1] * (window_size - len(recent_accesses))
        else:
            # Take last window_size accesses
            padded_accesses = recent_accesses[-window_size:]
        
        # Create feature vector
        features = list(padded_accesses)
        
        # Add statistical features
        valid_accesses = [p for p in recent_accesses if p >= 0]
        
        if valid_accesses:
            unique_pages = len(set(valid_accesses))
            features.append(unique_pages)
            
            # Access frequency
            page_counts = {}
            for page in valid_accesses:
                page_counts[page] = page_counts.get(page, 0) + 1
            
            max_freq = max(page_counts.values())
            avg_freq = np.mean(list(page_counts.values()))
            features.extend([max_freq, avg_freq])
            
            # Pattern detection
            sequential_count = 0
            for i in range(len(valid_accesses) - 1):
                if valid_accesses[i+1] == (valid_accesses[i] + 1) % page_range:
                    sequential_count += 1
            features.append(sequential_count)
            
            # Stride patterns
            stride_count = 0
            if len(valid_accesses) >= 3:
                for stride in [2, 4, 8]:
                    for i in range(len(valid_accesses) - stride):
                        if valid_accesses[i+stride] == (valid_accesses[i] + stride) % page_range:
                            stride_count += 1
            features.append(stride_count)
            
            # Locality features
            if len(valid_accesses) > 1:
                page_distances = []
                for i in range(len(valid_accesses) - 1):
                    dist = abs(valid_accesses[i+1] - valid_accesses[i])
                    page_distances.append(min(dist, page_range - dist))
                features.extend([np.mean(page_distances), np.std(page_distances)])
            else:
                features.extend([0, 0])
        else:
            # No valid accesses
            features.extend([0, 0, 0, 0, 0, 0, 0])
        
        return np.array(features).reshape(1, -1)
    
    def predict_pages(self, recent_accesses: List[int], top_k: int = 10) -> List[Dict[str, Any]]:
        """Predict most likely pages to be accessed next."""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        # Create features
        features = self.create_features(recent_accesses)
        
        # Get prediction probabilities for all pages
        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(features)[0]
            # For binary classification, we need to handle the case where model predicts
            # probability for each page individually
            if probabilities.shape[0] == 2:  # Binary classification
                page_probs = probabilities[1]  # Positive class probabilities
            else:
                page_probs = probabilities
        else:
            # For models without predict_proba, use decision function
            if hasattr(self.model, 'decision_function'):
                scores = self.model.decision_function(features)[0]
                page_probs = 1 / (1 + np.exp(-scores))  # Sigmoid transformation
            else:
                # Fallback: use predictions as binary scores
                predictions = self.model.predict(features)[0]
                page_probs = predictions.astype(float)
        
        # Get top-k pages
        if len(page_probs) == self.metadata['page_range']:
            # Model predicts for all pages
            top_indices = np.argsort(page_probs)[-top_k:][::-1]
            results = []
            for idx in top_indices:
                results.append({
                    'page': int(idx),
                    'score': float(page_probs[idx])
                })
        else:
            # Model predicts for subset of pages, need to map back
            # This is a simplified approach - in practice, you'd need more sophisticated mapping
            results = []
            for i, prob in enumerate(page_probs[:top_k]):
                results.append({
                    'page': int(i),
                    'score': float(prob)
                })
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.is_loaded:
            return {"error": "Model not loaded"}
        
        return {
            "model_name": self.metadata.get('model_name', 'unknown'),
            "page_range": self.metadata.get('page_range', 0),
            "window_size": self.metadata.get('window_size', 0),
            "prediction_horizon": self.metadata.get('prediction_horizon', 0),
            "feature_names": self.metadata.get('feature_names', []),
            "performance": self.metadata.get('performance', {})
        }
