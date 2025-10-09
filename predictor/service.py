"""
FastAPI service for Virtual Memory Manager AI predictions.
Provides REST API endpoint for page prediction.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import time
import asyncio
import os
from pathlib import Path

from predictor.models import VMMPredictor

# Environment variables
PREDICTOR_HOST = os.getenv('PREDICTOR_HOST', '0.0.0.0')
PREDICTOR_PORT = int(os.getenv('PREDICTOR_PORT', '5000'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MODEL_PATH = os.getenv('MODEL_PATH', 'model.pkl')
AI_MODEL_TYPE = os.getenv('AI_MODEL_TYPE', 'xgboost')
AI_PREDICTION_THRESHOLD = float(os.getenv('AI_PREDICTION_THRESHOLD', '0.7'))

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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

# Global predictor instance
predictor = None


# Pydantic models for API
class PredictionRequest(BaseModel):
    recent_accesses: List[int]
    context: Optional[Dict[str, Any]] = None
    top_k: Optional[int] = 10
    latency_simulation_ms: Optional[int] = 0


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
    model_info: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the predictor model on startup."""
    global predictor
    
    logger.info("Starting VMM AI Predictor Service...")
    
    # Try to load model
    if not Path(MODEL_PATH).exists():
        logger.warning(f"Model file {MODEL_PATH} not found. Service will start without model.")
        predictor = VMMPredictor(MODEL_PATH)
    else:
        predictor = VMMPredictor(MODEL_PATH)
        if not predictor.load_model():
            logger.error("Failed to load model. Service will start without model.")
        else:
            logger.info("Model loaded successfully!")
    
    logger.info("Service startup complete")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    global predictor
    
    if predictor is None:
        return HealthResponse(
            status="error",
            model_loaded=False,
            model_info=None
        )
    
    model_loaded = predictor.is_loaded
    model_info = predictor.get_model_info() if model_loaded else None
    
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        model_loaded=model_loaded,
        model_info=model_info
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict_pages(request: PredictionRequest):
    """
    Predict next pages to be accessed based on recent access pattern.
    
    Args:
        request: Prediction request with recent accesses and optional context
        
    Returns:
        List of predicted pages with confidence scores
    """
    global predictor
    
    if predictor is None or not predictor.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Predictor model not available. Please check if model is loaded."
        )
    
    start_time = time.time()
    
    try:
        # Simulate latency if requested (for testing)
        if request.latency_simulation_ms > 0:
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
    global predictor
    
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Predictor not initialized"
        )
    
    return predictor.get_model_info()


@app.post("/model/reload")
async def reload_model():
    """Reload the model from disk."""
    global predictor
    
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Predictor not initialized"
        )
    
    try:
        success = predictor.load_model()
        if success:
            return {"status": "success", "message": "Model reloaded successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reload model"
            )
    except Exception as e:
        logger.error(f"Model reload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Model reload failed: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "VMM AI Predictor Service",
        "version": "1.0.0",
        "endpoints": {
            "predict": "POST /predict",
            "health": "GET /health",
            "model_info": "GET /model/info",
            "reload_model": "POST /model/reload"
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
