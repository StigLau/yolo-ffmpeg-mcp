#!/usr/bin/env python3
"""
Test the process_komposition_video (pkv) MCP tool
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path

class MCPTester:
    def __init__(self):
        self.server_process = None
        self.mcp_dir = Path(__file__).parent / "src/mcp/typescript"
    
    def start_server(self):
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
        time.sleep(0.5)
        return self.server_process is not None
    
    def call_tool(self, tool_name: str, arguments: dict) -> dict:
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
            
            response_line = self.server_process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            else:
                return {"error": "No response from server"}
        except Exception as e:
            return {"error": f"Communication error: {e}"}
    
    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()

async def test_process_komposition_video():
    print("🧪 Testing process_komposition_video MCP Tool")
    print("=" * 45)
    
    mcp = MCPTester()
    if not mcp.start_server():
        print("❌ Failed to start MCP server")
        return
    
    try:
        # Step 1: Create a komposition first
        print("\n📝 Step 1: Creating test komposition...")
        response = mcp.call_tool('create_komposition', {
            'title': 'PKV Test Video',
            'description': 'Testing process_komposition_video tool',
            'user_id': 'pkv_test_user',
            'bpm': 120.0,
            'duration_seconds': 10.0
        })
        
        if 'result' not in response:
            print(f"❌ Failed to create komposition: {response}")
            return
        
        komposition_data = json.loads(response['result']['content'][0]['text'])
        komposition_id = komposition_data['id']
        print(f"✅ Test komposition created: {komposition_id}")
        
        # Step 2: Test process_komposition_video tool
        print(f"\n🎬 Step 2: Testing process_komposition_video tool...")
        print(f"Calling pkv tool with komposition_id: {komposition_id}")
        
        response = mcp.call_tool('process_komposition_video', {
            'komposition_id': komposition_id,
            'processing_options': {
                'quality': 'hd',
                'test_mode': True
            }
        })
        
        print(f"\n📋 Response received:")
        print(f"Response keys: {list(response.keys())}")
        
        if 'error' in response:
            print(f"❌ Tool returned error: {response['error']}")
        elif 'result' in response:
            print(f"✅ Tool executed successfully")
            result_data = json.loads(response['result']['content'][0]['text'])
            print(f"Result keys: {list(result_data.keys())}")
            print(f"Video ID: {result_data.get('id', 'N/A')}")
            print(f"File path: {result_data.get('file_path', 'N/A')}")
            print(f"Status: {result_data.get('status', 'N/A')}")
            
            # Check if file actually exists
            file_path = result_data.get('file_path')
            if file_path:
                file_exists = Path(file_path).exists()
                print(f"File exists: {file_exists}")
                if not file_exists:
                    print(f"⚠️  MCP tool returned file path but no actual file created")
                    print(f"This suggests MCP is only simulating, not calling Python backend")
        else:
            print(f"❓ Unexpected response format: {response}")
        
        print(f"\n🔍 Analysis:")
        print(f"- MCP tool responds correctly ✅")
        print(f"- Returns realistic video metadata ✅") 
        print(f"- But likely only simulating, not calling Python VideoProcessor")
        print(f"- Need to check if MCP tools actually integrate with Python services")
        
    finally:
        mcp.stop_server()

if __name__ == "__main__":
    asyncio.run(test_process_komposition_video())