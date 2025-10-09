#!/usr/bin/env python3
"""
Synthetic workload trace generator for Virtual Memory Manager training.
Generates various access patterns: sequential, strided, random, and zipf.
"""

import numpy as np
import pandas as pd
import argparse
import json
from typing import List, Tuple, Dict, Any
from enum import Enum
import random
from pathlib import Path


class WorkloadType(Enum):
    SEQUENTIAL = "sequential"
    RANDOM = "random"
    STRIDED = "strided"
    ZIPF = "zipf"
    WEBSERVER = "webserver"


class TraceGenerator:
    """Generates synthetic memory access traces for training the AI predictor."""
    
    def __init__(self, page_range: int = 1000, seed: int = 42):
        self.page_range = page_range
        self.rng = np.random.RandomState(seed)
        random.seed(seed)
    
    def generate_sequential_trace(self, length: int, start_page: int = 0) -> List[int]:
        """Generate sequential access pattern."""
        return [(start_page + i) % self.page_range for i in range(length)]
    
    def generate_random_trace(self, length: int) -> List[int]:
        """Generate random access pattern."""
        return self.rng.randint(0, self.page_range, length).tolist()
    
    def generate_strided_trace(self, length: int, stride: int = 1, start_page: int = 0) -> List[int]:
        """Generate strided access pattern."""
        return [(start_page + i * stride) % self.page_range for i in range(length)]
    
    def generate_zipf_trace(self, length: int, alpha: float = 1.0) -> List[int]:
        """Generate Zipfian access pattern."""
        # Create Zipf distribution
        ranks = np.arange(1, self.page_range + 1)
        probabilities = 1.0 / (ranks ** alpha)
        probabilities = probabilities / probabilities.sum()
        
        return self.rng.choice(self.page_range, size=length, p=probabilities).tolist()
    
    def generate_webserver_trace(self, length: int, working_set_size: int = 100, 
                                locality_factor: float = 0.8) -> List[int]:
        """Generate webserver-like access pattern with temporal locality."""
        trace = []
        working_set = set()
        
        for i in range(length):
            if len(working_set) < working_set_size:
                # Add new pages to working set
                new_page = self.rng.randint(0, self.page_range)
                working_set.add(new_page)
                trace.append(new_page)
            else:
                # Choose between working set and new page based on locality factor
                if self.rng.random() < locality_factor:
                    # Access from working set
                    page = random.choice(list(working_set))
                else:
                    # Access new page (replace one in working set)
                    new_page = self.rng.randint(0, self.page_range)
                    old_page = random.choice(list(working_set))
                    working_set.remove(old_page)
                    working_set.add(new_page)
                    page = new_page
                
                trace.append(page)
        
        return trace
    
    def generate_trace(self, workload_type: WorkloadType, length: int, **kwargs) -> List[int]:
        """Generate trace based on workload type."""
        if workload_type == WorkloadType.SEQUENTIAL:
            return self.generate_sequential_trace(length, kwargs.get('start_page', 0))
        elif workload_type == WorkloadType.RANDOM:
            return self.generate_random_trace(length)
        elif workload_type == WorkloadType.STRIDED:
            return self.generate_strided_trace(length, kwargs.get('stride', 1), kwargs.get('start_page', 0))
        elif workload_type == WorkloadType.ZIPF:
            return self.generate_zipf_trace(length, kwargs.get('alpha', 1.0))
        elif workload_type == WorkloadType.WEBSERVER:
            return self.generate_webserver_trace(
                length, 
                kwargs.get('working_set_size', 100),
                kwargs.get('locality_factor', 0.8)
            )
        else:
            raise ValueError(f"Unknown workload type: {workload_type}")
    
    def create_training_data(self, traces: List[List[int]], window_size: int = 10, 
                           prediction_horizon: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """Convert traces into training data for ML model."""
        X, y = [], []
        
        for trace in traces:
            for i in range(len(trace) - window_size - prediction_horizon + 1):
                # Features: recent access pattern
                recent_accesses = trace[i:i + window_size]
                
                # Target: pages accessed in the next prediction_horizon steps
                future_accesses = set(trace[i + window_size:i + window_size + prediction_horizon])
                
                # Create binary labels for each possible page
                labels = np.zeros(self.page_range)
                for page in future_accesses:
                    labels[page] = 1
                
                X.append(recent_accesses)
                y.append(labels)
        
        return np.array(X), np.array(y)
    
    def save_trace(self, trace: List[int], filename: str, metadata: Dict[str, Any] = None):
        """Save trace to file with metadata."""
        output = {
            'trace': trace,
            'metadata': metadata or {}
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
    
    def load_trace(self, filename: str) -> Tuple[List[int], Dict[str, Any]]:
        """Load trace from file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        return data['trace'], data.get('metadata', {})


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic workload traces')
    parser.add_argument('--output-dir', type=str, default='traces', 
                       help='Output directory for traces')
    parser.add_argument('--page-range', type=int, default=1000,
                       help='Range of page numbers (0 to page_range-1)')
    parser.add_argument('--trace-length', type=int, default=10000,
                       help='Length of each trace')
    parser.add_argument('--num-traces', type=int, default=10,
                       help='Number of traces to generate per workload type')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize generator
    generator = TraceGenerator(page_range=args.page_range, seed=args.seed)
    
    # Generate traces for each workload type
    workload_configs = [
        (WorkloadType.SEQUENTIAL, {}),
        (WorkloadType.RANDOM, {}),
        (WorkloadType.STRIDED, {'stride': 2}),
        (WorkloadType.STRIDED, {'stride': 4}),
        (WorkloadType.ZIPF, {'alpha': 0.8}),
        (WorkloadType.ZIPF, {'alpha': 1.2}),
        (WorkloadType.WEBSERVER, {'working_set_size': 50, 'locality_factor': 0.7}),
        (WorkloadType.WEBSERVER, {'working_set_size': 200, 'locality_factor': 0.9}),
    ]
    
    all_traces = []
    
    for workload_type, config in workload_configs:
        print(f"Generating {args.num_traces} traces for {workload_type.value} workload...")
        
        for i in range(args.num_traces):
            trace = generator.generate_trace(workload_type, args.trace_length, **config)
            
            # Save individual trace
            metadata = {
                'workload_type': workload_type.value,
                'length': len(trace),
                'page_range': args.page_range,
                'config': config,
                'trace_id': i
            }
            
            filename = output_dir / f"{workload_type.value}_{i:03d}.json"
            generator.save_trace(trace, str(filename), metadata)
            
            all_traces.append(trace)
    
    # Create combined training dataset
    print("Creating combined training dataset...")
    X, y = generator.create_training_data(all_traces)
    
    # Save training data
    training_data = {
        'X': X.tolist(),
        'y': y.tolist(),
        'page_range': args.page_range,
        'window_size': 10,
        'prediction_horizon': 5,
        'num_traces': len(all_traces),
        'total_samples': len(X)
    }
    
    training_file = output_dir / 'training_data.json'
    with open(training_file, 'w') as f:
        json.dump(training_data, f, indent=2)
    
    print(f"Generated {len(all_traces)} traces")
    print(f"Training dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Output directory: {output_dir}")
    print(f"Training data saved to: {training_file}")


if __name__ == '__main__':
    main()
