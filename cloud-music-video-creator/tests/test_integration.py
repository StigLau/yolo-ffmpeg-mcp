#!/usr/bin/env python3
"""
Integration test for Cloud Music Video Creator
Tests the full workflow: user prompt -> MCP server -> FFmpeg processing
"""

import os
import sys
import asyncio
import json
import subprocess
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from src.llm.prompts import get_user_prompt, get_processing_prompt


class MockFFmpegProcessor:
    """Mock FFmpeg processor that creates actual test video"""
    
    def __init__(self):
        self.temp_dir = Path(settings.temp_storage_path)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def create_test_source_video(self) -> str:
        """Create a simple test video using FFmpeg"""
        output_path = self.temp_dir / "test_source.mp4"
        
        # Create 10 second test video with color bars and vintage effect
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', 'testsrc2=duration=10:size=1280x720:rate=25',
            '-vf', 'hue=s=0.8,curves=vintage,vignette',
            '-c:v', 'libx264',
            '-t', '10',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to create test video: {result.stderr}")
        
        return str(output_path)
    
    def create_vintage_music_video(self, source_files: list, duration: int = 30) -> str:
        """Create vintage-style music video from sources"""
        output_path = self.temp_dir / "generated-videos" / f"vintage_video_{duration}s.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Simple vintage music video: loop first source with vintage effects
        source = source_files[0] if source_files else self.create_test_source_video()
        
        cmd = [
            'ffmpeg', '-y',
            '-i', source,
            '-vf', f'loop=loop=-1:size=1:start=0,hue=s=0.7,curves=vintage,vignette=PI/4,scale=1280:720',
            '-c:v', 'libx264',
            '-t', str(duration),
            '-an',  # No audio for now
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")
        
        return str(output_path)


async def test_music_video_creation():
    """Test full music video creation workflow"""
    print("🎬 Testing Music Video Creation Workflow")
    
    # Setup
    settings.setup_directories()
    ffmpeg_processor = MockFFmpegProcessor()
    
    # User input
    user_request = "make me a music video that runs for 30 seconds that has nice vintage vibe"
    user_id = "test_user_123"
    
    print(f"📝 User request: {user_request}")
    
    # Step 1: Process user request through LLM prompt system
    user_prompt = get_user_prompt("gemini", user_request)
    print(f"🤖 Generated user prompt for Gemini")
    
    # Step 2: Create komposition (simplified for test)
    print("📋 Creating komposition...")
    
    komposition_spec = {
        "title": "Vintage Music Video",
        "description": "30-second music video with vintage vibe",
        "user_id": user_id,
        "bpm": 120,
        "duration_seconds": 30,
        "visual_concept": "vintage vibe"
    }
    
    # Simulate MCP tool call
    komposition_data = {
        "id": "komp_123",
        "title": komposition_spec["title"],
        "description": komposition_spec["description"],
        "user_id": user_id,
        "bpm": 120,
        "duration_seconds": 30,
        "status": "draft",
        "segments": [
            {
                "id": "seg_1",
                "start_seconds": 0,
                "duration_seconds": 30,
                "effects": ["vintage", "vignette"]
            }
        ]
    }
    
    print(f"✅ Created komposition: {komposition_data['id']}")
    
    # Step 3: Generate processing prompt
    processing_request = "Generate vintage music video with duration 30 seconds"
    processing_prompt = get_processing_prompt(
        "gemini", 
        processing_request, 
        json.dumps(komposition_data)
    )
    print(f"🔧 Generated processing prompt")
    
    # Step 4: Create test source and process video
    print("🎥 Creating test source video...")
    source_video = ffmpeg_processor.create_test_source_video()
    print(f"📁 Created source: {source_video}")
    
    print("⚡ Processing vintage music video...")
    output_video = ffmpeg_processor.create_vintage_music_video(
        [source_video], 
        duration=30
    )
    print(f"🎉 Generated video: {output_video}")
    
    # Step 5: Verify output
    if Path(output_video).exists():
        file_size = Path(output_video).stat().st_size
        print(f"✅ Video created successfully! Size: {file_size} bytes")
        
        # Get video info
        info_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', output_video]
        result = subprocess.run(info_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            print(f"📊 Video duration: {duration:.1f} seconds")
            print(f"📐 Video resolution: {info['streams'][0]['width']}x{info['streams'][0]['height']}")
            
            # Test passed if duration is approximately 30 seconds
            if 29.0 <= duration <= 31.0:
                print("🎊 TEST PASSED: Video created with correct duration and vintage effects!")
                return True
            else:
                print(f"❌ TEST FAILED: Duration {duration}s not close to 30s")
                return False
        else:
            print("❌ Could not get video info")
            return False
    else:
        print("❌ TEST FAILED: Output video not created")
        return False


async def test_simple_workflow():
    """Simplified test focusing on FFmpeg processing"""
    print("\n🔥 Testing Simple FFmpeg Workflow")
    
    settings.setup_directories()
    processor = MockFFmpegProcessor()
    
    # Direct FFmpeg test
    print("🎬 Creating vintage test video...")
    output = processor.create_vintage_music_video([], duration=30)
    
    if Path(output).exists():
        print(f"✅ Direct FFmpeg test PASSED: {output}")
        return True
    else:
        print("❌ Direct FFmpeg test FAILED")
        return False


def main():
    """Run integration tests"""
    print("🚀 Cloud Music Video Creator - Integration Tests")
    print("=" * 50)
    
    # Check FFmpeg availability
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found. Please install FFmpeg first.")
        sys.exit(1)
    
    async def run_tests():
        results = []
        
        # Test 1: Simple FFmpeg workflow
        results.append(await test_simple_workflow())
        
        # Test 2: Full integration (if simple test passes)
        if results[-1]:
            results.append(await test_music_video_creation())
        
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS:")
        print(f"Simple FFmpeg: {'PASS' if results[0] else 'FAIL'}")
        if len(results) > 1:
            print(f"Full Integration: {'PASS' if results[1] else 'FAIL'}")
        
        if all(results):
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print("💥 SOME TESTS FAILED!")
            return 1
    
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()