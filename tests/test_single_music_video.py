#!/usr/bin/env python3
"""
Single Natural Language Music Video Test

Simplified test that creates one music video from natural language through the MCP server.
Tests the complete pipeline: Natural Language → Komposition JSON → uber-kompost → Verification
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


async def call_tool(name, **kwargs):
    """Helper to call MCP tools and parse JSON response."""
    from src.server import mcp
    result = await mcp.call_tool(name, kwargs)
    if result and len(result) > 0:
        return json.loads(result[0].text)
    return {}


async def test_single_music_video():
    """Test creating a single music video from natural language"""
    print("🎬 Single Natural Language Music Video Test")
    print("=" * 60)

    description = "Create a simple 30-second music video with available clips and background music"

    try:
        print(f"📝 Description: '{description}'")
        print(f"\n🔄 Step 1: Generating komposition from natural language...")

        # Generate komposition
        result = await call_tool(
            'generate_komposition_from_description',
            description=description,
            title="Test Music Video",
            custom_bpm=120
        )
        
        if result.get('success'):
            print(f"✅ Komposition generated successfully")
            
            # Save komposition to file
            komposition_data = result.get('komposition_data')
            if komposition_data:
                kompost_file = Path("/tmp/test_music_video.json")
                with open(kompost_file, 'w') as f:
                    json.dump(komposition_data, f, indent=2)
                
                print(f"📄 Saved komposition: {kompost_file}")
                print(f"📊 Komposition size: {len(str(komposition_data))} characters")
                
                # Test uber-kompost processing (will show if JAR is available)
                print(f"\n🔄 Step 2: Testing uber-kompost availability...")
                
                try:
                    sys.path.insert(0, str(Path(__file__).parent / "integration" / "komposteur"))
                    from bridge.uber_kompost_bridge import get_uber_bridge
                    
                    bridge = get_uber_bridge()
                    if bridge.is_available():
                        print(f"✅ Uber-kompost JAR available")
                        
                        # Process with uber-kompost
                        process_result = bridge.process_kompost_json(str(kompost_file))
                        
                        if process_result.get('success'):
                            print(f"✅ Uber-kompost processing successful")
                            print(f"📹 Processing result: {process_result}")
                            
                            # Check if output video exists
                            if 'output_path' in process_result:
                                output_path = Path(process_result['output_path'])
                                if output_path.exists():
                                    file_size = output_path.stat().st_size
                                    print(f"✅ Output video created: {file_size:,} bytes")
                                    print(f"📍 Location: {output_path}")
                                else:
                                    print(f"⚠️  Output path returned but file not found: {output_path}")
                            
                            return {
                                "success": True,
                                "workflow_complete": True,
                                "komposition_generated": True,
                                "uber_kompost_processed": True,
                                "video_output": process_result
                            }
                        else:
                            print(f"❌ Uber-kompost processing failed: {process_result.get('error')}")
                            return {
                                "success": False,
                                "step_failed": "uber_kompost_processing",
                                "error": process_result.get('error')
                            }
                    else:
                        print(f"⚠️  Uber-kompost JAR not available")
                        print(f"💡 Build with: mvn clean package -pl uber-kompost -DskipTests")
                        return {
                            "success": False,
                            "step_failed": "uber_kompost_unavailable", 
                            "komposition_generated": True,
                            "komposition_file": str(kompost_file)
                        }
                        
                except Exception as e:
                    print(f"❌ Uber-kompost test failed: {e}")
                    return {
                        "success": False,
                        "step_failed": "uber_kompost_error",
                        "error": str(e),
                        "komposition_generated": True
                    }
            else:
                print(f"❌ No komposition data in result")
                return {"success": False, "error": "No komposition data generated"}
        else:
            print(f"❌ Komposition generation failed: {result.get('error')}")
            return {"success": False, "error": result.get('error')}
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Run the single test"""
    result = await test_single_music_video()
    
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS")
    print(f"{'='*60}")
    
    if result.get('success'):
        print("✅ SUCCESS: Natural language music video pipeline working")
        if result.get('workflow_complete'):
            print("🎉 Complete end-to-end workflow functional!")
        return 0
    else:
        print("❌ FAILED: Pipeline incomplete")
        print(f"🐛 Failed at: {result.get('step_failed', 'unknown')}")
        print(f"💬 Error: {result.get('error', 'No error details')}")
        
        if result.get('komposition_generated'):
            print("✅ Komposition generation working")
            if result.get('komposition_file'):
                print(f"📄 Generated file: {result['komposition_file']}")
        
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)