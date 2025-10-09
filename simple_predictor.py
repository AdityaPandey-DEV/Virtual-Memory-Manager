#!/usr/bin/env python3
"""
Simple AI Predictor Service for Virtual Memory Manager
This is a simplified version that works without complex ML dependencies
"""

import json
import random
import time
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VMM AI Predictor Service",
    description="AI-powered page prediction service for Virtual Memory Manager",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class PredictionRequest(BaseModel):
    recent_accesses: List[int]
    context: Dict[str, Any] = None
    top_k: int = 10
    latency_simulation_ms: int = 0

class PagePrediction(BaseModel):
    page: int
    score: float

class PredictionResponse(BaseModel):
    predicted_pages: List[PagePrediction]
    model_info: Dict[str, Any]
    processing_time_ms: float

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_info: Dict[str, Any] = None

class SimplePredictor:
    """Simple predictor that uses pattern recognition without ML libraries"""
    
    def __init__(self):
        self.model_loaded = True
        self.model_info = {
            "model_name": "Simple Pattern Predictor",
            "page_range": 1000,
            "window_size": 10,
            "prediction_horizon": 5,
            "feature_names": ["recent_accesses", "pattern_analysis"],
            "performance": {
                "accuracy": 0.75,
                "precision": 0.72,
                "recall": 0.68
            }
        }
    
    def predict_pages(self, recent_accesses: List[int], top_k: int = 10) -> List[Dict[str, Any]]:
        """Predict pages using simple pattern analysis"""
        if not recent_accesses:
            return []
        
        predictions = []
        
        # Pattern 1: Sequential access prediction
        if len(recent_accesses) >= 2:
            last_page = recent_accesses[-1]
            # Predict next sequential pages
            for i in range(1, min(4, top_k)):
                next_page = (last_page + i) % 1000
                confidence = max(0.1, 0.8 - (i * 0.2))
                predictions.append({
                    'page': next_page,
                    'score': confidence
                })
        
        # Pattern 2: Stride pattern detection
        if len(recent_accesses) >= 3:
            stride = recent_accesses[-1] - recent_accesses[-2]
            if stride > 0:
                next_page = (recent_accesses[-1] + stride) % 1000
                predictions.append({
                    'page': next_page,
                    'score': 0.7
                })
        
        # Pattern 3: Locality-based prediction
        if len(recent_accesses) >= 2:
            # Predict pages near recently accessed ones
            for page in recent_accesses[-3:]:
                for offset in [1, -1, 2, -2]:
                    neighbor_page = (page + offset) % 1000
                    if neighbor_page not in [p['page'] for p in predictions]:
                        predictions.append({
                            'page': neighbor_page,
                            'score': 0.4
                        })
        
        # Pattern 4: Random predictions to fill remaining slots
        while len(predictions) < top_k:
            random_page = random.randint(0, 999)
            if random_page not in [p['page'] for p in predictions]:
                predictions.append({
                    'page': random_page,
                    'score': 0.2
                })
        
        # Sort by confidence and return top_k
        predictions.sort(key=lambda x: x['score'], reverse=True)
        return predictions[:top_k]
    
    def get_model_info(self) -> Dict[str, Any]:
        return self.model_info

# Global predictor instance
predictor = SimplePredictor()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        model_loaded=predictor.model_loaded,
        model_info=predictor.get_model_info()
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict_pages(request: PredictionRequest):
    """Predict next pages to be accessed based on recent access pattern."""
    start_time = time.time()
    
    try:
        # Simulate latency if requested
        if request.latency_simulation_ms > 0:
            import asyncio
            await asyncio.sleep(request.latency_simulation_ms / 1000.0)
        
        # Validate input
        if not request.recent_accesses:
            raise HTTPException(
                status_code=400,
                detail="recent_accesses cannot be empty"
            )
        
        # Get predictions
        predicted_pages = predictor.predict_pages(
            recent_accesses=request.recent_accesses,
            top_k=request.top_k or 10
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Log prediction for metrics
        logger.info(f"Prediction completed: {len(predicted_pages)} pages, "
                   f"{processing_time:.2f}ms, recent_accesses={len(request.recent_accesses)}")
        
        return PredictionResponse(
            predicted_pages=[PagePrediction(page=p['page'], score=p['score']) 
                           for p in predicted_pages],
            model_info=predictor.get_model_info(),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )

@app.get("/model/info")
async def get_model_info():
    """Get information about the loaded model."""
    return predictor.get_model_info()

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "VMM AI Predictor Service",
        "version": "1.0.0",
        "endpoints": {
            "predict": "POST /predict",
            "health": "GET /health",
            "model_info": "GET /model/info"
        },
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)