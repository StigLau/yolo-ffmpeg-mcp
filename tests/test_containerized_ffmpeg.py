#!/usr/bin/env python3
"""Test containerized FFmpeg implementation"""

import sys
import os
import asyncio
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.containerized_ffmpeg import ContainerizedFFmpeg, is_containerized_ffmpeg_available
from src.ffmpeg_wrapper import FFMPEGWrapper

async def test_containerized_availability():
    """Test if containerized FFmpeg is available"""
    print("🔍 Testing containerized FFmpeg availability...")
    
    available = is_containerized_ffmpeg_available()
    print(f"Containerized FFmpeg available: {available}")
    
    if not available:
        print("❌ Containerized FFmpeg not available - need to build container first")
        return False
    
    return True

def build_ffmpeg_container():
    """Build the FFmpeg runner container"""
    print("🏗️ Building FFmpeg runner container...")
    
    dockerfile_path = Path("docker/ffmpeg-runner")
    if not dockerfile_path.exists():
        print(f"❌ Dockerfile not found at {dockerfile_path}")
        return False
    
    # Build using Docker CLI
    import subprocess
    try:
        result = subprocess.run([
            "docker", "build", 
            "-t", "yolo-ffmpeg-runner:latest",
            "-f", str(dockerfile_path / "Dockerfile"),
            str(dockerfile_path.parent)
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ FFmpeg container built successfully")
            return True
        else:
            print(f"❌ Container build failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutError:
        print("❌ Container build timed out")
        return False
    except Exception as e:
        print(f"❌ Container build error: {e}")
        return False

async def test_basic_ffmpeg_operation():
    """Test basic FFmpeg operation with containerized vs native"""
    print("\n🧪 Testing basic FFmpeg operation...")
    
    # Create test directories
    input_dir = Path("/tmp/music/source")
    output_dir = Path("/tmp/music/temp")
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple test video (just audio tone)
    test_input = input_dir / "test_input.mp4"
    
    print("📹 Creating test video...")
    import subprocess
    result = subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
        "-c:v", "libx264", "-c:a", "aac", "-t", "2", 
        str(test_input), "-y"
    ], capture_output=True)
    
    if result.returncode != 0:
        print("❌ Failed to create test video - ffmpeg not available natively")
        return False
    
    print(f"✅ Test video created: {test_input}")
    
    # Test 1: Native FFmpeg
    print("\n🔄 Testing native FFmpeg...")
    native_wrapper = FFMPEGWrapper(use_containerized=False)
    
    start_time = time.time()
    native_result = await native_wrapper.execute_command([
        "ffmpeg", "-i", str(test_input), "-c:v", "libx264", "-t", "1",
        str(output_dir / "test_native.mp4"), "-y"
    ])
    native_duration = time.time() - start_time
    
    print(f"Native result: {native_result['success']}, Duration: {native_duration:.2f}s")
    
    # Test 2: Containerized FFmpeg
    print("\n🐳 Testing containerized FFmpeg...")
    container_wrapper = FFMPEGWrapper(use_containerized=True)
    
    start_time = time.time()
    container_result = await container_wrapper.execute_command([
        "ffmpeg", "-i", str(test_input), "-c:v", "libx264", "-t", "1", 
        str(output_dir / "test_container.mp4"), "-y"
    ])
    container_duration = time.time() - start_time
    
    print(f"Container result: {container_result['success']}, Duration: {container_duration:.2f}s")
    
    # Compare results
    print(f"\n📊 Performance comparison:")
    print(f"Native: {native_duration:.2f}s")
    print(f"Container: {container_duration:.2f}s")
    print(f"Overhead: {container_duration - native_duration:.2f}s ({((container_duration / native_duration - 1) * 100):.1f}%)")
    
    # Check output files
    native_output = output_dir / "test_native.mp4"
    container_output = output_dir / "test_container.mp4"
    
    print(f"\n📁 Output files:")
    print(f"Native output exists: {native_output.exists()}")
    print(f"Container output exists: {container_output.exists()}")
    
    if native_output.exists():
        print(f"Native file size: {native_output.stat().st_size} bytes")
    if container_output.exists():
        print(f"Container file size: {container_output.stat().st_size} bytes")
    
    return native_result['success'] and container_result['success']

async def test_trace_logging():
    """Test that trace logging works with containerized FFmpeg"""
    print("\n📝 Testing trace logging...")
    
    # Check for trace files
    trace_dir = Path("/tmp/mcp-traces")
    if trace_dir.exists():
        trace_files = list(trace_dir.glob("**/*.jsonl"))
        print(f"Found {len(trace_files)} trace files")
        
        if trace_files:
            latest_trace = max(trace_files, key=lambda f: f.stat().st_mtime)
            print(f"Latest trace: {latest_trace}")
            
            # Show last few lines
            with open(latest_trace) as f:
                lines = f.readlines()
                print("Last few trace entries:")
                for line in lines[-3:]:
                    print(f"  {line.strip()}")
    else:
        print("❌ No trace directory found")

async def main():
    """Main test function"""
    print("🚀 Containerized FFmpeg Test Suite")
    print("=" * 50)
    
    # Check if Docker is available
    try:
        import subprocess
        result = subprocess.run(["docker", "--version"], capture_output=True)
        if result.returncode != 0:
            print("❌ Docker not available - cannot test containerized FFmpeg")
            return
        print(f"✅ Docker available: {result.stdout.decode().strip()}")
    except Exception as e:
        print(f"❌ Docker check failed: {e}")
        return
    
    # Build container if needed
    if not await test_containerized_availability():
        if not build_ffmpeg_container():
            print("❌ Failed to build FFmpeg container")
            return
    
    # Run tests
    success = await test_basic_ffmpeg_operation()
    await test_trace_logging()
    
    if success:
        print("\n🎉 All tests passed! Containerized FFmpeg is working")
    else:
        print("\n❌ Some tests failed")

if __name__ == "__main__":
    asyncio.run(main())