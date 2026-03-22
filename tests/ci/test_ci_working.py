#!/usr/bin/env python3
"""
Working CI Test Suite: Core MCP Server Functionality
Tests that work reliably in CI environments without complex dependencies

FOCUS: Verifies production-ready MCP server capabilities:
- Server compilation and startup
- FFMPEG command generation workflow
- Music video processing patterns
- CI environment compatibility
"""

import subprocess
import json
import time
import os
from pathlib import Path

# Test configuration
OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/ci-working/"

def ensure_output_dir():
    """Ensure output directory exists"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def test_typescript_mcp_compilation():
    """Test TypeScript MCP server compiles successfully"""
    print("🔧 Testing TypeScript MCP compilation...")
    
    try:
        result = subprocess.run([
            'npm', 'run', 'build'
        ], 
        cwd='haiku-mcp-ts',
        capture_output=True, 
        text=True, 
        timeout=60
        )
        
        if result.returncode != 0:
            raise Exception(f"TypeScript compilation failed: {result.stderr}")
        
        # Verify essential files exist
        dist_dir = Path('haiku-mcp-ts/dist')
        if not dist_dir.exists():
            raise Exception("dist directory not created")
        if not (dist_dir / 'server.js').exists():
            raise Exception("server.js not compiled")
        
        print("   ✅ TypeScript compilation: SUCCESS")
        return True
        
    except subprocess.TimeoutExpired:
        raise Exception("TypeScript compilation timeout (60s)")
    except Exception as e:
        raise Exception(f"TypeScript compilation error: {e}")

def test_typescript_mcp_server_startup():
    """Test TypeScript MCP server starts without errors"""
    print("🚀 Testing TypeScript MCP server startup...")
    
    try:
        # Test server startup (short duration to verify no immediate crashes)
        result = subprocess.run([
            'timeout', '3', 'npm', 'start'  # 3 second startup test
        ], 
        cwd='haiku-mcp-ts',
        capture_output=True, 
        text=True
        )
        
        # Timeout exit code (124) is expected - server should run until killed
        if result.returncode not in [0, 124]:
            raise Exception(f"Server startup failed: {result.stderr}")
        
        # Check for successful initialization
        output = result.stderr + result.stdout
        if "Haiku MCP Server initialized" not in output:
            raise Exception(f"Server initialization failed: {output}")
        
        print("   ✅ TypeScript MCP server startup: SUCCESS")
        return True
        
    except Exception as e:
        raise Exception(f"TypeScript server startup error: {e}")

def test_ffmpeg_availability_and_basic_commands():
    """Test FFMPEG is available and can execute music video patterns"""
    print("🎬 Testing FFMPEG availability and music video patterns...")
    ensure_output_dir()
    
    # Test FFMPEG version
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise Exception("FFMPEG not available")
        
        version_output = result.stdout
        if 'ffmpeg version' not in version_output.lower():
            raise Exception("Invalid FFMPEG version output")
        
        print("   ✅ FFMPEG availability: SUCCESS")
        
    except subprocess.TimeoutExpired:
        raise Exception("FFMPEG version check timeout")
    except FileNotFoundError:
        raise Exception("FFMPEG not installed")
    except Exception as e:
        raise Exception(f"FFMPEG availability error: {e}")
    
    # Test music video workflow patterns
    test_patterns = [
        # Video processing with audio drop (music video pattern)
        {
            'name': 'Video with audio drop',
            'cmd': ['ffmpeg', '-f', 'lavfi', '-i', 'testsrc2=duration=2:size=320x240:rate=30', 
                    '-an', '-t', '2', '-y', f'{OUTPUT_DIR}/test_video_no_audio.mp4'],
            'expected_size': 1000  # Minimum expected file size
        },
        
        # Audio processing for music video
        {
            'name': 'Audio processing', 
            'cmd': ['ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=2', 
                    '-c:a', 'mp3', '-t', '2', '-y', f'{OUTPUT_DIR}/test_audio.mp3'],
            'expected_size': 1000
        },
        
        # Combined audio-video (final music video)
        {
            'name': 'Music video assembly',
            'cmd': ['ffmpeg', '-f', 'lavfi', '-i', 'testsrc2=duration=2:size=320x240:rate=30',
                    '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=2',
                    '-c:v', 'libx264', '-c:a', 'aac', '-t', '2', '-pix_fmt', 'yuv420p',
                    '-y', f'{OUTPUT_DIR}/test_music_video.mp4'],
            'expected_size': 2000
        }
    ]
    
    for pattern in test_patterns:
        try:
            result = subprocess.run(pattern['cmd'], capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                raise Exception(f"{pattern['name']} failed: {result.stderr}")
            
            # Verify output file was created
            output_file = Path(pattern['cmd'][-1])
            if not output_file.exists():
                raise Exception(f"{pattern['name']} output not created")
            
            file_size = output_file.stat().st_size
            if file_size < pattern['expected_size']:
                raise Exception(f"{pattern['name']} output too small: {file_size} bytes")
            
            print(f"   ✅ {pattern['name']}: {file_size:,} bytes")
            
        except subprocess.TimeoutExpired:
            raise Exception(f"{pattern['name']} timeout")
        except Exception as e:
            raise Exception(f"{pattern['name']} error: {e}")
    
    return True

def test_mcp_tool_structure():
    """Test MCP tool structure can be validated"""
    print("🔍 Testing MCP tool structure...")
    
    try:
        # Test Python MCP server structure via module inspection
        result = subprocess.run([
            'python3', '-c', '''
import sys
import os
sys.path.insert(0, "src")

# Test basic imports work
try:
    import models
    import config
    print("✅ Core modules importable")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test configuration loading
try:
    from config import load_config
    cfg = load_config()
    print(f"✅ Configuration loaded: {cfg.temp_dir}")
except Exception as e:
    print(f"⚠️ Config loading issue: {e}")

# Test model structures
try:
    from models import VideoProcessingRequest, VideoProcessingResult
    print("✅ Model structures available")
except Exception as e:
    print(f"❌ Model structure error: {e}")
    exit(1)

print("✅ MCP structure validation complete")
'''
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            raise Exception(f"MCP structure validation failed: {result.stderr}")
        
        output = result.stdout
        if "MCP structure validation complete" not in output:
            raise Exception(f"Incomplete validation: {output}")
        
        print("   ✅ MCP tool structure: SUCCESS")
        return True
        
    except subprocess.TimeoutExpired:
        raise Exception("MCP structure validation timeout")
    except Exception as e:
        raise Exception(f"MCP structure validation error: {e}")

def test_haiku_ai_basic_integration():
    """Test Haiku AI integration basics"""
    print("🧠 Testing Haiku AI basic integration...")
    
    try:
        # Test Haiku subagent can be imported and initialized
        result = subprocess.run([
            'python3', '-c', '''
import sys
sys.path.insert(0, "src")

try:
    from haiku_subagent import HaikuSubagent
    print("✅ Haiku subagent importable")
    
    # Test basic initialization
    haiku = HaikuSubagent(fallback_enabled=True)
    print("✅ Haiku subagent initializable")
    
    # Test creative transitions (heuristic function)
    transitions = haiku.get_creative_transitions()
    print(f"✅ Creative transitions: {len(transitions)} available")
    
    if len(transitions) == 0:
        print("❌ No transitions available")
        exit(1)
    
    print("✅ Haiku AI basic integration complete")
    
except Exception as e:
    print(f"❌ Haiku integration error: {e}")
    exit(1)
'''
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            raise Exception(f"Haiku AI integration failed: {result.stderr}")
        
        output = result.stdout
        if "Haiku AI basic integration complete" not in output:
            raise Exception(f"Incomplete integration: {output}")
        
        print("   ✅ Haiku AI integration: SUCCESS")
        return True
        
    except subprocess.TimeoutExpired:
        raise Exception("Haiku AI integration timeout")
    except Exception as e:
        raise Exception(f"Haiku AI integration error: {e}")

def test_ci_environment_requirements():
    """Test CI environment has required tools"""
    print("⚙️ Testing CI environment requirements...")
    
    requirements = {
        'node': ['node', '--version'],
        'npm': ['npm', '--version'],
        'ffmpeg': ['ffmpeg', '-version'],
        'python3': ['python3', '--version']
    }
    
    missing_requirements = []
    versions = {}
    
    for tool, cmd in requirements.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Extract version for reporting
                version_line = result.stdout.split('\n')[0] if result.stdout else result.stderr.split('\n')[0]
                versions[tool] = version_line.strip()
                print(f"   ✅ {tool}: {version_line.strip()}")
            else:
                missing_requirements.append(tool)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing_requirements.append(tool)
    
    if missing_requirements:
        raise Exception(f"Missing CI requirements: {missing_requirements}")
    
    return True

def run_ci_tests():
    """Run all CI tests and report results"""
    ensure_output_dir()
    
    print("🧪 Running CI Test Suite for MCP Server\n")
    print("="*60)
    
    test_functions = [
        ("CI Environment Requirements", test_ci_environment_requirements),
        ("FFMPEG & Music Video Patterns", test_ffmpeg_availability_and_basic_commands),
        ("MCP Tool Structure", test_mcp_tool_structure),
        ("Haiku AI Integration", test_haiku_ai_basic_integration),
        ("TypeScript Compilation", test_typescript_mcp_compilation),
        ("TypeScript Server Startup", test_typescript_mcp_server_startup),
    ]
    
    results = []
    
    for test_name, test_func in test_functions:
        print(f"\n📋 {test_name}")
        print("-" * len(f"📋 {test_name}"))
        
        try:
            start_time = time.time()
            test_func()
            duration = time.time() - start_time
            results.append((test_name, True, f"{duration:.2f}s", ""))
            print(f"   ⏱️ Duration: {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            results.append((test_name, False, f"{duration:.2f}s", str(e)))
            print(f"   ❌ FAILED: {e}")
            print(f"   ⏱️ Duration: {duration:.2f}s")
    
    # Summary
    print("\n" + "="*60)
    print("📊 CI TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success, _, _ in results if success)
    total = len(results)
    
    for test_name, success, duration, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name:<35} ({duration})")
        if error:
            print(f"     Error: {error}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎯 ALL TESTS PASSED - MCP Server CI Ready!")
        
        # Save success report
        report = {
            "timestamp": time.time(),
            "status": "SUCCESS",
            "tests_passed": passed,
            "tests_total": total,
            "details": [
                {
                    "test": name,
                    "success": success,
                    "duration": duration,
                    "error": error if error else None
                }
                for name, success, duration, error in results
            ]
        }
        
        report_file = Path(OUTPUT_DIR) / "ci_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved: {report_file}")
        return True
        
    else:
        print("⚠️ Some tests failed - review before CI deployment")
        return False

if __name__ == "__main__":
    success = run_ci_tests()
    exit(0 if success else 1)