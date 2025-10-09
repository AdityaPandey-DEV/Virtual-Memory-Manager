#!/usr/bin/env python3
"""
Train workload-specific and AI mode-specific models for Virtual Memory Manager.
This script creates specialized models for different workload types and AI modes.
"""

import numpy as np
import pandas as pd
import json
import joblib
from pathlib import Path
from typing import Tuple, List, Dict, Any
import argparse
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
import xgboost as xgb
from generate_traces import TraceGenerator, WorkloadType
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WorkloadSpecificTrainer:
    """Trains specialized ML models for different workload types and AI modes."""
    
    def __init__(self, page_range: int = 1000, window_size: int = 10, 
                 prediction_horizon: int = 5):
        self.page_range = page_range
        self.window_size = window_size
        self.prediction_horizon = prediction_horizon
        self.models = {}
        self.feature_importance = {}
        
        # Define workload types and AI modes
        self.workload_types = [
            WorkloadType.SEQUENTIAL,
            WorkloadType.RANDOM, 
            WorkloadType.STRIDED,
            WorkloadType.ZIPF,
            WorkloadType.WEBSERVER
        ]
        
        self.ai_modes = ['prefetch_only', 'replacement_only', 'hybrid']
        
    def generate_workload_specific_data(self, workload_type: WorkloadType, 
                                      num_samples: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """Generate training data for specific workload type."""
        logger.info(f"Generating data for workload: {workload_type.value}")
        
        generator = TraceGenerator(self.page_range)
        X, y = [], []
        
        for _ in range(num_samples):
            # Generate trace based on workload type
            if workload_type == WorkloadType.SEQUENTIAL:
                trace = generator.generate_sequential_trace(50)
            elif workload_type == WorkloadType.RANDOM:
                trace = generator.generate_random_trace(50)
            elif workload_type == WorkloadType.STRIDED:
                stride = np.random.randint(1, 10)
                trace = generator.generate_strided_trace(50, stride)
            elif workload_type == WorkloadType.ZIPF:
                alpha = np.random.uniform(0.5, 2.0)
                trace = generator.generate_zipf_trace(50, alpha)
            elif workload_type == WorkloadType.WEBSERVER:
                trace = generator.generate_webserver_trace(50)
            else:
                trace = generator.generate_random_trace(50)
            
            # Create training samples from trace
            for i in range(self.window_size, len(trace) - self.prediction_horizon):
                recent_accesses = trace[i-self.window_size:i]
                future_accesses = trace[i:i+self.prediction_horizon]
                
                X.append(recent_accesses)
                
                # Create target based on AI mode
                # For now, predict if next page will be accessed
                target = 1 if trace[i] in future_accesses else 0
                y.append(target)
        
        return np.array(X), np.array(y)
    
    def create_workload_specific_features(self, X: np.ndarray, workload_type: WorkloadType) -> np.ndarray:
        """Create features optimized for specific workload type."""
        features = []
        
        for recent_accesses in X:
            feature_vector = list(recent_accesses)
            
            # Workload-specific feature engineering
            if workload_type == WorkloadType.SEQUENTIAL:
                # Sequential patterns
                sequential_count = 0
                for i in range(len(recent_accesses) - 1):
                    if recent_accesses[i+1] == (recent_accesses[i] + 1) % self.page_range:
                        sequential_count += 1
                feature_vector.append(sequential_count)
                
                # Direction (forward/backward)
                direction = 1 if recent_accesses[-1] > recent_accesses[0] else -1
                feature_vector.append(direction)
                
            elif workload_type == WorkloadType.STRIDED:
                # Stride detection
                strides = []
                for i in range(len(recent_accesses) - 1):
                    stride = (recent_accesses[i+1] - recent_accesses[i]) % self.page_range
                    strides.append(stride)
                
                if strides:
                    feature_vector.extend([
                        np.mean(strides),
                        np.std(strides),
                        max(set(strides), key=strides.count)  # Most common stride
                    ])
                else:
                    feature_vector.extend([0, 0, 0])
                    
            elif workload_type == WorkloadType.ZIPF:
                # Zipf-specific features
                page_counts = {}
                for page in recent_accesses:
                    page_counts[page] = page_counts.get(page, 0) + 1
                
                # Frequency distribution features
                frequencies = list(page_counts.values())
                if frequencies:
                    feature_vector.extend([
                        max(frequencies),
                        np.mean(frequencies),
                        np.std(frequencies),
                        len(page_counts)  # Unique pages
                    ])
                else:
                    feature_vector.extend([0, 0, 0, 0])
                    
            elif workload_type == WorkloadType.WEBSERVER:
                # Webserver-specific features (bursty, locality)
                # Time locality (recent pages)
                recent_pages = set(recent_accesses[-5:])
                feature_vector.append(len(recent_pages))
                
                # Spatial locality
                page_distances = []
                for i in range(len(recent_accesses) - 1):
                    dist = abs(recent_accesses[i+1] - recent_accesses[i])
                    page_distances.append(min(dist, self.page_range - dist))
                
                if page_distances:
                    feature_vector.extend([
                        np.mean(page_distances),
                        np.std(page_distances)
                    ])
                else:
                    feature_vector.extend([0, 0])
            
            # Common features for all workload types
            unique_pages = len(set(recent_accesses))
            feature_vector.append(unique_pages)
            
            # Access frequency
            page_counts = {}
            for page in recent_accesses:
                page_counts[page] = page_counts.get(page, 0) + 1
            
            max_freq = max(page_counts.values()) if page_counts else 0
            avg_freq = np.mean(list(page_counts.values())) if page_counts else 0
            feature_vector.extend([max_freq, avg_freq])
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def train_workload_model(self, workload_type: WorkloadType, ai_mode: str) -> Dict[str, Any]:
        """Train model for specific workload type and AI mode."""
        logger.info(f"Training model for {workload_type.value} workload, {ai_mode} mode")
        
        # Generate training data
        X, y = self.generate_workload_specific_data(workload_type)
        
        # Create workload-specific features
        X_features = self.create_workload_specific_features(X, workload_type)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_features, y, test_size=0.2, random_state=42, stratify=None
        )
        
        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")
        logger.info(f"Positive class ratio: {y.sum() / y.size:.3f}")
        
        # Model selection based on workload type
        if workload_type == WorkloadType.SEQUENTIAL:
            # Sequential patterns work well with linear models
            model = LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced')
        elif workload_type == WorkloadType.RANDOM:
            # Random patterns need ensemble methods
            model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
        elif workload_type == WorkloadType.STRIDED:
            # Strided patterns benefit from gradient boosting
            model = xgb.XGBClassifier(random_state=42, eval_metric='logloss', scale_pos_weight=10)
        elif workload_type == WorkloadType.ZIPF:
            # Zipf patterns work well with XGBoost
            model = xgb.XGBClassifier(random_state=42, eval_metric='logloss', scale_pos_weight=5)
        else:  # WEBSERVER
            # Webserver patterns benefit from ensemble methods
            model = RandomForestClassifier(n_estimators=150, random_state=42, class_weight='balanced')
        
        # Train model
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted', zero_division=0
        )
        
        logger.info(f"Model performance - Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")
        
        return {
            'model': model,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'workload_type': workload_type.value,
            'ai_mode': ai_mode,
            'feature_importance': getattr(model, 'feature_importances_', None)
        }
    
    def train_all_models(self):
        """Train models for all workload types and AI modes."""
        logger.info("Starting training for all workload types and AI modes")
        
        # Create models directory
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        all_results = {}
        
        for workload_type in self.workload_types:
            for ai_mode in self.ai_modes:
                try:
                    # Train model
                    result = self.train_workload_model(workload_type, ai_mode)
                    
                    # Save model
                    model_name = f"{workload_type.value}_{ai_mode}_model.pkl"
                    model_path = models_dir / model_name
                    joblib.dump(result['model'], model_path)
                    
                    # Save metadata
                    metadata = {
                        'model_name': f"{workload_type.value}_{ai_mode}_model",
                        'workload_type': workload_type.value,
                        'ai_mode': ai_mode,
                        'page_range': self.page_range,
                        'window_size': self.window_size,
                        'prediction_horizon': self.prediction_horizon,
                        'performance': {
                            'precision': result['precision'],
                            'recall': result['recall'],
                            'f1_score': result['f1_score']
                        },
                        'model_path': str(model_path)
                    }
                    
                    metadata_path = models_dir / f"{workload_type.value}_{ai_mode}_metadata.json"
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    all_results[f"{workload_type.value}_{ai_mode}"] = result
                    logger.info(f"Saved model: {model_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to train model for {workload_type.value}_{ai_mode}: {e}")
        
        # Save training summary
        summary = {
            'training_date': pd.Timestamp.now().isoformat(),
            'total_models': len(all_results),
            'workload_types': [wt.value for wt in self.workload_types],
            'ai_modes': self.ai_modes,
            'results': {
                name: {
                    'precision': result['precision'],
                    'recall': result['recall'],
                    'f1_score': result['f1_score']
                }
                for name, result in all_results.items()
            }
        }
        
        with open(models_dir / "training_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Training completed! {len(all_results)} models saved to {models_dir}")
        return all_results


def main():
    parser = argparse.ArgumentParser(description='Train workload-specific VMM predictor models')
    parser.add_argument('--page-range', type=int, default=1000,
                       help='Range of page numbers')
    parser.add_argument('--window-size', type=int, default=10,
                       help='Size of recent access window')
    parser.add_argument('--prediction-horizon', type=int, default=5,
                       help='Number of future accesses to predict')
    parser.add_argument('--samples-per-workload', type=int, default=10000,
                       help='Number of training samples per workload type')
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = WorkloadSpecificTrainer(
        page_range=args.page_range,
        window_size=args.window_size,
        prediction_horizon=args.prediction_horizon
    )
    
    # Train all models
    results = trainer.train_all_models()
    
    logger.info("Training completed successfully!")
    logger.info(f"Trained {len(results)} models for different workload types and AI modes")


if __name__ == '__main__':
    main()
