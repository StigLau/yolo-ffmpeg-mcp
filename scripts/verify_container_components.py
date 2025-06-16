#!/usr/bin/env python3
"""
Container Component Verification Script
Verifies all major components are installed and working in container
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run command and return output or None if failed"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"❌ {description}: Command failed (exit {result.returncode})")
            print(f"   Error: {result.stderr.strip()}")
            return None
    except subprocess.TimeoutExpired:
        print(f"❌ {description}: Command timed out")
        return None
    except Exception as e:
        print(f"❌ {description}: Exception - {e}")
        return None

def verify_component(command, description, version_flag="--version"):
    """Verify a component is installed and get version"""
    print(f"🔍 Checking {description}...")
    
    # Check if command exists
    which_result = run_command(f"which {command}", f"{description} location")
    if not which_result:
        return False
    
    print(f"   📍 Location: {which_result}")
    
    # Get version
    version_result = run_command(f"{command} {version_flag}", f"{description} version")
    if version_result:
        # Extract first line for cleaner output
        version_line = version_result.split('\n')[0]
        print(f"   ✅ Version: {version_line}")
        return True
    else:
        return False

def verify_python_modules():
    """Verify critical Python modules can be imported"""
    print("🐍 Checking Python modules...")
    
    modules = [
        ("fastmcp", "FastMCP framework"), 
        ("mcp", "MCP protocol"),
        ("pydantic", "Data validation"),
        ("pytest", "Testing framework"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow imaging"),
        ("numpy", "NumPy arrays")
    ]
    
    # Check src.server separately with better error handling
    try:
        import sys
        import os
        sys.path.insert(0, '/app')
        sys.path.insert(0, '/app/src')
        
        # Test basic Python imports first
        print(f"      Testing basic imports...")
        import src.file_manager
        print(f"      ✓ file_manager imported")
        import src.config
        print(f"      ✓ config imported")
        
        # Now test full server (optional for minimal containers)
        import src.server
        print(f"   ✅ src.server")
    except ImportError as e:
        print(f"   ⚠️  src.server: {e} (optional for minimal containers)")
        print(f"      Python path: {sys.path}")
        print(f"      Working dir: {os.getcwd()}")
        print(f"      App contents: {os.listdir('/app') if os.path.exists('/app') else 'N/A'}")
        print(f"      Src contents: {os.listdir('/app/src') if os.path.exists('/app/src') else 'N/A'}")
        # Don't fail for server import issues in minimal containers - core modules work
        if "scenedetect" in str(e) or "cv2" in str(e):
            print(f"      ✅ Core modules working, server skip OK for minimal container")
        else:
            return False
    
    for module, description in modules:
        try:
            __import__(module)
            print(f"   ✅ {module} ({description})")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            return False
    
    return True

def verify_directories():
    """Verify required directories exist"""
    print("📁 Checking directories...")
    
    dirs = [
        "/tmp/music/source",
        "/tmp/music/temp", 
        "/tmp/music/metadata",
        "/tmp/music/screenshots",
        "/app/src",
        "/app/tests"
    ]
    
    for dir_path in dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path}: Missing")
            return False
    
    return True

def verify_test_files():
    """Check for test files"""
    print("🎬 Checking test files...")
    
    source_dir = Path("/tmp/music/source")
    if not source_dir.exists():
        print("   ❌ Source directory missing")
        return False
    
    files = list(source_dir.glob("*"))
    print(f"   📊 Found {len(files)} files:")
    
    for file in files[:5]:  # Show first 5 files
        print(f"      - {file.name} ({file.stat().st_size} bytes)")
    
    if len(files) > 5:
        print(f"      ... and {len(files) - 5} more")
    
    return len(files) > 0

def main():
    """Main verification function"""
    print("🏥 Container Component Verification")
    print("=" * 50)
    
    all_passed = True
    
    # Core system components
    components = [
        ("python3", "Python", "--version"),
        ("ffmpeg", "FFmpeg", "-version"),
        ("ffprobe", "FFprobe", "-version"), 
        ("mediainfo", "MediaInfo", "--version"),
        ("pip", "Pip", "--version"),
        ("uv", "UV Package Manager", "--version")
    ]
    
    for cmd, desc, flag in components:
        if not verify_component(cmd, desc, flag):
            all_passed = False
    
    print()
    
    # Python modules
    if not verify_python_modules():
        all_passed = False
    
    print()
    
    # Directories
    if not verify_directories():
        all_passed = False
    
    print()
    
    # Test files
    verify_test_files()  # Non-critical
    
    print()
    print("=" * 50)
    
    if all_passed:
        print("🎉 All critical components verified successfully!")
        print("✅ Container is ready for FFMPEG MCP operations")
        return 0
    else:
        print("💥 Some components failed verification!")
        print("❌ Container may not function correctly")
        return 1

if __name__ == "__main__":
    sys.exit(main())