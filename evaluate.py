#!/usr/bin/env python3
"""
Evaluation script for Virtual Memory Manager AI predictor.
Tests predictor performance on sample traces and provides metrics.
"""

import numpy as np
import pandas as pd
import json
import argparse
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
import requests
import time
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from generate_traces import TraceGenerator, WorkloadType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PredictorEvaluator:
    """Evaluates the performance of the VMM AI predictor."""
    
    def __init__(self, predictor_url: str = "http://localhost:5000"):
        self.predictor_url = predictor_url
        self.results = []
    
    def test_predictor_health(self) -> bool:
        """Test if predictor service is running and healthy."""
        try:
            response = requests.get(f"{self.predictor_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"Predictor health: {health_data['status']}")
                return health_data['model_loaded']
            else:
                logger.error(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to predictor: {e}")
            return False
    
    def generate_test_traces(self, num_traces: int = 5, trace_length: int = 1000) -> List[List[int]]:
        """Generate test traces for evaluation."""
        generator = TraceGenerator(page_range=1000, seed=42)
        
        test_configs = [
            (WorkloadType.SEQUENTIAL, {}),
            (WorkloadType.RANDOM, {}),
            (WorkloadType.STRIDED, {'stride': 2}),
            (WorkloadType.ZIPF, {'alpha': 1.0}),
            (WorkloadType.WEBSERVER, {'working_set_size': 100, 'locality_factor': 0.8})
        ]
        
        traces = []
        for workload_type, config in test_configs:
            for i in range(num_traces):
                trace = generator.generate_trace(workload_type, trace_length, **config)
                traces.append(trace)
        
        return traces
    
    def evaluate_trace(self, trace: List[int], window_size: int = 10, 
                      prediction_horizon: int = 5) -> Dict[str, Any]:
        """Evaluate predictor on a single trace."""
        results = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'precision_scores': [],
            'recall_scores': [],
            'f1_scores': [],
            'response_times': [],
            'predictions': []
        }
        
        for i in range(len(trace) - window_size - prediction_horizon + 1):
            # Get recent accesses
            recent_accesses = trace[i:i + window_size]
            
            # Get actual future accesses
            future_accesses = set(trace[i + window_size:i + window_size + prediction_horizon])
            
            # Make prediction
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.predictor_url}/predict",
                    json={
                        "recent_accesses": recent_accesses,
                        "top_k": 20,
                        "latency_simulation_ms": 0
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    pred_data = response.json()
                    response_time = (time.time() - start_time) * 1000
                    
                    # Extract predicted pages
                    predicted_pages = set(p['page'] for p in pred_data['predicted_pages'])
                    
                    # Calculate metrics
                    if future_accesses:
                        # Precision: how many predicted pages were actually accessed
                        true_positives = len(predicted_pages.intersection(future_accesses))
                        precision = true_positives / len(predicted_pages) if predicted_pages else 0
                        
                        # Recall: how many future accesses were predicted
                        recall = true_positives / len(future_accesses) if future_accesses else 0
                        
                        # F1 score
                        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                        
                        results['precision_scores'].append(precision)
                        results['recall_scores'].append(recall)
                        results['f1_scores'].append(f1)
                        results['response_times'].append(response_time)
                        results['predictions'].append({
                            'predicted': list(predicted_pages),
                            'actual': list(future_accesses),
                            'precision': precision,
                            'recall': recall,
                            'f1': f1
                        })
                        
                        results['total_predictions'] += 1
                        if f1 > 0:
                            results['correct_predictions'] += 1
                
            except Exception as e:
                logger.warning(f"Prediction failed at position {i}: {e}")
                continue
        
        return results
    
    def evaluate_predictor(self, traces: List[List[int]], window_size: int = 10, 
                          prediction_horizon: int = 5) -> Dict[str, Any]:
        """Evaluate predictor on multiple traces."""
        logger.info(f"Evaluating predictor on {len(traces)} traces...")
        
        # Check if predictor is available
        if not self.test_predictor_health():
            raise RuntimeError("Predictor service not available or model not loaded")
        
        all_results = []
        
        for i, trace in enumerate(traces):
            logger.info(f"Evaluating trace {i+1}/{len(traces)} (length: {len(trace)})")
            trace_results = self.evaluate_trace(trace, window_size, prediction_horizon)
            trace_results['trace_id'] = i
            trace_results['trace_length'] = len(trace)
            all_results.append(trace_results)
        
        # Aggregate results
        total_predictions = sum(r['total_predictions'] for r in all_results)
        total_correct = sum(r['correct_predictions'] for r in all_results)
        
        all_precisions = []
        all_recalls = []
        all_f1s = []
        all_response_times = []
        
        for result in all_results:
            all_precisions.extend(result['precision_scores'])
            all_recalls.extend(result['recall_scores'])
            all_f1s.extend(result['f1_scores'])
            all_response_times.extend(result['response_times'])
        
        # Calculate overall metrics
        overall_metrics = {
            'total_traces': len(traces),
            'total_predictions': total_predictions,
            'total_correct': total_correct,
            'accuracy': total_correct / total_predictions if total_predictions > 0 else 0,
            'avg_precision': np.mean(all_precisions) if all_precisions else 0,
            'avg_recall': np.mean(all_recalls) if all_recalls else 0,
            'avg_f1': np.mean(all_f1s) if all_f1s else 0,
            'avg_response_time_ms': np.mean(all_response_times) if all_response_times else 0,
            'std_precision': np.std(all_precisions) if all_precisions else 0,
            'std_recall': np.std(all_recalls) if all_recalls else 0,
            'std_f1': np.std(all_f1s) if all_f1s else 0,
            'std_response_time_ms': np.std(all_response_times) if all_response_times else 0
        }
        
        return {
            'overall_metrics': overall_metrics,
            'trace_results': all_results
        }
    
    def save_results(self, results: Dict[str, Any], output_file: str):
        """Save evaluation results to file."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_file}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Print evaluation summary."""
        metrics = results['overall_metrics']
        
        print("\n" + "="*60)
        print("VMM AI PREDICTOR EVALUATION SUMMARY")
        print("="*60)
        print(f"Total traces evaluated: {metrics['total_traces']}")
        print(f"Total predictions made: {metrics['total_predictions']}")
        print(f"Correct predictions: {metrics['total_correct']}")
        print(f"Overall accuracy: {metrics['accuracy']:.3f}")
        print()
        print("Performance Metrics:")
        print(f"  Average Precision: {metrics['avg_precision']:.3f} ± {metrics['std_precision']:.3f}")
        print(f"  Average Recall:    {metrics['avg_recall']:.3f} ± {metrics['std_recall']:.3f}")
        print(f"  Average F1 Score:  {metrics['avg_f1']:.3f} ± {metrics['std_f1']:.3f}")
        print()
        print("Response Time:")
        print(f"  Average: {metrics['avg_response_time_ms']:.2f} ms")
        print(f"  Std Dev: {metrics['std_response_time_ms']:.2f} ms")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description='Evaluate VMM AI predictor')
    parser.add_argument('--predictor-url', type=str, default='http://localhost:5000',
                       help='URL of the predictor service')
    parser.add_argument('--num-traces', type=int, default=5,
                       help='Number of test traces per workload type')
    parser.add_argument('--trace-length', type=int, default=1000,
                       help='Length of each test trace')
    parser.add_argument('--window-size', type=int, default=10,
                       help='Size of recent access window')
    parser.add_argument('--prediction-horizon', type=int, default=5,
                       help='Number of future accesses to predict')
    parser.add_argument('--output-file', type=str, default='evaluation_results.json',
                       help='Output file for evaluation results')
    
    args = parser.parse_args()
    
    # Initialize evaluator
    evaluator = PredictorEvaluator(args.predictor_url)
    
    # Generate test traces
    logger.info("Generating test traces...")
    traces = evaluator.generate_test_traces(args.num_traces, args.trace_length)
    
    # Run evaluation
    logger.info("Starting evaluation...")
    results = evaluator.evaluate_predictor(
        traces, 
        window_size=args.window_size,
        prediction_horizon=args.prediction_horizon
    )
    
    # Save results
    evaluator.save_results(results, args.output_file)
    
    # Print summary
    evaluator.print_summary(results)
    
    logger.info("Evaluation completed!")


if __name__ == '__main__':
    main()
