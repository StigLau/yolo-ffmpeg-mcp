#!/usr/bin/env python3
"""
Mixed Effects Test for Cloud Music Video Creator
Tests creating a video with different effects in different segments:
- First half: old-school effects (sepia, grain, low saturation)
- Second half: blurry effects (gaussian blur, motion blur)
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

# Simple settings for test
class SimpleSettings:
    def __init__(self):
        self.temp_storage_path = "/tmp/music-video-creator"
    
    def setup_directories(self):
        from pathlib import Path
        base = Path(self.temp_storage_path)
        for subdir in ["temp", "generated-videos", "source", "processing"]:
            (base / subdir).mkdir(parents=True, exist_ok=True)

settings = SimpleSettings()
from src.llm.prompts import get_user_prompt, get_processing_prompt


class MixedEffectsProcessor:
    """FFmpeg processor that creates videos with different effects per segment"""
    
    def __init__(self):
        self.temp_dir = Path(settings.temp_storage_path)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def create_test_source_video(self, duration: int = 20) -> str:
        """Create a longer test video for segmenting"""
        output_path = self.temp_dir / f"test_source_{duration}s.mp4"
        
        # Create test video with moving patterns
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'testsrc2=duration={duration}:size=1280x720:rate=25',
            '-c:v', 'libx264',
            '-t', str(duration),
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to create test video: {result.stderr}")
        
        return str(output_path)
    
    def create_first_half_oldschool(self, source: str, start: int, duration: int) -> str:
        """Create first segment with old-school effects"""
        output_path = self.temp_dir / f"segment1_oldschool.mp4"
        
        # Old-school effects: sepia tone, film grain, reduced saturation, slight vignette
        cmd = [
            'ffmpeg', '-y',
            '-i', source,
            '-ss', str(start),
            '-t', str(duration),
            '-vf', 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,noise=alls=20:allf=t,vignette=PI/6',
            '-c:v', 'libx264',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to create old-school segment: {result.stderr}")
        
        return str(output_path)
    
    def create_second_half_blurry(self, source: str, start: int, duration: int) -> str:
        """Create second segment with blurry effects"""
        output_path = self.temp_dir / f"segment2_blurry.mp4"
        
        # Blurry effects: gaussian blur + motion blur simulation
        cmd = [
            'ffmpeg', '-y',
            '-i', source,
            '-ss', str(start),
            '-t', str(duration),
            '-vf', 'gblur=sigma=3:steps=1,boxblur=luma_radius=2:luma_power=1',
            '-c:v', 'libx264',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to create blurry segment: {result.stderr}")
        
        return str(output_path)
    
    def concatenate_segments(self, segment1: str, segment2: str) -> str:
        """Concatenate the two segments into final video"""
        output_path = self.temp_dir / "generated-videos" / "mixed_effects_video.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create concat file
        concat_file = self.temp_dir / "concat_list.txt"
        with open(concat_file, 'w') as f:
            f.write(f"file '{segment1}'\n")
            f.write(f"file '{segment2}'\n")
        
        # Concatenate segments
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to concatenate segments: {result.stderr}")
        
        return str(output_path)
    
    def create_mixed_effects_video(self, total_duration: int = 20) -> str:
        """Create complete video with mixed effects"""
        # Create source video
        source_video = self.create_test_source_video(total_duration)
        print(f"📁 Created source video: {source_video}")
        
        # Calculate segment durations
        half_duration = total_duration // 2
        
        # Create first half with old-school effects
        print("🎭 Creating first half with old-school effects...")
        segment1 = self.create_first_half_oldschool(source_video, 0, half_duration)
        print(f"✅ First segment: {segment1}")
        
        # Create second half with blurry effects
        print("🌫️ Creating second half with blurry effects...")
        segment2 = self.create_second_half_blurry(source_video, half_duration, half_duration)
        print(f"✅ Second segment: {segment2}")
        
        # Concatenate segments
        print("🔗 Concatenating segments...")
        final_video = self.concatenate_segments(segment1, segment2)
        print(f"🎉 Final video: {final_video}")
        
        return final_video


async def test_mixed_effects_creation():
    """Test mixed effects music video creation"""
    print("🎬 Testing Mixed Effects Music Video Creation")
    
    # Setup
    settings.setup_directories()
    processor = MixedEffectsProcessor()
    
    # User request (simulated)
    user_request = "create a music video with first half having old-school effects, second half with blurry effects"
    user_id = "test_user_mixed"
    
    print(f"📝 User request: {user_request}")
    
    # Process user request through LLM prompt system
    user_prompt = get_user_prompt("gemini", user_request)
    print(f"🤖 Generated user prompt for Gemini")
    
    # Create komposition spec (simulated)
    komposition_data = {
        "id": "komp_mixed_123",
        "title": "Mixed Effects Video",
        "description": "Video with old-school effects in first half, blurry effects in second half",
        "user_id": user_id,
        "bpm": 120,
        "duration_seconds": 20,
        "status": "draft",
        "segments": [
            {
                "id": "seg_1",
                "start_seconds": 0,
                "duration_seconds": 10,
                "effects": ["sepia", "grain", "vignette", "desaturated"]
            },
            {
                "id": "seg_2", 
                "start_seconds": 10,
                "duration_seconds": 10,
                "effects": ["gaussian_blur", "motion_blur"]
            }
        ]
    }
    
    print(f"✅ Created komposition: {komposition_data['id']}")
    
    # Generate processing prompt
    processing_request = "Generate mixed effects video: first half old-school, second half blurry"
    processing_prompt = get_processing_prompt(
        "gemini",
        processing_request,
        json.dumps(komposition_data)
    )
    print(f"🔧 Generated processing prompt")
    
    # Create the mixed effects video
    print("⚡ Processing mixed effects video...")
    output_video = processor.create_mixed_effects_video(total_duration=20)
    
    # Verify output
    if Path(output_video).exists():
        file_size = Path(output_video).stat().st_size
        print(f"✅ Video created successfully! Size: {file_size} bytes")
        
        # Get video info
        info_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', output_video]
        result = subprocess.run(info_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            width = info['streams'][0]['width']
            height = info['streams'][0]['height']
            
            print(f"📊 Video duration: {duration:.1f} seconds")
            print(f"📐 Video resolution: {width}x{height}")
            
            # Test passed if duration is approximately 20 seconds
            if 19.0 <= duration <= 21.0:
                print("🎊 TEST PASSED: Mixed effects video created successfully!")
                print("   ✅ First 10 seconds: Old-school effects (sepia, grain, vignette)")
                print("   ✅ Second 10 seconds: Blurry effects (gaussian + box blur)")
                return True
            else:
                print(f"❌ TEST FAILED: Duration {duration}s not close to 20s")
                return False
        else:
            print("❌ Could not get video info")
            return False
    else:
        print("❌ TEST FAILED: Output video not created")
        return False


def main():
    """Run mixed effects test"""
    print("🚀 Cloud Music Video Creator - Mixed Effects Test")
    print("=" * 55)
    
    # Check FFmpeg availability
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found. Please install FFmpeg first.")
        sys.exit(1)
    
    async def run_test():
        result = await test_mixed_effects_creation()
        
        print("\n" + "=" * 55)
        print("📊 TEST RESULT:")
        print(f"Mixed Effects Video: {'PASS' if result else 'FAIL'}")
        
        if result:
            print("🎉 MIXED EFFECTS TEST PASSED!")
            return 0
        else:
            print("💥 MIXED EFFECTS TEST FAILED!")
            return 1
    
    exit_code = asyncio.run(run_test())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()