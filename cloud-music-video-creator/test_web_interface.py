#!/usr/bin/env python3
"""
Web Interface Test - Complete Feature Test
Tests the minimal web UI and API functionality
"""

import asyncio
import json
import time
import requests


class WebInterfaceTest:
    def __init__(self, base_url="http://localhost:8005"):
        self.base_url = base_url
        
    def test_health(self):
        """Test server health endpoint"""
        print("🏥 Testing health endpoint...")
        response = requests.get(f"{self.base_url}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ Health: {data['message']}")
        
    def test_create_video(self):
        """Test video creation endpoint"""
        print("🎬 Testing video creation...")
        payload = {
            "description": "Create a test video with vintage effects",
            "duration": 10,
            "music_style": "electronic"
        }
        
        response = requests.post(
            f"{self.base_url}/api/create-video",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"
        
        job_id = data["job_id"]
        print(f"✅ Video job created: {job_id}")
        return job_id
        
    def test_status_polling(self, job_id):
        """Test status polling until completion"""
        print("📊 Testing status polling...")
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            response = requests.get(f"{self.base_url}/api/status/{job_id}")
            assert response.status_code == 200
            
            data = response.json()
            print(f"  Status: {data['message']} ({data['progress']}%)")
            
            if data["status"] == "completed":
                print("✅ Video creation completed!")
                assert "video_url" in data
                return data["video_url"]
                
            elif data["status"] == "failed":
                raise Exception(f"Video creation failed: {data['message']}")
                
            time.sleep(2)
            attempt += 1
            
        raise Exception("Status polling timed out")
        
    def test_download_availability(self, video_url):
        """Test that download URL responds (without downloading full file)"""
        print("💾 Testing download availability...")
        full_url = f"{self.base_url}{video_url}"
        
        # Make a range request to test availability without downloading full file
        response = requests.get(full_url, headers={"Range": "bytes=0-1023"}, stream=True)
        
        # Accept either 206 (partial content) or 200 (full file)
        assert response.status_code in [200, 206]
        print("✅ Download URL is accessible")
        
    def test_concurrent_requests(self):
        """Test multiple concurrent video creation requests"""
        print("🔄 Testing concurrent requests...")
        
        # Create two videos simultaneously
        payload1 = {"description": "Vintage video test", "duration": 10}
        payload2 = {"description": "Modern video test", "duration": 10}
        
        response1 = requests.post(f"{self.base_url}/api/create-video", json=payload1)
        response2 = requests.post(f"{self.base_url}/api/create-video", json=payload2)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        job1 = response1.json()["job_id"]
        job2 = response2.json()["job_id"]
        
        print(f"✅ Two concurrent jobs created: {job1[:8]}... and {job2[:8]}...")
        
        # Check server can handle both
        health = requests.get(f"{self.base_url}/api/health")
        data = health.json()
        assert data["active_jobs"] >= 2
        print(f"✅ Server managing {data['active_jobs']} active jobs")
        
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Starting Web Interface Test Suite")
        print("=" * 50)
        
        try:
            # Basic functionality tests
            self.test_health()
            
            # Core workflow test
            job_id = self.test_create_video()
            video_url = self.test_status_polling(job_id)
            self.test_download_availability(video_url)
            
            # Advanced tests
            self.test_concurrent_requests()
            
            print("\n🎉 ALL TESTS PASSED")
            print("✅ Web interface is fully functional")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


def test_web_ui_manually():
    """Instructions for manual UI testing"""
    print("\n🖥️  Manual Web UI Test")
    print("=" * 30)
    print("1. Open http://localhost:8005")
    print("2. Enter: 'Create a vintage music video with dreamy effects'")
    print("3. Click 'Send Request'")
    print("4. Watch responses log in real-time")
    print("5. Should see: Job created → Status updates → COMPLETED with download URL")


if __name__ == "__main__":
    test = WebInterfaceTest()
    
    try:
        test.run_all_tests()
        test_web_ui_manually()
        
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: python3 simple_server.py 8005")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")