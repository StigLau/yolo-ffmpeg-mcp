#!/usr/bin/env python3
"""
Test FFmpeg operations directly to see what's happening
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_ffmpeg_direct():
    print("🔧 Testing FFmpeg Direct Operations")
    print("=" * 50)
    
    try:
        # Import components 
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        
        # Initialize FFmpeg wrapper
        ffmpeg_wrapper = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        
        # Test file paths
        input_file = Path("/tmp/music/source/lookin.mp4")
        output_file = Path("/tmp/music/temp/test_trim_output.mp4")
        
        print(f"📁 Input file: {input_file}")
        print(f"📁 Input exists: {input_file.exists()}")
        print(f"📁 Output file: {output_file}")
        
        if not input_file.exists():
            print("❌ Input file doesn't exist!")
            return
            
        # Test 1: Get file info first
        print(f"\n📊 Getting file info...")
        
        info_cmd = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(input_file),
            "-f", "null", "-"  # Null output to just get info
        ]
        
        info_result = await ffmpeg_wrapper.execute_command(info_cmd, timeout=30)
        print(f"   Info command success: {info_result['success']}")
        print(f"   Info logs: {info_result.get('logs', 'No logs')[:200]}...")
        
        # Test 2: Simple trim with re-encoding
        print(f"\n🔪 Testing trim with re-encoding...")
        
        cmd = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(input_file),
            "-ss", "0",      # Start at 0 seconds
            "-t", "3",       # Duration 3 seconds (shorter for faster test)
            "-c:v", "libx264",   # Re-encode video
            "-c:a", "aac",       # Re-encode audio
            "-y",                # Overwrite output
            str(output_file)
        ]
        
        print(f"   Command: {' '.join(cmd)}")
        
        # Execute command
        result = await ffmpeg_wrapper.execute_command(cmd, timeout=120)
        
        print(f"   ✅ Success: {result['success']}")
        print(f"   📂 Output exists: {output_file.exists()}")
        
        if result.get('logs'):
            print(f"   📋 FFmpeg logs (last 300 chars):")
            print(f"      {result['logs'][-300:]}")
        
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"   📏 Output size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            if file_size > 0:
                print(f"   🎉 TRIM WITH RE-ENCODING SUCCESSFUL!")
                return True
            else:
                print(f"   ❌ Output file is empty")
        else:
            print(f"   ❌ Output file not created")
            
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ffmpeg_direct())
    if success:
        print(f"\n🎉 FFmpeg is working correctly!")
    else:
        print(f"\n❌ FFmpeg issues detected")