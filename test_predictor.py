#!/usr/bin/env python3
"""
Simple test script to validate the VMM AI Predictor service.
Tests basic functionality without requiring the full training pipeline.
"""

import requests
import json
import time
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_predictor_service(base_url: str = "http://localhost:5001") -> bool:
    """Test the predictor service with basic functionality."""
    
    logger.info("Testing VMM AI Predictor Service...")
    
    # Test 1: Health check
    logger.info("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"✓ Health check passed: {health_data['status']}")
            logger.info(f"  Model loaded: {health_data['model_loaded']}")
        else:
            logger.error(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Health check failed: {e}")
        return False
    
    # Test 2: Model info
    logger.info("2. Testing model info endpoint...")
    try:
        response = requests.get(f"{base_url}/model/info", timeout=5)
        if response.status_code == 200:
            model_info = response.json()
            logger.info(f"✓ Model info retrieved")
            logger.info(f"  Model: {model_info.get('model_name', 'unknown')}")
            logger.info(f"  Page range: {model_info.get('page_range', 'unknown')}")
        else:
            logger.warning(f"⚠ Model info failed: {response.status_code}")
    except Exception as e:
        logger.warning(f"⚠ Model info failed: {e}")
    
    # Test 3: Prediction (if model is loaded)
    if health_data.get('model_loaded', False):
        logger.info("3. Testing prediction endpoint...")
        try:
            test_request = {
                "recent_accesses": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "top_k": 5,
                "latency_simulation_ms": 0
            }
            
            response = requests.post(
                f"{base_url}/predict",
                json=test_request,
                timeout=10
            )
            
            if response.status_code == 200:
                pred_data = response.json()
                logger.info(f"✓ Prediction successful")
                logger.info(f"  Predicted pages: {len(pred_data['predicted_pages'])}")
                logger.info(f"  Processing time: {pred_data['processing_time_ms']:.2f}ms")
                
                # Show top predictions
                for i, pred in enumerate(pred_data['predicted_pages'][:3]):
                    logger.info(f"    {i+1}. Page {pred['page']} (score: {pred['score']:.3f})")
            else:
                logger.error(f"✗ Prediction failed: {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ Prediction failed: {e}")
            return False
    else:
        logger.warning("⚠ Model not loaded, skipping prediction test")
    
    # Test 4: Root endpoint
    logger.info("4. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            root_data = response.json()
            logger.info(f"✓ Root endpoint working")
            logger.info(f"  Service: {root_data.get('service', 'unknown')}")
        else:
            logger.warning(f"⚠ Root endpoint failed: {response.status_code}")
    except Exception as e:
        logger.warning(f"⚠ Root endpoint failed: {e}")
    
    logger.info("✓ All tests completed!")
    return True


def test_without_model(base_url: str = "http://localhost:5001") -> bool:
    """Test service behavior when no model is loaded."""
    
    logger.info("Testing service without model...")
    
    # Test prediction with no model
    try:
        test_request = {
            "recent_accesses": [1, 2, 3],
            "top_k": 3
        }
        
        response = requests.post(f"{base_url}/predict", json=test_request, timeout=5)
        
        if response.status_code == 503:
            logger.info("✓ Service correctly returns 503 when model not available")
            return True
        else:
            logger.warning(f"⚠ Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        return False


def main():
    """Run all tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test VMM AI Predictor Service')
    parser.add_argument('--url', type=str, default='http://localhost:5001',
                       help='Base URL of the predictor service')
    parser.add_argument('--no-model-test', action='store_true',
                       help='Test service behavior without model')
    
    args = parser.parse_args()
    
    logger.info(f"Testing predictor service at {args.url}")
    
    if args.no_model_test:
        success = test_without_model(args.url)
    else:
        success = test_predictor_service(args.url)
    
    if success:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed!")
        return 1


if __name__ == '__main__':
    exit(main())
