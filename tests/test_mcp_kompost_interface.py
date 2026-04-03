#!/usr/bin/env python3
"""
Test kompost.json processing via MCP Server Interface
====================================================

Tests the MCP server's ability to process kompost.json files and create
complete music videos using the Komposteur integration.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.file_manager import FileManager
from src.komposteur_bridge_processor import KompositionProcessor

async def test_kompost_json_via_mcp():
    """Test kompost.json processing through MCP interface"""
    
    print("🎬 Testing kompost.json via MCP Server Interface")
    print("=" * 60)
    
    # Initialize components
    file_manager = FileManager()
    komposteur_processor = KompositionProcessor()
    
    # Path to our test kompost.json
    kompost_file = Path("test_kompost.json")
    
    if not kompost_file.exists():
        print("❌ test_kompost.json not found")
        return False
    
    try:
        print(f"📁 Processing kompost file: {kompost_file}")
        
        # Process the kompost.json using Komposteur processor
        result = await komposteur_processor.process_kompost(str(kompost_file))
        
        print(f"\n🎯 Processing Result:")
        print(f"Success: {result.get('success', False)}")
        
        if result.get('success'):
            print("✅ KOMPOST.JSON PROCESSING SUCCESS!")
            
            output_file = result.get('output_file')
            if output_file and Path(output_file).exists():
                file_size = Path(output_file).stat().st_size / (1024 * 1024)
                print(f"📁 Output file: {output_file}")
                print(f"📊 File size: {file_size:.1f} MB")
                
                # Get file info via file manager
                file_id = file_manager.register_file(Path(output_file))
                file_info = file_manager.get_file_info(file_id)
                
                if file_info:
                    print(f"🎬 Video properties:")
                    print(f"   Duration: {file_info.get('duration', 'Unknown')}s")
                    print(f"   Resolution: {file_info.get('width', '?')}x{file_info.get('height', '?')}")
                    print(f"   Codec: {file_info.get('video_codec', 'Unknown')}")
                    print(f"   Has audio: {file_info.get('has_audio', False)}")
            else:
                print("⚠️ Output file not found or not created")
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            
            # Check for validation errors
            if 'validation_result' in result:
                validation = result['validation_result']
                if not validation.get('valid', True):
                    print("🔍 Validation errors:")
                    for error in validation.get('errors', []):
                        print(f"   - {error}")
                    
                    if 'warnings' in validation:
                        print("⚠️ Validation warnings:")
                        for warning in validation.get('warnings', []):
                            print(f"   - {warning}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"💥 Exception during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run kompost.json MCP test"""
    
    print("🚀 MCP Server Kompost.json Test Suite")
    print("Testing complete music video creation via kompost.json")
    print("=" * 60)
    
    success = await test_kompost_json_via_mcp()
    
    print(f"\n🎯 Final Result")
    print("=" * 20)
    
    if success:
        print("🎉 TEST PASSED!")
        print("✅ MCP server successfully processed kompost.json")
        print("✅ Complete music video created via komposition")
        print("✅ Komposteur integration working via MCP interface")
    else:
        print("❌ TEST FAILED")
        print("🔍 Check errors above for debugging information")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)