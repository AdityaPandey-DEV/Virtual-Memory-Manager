#!/usr/bin/env python3
"""
System Validation Script for AI-Enhanced VMM
Validates metrics, predictions, and system behavior.
"""

import requests
import json
import time
import sys
import statistics
from datetime import datetime
from typing import Dict, Any, List

class SystemValidator:
    def __init__(self):
        self.predictor_url = "http://localhost:5000"
        self.backend_url = "http://localhost:8080"
        self.results = {}
        
    def validate_ai_predictions(self) -> bool:
        """Validate AI prediction quality and consistency"""
        print("🤖 Validating AI Predictions...")
        
        try:
            test_patterns = [
                {
                    "name": "Sequential Pattern",
                    "accesses": list(range(1, 11)),
                    "expected_behavior": "Should predict next sequential pages"
                },
                {
                    "name": "Random Pattern", 
                    "accesses": [5, 2, 8, 1, 9, 3, 7, 4, 6, 10],
                    "expected_behavior": "Should handle random access gracefully"
                },
                {
                    "name": "Locality Pattern",
                    "accesses": [100, 101, 102, 103, 104, 200, 201, 202, 203, 204],
                    "expected_behavior": "Should recognize spatial locality"
                }
            ]
            
            prediction_results = []
            
            for pattern in test_patterns:
                print(f"   Testing {pattern['name']}...")
                
                payload = {
                    "recent_accesses": pattern["accesses"],
                    "top_k": 5,
                    "latency_simulation_ms": 0
                }
                
                response = requests.post(f"{self.predictor_url}/predict", 
                                       json=payload, timeout=10)
                
                if response.status_code != 200:
                    print(f"   ✗ Prediction failed: {response.status_code}")
                    return False
                
                data = response.json()
                predictions = data['predicted_pages']
                processing_time = data['processing_time_ms']
                
                # Validate prediction quality
                if len(predictions) == 0:
                    print(f"   ✗ No predictions returned")
                    return False
                
                # Check confidence scores are reasonable
                scores = [p['score'] for p in predictions]
                if max(scores) > 1.0 or min(scores) < 0.0:
                    print(f"   ✗ Invalid confidence scores: {scores}")
                    return False
                
                # Check processing time is reasonable
                if processing_time > 1000:  # More than 1 second
                    print(f"   ⚠ High processing time: {processing_time:.2f}ms")
                
                print(f"   ✓ {len(predictions)} predictions, {processing_time:.2f}ms")
                prediction_results.append({
                    'pattern': pattern['name'],
                    'predictions': len(predictions),
                    'processing_time': processing_time,
                    'scores': scores
                })
            
            self.results['ai_predictions'] = {
                'status': 'valid',
                'test_patterns': prediction_results
            }
            return True
            
        except Exception as e:
            print(f"   ✗ AI prediction validation error: {e}")
            self.results['ai_predictions'] = {'status': 'error', 'error': str(e)}
            return False
    
    def validate_metrics_consistency(self) -> bool:
        """Validate that metrics are consistent and reasonable"""
        print("\n📊 Validating Metrics Consistency...")
        
        try:
            # Get initial metrics
            response = requests.get(f"{self.backend_url}/metrics", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Failed to get metrics: {response.status_code}")
                return False
            
            initial_metrics = response.json()
            print(f"   Initial metrics: {initial_metrics}")
            
            # Start simulation
            print("   Starting simulation...")
            response = requests.post(f"{self.backend_url}/simulate/start", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Failed to start simulation: {response.status_code}")
                return False
            
            # Collect metrics over time
            metrics_history = []
            for i in range(10):  # 10 samples over 5 seconds
                time.sleep(0.5)
                response = requests.get(f"{self.backend_url}/metrics", timeout=5)
                if response.status_code == 200:
                    metrics = response.json()
                    metrics_history.append(metrics)
                    print(f"   Sample {i+1}: accesses={metrics.get('total_accesses', 0)}, "
                          f"faults={metrics.get('page_faults', 0)}")
            
            # Stop simulation
            response = requests.post(f"{self.backend_url}/simulate/stop", timeout=5)
            
            # Validate metrics consistency
            final_metrics = metrics_history[-1] if metrics_history else initial_metrics
            
            # Check that metrics are non-decreasing
            total_accesses = [m.get('total_accesses', 0) for m in metrics_history]
            page_faults = [m.get('page_faults', 0) for m in metrics_history]
            
            if not all(total_accesses[i] <= total_accesses[i+1] for i in range(len(total_accesses)-1)):
                print(f"   ✗ Total accesses decreased: {total_accesses}")
                return False
            
            if not all(page_faults[i] <= page_faults[i+1] for i in range(len(page_faults)-1)):
                print(f"   ✗ Page faults decreased: {page_faults}")
                return False
            
            # Check page fault rate is reasonable
            if final_metrics.get('total_accesses', 0) > 0:
                fault_rate = final_metrics.get('page_fault_rate', 0)
                if fault_rate < 0 or fault_rate > 1:
                    print(f"   ✗ Invalid page fault rate: {fault_rate}")
                else:
                    print(f"   ✓ Page fault rate: {fault_rate:.2%}")
            
            # Check AI metrics
            ai_predictions = final_metrics.get('ai_predictions', 0)
            ai_hit_rate = final_metrics.get('ai_hit_rate', 0)
            print(f"   ✓ AI predictions: {ai_predictions}")
            print(f"   ✓ AI hit rate: {ai_hit_rate:.2%}")
            
            self.results['metrics_consistency'] = {
                'status': 'valid',
                'initial_metrics': initial_metrics,
                'final_metrics': final_metrics,
                'metrics_history': metrics_history
            }
            return True
            
        except Exception as e:
            print(f"   ✗ Metrics validation error: {e}")
            self.results['metrics_consistency'] = {'status': 'error', 'error': str(e)}
            return False
    
    def validate_performance(self) -> bool:
        """Validate system performance characteristics"""
        print("\n⚡ Validating Performance...")
        
        try:
            # Test prediction latency
            prediction_times = []
            for i in range(5):
                payload = {
                    "recent_accesses": list(range(i, i+10)),
                    "top_k": 5,
                    "latency_simulation_ms": 0
                }
                
                start_time = time.time()
                response = requests.post(f"{self.predictor_url}/predict", 
                                       json=payload, timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    prediction_times.append((end_time - start_time) * 1000)
            
            if prediction_times:
                avg_latency = statistics.mean(prediction_times)
                max_latency = max(prediction_times)
                print(f"   ✓ Average prediction latency: {avg_latency:.2f}ms")
                print(f"   ✓ Maximum prediction latency: {max_latency:.2f}ms")
                
                # Performance thresholds
                if avg_latency > 100:  # More than 100ms average
                    print(f"   ⚠ High average latency: {avg_latency:.2f}ms")
                
                if max_latency > 500:  # More than 500ms max
                    print(f"   ⚠ High maximum latency: {max_latency:.2f}ms")
            else:
                print(f"   ✗ No successful predictions for latency test")
                return False
            
            # Test backend response time
            backend_times = []
            for i in range(5):
                start_time = time.time()
                response = requests.get(f"{self.backend_url}/metrics", timeout=5)
                end_time = time.time()
                
                if response.status_code == 200:
                    backend_times.append((end_time - start_time) * 1000)
            
            if backend_times:
                avg_backend_latency = statistics.mean(backend_times)
                print(f"   ✓ Average backend latency: {avg_backend_latency:.2f}ms")
                
                if avg_backend_latency > 50:  # More than 50ms
                    print(f"   ⚠ High backend latency: {avg_backend_latency:.2f}ms")
            
            self.results['performance'] = {
                'status': 'valid',
                'prediction_latency': {
                    'average': statistics.mean(prediction_times),
                    'maximum': max(prediction_times),
                    'samples': prediction_times
                },
                'backend_latency': {
                    'average': statistics.mean(backend_times) if backend_times else 0,
                    'samples': backend_times
                }
            }
            return True
            
        except Exception as e:
            print(f"   ✗ Performance validation error: {e}")
            self.results['performance'] = {'status': 'error', 'error': str(e)}
            return False
    
    def validate_system_behavior(self) -> bool:
        """Validate overall system behavior and AI integration"""
        print("\n🔧 Validating System Behavior...")
        
        try:
            # Start simulation
            print("   Starting simulation...")
            response = requests.post(f"{self.backend_url}/simulate/start", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Failed to start simulation: {response.status_code}")
                return False
            
            # Let simulation run
            print("   Running simulation for 10 seconds...")
            time.sleep(10)
            
            # Get final metrics
            response = requests.get(f"{self.backend_url}/metrics", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Failed to get final metrics: {response.status_code}")
                return False
            
            metrics = response.json()
            
            # Validate system behavior
            total_accesses = metrics.get('total_accesses', 0)
            page_faults = metrics.get('page_faults', 0)
            ai_predictions = metrics.get('ai_predictions', 0)
            ai_hit_rate = metrics.get('ai_hit_rate', 0)
            
            print(f"   ✓ Total accesses: {total_accesses}")
            print(f"   ✓ Page faults: {page_faults}")
            print(f"   ✓ AI predictions: {ai_predictions}")
            print(f"   ✓ AI hit rate: {ai_hit_rate:.2%}")
            
            # Validate AI integration
            if ai_predictions > 0:
                print(f"   ✓ AI predictions are being used")
            else:
                print(f"   ⚠ No AI predictions recorded")
            
            # Validate reasonable page fault rate
            if total_accesses > 0:
                fault_rate = page_faults / total_accesses
                if fault_rate > 0.5:  # More than 50% fault rate
                    print(f"   ⚠ High page fault rate: {fault_rate:.2%}")
                else:
                    print(f"   ✓ Reasonable page fault rate: {fault_rate:.2%}")
            
            # Stop simulation
            response = requests.post(f"{self.backend_url}/simulate/stop", timeout=5)
            
            self.results['system_behavior'] = {
                'status': 'valid',
                'final_metrics': metrics,
                'ai_integration': ai_predictions > 0
            }
            return True
            
        except Exception as e:
            print(f"   ✗ System behavior validation error: {e}")
            self.results['system_behavior'] = {'status': 'error', 'error': str(e)}
            return False
    
    def run_validation(self) -> bool:
        """Run all validation tests"""
        print("=" * 60)
        print("AI-ENHANCED VMM SYSTEM VALIDATION")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        tests = [
            ("AI Predictions", self.validate_ai_predictions),
            ("Metrics Consistency", self.validate_metrics_consistency),
            ("Performance", self.validate_performance),
            ("System Behavior", self.validate_system_behavior)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"✗ {test_name} validation failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{test_name:20} {status}")
        
        print(f"\nOverall: {passed}/{total} validations passed")
        
        if passed == total:
            print("\n🎉 ALL VALIDATIONS PASSED!")
            print("Your AI-Enhanced VMM system is working correctly!")
        else:
            print(f"\n⚠️  {total - passed} validations failed.")
            print("Check the logs above for details.")
        
        return passed == total

def main():
    validator = SystemValidator()
    success = validator.run_validation()
    
    # Save results to file
    with open('validation_results.json', 'w') as f:
        json.dump(validator.results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: validation_results.json")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()