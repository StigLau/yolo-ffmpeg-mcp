#!/usr/bin/env python3
"""
Test TypeScript Haiku MCP Server Performance vs Python FFMPEG MCP
Validates Haiku AI integration and video processing capabilities
"""

import asyncio
import json
import time
import subprocess
from pathlib import Path
import tempfile
import os

TEST_VIDEO = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4"
TEST_AUDIO = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/16BL - Deep In My Soul (Original Mix).mp3"
OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/test-performance/"

def ensure_output_dir():
    """Ensure output directory exists"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def test_typescript_haiku_mcp():
    """Test TypeScript Haiku MCP server functionality"""
    print("🔄 Testing TypeScript Haiku MCP Server...")
    
    start_time = time.time()
    
    try:
        # Test video processing
        result = subprocess.run([
            'node', 'client.js'
        ], 
        cwd='haiku-mcp-ts',
        capture_output=True, 
        text=True, 
        timeout=60
        )
        
        processing_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ TypeScript MCP: SUCCESS ({processing_time:.2f}s)")
            
            # Extract response details
            output = result.stdout
            if "Video Processing Response:" in output:
                response_start = output.find('{"content":')
                if response_start != -1:
                    try:
                        response_data = output[response_start:]
                        # Find the end of the JSON
                        json_end = response_data.find('}\n✅ Disconnected')
                        if json_end != -1:
                            json_data = json.loads(response_data[:json_end + 1])
                            
                            # Extract processing details
                            content = json.loads(json_data['content'][0]['text'])
                            return {
                                'success': True,
                                'processing_time': processing_time,
                                'llm_tokens': content.get('llm_tokens_used', 0),
                                'llm_cost': content.get('llm_cost', 0),
                                'execution_time': content.get('execution_time_ms', 0),
                                'command_used': content.get('command_used', 'unknown'),
                                'output': output
                            }
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON parsing error: {e}")
                        
            return {
                'success': True,
                'processing_time': processing_time,
                'output': output
            }
        else:
            print(f"❌ TypeScript MCP: FAILED ({processing_time:.2f}s)")
            print(f"Error: {result.stderr}")
            return {
                'success': False,
                'processing_time': processing_time,
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        print(f"❌ TypeScript MCP: TIMEOUT (60s)")
        return {
            'success': False,
            'processing_time': 60,
            'error': 'TIMEOUT'
        }
    except Exception as e:
        print(f"❌ TypeScript MCP: EXCEPTION ({str(e)})")
        return {
            'success': False,
            'processing_time': time.time() - start_time,
            'error': str(e)
        }

def test_python_haiku_integration():
    """Test Python Haiku integration via FastTrack"""
    print("\n🧠 Testing Python Haiku AI Integration...")
    
    start_time = time.time()
    
    try:
        # Test FastTrack analysis
        result = subprocess.run([
            './tools/ft', 'analyze', TEST_VIDEO
        ], 
        capture_output=True, 
        text=True, 
        timeout=30
        )
        
        processing_time = time.time() - start_time
        
        if result.returncode == 0:
            try:
                analysis_result = json.loads(result.stdout)
                print(f"✅ Python Haiku: SUCCESS ({processing_time:.2f}s)")
                print(f"   Status: {analysis_result.get('status', 'UNKNOWN')}")
                print(f"   Confidence: {analysis_result.get('confidence', 'N/A')}")
                
                return {
                    'success': True,
                    'processing_time': processing_time,
                    'analysis': analysis_result
                }
            except json.JSONDecodeError:
                print(f"⚠️ Haiku output not JSON: {result.stdout}")
                return {
                    'success': False,
                    'processing_time': processing_time,
                    'error': 'Invalid JSON response'
                }
        else:
            print(f"❌ Python Haiku: FAILED ({processing_time:.2f}s)")
            print(f"Error: {result.stderr}")
            return {
                'success': False,
                'processing_time': processing_time,
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        print(f"❌ Python Haiku: TIMEOUT (30s)")
        return {
            'success': False,
            'processing_time': 30,
            'error': 'TIMEOUT'
        }
    except Exception as e:
        print(f"❌ Python Haiku: EXCEPTION ({str(e)})")
        return {
            'success': False,
            'processing_time': time.time() - start_time,
            'error': str(e)
        }

def test_music_video_creation():
    """Test music video creation workflow"""
    print("\n🎬 Testing Music Video Creation Workflow...")
    
    # Check if files exist
    if not Path(TEST_VIDEO).exists():
        print(f"❌ Test video not found: {TEST_VIDEO}")
        return {'success': False, 'error': 'Test video not found'}
        
    if not Path(TEST_AUDIO).exists():
        print(f"❌ Test audio not found: {TEST_AUDIO}")
        return {'success': False, 'error': 'Test audio not found'}
    
    start_time = time.time()
    
    # Test basic video trimming (simulates music video preparation)
    output_file = Path(OUTPUT_DIR) / 'music_video_test.mp4'
    
    try:
        result = subprocess.run([
            'ffmpeg', '-y',
            '-i', TEST_VIDEO,
            '-t', '10',  # 10 second clip
            '-c:v', 'libx264', '-preset', 'medium',
            '-an',  # Drop audio (music video workflow)
            str(output_file)
        ], 
        capture_output=True, 
        text=True, 
        timeout=30
        )
        
        processing_time = time.time() - start_time
        
        if result.returncode == 0 and output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✅ Music Video Prep: SUCCESS ({processing_time:.2f}s)")
            print(f"   Output: {file_size:,} bytes")
            
            return {
                'success': True,
                'processing_time': processing_time,
                'output_file': str(output_file),
                'file_size': file_size
            }
        else:
            print(f"❌ Music Video Prep: FAILED ({processing_time:.2f}s)")
            print(f"FFmpeg Error: {result.stderr}")
            return {
                'success': False,
                'processing_time': processing_time,
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        print(f"❌ Music Video Prep: TIMEOUT (30s)")
        return {
            'success': False,
            'processing_time': 30,
            'error': 'TIMEOUT'
        }
    except Exception as e:
        print(f"❌ Music Video Prep: EXCEPTION ({str(e)})")
        return {
            'success': False,
            'processing_time': time.time() - start_time,
            'error': str(e)
        }

def main():
    """Run comprehensive Haiku MCP performance tests"""
    print("🧪 Haiku FFMPEG MCP Performance Test\n")
    
    ensure_output_dir()
    
    results = {
        'timestamp': time.time(),
        'test_environment': {
            'test_video': TEST_VIDEO,
            'test_audio': TEST_AUDIO,
            'output_dir': OUTPUT_DIR
        }
    }
    
    # Test 1: TypeScript Haiku MCP Server
    results['typescript_mcp'] = test_typescript_haiku_mcp()
    
    # Test 2: Python Haiku AI Integration 
    results['python_haiku'] = test_python_haiku_integration()
    
    # Test 3: Music Video Creation Workflow
    results['music_video_workflow'] = test_music_video_creation()
    
    # Summary
    print("\n📊 PERFORMANCE SUMMARY:")
    print("=" * 50)
    
    ts_success = results['typescript_mcp']['success']
    py_success = results['python_haiku']['success']
    mv_success = results['music_video_workflow']['success']
    
    print(f"TypeScript Haiku MCP:     {'✅' if ts_success else '❌'}")
    if ts_success:
        ts_time = results['typescript_mcp']['processing_time']
        ts_tokens = results['typescript_mcp'].get('llm_tokens', 'N/A')
        ts_cost = results['typescript_mcp'].get('llm_cost', 'N/A')
        print(f"  Processing Time:        {ts_time:.2f}s")
        print(f"  LLM Tokens Used:        {ts_tokens}")
        print(f"  LLM Cost:               ${ts_cost}")
    
    print(f"Python Haiku AI:          {'✅' if py_success else '❌'}")
    if py_success:
        py_time = results['python_haiku']['processing_time']
        py_status = results['python_haiku'].get('analysis', {}).get('status', 'N/A')
        print(f"  Processing Time:        {py_time:.2f}s")
        print(f"  Analysis Status:        {py_status}")
    
    print(f"Music Video Workflow:     {'✅' if mv_success else '❌'}")
    if mv_success:
        mv_time = results['music_video_workflow']['processing_time']
        mv_size = results['music_video_workflow'].get('file_size', 0)
        print(f"  Processing Time:        {mv_time:.2f}s")
        print(f"  Output File Size:       {mv_size:,} bytes")
    
    # Overall assessment
    success_count = sum([ts_success, py_success, mv_success])
    print(f"\nOverall Success Rate:     {success_count}/3 ({success_count/3*100:.1f}%)")
    
    # Save detailed results
    results_file = Path(OUTPUT_DIR) / 'haiku_mcp_performance_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Detailed results saved: {results_file}")
    
    return results

if __name__ == "__main__":
    main()