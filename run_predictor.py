#!/usr/bin/env python3
"""
Convenience script to run the VMM AI Predictor service.
Handles model loading and service startup.
"""

import uvicorn
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Run VMM AI Predictor Service')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind the service to')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind the service to')
    parser.add_argument('--model-path', type=str, default='model.pkl',
                       help='Path to the trained model file')
    parser.add_argument('--workers', type=int, default=1,
                       help='Number of worker processes')
    parser.add_argument('--reload', action='store_true',
                       help='Enable auto-reload for development')
    
    args = parser.parse_args()
    
    # Check if model exists
    if not Path(args.model_path).exists():
        logger.warning(f"Model file {args.model_path} not found!")
        logger.warning("Please train a model first using: python train_predictor.py")
        logger.warning("The service will start but predictions will fail until a model is available.")
    
    logger.info(f"Starting VMM AI Predictor Service on {args.host}:{args.port}")
    logger.info(f"Model path: {args.model_path}")
    
    # Run the service
    uvicorn.run(
        "predictor.service:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info"
    )


if __name__ == '__main__':
    main()
