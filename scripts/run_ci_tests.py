#!/usr/bin/env python3
"""
CI/CD Test Runner

Orchestrates all CI/CD tests and provides proper exit codes.
"""

import sys
import subprocess
from pathlib import Path

def run_test(test_name: str, test_command: list) -> bool:
    """Run a single test and return success status"""
    print(f"\n🧪 Running {test_name}")
    print(f"   File: {' '.join(test_command)}")
    
    try:
        result = subprocess.run(
            test_command,
            cwd=Path(__file__).parent.parent,  # Run from project root
            capture_output=False,  # Let output show directly
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {test_name} PASSED")
            return True
        else:
            print(f"❌ {test_name} FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ {test_name} TIMED OUT")
        return False
    except Exception as e:
        print(f"❌ {test_name} ERROR: {e}")
        return False

def main():
    """Main CI/CD test runner"""
    print("🚀 FFMPEG MCP Server CI/CD Test Suite")
    print("=" * 37)
    
    # Environment validation
    print("\n📋 Environment Validation")
    try:
        # Check Python version
        python_version = subprocess.run([sys.executable, "--version"], 
                                      capture_output=True, text=True)
        print(f"Python version: {python_version.stdout.strip()}")
        
        # Check FFMPEG
        ffmpeg_version = subprocess.run(["ffmpeg", "-version"], 
                                      capture_output=True, text=True)
        if ffmpeg_version.returncode == 0:
            first_line = ffmpeg_version.stdout.split('\n')[0]
            print(f"FFMPEG version: {first_line}")
        else:
            print("❌ FFMPEG not found")
            # Debug: Check what's in PATH
            try:
                which_result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
                print(f"which ffmpeg: {which_result.stdout.strip() if which_result.stdout else 'not found'}")
                if which_result.stderr:
                    print(f"which ffmpeg error: {which_result.stderr.strip()}")
            except Exception as e:
                print(f"which ffmpeg failed: {e}")
            return 1
            
        # Check test data
        test_data_dir = Path("/app/test-data")
        if test_data_dir.exists():
            file_count = len(list(test_data_dir.iterdir()))
            print(f"Test data directory: {file_count} files")
            
            # Show available test files
            print("Test files available:")
            subprocess.run(["ls", "-la", str(test_data_dir)])
        else:
            print("⚠️  Test data directory not found")
            
    except Exception as e:
        print(f"❌ Environment validation error: {e}")
        return 1
    
    # Define tests to run
    tests = [
        ("test_unit_core", ["python", "-m", "pytest", "tests/ci/test_unit_core.py", "-v"]),
        # Add more tests here as needed
    ]
    
    # Run all tests
    all_passed = True
    results = {}
    
    for test_name, test_command in tests:
        success = run_test(test_name, test_command)
        results[test_name] = success
        if not success:
            all_passed = False
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 25)
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        emoji = "✅" if passed else "❌"
        print(f"{emoji} {test_name}: {status}")
    
    if all_passed:
        print(f"\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
