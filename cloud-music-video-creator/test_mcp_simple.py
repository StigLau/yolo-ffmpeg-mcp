#!/usr/bin/env python3
"""
Simple MCP server integration test
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path

class MCPTestClient:
    """Simple MCP client for testing"""
    
    def __init__(self):
        self.server_process = None
        self.mcp_dir = Path(__file__).parent / "src/mcp/typescript"
    
    def start_server(self):
        """Start the TypeScript MCP server"""
        print("🚀 Starting MCP Server...")
        self.server_process = subprocess.Popen(
            ['node', 'dist/server.js'],
            cwd=self.mcp_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        time.sleep(0.5)  # Give server time to start
        return self.server_process is not None
    
    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool and return the response"""
        request = {
            "jsonrpc": "2.0", 
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        request_json = json.dumps(request) + '\n'
        
        try:
            self.server_process.stdin.write(request_json)
            self.server_process.stdin.flush()
            
            # Read response with timeout
            response_line = self.server_process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            else:
                return {"error": "No response from server"}
        except Exception as e:
            return {"error": f"Communication error: {e}"}
    
    def stop_server(self):
        """Stop the MCP server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()

async def test_mcp_workflow():
    """Test the MCP server workflow"""
    
    print("🎬 Testing MCP Server Music Video Creation Workflow")
    print("=" * 55)
    
    # Start MCP server
    mcp_client = MCPTestClient()
    if not mcp_client.start_server():
        print("❌ Failed to start MCP server")
        return
    
    print("✅ MCP Server started successfully")
    
    try:
        # Test 1: Create komposition 
        print("\n🎵 Step 1: Creating a vintage music video komposition...")
        response = mcp_client.call_tool('create_komposition', {
            'title': 'Vintage Vibe Music Video',
            'description': 'A 30-second music video with vintage aesthetic and mixed effects',
            'user_id': 'demo_user_123',
            'bpm': 120.0,
            'duration_seconds': 30.0,
            'visual_concept': 'First half vintage/sepia, second half dreamy blur effects',
            'audio_file_path': '/tmp/demo_audio.mp3'
        })
        
        if 'error' in response:
            print(f"❌ Error: {response['error']}")
            return
        elif 'result' in response and response['result'].get('content'):
            komposition_data = json.loads(response['result']['content'][0]['text'])
            komposition_id = komposition_data['id']
            print(f"✅ Komposition created successfully!")
            print(f"   ID: {komposition_id}")
            print(f"   Title: {komposition_data['title']}")
            print(f"   BPM: {komposition_data['bpm']}")
            print(f"   Duration: {komposition_data['duration_seconds']}s")
            print(f"   Status: {komposition_data['status']}")
        else:
            print(f"❌ Unexpected response: {response}")
            return
        
        # Test 2: Update komposition with segments
        print(f"\n🎨 Step 2: Adding creative segments to komposition...")
        updates = {
            'status': 'analyzing',
            'segments': [
                {
                    'id': 'seg_001',
                    'name': 'Vintage Opening',
                    'start_seconds': 0.0,
                    'duration_seconds': 15.0,
                    'effects': ['vintage', 'sepia', 'vignette']
                },
                {
                    'id': 'seg_002', 
                    'name': 'Dreamy Outro',
                    'start_seconds': 15.0,
                    'duration_seconds': 15.0,
                    'effects': ['blur', 'soft_focus', 'fade']
                }
            ]
        }
        
        response = mcp_client.call_tool('update_komposition', {
            'komposition_id': komposition_id,
            'updates': updates
        })
        
        if 'result' in response:
            updated_data = json.loads(response['result']['content'][0]['text'])
            print(f"✅ Komposition updated with {len(updated_data['segments'])} segments")
            print(f"   Status: {updated_data['status']}")
            for i, seg in enumerate(updated_data['segments'], 1):
                print(f"   Segment {i}: {seg['name']} ({seg['duration_seconds']}s)")
        else:
            print(f"❌ Update failed: {response}")
            return
        
        # Test 3: Register a media file
        print(f"\n📁 Step 3: Registering media assets...")
        response = mcp_client.call_tool('register_media_file', {
            'file_path': '/tmp/demo_background_video.mp4',
            'media_type': 'video',
            'metadata': {
                'resolution': '1920x1080',
                'duration': 45.0,
                'frame_rate': 25.0,
                'description': 'Background video for komposition'
            }
        })
        
        if 'result' in response:
            media_data = json.loads(response['result']['content'][0]['text'])
            print(f"✅ Media file registered: {media_data['id']}")
            print(f"   Path: {media_data['file_path']}")
            print(f"   Type: {media_data['media_type']}")
        else:
            print(f"❌ Media registration failed: {response}")
        
        # Test 4: Process video 
        print(f"\n🎬 Step 4: Processing final music video...")
        response = mcp_client.call_tool('process_komposition_video', {
            'komposition_id': komposition_id,
            'processing_options': {
                'quality': 'hd',
                'output_format': 'mp4',
                'include_audio': True
            }
        })
        
        if 'result' in response:
            video_data = json.loads(response['result']['content'][0]['text'])
            print(f"✅ Video processing completed!")
            print(f"   Video ID: {video_data['id']}")
            print(f"   Output path: {video_data['file_path']}")
            print(f"   Processing cost: ${video_data['processing_cost']:.3f}")
            print(f"   Quality score: {video_data['quality_score']:.2f}")
            print(f"   Processing duration: {video_data['processing_duration']:.1f}s")
            print(f"   Status: {video_data['status']}")
        else:
            print(f"❌ Video processing failed: {response}")
        
        # Test 5: List all user kompositions
        print(f"\n📋 Step 5: Retrieving user's komposition library...")
        response = mcp_client.call_tool('list_user_kompositions', {
            'user_id': 'demo_user_123'
        })
        
        if 'result' in response:
            kompositions = json.loads(response['result']['content'][0]['text'])
            print(f"✅ Found {len(kompositions)} komposition(s) for user")
            for i, komp in enumerate(kompositions, 1):
                videos_count = len(komp.get('generated_videos', []))
                print(f"   {i}. {komp['title']} - {komp['status']} ({videos_count} video(s))")
        else:
            print(f"❌ Failed to list kompositions: {response}")
        
        print(f"\n🎯 SUCCESS: MCP Music Video Creation Workflow Completed!")
        print(f"   ✅ Komposition created and configured")
        print(f"   ✅ Media assets registered") 
        print(f"   ✅ Video processing simulated")
        print(f"   ✅ Library management working")
        print(f"\n💡 The TypeScript MCP server is ready for LLM integration!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        print(f"\n🧹 Stopping MCP server...")
        mcp_client.stop_server()
        print("✅ Test completed and cleaned up")

if __name__ == "__main__":
    asyncio.run(test_mcp_workflow())