#!/usr/bin/env python3
"""
Complete setup script for VMM AI Predictor training pipeline.
Generates traces, trains model, and validates the setup.
"""

import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"✓ {description} completed successfully")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed")
        logger.error(f"Error: {e.stderr}")
        return False


def main():
    logger.info("Setting up VMM AI Predictor training pipeline...")
    
    # Step 1: Generate synthetic traces
    logger.info("Step 1: Generating synthetic workload traces...")
    if not run_command([
        sys.executable, "generate_traces.py",
        "--output-dir", "traces",
        "--page-range", "1000",
        "--trace-length", "5000",
        "--num-traces", "5"
    ], "Trace generation"):
        logger.error("Failed to generate traces. Exiting.")
        return False
    
    # Step 2: Train the model
    logger.info("Step 2: Training the predictor model...")
    if not run_command([
        sys.executable, "train_predictor.py",
        "--data-file", "traces/training_data.json",
        "--output-file", "model.pkl",
        "--page-range", "1000"
    ], "Model training"):
        logger.error("Failed to train model. Exiting.")
        return False
    
    # Step 3: Verify model was created
    if not Path("model.pkl").exists():
        logger.error("Model file was not created. Training failed.")
        return False
    
    logger.info("✓ Model training completed successfully!")
    logger.info("✓ Setup complete! You can now run the predictor service.")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Start the predictor service: python run_predictor.py")
    logger.info("2. Test the service: python evaluate.py")
    logger.info("3. The C++ backend can now connect to http://localhost:5000/predict")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
