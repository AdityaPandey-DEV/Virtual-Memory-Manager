#!/usr/bin/env python3
"""
Train AI predictor model for Virtual Memory Manager.
Uses synthetic workload traces to train a model for page prediction.
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


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VMMPredictorTrainer:
    """Trains ML models for Virtual Memory Manager page prediction."""
    
    def __init__(self, page_range: int = 1000, window_size: int = 10, 
                 prediction_horizon: int = 5):
        self.page_range = page_range
        self.window_size = window_size
        self.prediction_horizon = prediction_horizon
        self.models = {}
        self.feature_importance = {}
        
    def load_training_data(self, data_file: str) -> Tuple[np.ndarray, np.ndarray]:
        """Load training data from file."""
        logger.info(f"Loading training data from {data_file}")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        X = np.array(data['X'])
        y = np.array(data['y'])
        
        logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features")
        logger.info(f"Positive class ratio: {y.sum() / y.size:.3f}")
        
        return X, y
    
    def create_features(self, X: np.ndarray) -> np.ndarray:
        """Create additional features from recent access patterns."""
        features = []
        
        for recent_accesses in X:
            # Basic features: recent access pattern
            feature_vector = list(recent_accesses)
            
            # Statistical features
            unique_pages = len(set(recent_accesses))
            feature_vector.append(unique_pages)
            
            # Access frequency features
            page_counts = {}
            for page in recent_accesses:
                page_counts[page] = page_counts.get(page, 0) + 1
            
            # Most frequent page count
            max_freq = max(page_counts.values()) if page_counts else 0
            feature_vector.append(max_freq)
            
            # Average frequency
            avg_freq = np.mean(list(page_counts.values())) if page_counts else 0
            feature_vector.append(avg_freq)
            
            # Sequential pattern detection
            sequential_count = 0
            for i in range(len(recent_accesses) - 1):
                if recent_accesses[i+1] == (recent_accesses[i] + 1) % self.page_range:
                    sequential_count += 1
            feature_vector.append(sequential_count)
            
            # Stride pattern detection
            stride_count = 0
            if len(recent_accesses) >= 3:
                for stride in [2, 4, 8]:
                    for i in range(len(recent_accesses) - stride):
                        if recent_accesses[i+stride] == (recent_accesses[i] + stride) % self.page_range:
                            stride_count += 1
            feature_vector.append(stride_count)
            
            # Locality features
            if len(recent_accesses) > 1:
                page_distances = []
                for i in range(len(recent_accesses) - 1):
                    dist = abs(recent_accesses[i+1] - recent_accesses[i])
                    page_distances.append(min(dist, self.page_range - dist))
                feature_vector.append(np.mean(page_distances))
                feature_vector.append(np.std(page_distances))
            else:
                feature_vector.extend([0, 0])
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def train_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train multiple models and compare performance."""
        logger.info("Creating enhanced features...")
        X_features = self.create_features(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_features, y, test_size=0.2, random_state=42, stratify=None
        )
        
        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")
        
        # Define models to train
        models_config = {
            'logistic_regression': LogisticRegression(
                random_state=42, 
                max_iter=1000,
                class_weight='balanced'
            ),
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced',
                n_jobs=-1
            ),
            'xgboost': xgb.XGBClassifier(
                random_state=42,
                eval_metric='logloss',
                scale_pos_weight=10  # Handle class imbalance
            )
        }
        
        results = {}
        
        for name, model in models_config.items():
            logger.info(f"Training {name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_test, y_pred, average='weighted', zero_division=0
            )
            
            # Store results
            results[name] = {
                'model': model,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'feature_importance': getattr(model, 'feature_importances_', None)
            }
            
            logger.info(f"{name} - Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")
        
        # Select best model
        best_model_name = max(results.keys(), key=lambda k: results[k]['f1_score'])
        logger.info(f"Best model: {best_model_name} (F1: {results[best_model_name]['f1_score']:.3f})")
        
        return {
            'best_model': results[best_model_name]['model'],
            'best_model_name': best_model_name,
            'all_results': results,
            'feature_names': self.get_feature_names()
        }
    
    def get_feature_names(self) -> List[str]:
        """Get names of features used in the model."""
        base_features = [f'recent_access_{i}' for i in range(self.window_size)]
        additional_features = [
            'unique_pages',
            'max_frequency',
            'avg_frequency',
            'sequential_count',
            'stride_count',
            'mean_distance',
            'std_distance'
        ]
        return base_features + additional_features
    
    def save_model(self, model_data: Dict[str, Any], output_file: str):
        """Save trained model and metadata."""
        logger.info(f"Saving model to {output_file}")
        
        # Save model
        joblib.dump(model_data['best_model'], output_file)
        
        # Save metadata
        metadata = {
            'model_name': model_data['best_model_name'],
            'page_range': self.page_range,
            'window_size': self.window_size,
            'prediction_horizon': self.prediction_horizon,
            'feature_names': model_data['feature_names'],
            'performance': {
                name: {
                    'precision': result['precision'],
                    'recall': result['recall'],
                    'f1_score': result['f1_score']
                }
                for name, result in model_data['all_results'].items()
            }
        }
        
        metadata_file = output_file.replace('.pkl', '_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Model metadata saved to {metadata_file}")
    
    def load_model(self, model_file: str) -> Tuple[Any, Dict[str, Any]]:
        """Load trained model and metadata."""
        model = joblib.load(model_file)
        
        metadata_file = model_file.replace('.pkl', '_metadata.json')
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        return model, metadata


def main():
    parser = argparse.ArgumentParser(description='Train VMM predictor model')
    parser.add_argument('--data-file', type=str, default='traces/training_data.json',
                       help='Path to training data file')
    parser.add_argument('--output-file', type=str, default='model.pkl',
                       help='Output file for trained model')
    parser.add_argument('--page-range', type=int, default=1000,
                       help='Range of page numbers')
    parser.add_argument('--window-size', type=int, default=10,
                       help='Size of recent access window')
    parser.add_argument('--prediction-horizon', type=int, default=5,
                       help='Number of future accesses to predict')
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = VMMPredictorTrainer(
        page_range=args.page_range,
        window_size=args.window_size,
        prediction_horizon=args.prediction_horizon
    )
    
    # Load training data
    X, y = trainer.load_training_data(args.data_file)
    
    # Train models
    model_data = trainer.train_models(X, y)
    
    # Save model
    trainer.save_model(model_data, args.output_file)
    
    logger.info("Training completed successfully!")


if __name__ == '__main__':
    main()
