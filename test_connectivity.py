#!/usr/bin/env python3
"""
Connectivity Testing Script for AI-Enhanced VMM System
Tests all three services and their integration.
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

class ConnectivityTester:
    def __init__(self):
        self.predictor_url = "http://localhost:5001"
        self.backend_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:3000"
        self.results = {}
        
    def test_predictor_service(self) -> bool:
        """Test AI Predictor service"""
        print("🔍 Testing AI Predictor Service...")
        
        try:
            # Test health endpoint
            response = requests.get(f"{self.predictor_url}/health", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Health check failed: {response.status_code}")
                return False
                
            health_data = response.json()
            print(f"   ✓ Health: {health_data['status']}")
            print(f"   ✓ Model loaded: {health_data['model_loaded']}")
            
            # Test prediction endpoint
            test_payload = {
                "recent_accesses": [1, 2, 3, 4, 5],
                "top_k": 5,
                "latency_simulation_ms": 0
            }
            
            response = requests.post(f"{self.predictor_url}/predict", 
                                   json=test_payload, timeout=10)
            if response.status_code != 200:
                print(f"   ✗ Prediction failed: {response.status_code}")
                return False
                
            pred_data = response.json()
            print(f"   ✓ Predictions: {len(pred_data['predicted_pages'])} pages")
            print(f"   ✓ Processing time: {pred_data['processing_time_ms']:.2f}ms")
            
            self.results['predictor'] = {
                'status': 'healthy',
                'health': health_data,
                'prediction_test': pred_data
            }
            return True
            
        except Exception as e:
            print(f"   ✗ AI Predictor error: {e}")
            self.results['predictor'] = {'status': 'error', 'error': str(e)}
            return False
    
    def test_backend_service(self) -> bool:
        """Test C++ Backend service"""
        print("\n🔍 Testing C++ Backend Service...")
        
        try:
            # Test metrics endpoint
            response = requests.get(f"{self.backend_url}/metrics", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Metrics endpoint failed: {response.status_code}")
                return False
                
            metrics_data = response.json()
            print(f"   ✓ Metrics endpoint working")
            print(f"   ✓ Total accesses: {metrics_data.get('total_accesses', 0)}")
            print(f"   ✓ Page faults: {metrics_data.get('page_faults', 0)}")
            print(f"   ✓ AI predictions: {metrics_data.get('ai_predictions', 0)}")
            
            # Test simulation start
            response = requests.post(f"{self.backend_url}/simulate/start", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Simulation start failed: {response.status_code}")
                return False
                
            start_data = response.json()
            print(f"   ✓ Simulation started: {start_data.get('status')}")
            
            # Wait a bit for simulation to run
            time.sleep(2)
            
            # Test simulation stop
            response = requests.post(f"{self.backend_url}/simulate/stop", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Simulation stop failed: {response.status_code}")
                return False
                
            stop_data = response.json()
            print(f"   ✓ Simulation stopped: {stop_data.get('status')}")
            
            self.results['backend'] = {
                'status': 'healthy',
                'metrics': metrics_data,
                'simulation_test': {'start': start_data, 'stop': stop_data}
            }
            return True
            
        except Exception as e:
            print(f"   ✗ C++ Backend error: {e}")
            self.results['backend'] = {'status': 'error', 'error': str(e)}
            return False
    
    def test_frontend_service(self) -> bool:
        """Test React Frontend service"""
        print("\n🔍 Testing React Frontend Service...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code != 200:
                print(f"   ✗ Frontend not accessible: {response.status_code}")
                return False
                
            print(f"   ✓ Frontend accessible")
            print(f"   ✓ React app running")
            
            self.results['frontend'] = {
                'status': 'healthy',
                'accessible': True
            }
            return True
            
        except Exception as e:
            print(f"   ✗ Frontend error: {e}")
            self.results['frontend'] = {'status': 'error', 'error': str(e)}
            return False
    
    def test_sse_streaming(self) -> bool:
        """Test Server-Sent Events streaming"""
        print("\n🔍 Testing SSE Event Streaming...")
        
        try:
            # Start simulation to generate events
            requests.post(f"{self.backend_url}/simulate/start", timeout=5)
            
            # Test SSE connection
            response = requests.get(f"{self.backend_url}/events/stream", 
                                  stream=True, timeout=10)
            if response.status_code != 200:
                print(f"   ✗ SSE endpoint failed: {response.status_code}")
                return False
                
            print(f"   ✓ SSE connection established")
            
            # Read a few events
            event_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    event_data = line[6:]  # Remove 'data: ' prefix
                    try:
                        event_json = json.loads(event_data)
                        print(f"   ✓ Event received: {event_json.get('type', 'unknown')}")
                        event_count += 1
                        if event_count >= 3:  # Read 3 events then stop
                            break
                    except json.JSONDecodeError:
                        print(f"   ⚠ Invalid JSON event: {event_data}")
            
            # Stop simulation
            requests.post(f"{self.backend_url}/simulate/stop", timeout=5)
            
            if event_count > 0:
                print(f"   ✓ Received {event_count} events")
                self.results['sse'] = {'status': 'healthy', 'events_received': event_count}
                return True
            else:
                print(f"   ✗ No events received")
                self.results['sse'] = {'status': 'error', 'error': 'No events received'}
                return False
                
        except Exception as e:
            print(f"   ✗ SSE error: {e}")
            self.results['sse'] = {'status': 'error', 'error': str(e)}
            return False
    
    def test_integration(self) -> bool:
        """Test end-to-end integration"""
        print("\n🔍 Testing End-to-End Integration...")
        
        try:
            # Start simulation
            print("   Starting simulation...")
            response = requests.post(f"{self.backend_url}/simulate/start", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Failed to start simulation: {response.status_code}")
                return False
            
            # Let simulation run for a few seconds
            print("   Running simulation for 5 seconds...")
            time.sleep(5)
            
            # Check metrics
            response = requests.get(f"{self.backend_url}/metrics", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Failed to get metrics: {response.status_code}")
                return False
                
            metrics = response.json()
            print(f"   ✓ Total accesses: {metrics.get('total_accesses', 0)}")
            print(f"   ✓ Page faults: {metrics.get('page_faults', 0)}")
            print(f"   ✓ AI predictions: {metrics.get('ai_predictions', 0)}")
            print(f"   ✓ AI hit rate: {metrics.get('ai_hit_rate', 0):.2%}")
            
            # Stop simulation
            response = requests.post(f"{self.backend_url}/simulate/stop", timeout=5)
            if response.status_code != 200:
                print(f"   ✗ Failed to stop simulation: {response.status_code}")
                return False
            
            print(f"   ✓ Integration test completed")
            
            self.results['integration'] = {
                'status': 'healthy',
                'final_metrics': metrics
            }
            return True
            
        except Exception as e:
            print(f"   ✗ Integration error: {e}")
            self.results['integration'] = {'status': 'error', 'error': str(e)}
            return False
    
    def run_all_tests(self) -> bool:
        """Run all connectivity tests"""
        print("=" * 60)
        print("AI-ENHANCED VMM CONNECTIVITY TEST")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        tests = [
            ("AI Predictor", self.test_predictor_service),
            ("C++ Backend", self.test_backend_service),
            ("React Frontend", self.test_frontend_service),
            ("SSE Streaming", self.test_sse_streaming),
            ("Integration", self.test_integration)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"✗ {test_name} test failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("CONNECTIVITY TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{test_name:20} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("Your AI-Enhanced VMM system is working correctly!")
        else:
            print(f"\n⚠️  {total - passed} tests failed.")
            print("Check the logs above for details.")
        
        return passed == total

def main():
    tester = ConnectivityTester()
    success = tester.run_all_tests()
    
    # Save results to file
    with open('connectivity_test_results.json', 'w') as f:
        json.dump(tester.results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: connectivity_test_results.json")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()