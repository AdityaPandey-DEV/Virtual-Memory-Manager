#!/usr/bin/env python3
"""
Quick fix for AI integration issues in the VMM system.
This script improves the current simple predictor to work better with the backend.
"""

import requests
import json
import time
import threading
from typing import List, Dict, Any

class ImprovedSimplePredictor:
    """Improved simple predictor that works better with the VMM backend."""
    
    def __init__(self):
        self.recent_accesses = []
        self.prediction_history = []
        self.hit_count = 0
        self.prediction_count = 0
        
    def predict_pages(self, recent_accesses: List[int], top_k: int = 5) -> List[Dict[str, Any]]:
        """Generate improved predictions based on access patterns."""
        self.recent_accesses = recent_accesses[-10:]  # Keep last 10 accesses
        self.prediction_count += 1
        
        predictions = []
        
        if len(self.recent_accesses) >= 3:
            # Pattern 1: Sequential access
            if self._is_sequential():
                next_page = (self.recent_accesses[-1] + 1) % 1000
                predictions.append({'page': next_page, 'score': 0.9})
                if top_k > 1:
                    predictions.append({'page': (next_page + 1) % 1000, 'score': 0.8})
            
            # Pattern 2: Strided access
            elif self._is_strided():
                stride = self.recent_accesses[-1] - self.recent_accesses[-2]
                next_page = (self.recent_accesses[-1] + stride) % 1000
                predictions.append({'page': next_page, 'score': 0.8})
                if top_k > 1:
                    predictions.append({'page': (next_page + stride) % 1000, 'score': 0.7})
            
            # Pattern 3: Locality-based
            else:
                # Predict pages in the same locality (within 10 pages)
                last_page = self.recent_accesses[-1]
                base = (last_page // 10) * 10
                
                for i in range(1, min(top_k + 1, 6)):
                    page = (base + (last_page % 10 + i) % 10) % 1000
                    if page not in [p['page'] for p in predictions]:
                        predictions.append({'page': page, 'score': 0.6 - (i * 0.1)})
            
            # Add some diversity predictions
            if len(predictions) < top_k:
                # Predict pages that were accessed recently but not in the last few accesses
                recent_set = set(self.recent_accesses[-3:])
                for page in self.recent_accesses[:-3]:
                    if page not in recent_set and len(predictions) < top_k:
                        predictions.append({'page': page, 'score': 0.4})
        
        # Ensure we have at least some predictions
        if not predictions:
            last_page = self.recent_accesses[-1] if self.recent_accesses else 0
            for i in range(1, min(top_k + 1, 4)):
                predictions.append({'page': (last_page + i) % 1000, 'score': 0.3})
        
        return predictions[:top_k]
    
    def _is_sequential(self) -> bool:
        """Check if recent accesses are sequential."""
        if len(self.recent_accesses) < 3:
            return False
        
        for i in range(len(self.recent_accesses) - 2):
            if (self.recent_accesses[i+1] - self.recent_accesses[i]) % 1000 != 1:
                return False
        return True
    
    def _is_strided(self) -> bool:
        """Check if recent accesses follow a stride pattern."""
        if len(self.recent_accesses) < 3:
            return False
        
        stride = self.recent_accesses[1] - self.recent_accesses[0]
        for i in range(1, len(self.recent_accesses) - 1):
            if (self.recent_accesses[i+1] - self.recent_accesses[i]) % 1000 != stride:
                return False
        return True
    
    def record_hit(self, page: int):
        """Record when a prediction was correct."""
        self.hit_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get prediction statistics."""
        hit_rate = self.hit_count / max(self.prediction_count, 1)
        return {
            'predictions_made': self.prediction_count,
            'hits': self.hit_count,
            'hit_rate': hit_rate
        }

# Global predictor instance
predictor = ImprovedSimplePredictor()

def test_ai_predictor():
    """Test the AI predictor with sample data."""
    print("Testing AI Predictor...")
    
    # Test sequential pattern
    sequential_accesses = [1, 2, 3, 4, 5]
    predictions = predictor.predict_pages(sequential_accesses, top_k=3)
    print(f"Sequential pattern: {sequential_accesses}")
    print(f"Predictions: {predictions}")
    
    # Test strided pattern
    strided_accesses = [0, 5, 10, 15, 20]
    predictions = predictor.predict_pages(strided_accesses, top_k=3)
    print(f"Strided pattern: {strided_accesses}")
    print(f"Predictions: {predictions}")
    
    # Test random pattern
    random_accesses = [42, 17, 89, 156, 203]
    predictions = predictor.predict_pages(random_accesses, top_k=3)
    print(f"Random pattern: {random_accesses}")
    print(f"Predictions: {predictions}")

def start_improved_predictor_service():
    """Start an improved predictor service."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    
    app = FastAPI(title="Improved VMM Predictor")
    
    class PredictionRequest(BaseModel):
        recent_accesses: List[int]
        top_k: int = 5
    
    class PredictionResponse(BaseModel):
        predicted_pages: List[Dict[str, Any]]
        model_info: Dict[str, Any]
        processing_time_ms: float
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "model_loaded": True,
            "model_info": {
                "model_name": "Improved Simple Pattern Predictor",
                "version": "2.0",
                "features": ["sequential", "strided", "locality"],
                "performance": predictor.get_stats()
            }
        }
    
    @app.post("/predict", response_model=PredictionResponse)
    async def predict_pages(request: PredictionRequest):
        start_time = time.time()
        
        try:
            predictions = predictor.predict_pages(request.recent_accesses, request.top_k)
            
            processing_time = (time.time() - start_time) * 1000
            
            return PredictionResponse(
                predicted_pages=predictions,
                model_info={
                    "model_name": "Improved Simple Pattern Predictor",
                    "version": "2.0",
                    "performance": predictor.get_stats()
                },
                processing_time_ms=processing_time
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    print("Starting improved predictor service on port 5001...")
    uvicorn.run(app, host="0.0.0.0", port=5001)

if __name__ == "__main__":
    test_ai_predictor()
    start_improved_predictor_service()
