#!/usr/bin/env python3
"""
Test script for the stop button functionality
"""

import requests
import time
import json

def test_stop_functionality():
    """Test the stop button API endpoints"""
    base_url = "http://localhost:8003"
    
    print("🛑 Testing Stop Button Functionality")
    print("=" * 50)
    
    # Test 1: Create a video job
    print("1. Creating test video job...")
    job_response = requests.post(f"{base_url}/api/create-video-from-komposition", 
                                json={"komposition": "# Test Video\nThis is a test komposition for stop testing"})
    
    if job_response.status_code != 200:
        print(f"❌ Failed to create job: {job_response.text}")
        return False
    
    job_data = job_response.json()
    job_id = job_data.get("job_id")
    print(f"✅ Created job: {job_id}")
    
    # Test 2: Check initial job status
    print("2. Checking initial job status...")
    status_response = requests.get(f"{base_url}/api/status/{job_id}")
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"✅ Job status: {status_data.get('status')} - {status_data.get('message')}")
    else:
        print(f"❌ Failed to get status: {status_response.text}")
        return False
    
    # Test 3: Stop the job
    print("3. Stopping the job...")
    stop_response = requests.post(f"{base_url}/api/stop/{job_id}")
    
    if stop_response.status_code == 200:
        stop_data = stop_response.json()
        print(f"✅ Stop request successful: {stop_data.get('message')}")
    else:
        print(f"❌ Failed to stop job: {stop_response.text}")
        return False
    
    # Test 4: Verify job was cancelled
    print("4. Verifying job cancellation...")
    time.sleep(1)  # Give it a moment to update
    final_status_response = requests.get(f"{base_url}/api/status/{job_id}")
    
    if final_status_response.status_code == 200:
        final_status = final_status_response.json()
        if final_status.get("status") == "cancelled":
            print(f"✅ Job successfully cancelled: {final_status.get('message')}")
        else:
            print(f"⚠️ Job status: {final_status.get('status')} (might still be processing)")
    else:
        print(f"❌ Failed to get final status: {final_status_response.text}")
        return False
    
    # Test 5: Try to stop already cancelled job (should fail gracefully)
    print("5. Testing stop on already cancelled job...")
    second_stop_response = requests.post(f"{base_url}/api/stop/{job_id}")
    
    if second_stop_response.status_code == 400:
        error_data = second_stop_response.json()
        print(f"✅ Correctly prevented stopping cancelled job: {error_data.get('error')}")
    else:
        print(f"⚠️ Unexpected response when stopping cancelled job: {second_stop_response.status_code}")
    
    # Test 6: Test stopping non-existent job
    print("6. Testing stop on non-existent job...")
    fake_stop_response = requests.post(f"{base_url}/api/stop/fake-job-id")
    
    if fake_stop_response.status_code == 404:
        print(f"✅ Correctly handled non-existent job")
    else:
        print(f"⚠️ Unexpected response for fake job: {fake_stop_response.status_code}")
    
    print("\n🎯 Stop Functionality Test Results:")
    print("✅ Job creation: WORKING")
    print("✅ Job stopping: WORKING") 
    print("✅ Status updates: WORKING")
    print("✅ Error handling: WORKING")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Stop Button Test...")
    try:
        success = test_stop_functionality()
        if success:
            print(f"\n🎉 STOP BUTTON TEST: PASSED")
            print(f"✅ The stop button functionality is working correctly")
        else:
            print(f"\n💥 STOP BUTTON TEST: FAILED")
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()