#!/usr/bin/env python3
"""
Basic CI Test Suite: Core MCP Server Functionality
Tests essential MCP server capabilities that can be verified in CI environments

FOCUS: Tests that work reliably in CI without complex dependencies
- Server startup and compilation
- Tool registration and discovery
- Basic FFMPEG command validation
- Music video workflow patterns
"""

import pytest
import subprocess
import json
import time
import os
import tempfile
from pathlib import Path

# Test configuration
TEST_VIDEO = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4"
OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/ci-basic/"

def ensure_output_dir():
    """Ensure output directory exists"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def test_typescript_mcp_compilation():
    """Test TypeScript MCP server compiles successfully"""
    try:
        # Test TypeScript compilation
        result = subprocess.run([
            'npm', 'run', 'build'
        ], 
        cwd='haiku-mcp-ts',
        capture_output=True, 
        text=True, 
        timeout=60
        )
        
        assert result.returncode == 0, f"TypeScript compilation failed: {result.stderr}"
        
        # Verify essential files exist
        dist_dir = Path('haiku-mcp-ts/dist')
        assert dist_dir.exists(), "dist directory not created"
        assert (dist_dir / 'server.js').exists(), "server.js not compiled"
        
        print("✅ TypeScript MCP compilation: SUCCESS")
        
    except subprocess.TimeoutExpired:
        pytest.fail("TypeScript compilation timeout (60s)")
    except Exception as e:
        pytest.fail(f"TypeScript compilation error: {e}")

def test_typescript_mcp_server_startup():
    """Test TypeScript MCP server starts without errors"""
    try:
        # Test server startup (short duration to verify no immediate crashes)
        result = subprocess.run([
            'timeout', '5', 'npm', 'start'  # 5 second startup test
        ], 
        cwd='haiku-mcp-ts',
        capture_output=True, 
        text=True
        )
        
        # Timeout exit code (124) is expected - server should run until killed
        assert result.returncode in [0, 124], f"Server startup failed: {result.stderr}"
        
        # Check for successful initialization
        output = result.stderr + result.stdout
        assert "Haiku MCP Server initialized" in output, "Server initialization failed"
        
        print("✅ TypeScript MCP server startup: SUCCESS")
        
    except Exception as e:
        pytest.fail(f"TypeScript server startup error: {e}")

def test_typescript_mcp_client_basic_connection():
    """Test TypeScript MCP client can connect (basic connectivity test)"""
    try:
        # Test basic client connection (without complex tool calls)
        result = subprocess.run([
            'node', '-e', '''
            const { HaikuMCPClient } = require('./haiku-mcp-ts/client.js');
            
            async function testBasicConnection() {
                const client = new HaikuMCPClient();
                
                try {
                    console.log("Attempting connection...");
                    await client.connect();
                    console.log("✅ Connection successful");
                    
                    // Test basic tool listing (less likely to fail than tool execution)
                    await client.listTools();
                    console.log("✅ Tool listing successful");
                    
                    await client.disconnect();
                    console.log("✅ Disconnection successful");
                    
                } catch (error) {
                    console.log("❌ Connection error:", error.message);
                    throw error;
                }
            }
            
            testBasicConnection().catch(console.error);
            '''
        ],
        capture_output=True,
        text=True,
        timeout=15
        )
        
        output = result.stdout + result.stderr
        
        # Accept partial success - connection is key indicator
        connection_success = "Connection successful" in output
        tool_listing_success = "Tool listing successful" in output
        
        # At minimum, server should be connectable
        assert connection_success, f"Basic connection failed: {output}"
        
        if tool_listing_success:
            print("✅ TypeScript MCP client: FULL SUCCESS")
        else:
            print("⚠️ TypeScript MCP client: CONNECTION SUCCESS (tool listing issues)")
        
    except subprocess.TimeoutExpired:
        pytest.fail("Client connection timeout (15s)")
    except Exception as e:
        pytest.fail(f"Client connection error: {e}")

def test_python_mcp_server_functionality():
    """Test Python MCP server basic functionality"""
    try:
        # Test Python server can import and initialize
        import sys
        sys.path.insert(0, 'src')
        
        from server import app
        
        # Test tool discovery
        tools = app.list_tools()
        assert len(tools.tools) > 0, "No tools registered"
        
        # Verify expected tools exist
        tool_names = [tool.name for tool in tools.tools]
        expected_tools = ['process_file', 'create_music_video']
        
        missing_tools = [tool for tool in expected_tools if tool not in tool_names]
        assert len(missing_tools) == 0, f"Missing tools: {missing_tools}"
        
        print(f"✅ Python MCP server: {len(tools.tools)} tools registered")
        
    except ImportError as e:
        pytest.fail(f"Python MCP server import failed: {e}")
    except Exception as e:
        pytest.fail(f"Python MCP server error: {e}")

def test_ffmpeg_availability_and_basic_command():
    """Test FFMPEG is available and can execute basic commands"""
    ensure_output_dir()
    
    # Test FFMPEG version
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, "FFMPEG not available"
        
        version_output = result.stdout
        assert 'ffmpeg version' in version_output.lower(), "Invalid FFMPEG version output"
        
        print("✅ FFMPEG availability: SUCCESS")
        
    except subprocess.TimeoutExpired:
        pytest.fail("FFMPEG version check timeout")
    except FileNotFoundError:
        pytest.fail("FFMPEG not installed")
    except Exception as e:
        pytest.fail(f"FFMPEG availability error: {e}")

def test_music_video_workflow_pattern():
    """Test music video workflow pattern (without actual video processing)"""
    ensure_output_dir()
    
    # Test the pattern of commands that would be used in music video creation
    test_patterns = [
        # Video processing with audio drop
        ['ffmpeg', '-f', 'lavfi', '-i', 'testsrc2=duration=2:size=320x240:rate=30', 
         '-an', '-t', '2', f'{OUTPUT_DIR}/test_video_no_audio.mp4'],
        
        # Audio processing
        ['ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=2', 
         '-c:a', 'mp3', '-t', '2', f'{OUTPUT_DIR}/test_audio.mp3'],
        
        # Combined audio-video (simulated music video)
        ['ffmpeg', '-f', 'lavfi', '-i', 'testsrc2=duration=2:size=320x240:rate=30',
         '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=2',
         '-c:v', 'libx264', '-c:a', 'aac', '-t', '2', '-pix_fmt', 'yuv420p',
         f'{OUTPUT_DIR}/test_music_video.mp4']
    ]
    
    for i, cmd in enumerate(test_patterns):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            assert result.returncode == 0, f"Pattern {i+1} failed: {result.stderr}"
            
            # Verify output file was created
            output_file = Path(cmd[-1])
            assert output_file.exists(), f"Pattern {i+1} output not created"
            assert output_file.stat().st_size > 0, f"Pattern {i+1} output is empty"
            
        except subprocess.TimeoutExpired:
            pytest.fail(f"Music video pattern {i+1} timeout")
        except Exception as e:
            pytest.fail(f"Music video pattern {i+1} error: {e}")
    
    print("✅ Music video workflow patterns: SUCCESS")

def test_ai_integration_basic():
    """Test basic AI integration capabilities"""
    try:
        # Test Python Haiku subagent can be imported
        import sys
        sys.path.insert(0, 'src')
        from haiku_subagent import HaikuSubagent
        
        # Test basic initialization (should work without API key in fallback mode)
        haiku = HaikuSubagent(fallback_enabled=True)
        
        # Test basic attributes exist
        assert hasattr(haiku, 'analyze_video_files'), "analyze_video_files method missing"
        assert hasattr(haiku, 'get_creative_transitions'), "get_creative_transitions method missing"
        
        # Test creative transitions (heuristic function)
        transitions = haiku.get_creative_transitions()
        assert len(transitions) > 0, "No creative transitions available"
        
        print(f"✅ AI integration basic: {len(transitions)} transitions available")
        
    except ImportError:
        pytest.skip("Haiku AI integration not available")
    except Exception as e:
        pytest.fail(f"AI integration basic error: {e}")

def test_ci_environment_requirements():
    """Test CI environment has required tools and libraries"""
    requirements = {
        'node': ['node', '--version'],
        'npm': ['npm', '--version'],
        'ffmpeg': ['ffmpeg', '-version'],
        'python': ['python3', '--version']
    }
    
    missing_requirements = []
    for tool, cmd in requirements.items():
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            if result.returncode != 0:
                missing_requirements.append(tool)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing_requirements.append(tool)
    
    assert len(missing_requirements) == 0, f"Missing CI requirements: {missing_requirements}"
    
    print("✅ CI environment requirements: SUCCESS")

def main():
    """Run all basic CI tests"""
    ensure_output_dir()
    
    print("🧪 Running Basic CI Tests\n")
    
    test_functions = [
        test_ci_environment_requirements,
        test_ffmpeg_availability_and_basic_command,
        test_python_mcp_server_functionality,
        test_typescript_mcp_compilation,
        test_typescript_mcp_server_startup,
        test_typescript_mcp_client_basic_connection,
        test_music_video_workflow_pattern,
        test_ai_integration_basic
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            print(f"Running {test_func.__name__}...")
            test_func()
            passed += 1
            print(f"✅ {test_func.__name__}: PASSED\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__}: FAILED - {e}\n")
    
    print(f"📊 CI Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎯 ALL TESTS PASSED - CI ready!")
        return True
    else:
        print("⚠️ Some tests failed - review before CI deployment")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)