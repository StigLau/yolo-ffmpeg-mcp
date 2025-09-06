#!/usr/bin/env python3
"""
Test script for Haiku MCP integration.
Validates the bridge connection and basic FFmpeg operations.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path

from src.ffmpeg_processor import HaikuMCPBridge, create_haiku_ffmpeg_processor

async def test_haiku_bridge():
    """Test basic Haiku MCP bridge functionality."""
    print("🧠 Testing Haiku MCP Bridge...")
    
    # Create bridge instance
    bridge = HaikuMCPBridge()
    
    # Test initialization
    print("📡 Initializing Haiku MCP Bridge...")
    success = await bridge.initialize()
    
    if not success:
        print("❌ Bridge initialization failed")
        return False
    
    print("✅ Bridge initialized successfully")
    
    # Test LLM stats
    print("📊 Getting LLM statistics...")
    stats_result = await bridge.get_llm_stats()
    
    if stats_result.get("success"):
        print("✅ LLM stats retrieved successfully:")
        print(json.dumps(stats_result, indent=2))
    else:
        print(f"⚠️ LLM stats failed: {stats_result.get('error')}")
    
    return True

async def test_video_processing():
    """Test video processing with Haiku MCP."""
    print("\n🎬 Testing video processing...")
    
    # Create temp directory for outputs
    with tempfile.TemporaryDirectory(prefix="haiku_test_") as temp_dir:
        output_file = os.path.join(temp_dir, "test_output.mp4")
        
        # Create FFmpeg processor with Haiku
        processor = create_haiku_ffmpeg_processor()
        
        if not processor.haiku_bridge:
            print("❌ Haiku bridge not available")
            return False
        
        # Test simple video generation
        print("🎥 Testing simple video generation...")
        result = await processor.haiku_bridge.process_video_file(
            input_file="testsrc2=duration=5:size=640x480:rate=30",  # Test pattern
            output_file=output_file,
            operation="generate_test_video",
            parameters={"duration": 5, "format": "mp4"}
        )
        
        if result.get("success"):
            print("✅ Video processing successful")
            print(f"📁 Output: {result.get('output_file', 'N/A')}")
            
            # Check if file was created
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"📏 File size: {file_size} bytes")
            else:
                print("⚠️ Output file not found at expected location")
        else:
            print(f"❌ Video processing failed: {result.get('error')}")
            return False
    
    return True

async def test_komposition_integration():
    """Test full komposition processing integration."""
    print("\n🎼 Testing komposition integration...")
    
    # Sample YOLO-format komposition
    sample_komposition = {
        "metadata": {
            "title": "Test Komposition",
            "duration": 10,
            "bpm": 120
        },
        "segments": [
            {
                "id": "seg_001",
                "start": 0,
                "duration": 5,
                "source": {
                    "type": "video",
                    "path": "../.testdata/JJVtt947FfI_136.mp4"
                },
                "filters": ["fade_in", "sepia"]
            },
            {
                "id": "seg_002", 
                "start": 5,
                "duration": 5,
                "source": {
                    "type": "video",
                    "path": "../.testdata/_wZ5Hof5tXY_136.mp4"
                },
                "filters": ["crossfade", "modern"]
            }
        ],
        "audio": {
            "source": {
                "type": "audio",
                "path": "../.testdata/16BL - Deep In My Soul (Original Mix).mp3"
            }
        }
    }
    
    # Create temp directory for outputs
    with tempfile.TemporaryDirectory(prefix="kompo_test_") as temp_dir:
        output_path = os.path.join(temp_dir, "komposition_output.mp4")
        
        # Create processor
        processor = create_haiku_ffmpeg_processor()
        
        # Test komposition processing
        print("🔄 Processing komposition...")
        result = await processor.create_komposition_video_with_haiku(
            komposition=sample_komposition,
            output_path=output_path
        )
        
        if result.get("success"):
            print("✅ Komposition processing successful")
            print(f"📁 Output: {result.get('output_file', 'N/A')}")
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) 
                print(f"📏 File size: {file_size} bytes")
            else:
                print("⚠️ Output file not found")
        else:
            print(f"❌ Komposition processing failed: {result.get('error')}")
            return False
    
    return True

async def main():
    """Run all Haiku integration tests."""
    print("🚀 Haiku MCP Integration Test Suite")
    print("=" * 50)
    
    # Check if Haiku server is available
    haiku_path = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/haiku-mcp-ts"
    if not os.path.exists(haiku_path):
        print(f"❌ Haiku MCP server not found at {haiku_path}")
        return
    
    # Test environment
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if anthropic_key:
        print("✅ ANTHROPIC_API_KEY found")
    else:
        print("⚠️ ANTHROPIC_API_KEY not set - will use fallback mode")
    
    print()
    
    # Run tests
    tests = [
        ("Haiku Bridge", test_haiku_bridge),
        ("Video Processing", test_video_processing),
        ("Komposition Integration", test_komposition_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Haiku MCP integration is working.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(main())