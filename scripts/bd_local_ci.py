#!/usr/bin/env python3
"""
Build Detective Local CI Verification
Minimal implementation to validate changes before pushing
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description, cwd=None):
    """Run command and return success status"""
    print(f"🔍 BD: {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def bd_local_ci_verify(include_docker=False):
    """Run minimal local CI verification"""
    project_root = Path(__file__).parent.parent
    
    print("🔧 Build Detective: Local CI Verification")
    print("=" * 50)
    
    # Fast tests (always run)
    tests = [
        # Test 1: UV sync and pytest availability
        ("uv sync && uv run python -c 'import pytest; print(\"pytest OK\")'", 
         "UV dependencies and pytest"),
         
        # Test 2: Core music video workflow CI test (fast)
        ("uv run python -m pytest tests/ci/test_music_video_workflow_ci.py -v --tb=short", 
         "Music video workflow CI"),
    ]
    
    # Docker tests (optional, slower) - Enhanced with CI-specific validation
    if include_docker:
        tests.extend([
            ("docker build -t ffmpeg-mcp:local-test . --quiet", 
             "Main Docker build"),
             
            ("docker build -f Dockerfile.ci -t ffmpeg-mcp:local-ci-test . --quiet", 
             "CI Docker build"),
             
            # NEW: Test the CI Docker container actually runs the tests
            ("docker run --rm ffmpeg-mcp:local-ci-test", 
             "CI Docker test execution"),
        ])
    
    passed = 0
    total = len(tests)
    
    for cmd, description in tests:
        if run_command(cmd, description, cwd=project_root):
            passed += 1
        else:
            print(f"\n💥 BD: Stopping at first failure to prevent unnecessary processing")
            break
    
    print(f"\n📊 BD Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ BD: All local CI checks PASSED - safe to push!")
        return True
    else:
        print("❌ BD: Local CI checks FAILED - fix before pushing!")
        return False

if __name__ == "__main__":
    include_docker = "--docker" in sys.argv
    if include_docker:
        print("🐳 Including Docker build tests (slower)")
    else:
        print("⚡ Fast mode (use --docker to include Docker builds)")
    
    success = bd_local_ci_verify(include_docker)
    sys.exit(0 if success else 1)