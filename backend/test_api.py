#!/usr/bin/env python3
"""
Test script for Virtual Memory Manager Simulator API
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8080"

def test_metrics():
    """Test the /metrics endpoint"""
    print("Testing /metrics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        if response.status_code == 200:
            metrics = response.json()
            print("✓ Metrics retrieved successfully:")
            print(f"  Total accesses: {metrics.get('total_accesses', 0)}")
            print(f"  Page faults: {metrics.get('page_faults', 0)}")
            print(f"  Page fault rate: {metrics.get('page_fault_rate', 0):.3f}")
            print(f"  Free frames: {metrics.get('free_frames', 0)}")
            print(f"  Used frames: {metrics.get('used_frames', 0)}")
            return True
        else:
            print(f"✗ Failed to get metrics: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to server: {e}")
        return False

def test_start_simulation():
    """Test the /simulate/start endpoint"""
    print("\nTesting /simulate/start endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/simulate/start")
        if response.status_code == 200:
            result = response.json()
            print("✓ Simulation started successfully:")
            print(f"  Status: {result.get('status', 'unknown')}")
            print(f"  Workload type: {result.get('workload_type', 'unknown')}")
            return True
        else:
            print(f"✗ Failed to start simulation: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error starting simulation: {e}")
        return False

def test_stop_simulation():
    """Test the /simulate/stop endpoint"""
    print("\nTesting /simulate/stop endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/simulate/stop")
        if response.status_code == 200:
            result = response.json()
            print("✓ Simulation stopped successfully:")
            print(f"  Status: {result.get('status', 'unknown')}")
            return True
        else:
            print(f"✗ Failed to stop simulation: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error stopping simulation: {e}")
        return False

def test_events_stream():
    """Test the /events/stream endpoint"""
    print("\nTesting /events/stream endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/events/stream", stream=True)
        if response.status_code == 200:
            print("✓ Event stream connected successfully")
            print("  Listening for events (5 seconds)...")
            
            start_time = time.time()
            event_count = 0
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        event_count += 1
                        try:
                            event_data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            print(f"  Event {event_count}: {event_data.get('type', 'unknown')} - {event_data.get('message', '')}")
                        except json.JSONDecodeError:
                            print(f"  Event {event_count}: {line_str}")
                
                # Stop after 5 seconds
                if time.time() - start_time > 5:
                    break
            
            print(f"✓ Received {event_count} events in 5 seconds")
            return True
        else:
            print(f"✗ Failed to connect to event stream: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error connecting to event stream: {e}")
        return False

def main():
    """Run all API tests"""
    print("Virtual Memory Manager Simulator API Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
    except requests.exceptions.RequestException:
        print("✗ Server is not running. Please start the simulator first.")
        print("  Run: ./bin/vmm_simulator")
        sys.exit(1)
    
    # Run tests
    tests = [
        test_metrics,
        test_start_simulation,
        test_events_stream,
        test_stop_simulation,
        test_metrics  # Test metrics again after simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The API is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Check the server logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
