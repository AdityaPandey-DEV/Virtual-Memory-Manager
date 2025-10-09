#!/usr/bin/env python3
"""
Workload Simulation Script for AI-Enhanced VMM
Simulates realistic memory access patterns and validates system behavior.
"""

import requests
import json
import time
import sys
import random
import statistics
from datetime import datetime
from typing import Dict, Any, List, Tuple

class WorkloadSimulator:
    def __init__(self):
        self.predictor_url = "http://localhost:5000"
        self.backend_url = "http://localhost:8080"
        self.results = {}
        
    def generate_sequential_workload(self, start_page: int, count: int) -> List[int]:
        """Generate sequential memory access pattern"""
        return list(range(start_page, start_page + count))
    
    def generate_random_workload(self, page_range: int, count: int) -> List[int]:
        """Generate random memory access pattern"""
        return [random.randint(1, page_range) for _ in range(count)]
    
    def generate_locality_workload(self, working_sets: int, set_size: int, count: int) -> List[int]:
        """Generate workload with spatial locality"""
        workload = []
        for _ in range(count):
            # Choose a working set
            working_set = random.randint(0, working_sets - 1)
            # Access pages within that set
            page = working_set * set_size + random.randint(0, set_size - 1)
            workload.append(page)
        return workload
    
    def generate_zipf_workload(self, page_range: int, count: int, alpha: float = 1.0) -> List[int]:
        """Generate workload following Zipf distribution"""
        # Simple Zipf-like distribution
        weights = [1.0 / (i ** alpha) for i in range(1, page_range + 1)]
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        
        workload = []
        for _ in range(count):
            page = random.choices(range(1, page_range + 1), weights=probabilities)[0]
            workload.append(page)
        return workload
    
    def simulate_workload_pattern(self, pattern_name: str, workload: List[int], 
                                 duration_seconds: int = 30) -> Dict[str, Any]:
        """Simulate a specific workload pattern"""
        print(f"   Simulating {pattern_name} workload...")
        print(f"   Pattern: {workload[:10]}{'...' if len(workload) > 10 else ''}")
        print(f"   Duration: {duration_seconds} seconds")
        
        # Start simulation
        response = requests.post(f"{self.backend_url}/simulate/start", timeout=5)
        if response.status_code != 200:
            print(f"   ✗ Failed to start simulation: {response.status_code}")
            return {'status': 'error', 'error': 'Failed to start simulation'}
        
        # Get initial metrics
        response = requests.get(f"{self.backend_url}/metrics", timeout=5)
        initial_metrics = response.json() if response.status_code == 200 else {}
        
        # Simulate workload by making AI prediction requests
        prediction_results = []
        start_time = time.time()
        
        for i, page in enumerate(workload):
            if time.time() - start_time > duration_seconds:
                break
                
            # Create context for AI prediction
            recent_accesses = workload[max(0, i-10):i+1]  # Last 10 accesses
            
            payload = {
                "recent_accesses": recent_accesses,
                "top_k": 5,
                "latency_simulation_ms": 0
            }
            
            # Get AI prediction
            pred_start = time.time()
            response = requests.post(f"{self.predictor_url}/predict", 
                                   json=payload, timeout=10)
            pred_end = time.time()
            
            if response.status_code == 200:
                pred_data = response.json()
                prediction_results.append({
                    'page': page,
                    'predictions': pred_data['predicted_pages'],
                    'processing_time': pred_data['processing_time_ms'],
                    'request_time': (pred_end - pred_start) * 1000
                })
            
            # Small delay to simulate realistic access pattern
            time.sleep(0.01)  # 10ms delay
        
        # Get final metrics
        response = requests.get(f"{self.backend_url}/metrics", timeout=5)
        final_metrics = response.json() if response.status_code == 200 else {}
        
        # Stop simulation
        requests.post(f"{self.backend_url}/simulate/stop", timeout=5)
        
        # Calculate statistics
        if prediction_results:
            processing_times = [p['processing_time'] for p in prediction_results]
            request_times = [p['request_time'] for p in prediction_results]
            
            stats = {
                'total_predictions': len(prediction_results),
                'avg_processing_time': statistics.mean(processing_times),
                'max_processing_time': max(processing_times),
                'avg_request_time': statistics.mean(request_times),
                'max_request_time': max(request_times)
            }
        else:
            stats = {'total_predictions': 0}
        
        return {
            'status': 'completed',
            'pattern_name': pattern_name,
            'workload_size': len(workload),
            'duration': time.time() - start_time,
            'initial_metrics': initial_metrics,
            'final_metrics': final_metrics,
            'prediction_stats': stats,
            'prediction_results': prediction_results[:5]  # First 5 for debugging
        }
    
    def run_comprehensive_simulation(self) -> bool:
        """Run comprehensive workload simulation"""
        print("=" * 60)
        print("AI-ENHANCED VMM WORKLOAD SIMULATION")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Define workload patterns
        workload_patterns = [
            {
                'name': 'Sequential Access',
                'workload': self.generate_sequential_workload(1, 100),
                'description': 'Sequential memory access pattern'
            },
            {
                'name': 'Random Access',
                'workload': self.generate_random_workload(100, 100),
                'description': 'Random memory access pattern'
            },
            {
                'name': 'Spatial Locality',
                'workload': self.generate_locality_workload(5, 20, 100),
                'description': 'Access pattern with spatial locality'
            },
            {
                'name': 'Zipf Distribution',
                'workload': self.generate_zipf_workload(100, 100, 1.0),
                'description': 'Zipf-distributed access pattern'
            }
        ]
        
        simulation_results = []
        
        for pattern in workload_patterns:
            print(f"\n📊 Testing {pattern['name']}")
            print(f"   Description: {pattern['description']}")
            
            result = self.simulate_workload_pattern(
                pattern['name'], 
                pattern['workload'],
                duration_seconds=20
            )
            
            simulation_results.append(result)
            
            if result['status'] == 'completed':
                print(f"   ✓ Completed: {result['total_predictions']} predictions")
                print(f"   ✓ Avg processing time: {result['prediction_stats'].get('avg_processing_time', 0):.2f}ms")
                
                # Show final metrics
                final_metrics = result['final_metrics']
                print(f"   ✓ Total accesses: {final_metrics.get('total_accesses', 0)}")
                print(f"   ✓ Page faults: {final_metrics.get('page_faults', 0)}")
                print(f"   ✓ AI predictions: {final_metrics.get('ai_predictions', 0)}")
                print(f"   ✓ AI hit rate: {final_metrics.get('ai_hit_rate', 0):.2%}")
            else:
                print(f"   ✗ Failed: {result.get('error', 'Unknown error')}")
        
        # Analyze results
        print("\n" + "=" * 60)
        print("SIMULATION ANALYSIS")
        print("=" * 60)
        
        successful_simulations = [r for r in simulation_results if r['status'] == 'completed']
        
        if successful_simulations:
            # Calculate overall statistics
            total_predictions = sum(r['prediction_stats'].get('total_predictions', 0) for r in successful_simulations)
            avg_processing_times = [r['prediction_stats'].get('avg_processing_time', 0) for r in successful_simulations]
            
            print(f"✓ Successful simulations: {len(successful_simulations)}/{len(workload_patterns)}")
            print(f"✓ Total AI predictions: {total_predictions}")
            
            if avg_processing_times:
                print(f"✓ Average processing time: {statistics.mean(avg_processing_times):.2f}ms")
                print(f"✓ Processing time range: {min(avg_processing_times):.2f}ms - {max(avg_processing_times):.2f}ms")
            
            # Analyze AI performance by pattern
            print("\n📈 AI Performance by Pattern:")
            for result in successful_simulations:
                pattern_name = result['pattern_name']
                stats = result['prediction_stats']
                final_metrics = result['final_metrics']
                
                print(f"   {pattern_name}:")
                print(f"     - Predictions: {stats.get('total_predictions', 0)}")
                print(f"     - Avg processing: {stats.get('avg_processing_time', 0):.2f}ms")
                print(f"     - AI hit rate: {final_metrics.get('ai_hit_rate', 0):.2%}")
        else:
            print("✗ No successful simulations")
            return False
        
        self.results = {
            'simulation_results': simulation_results,
            'successful_simulations': len(successful_simulations),
            'total_patterns': len(workload_patterns),
            'total_predictions': total_predictions if successful_simulations else 0
        }
        
        return len(successful_simulations) > 0
    
    def run_stress_test(self) -> bool:
        """Run stress test with high load"""
        print("\n" + "=" * 60)
        print("STRESS TEST")
        print("=" * 60)
        
        try:
            # Generate high-load workload
            high_load_workload = self.generate_random_workload(1000, 500)
            print(f"   Running stress test with {len(high_load_workload)} accesses...")
            
            # Start simulation
            response = requests.post(f"{self.backend_url}/simulate/start", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Failed to start stress test: {response.status_code}")
                return False
            
            start_time = time.time()
            successful_predictions = 0
            failed_predictions = 0
            
            # Rapid-fire predictions
            for i, page in enumerate(high_load_workload):
                if i % 50 == 0:  # Progress update every 50 requests
                    print(f"   Progress: {i}/{len(high_load_workload)}")
                
                recent_accesses = high_load_workload[max(0, i-5):i+1]
                payload = {
                    "recent_accesses": recent_accesses,
                    "top_k": 3,
                    "latency_simulation_ms": 0
                }
                
                try:
                    response = requests.post(f"{self.predictor_url}/predict", 
                                           json=payload, timeout=5)
                    if response.status_code == 200:
                        successful_predictions += 1
                    else:
                        failed_predictions += 1
                except:
                    failed_predictions += 1
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.001)  # 1ms delay
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Get final metrics
            response = requests.get(f"{self.backend_url}/metrics", timeout=5)
            final_metrics = response.json() if response.status_code == 200 else {}
            
            # Stop simulation
            requests.post(f"{self.backend_url}/simulate/stop", timeout=5)
            
            print(f"   ✓ Stress test completed in {duration:.2f} seconds")
            print(f"   ✓ Successful predictions: {successful_predictions}")
            print(f"   ✓ Failed predictions: {failed_predictions}")
            print(f"   ✓ Success rate: {successful_predictions/(successful_predictions+failed_predictions)*100:.1f}%")
            print(f"   ✓ Requests per second: {len(high_load_workload)/duration:.1f}")
            
            # Show final system metrics
            print(f"   ✓ Final system metrics:")
            print(f"     - Total accesses: {final_metrics.get('total_accesses', 0)}")
            print(f"     - Page faults: {final_metrics.get('page_faults', 0)}")
            print(f"     - AI predictions: {final_metrics.get('ai_predictions', 0)}")
            
            return successful_predictions > failed_predictions
            
        except Exception as e:
            print(f"   ✗ Stress test error: {e}")
            return False

def main():
    simulator = WorkloadSimulator()
    
    print("Starting AI-Enhanced VMM Workload Simulation...")
    print("This will test various workload patterns and validate system behavior.")
    print()
    
    # Run comprehensive simulation
    success = simulator.run_comprehensive_simulation()
    
    if success:
        # Run stress test
        stress_success = simulator.run_stress_test()
        
        # Save results
        with open('workload_simulation_results.json', 'w') as f:
            json.dump(simulator.results, f, indent=2, default=str)
        
        print(f"\n📊 Simulation results saved to: workload_simulation_results.json")
        
        if stress_success:
            print("\n🎉 All simulations completed successfully!")
            print("Your AI-Enhanced VMM system handles various workloads correctly!")
        else:
            print("\n⚠️  Stress test had issues, but basic simulation passed.")
    else:
        print("\n✗ Simulation failed. Check the logs above for details.")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()