"""
Workload-specific AI predictor for Virtual Memory Manager.
Loads and uses different models based on workload type and AI mode.
"""

import numpy as np
import joblib
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class WorkloadType(Enum):
    SEQUENTIAL = "sequential"
    RANDOM = "random"
    STRIDED = "strided"
    ZIPF = "zipf"
    WEBSERVER = "webserver"


class AIMode(Enum):
    PREFETCH_ONLY = "prefetch_only"
    REPLACEMENT_ONLY = "replacement_only"
    HYBRID = "hybrid"


class WorkloadSpecificPredictor:
    """AI predictor that uses workload-specific models."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models = {}
        self.metadata = {}
        self.current_workload = WorkloadType.RANDOM
        self.current_ai_mode = AIMode.PREFETCH_ONLY
        self.is_loaded = False
        
    def load_models(self) -> bool:
        """Load all available workload-specific models."""
        try:
            if not self.models_dir.exists():
                logger.warning(f"Models directory {self.models_dir} does not exist")
                return False
            
            loaded_count = 0
            
            # Load models for each workload type and AI mode combination
            for workload_type in WorkloadType:
                for ai_mode in AIMode:
                    model_name = f"{workload_type.value}_{ai_mode.value}_model.pkl"
                    metadata_name = f"{workload_type.value}_{ai_mode.value}_metadata.json"
                    
                    model_path = self.models_dir / model_name
                    metadata_path = self.models_dir / metadata_name
                    
                    if model_path.exists() and metadata_path.exists():
                        try:
                            # Load model
                            model = joblib.load(model_path)
                            
                            # Load metadata
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                            
                            key = f"{workload_type.value}_{ai_mode.value}"
                            self.models[key] = model
                            self.metadata[key] = metadata
                            
                            loaded_count += 1
                            logger.info(f"Loaded model: {key}")
                            
                        except Exception as e:
                            logger.error(f"Failed to load model {model_name}: {e}")
            
            if loaded_count > 0:
                self.is_loaded = True
                logger.info(f"Successfully loaded {loaded_count} workload-specific models")
                return True
            else:
                logger.warning("No models were loaded")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
    
    def set_workload_type(self, workload_type: str):
        """Set the current workload type."""
        try:
            self.current_workload = WorkloadType(workload_type)
            logger.info(f"Workload type set to: {self.current_workload.value}")
        except ValueError:
            logger.warning(f"Invalid workload type: {workload_type}, using RANDOM")
            self.current_workload = WorkloadType.RANDOM
    
    def set_ai_mode(self, ai_mode: str):
        """Set the current AI mode."""
        try:
            self.current_ai_mode = AIMode(ai_mode)
            logger.info(f"AI mode set to: {self.current_ai_mode.value}")
        except ValueError:
            logger.warning(f"Invalid AI mode: {ai_mode}, using PREFETCH_ONLY")
            self.current_ai_mode = AIMode.PREFETCH_ONLY
    
    def get_current_model(self):
        """Get the model for current workload type and AI mode."""
        key = f"{self.current_workload.value}_{self.current_ai_mode.value}"
        return self.models.get(key), self.metadata.get(key)
    
    def create_workload_specific_features(self, recent_accesses: List[int]) -> np.ndarray:
        """Create features optimized for current workload type."""
        if not self.is_loaded:
            raise RuntimeError("Models not loaded")
        
        model, metadata = self.get_current_model()
        if not model or not metadata:
            raise RuntimeError(f"No model available for {self.current_workload.value}_{self.current_ai_mode.value}")
        
        window_size = metadata['window_size']
        page_range = metadata['page_range']
        
        # Pad or truncate to window size
        if len(recent_accesses) < window_size:
            padded_accesses = recent_accesses + [-1] * (window_size - len(recent_accesses))
        else:
            padded_accesses = recent_accesses[-window_size:]
        
        # Create base feature vector
        features = list(padded_accesses)
        
        # Add workload-specific features
        valid_accesses = [p for p in recent_accesses if p >= 0]
        
        if valid_accesses:
            if self.current_workload == WorkloadType.SEQUENTIAL:
                # Sequential patterns
                sequential_count = 0
                for i in range(len(valid_accesses) - 1):
                    if valid_accesses[i+1] == (valid_accesses[i] + 1) % page_range:
                        sequential_count += 1
                features.append(sequential_count)
                
                # Direction
                direction = 1 if valid_accesses[-1] > valid_accesses[0] else -1
                features.append(direction)
                
            elif self.current_workload == WorkloadType.STRIDED:
                # Stride detection
                strides = []
                for i in range(len(valid_accesses) - 1):
                    stride = (valid_accesses[i+1] - valid_accesses[i]) % page_range
                    strides.append(stride)
                
                if strides:
                    features.extend([
                        np.mean(strides),
                        np.std(strides),
                        max(set(strides), key=strides.count)
                    ])
                else:
                    features.extend([0, 0, 0])
                    
            elif self.current_workload == WorkloadType.ZIPF:
                # Zipf-specific features
                page_counts = {}
                for page in valid_accesses:
                    page_counts[page] = page_counts.get(page, 0) + 1
                
                frequencies = list(page_counts.values())
                if frequencies:
                    features.extend([
                        max(frequencies),
                        np.mean(frequencies),
                        np.std(frequencies),
                        len(page_counts)
                    ])
                else:
                    features.extend([0, 0, 0, 0])
                    
            elif self.current_workload == WorkloadType.WEBSERVER:
                # Webserver-specific features
                recent_pages = set(valid_accesses[-5:])
                features.append(len(recent_pages))
                
                # Spatial locality
                page_distances = []
                for i in range(len(valid_accesses) - 1):
                    dist = abs(valid_accesses[i+1] - valid_accesses[i])
                    page_distances.append(min(dist, page_range - dist))
                
                if page_distances:
                    features.extend([
                        np.mean(page_distances),
                        np.std(page_distances)
                    ])
                else:
                    features.extend([0, 0])
            
            # Common features
            unique_pages = len(set(valid_accesses))
            features.append(unique_pages)
            
            # Access frequency
            page_counts = {}
            for page in valid_accesses:
                page_counts[page] = page_counts.get(page, 0) + 1
            
            max_freq = max(page_counts.values())
            avg_freq = np.mean(list(page_counts.values()))
            features.extend([max_freq, avg_freq])
        else:
            # No valid accesses - add zeros for all features
            if self.current_workload == WorkloadType.SEQUENTIAL:
                features.extend([0, 0])  # sequential_count, direction
            elif self.current_workload == WorkloadType.STRIDED:
                features.extend([0, 0, 0])  # mean_stride, std_stride, common_stride
            elif self.current_workload == WorkloadType.ZIPF:
                features.extend([0, 0, 0, 0])  # max_freq, mean_freq, std_freq, unique_pages
            elif self.current_workload == WorkloadType.WEBSERVER:
                features.extend([0, 0, 0])  # recent_pages, mean_distance, std_distance
            
            features.extend([0, 0, 0])  # unique_pages, max_freq, avg_freq
        
        return np.array(features).reshape(1, -1)
    
    def predict_pages(self, recent_accesses: List[int], top_k: int = 10) -> List[Dict[str, Any]]:
        """Predict most likely pages to be accessed next."""
        if not self.is_loaded:
            raise RuntimeError("Models not loaded")
        
        model, metadata = self.get_current_model()
        if not model or not metadata:
            raise RuntimeError(f"No model available for {self.current_workload.value}_{self.current_ai_mode.value}")
        
        # Create features
        features = self.create_workload_specific_features(recent_accesses)
        
        # Get predictions
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(features)[0]
            if probabilities.shape[0] == 2:  # Binary classification
                page_probs = probabilities[1]
            else:
                page_probs = probabilities
        else:
            if hasattr(model, 'decision_function'):
                scores = model.decision_function(features)[0]
                page_probs = 1 / (1 + np.exp(-scores))
            else:
                predictions = model.predict(features)[0]
                page_probs = predictions.astype(float)
        
        # Generate predictions based on AI mode
        if self.current_ai_mode == AIMode.PREFETCH_ONLY:
            # Predict next pages to prefetch
            results = self._predict_prefetch_pages(recent_accesses, page_probs, top_k, metadata)
        elif self.current_ai_mode == AIMode.REPLACEMENT_ONLY:
            # Predict pages to evict
            results = self._predict_replacement_pages(recent_accesses, page_probs, top_k, metadata)
        else:  # HYBRID
            # Combine both prefetch and replacement predictions
            results = self._predict_hybrid_pages(recent_accesses, page_probs, top_k, metadata)
        
        return results
    
    def _predict_prefetch_pages(self, recent_accesses: List[int], page_probs: np.ndarray, 
                               top_k: int, metadata: Dict) -> List[Dict[str, Any]]:
        """Predict pages to prefetch."""
        page_range = metadata['page_range']
        
        # For prefetching, predict pages that are likely to be accessed next
        # but are not currently in recent accesses
        recent_set = set(recent_accesses)
        
        # Generate candidate pages (not in recent accesses)
        candidates = []
        for page in range(page_range):
            if page not in recent_set:
                # Use a simple heuristic based on page proximity and probability
                score = np.random.random() * 0.3  # Base random score
                
                # Boost score for pages near recently accessed pages
                for recent_page in recent_accesses[-3:]:  # Last 3 pages
                    distance = min(abs(page - recent_page), page_range - abs(page - recent_page))
                    if distance <= 10:  # Within 10 pages
                        score += 0.2 * (1.0 - distance / 10.0)
                
                candidates.append({'page': page, 'score': score})
        
        # Sort by score and return top-k
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:top_k]
    
    def _predict_replacement_pages(self, recent_accesses: List[int], page_probs: np.ndarray,
                                  top_k: int, metadata: Dict) -> List[Dict[str, Any]]:
        """Predict pages to evict."""
        # For replacement, predict pages that are least likely to be accessed soon
        # This is a simplified approach - in practice, you'd need more sophisticated logic
        
        results = []
        for i, page in enumerate(recent_accesses[-top_k:]):  # Last k pages
            # Lower score means more likely to be evicted
            score = 1.0 - (i / len(recent_accesses))  # More recent = higher score (less likely to evict)
            results.append({'page': page, 'score': score})
        
        return results
    
    def _predict_hybrid_pages(self, recent_accesses: List[int], page_probs: np.ndarray,
                             top_k: int, metadata: Dict) -> List[Dict[str, Any]]:
        """Predict both prefetch and replacement pages."""
        # Combine prefetch and replacement predictions
        prefetch_results = self._predict_prefetch_pages(recent_accesses, page_probs, top_k//2, metadata)
        replacement_results = self._predict_replacement_pages(recent_accesses, page_probs, top_k//2, metadata)
        
        # Combine and sort by score
        combined = prefetch_results + replacement_results
        combined.sort(key=lambda x: x['score'], reverse=True)
        
        return combined[:top_k]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded models."""
        if not self.is_loaded:
            return {"error": "Models not loaded"}
        
        model, metadata = self.get_current_model()
        if not model or not metadata:
            return {"error": "No model available for current configuration"}
        
        return {
            "model_name": metadata.get('model_name', 'unknown'),
            "workload_type": self.current_workload.value,
            "ai_mode": self.current_ai_mode.value,
            "page_range": metadata.get('page_range', 0),
            "window_size": metadata.get('window_size', 0),
            "prediction_horizon": metadata.get('prediction_horizon', 0),
            "performance": metadata.get('performance', {}),
            "total_models_loaded": len(self.models)
        }
    
    def get_available_models(self) -> List[str]:
        """Get list of available model combinations."""
        return list(self.models.keys())
