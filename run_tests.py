#!/usr/bin/env python3
"""
Test Runner for FFMPEG MCP Server

Quick verification that the system is functional.
"""

import subprocess
import sys
from pathlib import Path

def run_test(test_name: str, test_command: list) -> bool:
    """Run a test and return success status"""
    print(f"\n🧪 Running {test_name}...")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            test_command,
            capture_output=False,  # Show real-time output
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"✅ {test_name} PASSED")
            return True
        else:
            print(f"❌ {test_name} FAILED (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {test_name} ERROR: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🎬 FFMPEG MCP Server Test Suite")
    print("=" * 50)
    
    tests = [
        ("Unit Tests", ["uv", "run", "pytest", "tests/test_ffmpeg_integration.py", "-v"]),
        ("End-to-End Music Video Test", ["uv", "run", "python", "tests/test_end_to_end_music_video.py"]),
        ("Intelligent Content Analysis Test", ["uv", "run", "python", "tests/test_intelligent_content_analysis.py"])
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_command in tests:
        if run_test(test_name, test_command):
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - MCP Server is fully functional!")
        return 0
    else:
        print("🔧 Some tests failed - check output above for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())