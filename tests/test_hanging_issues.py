#!/usr/bin/env python3
"""
Test script to isolate and identify hanging issues in video processing tasks
"""
import asyncio
import signal
import time
import subprocess
from pathlib import Path
import logging
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeoutManager:
    def __init__(self, timeout_seconds=30):
        self.timeout_seconds = timeout_seconds
        self.timed_out = False
    
    def timeout_handler(self, signum, frame):
        self.timed_out = True
        logger.error(f"⏰ TIMEOUT: Operation exceeded {self.timeout_seconds} seconds")
        raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")
    
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(self.timeout_seconds)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)

async def test_opencv_import():
    """Test if OpenCV import hangs"""
    logger.info("🧪 Testing OpenCV import...")
    try:
        with TimeoutManager(10):
            import cv2
            logger.info("✅ OpenCV imported successfully")
            return True
    except TimeoutError:
        logger.error("❌ OpenCV import timed out")
        return False
    except ImportError as e:
        logger.error(f"❌ OpenCV import failed: {e}")
        return False

async def test_video_file_access():
    """Test basic video file access"""
    logger.info("🧪 Testing video file access...")
    try:
        with TimeoutManager(10):
            test_files = [
                "Oa8iS1W3OCM.mp4",
                "3xEMCU1fyl8.mp4", 
                "PLnPZVqiyjA.mp4"
            ]
            
            for file_name in test_files:
                file_path = Path(file_name)
                if file_path.exists():
                    size = file_path.stat().st_size
                    logger.info(f"  📁 {file_name}: {size:,} bytes")
                else:
                    logger.warning(f"  ⚠️ {file_name}: Not found")
            
            logger.info("✅ Video file access completed")
            return True
    except TimeoutError:
        logger.error("❌ Video file access timed out")
        return False

async def test_ffprobe_command():
    """Test FFprobe subprocess calls"""
    logger.info("🧪 Testing FFprobe subprocess...")
    try:
        with TimeoutManager(15):
            test_file = "Oa8iS1W3OCM.mp4"
            if not Path(test_file).exists():
                logger.warning(f"⚠️ Test file {test_file} not found, skipping")
                return False
            
            # Test basic ffprobe call
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_format', test_file
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("✅ FFprobe subprocess completed successfully")
                return True
            else:
                logger.error(f"❌ FFprobe failed: {result.stderr}")
                return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ FFprobe subprocess timed out")
        return False
    except TimeoutError:
        logger.error("❌ FFprobe test timed out")
        return False

async def test_opencv_video_operations():
    """Test OpenCV video operations that previously hung"""
    logger.info("🧪 Testing OpenCV video operations...")
    try:
        with TimeoutManager(30):
            import cv2
            
            test_file = "Oa8iS1W3OCM.mp4"
            if not Path(test_file).exists():
                logger.warning(f"⚠️ Test file {test_file} not found, skipping")
                return False
            
            # Test video capture
            logger.info("  📹 Testing video capture...")
            cap = cv2.VideoCapture(str(test_file))
            
            if not cap.isOpened():
                logger.error("❌ Failed to open video file")
                return False
            
            # Read a few frames
            frame_count = 0
            for i in range(10):  # Only read 10 frames
                ret, frame = cap.read()
                if ret:
                    frame_count += 1
                else:
                    break
            
            cap.release()
            logger.info(f"  ✅ Read {frame_count} frames successfully")
            
            # Test scene detection (simplified)
            logger.info("  🎬 Testing scene detection...")
            cap = cv2.VideoCapture(str(test_file))
            ret, prev_frame = cap.read()
            
            if ret:
                prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                scene_changes = 0
                
                for i in range(100):  # Test with limited frames
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    diff = cv2.absdiff(prev_gray, gray)
                    mean_diff = diff.mean()
                    
                    if mean_diff > 30:  # Simple threshold
                        scene_changes += 1
                    
                    prev_gray = gray
                
                cap.release()
                logger.info(f"  ✅ Detected {scene_changes} potential scene changes")
            
            logger.info("✅ OpenCV video operations completed")
            return True
            
    except TimeoutError:
        logger.error("❌ OpenCV video operations timed out")
        return False
    except Exception as e:
        logger.error(f"❌ OpenCV video operations failed: {e}")
        return False

async def test_subprocess_isolation():
    """Test the subprocess isolation approach we implemented"""
    logger.info("🧪 Testing subprocess isolation...")
    try:
        with TimeoutManager(45):
            subprocess_script = Path("src/opencv_subprocess.py")
            if not subprocess_script.exists():
                logger.warning("⚠️ opencv_subprocess.py not found, skipping")
                return False
            
            test_file = "Oa8iS1W3OCM.mp4"
            if not Path(test_file).exists():
                logger.warning(f"⚠️ Test file {test_file} not found, skipping")
                return False
            
            # Test scene detection subprocess
            logger.info("  🔄 Starting scene detection subprocess...")
            process = await asyncio.create_subprocess_exec(
                'python', str(subprocess_script), 'detect_scenes', str(test_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                
                if process.returncode == 0:
                    logger.info("  ✅ Scene detection subprocess completed successfully")
                    result = stdout.decode()
                    if result.strip():
                        logger.info(f"  📊 Result length: {len(result)} characters")
                else:
                    logger.error(f"  ❌ Scene detection subprocess failed: {stderr.decode()}")
                    return False
                    
            except asyncio.TimeoutError:
                logger.error("  ❌ Scene detection subprocess timed out")
                process.kill()
                return False
            
            logger.info("✅ Subprocess isolation test completed")
            return True
            
    except TimeoutError:
        logger.error("❌ Subprocess isolation test timed out")
        return False

async def main():
    """Run all hanging issue tests"""
    logger.info("🚀 Starting hanging issues investigation...")
    
    tests = [
        ("OpenCV Import", test_opencv_import),
        ("Video File Access", test_video_file_access),
        ("FFprobe Command", test_ffprobe_command),
        ("OpenCV Video Operations", test_opencv_video_operations),
        ("Subprocess Isolation", test_subprocess_isolation)
    ]
    
    results = {}
    total_start = time.time()
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 RUNNING: {test_name}")
        logger.info(f"{'='*50}")
        
        start_time = time.time()
        try:
            result = await test_func()
            duration = time.time() - start_time
            results[test_name] = {
                'success': result,
                'duration': duration
            }
            logger.info(f"⏱️  Duration: {duration:.2f} seconds")
        except Exception as e:
            duration = time.time() - start_time
            results[test_name] = {
                'success': False,
                'duration': duration,
                'error': str(e)
            }
            logger.error(f"❌ Test {test_name} failed with exception: {e}")
    
    total_duration = time.time() - total_start
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("📊 HANGING ISSUES TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = result['duration']
        logger.info(f"{status:8} {test_name:25} ({duration:6.2f}s)")
        if result['success']:
            passed += 1
        elif 'error' in result:
            logger.info(f"         Error: {result['error']}")
    
    logger.info(f"\nResults: {passed}/{len(tests)} tests passed")
    logger.info(f"Total Duration: {total_duration:.2f} seconds")
    
    if passed == len(tests):
        logger.info("🎉 All tests passed - no hanging issues detected!")
    else:
        logger.warning("⚠️  Some tests failed - investigate specific issues")

if __name__ == "__main__":
    asyncio.run(main())