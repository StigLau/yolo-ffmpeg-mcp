#!/usr/bin/env python3
"""
Test basic video operations that should work
"""

import asyncio
import sys
from pathlib import Path
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_basic_operations():
    print("🎬 Testing Basic Video Operations")
    print("=" * 50)
    
    try:
        # Import components 
        from file_manager import FileManager
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        
        # Initialize components
        file_manager = FileManager()
        ffmpeg_wrapper = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        
        # Get file ID for lookin.mp4
        print("📁 Getting file ID for lookin.mp4...")
        lookin_id = file_manager.get_id_by_name("lookin.mp4")
        print(f"📋 File ID: {lookin_id}")
        
        if not lookin_id:
            print("❌ Could not get file ID for lookin.mp4")
            return
            
        # Test 1: Trim video
        print(f"\n🔪 Testing video trim operation...")
        
        # Create output file
        output_file_id, output_path = file_manager.create_temp_file("mp4")
        input_path = file_manager.resolve_id(lookin_id)
        
        print(f"   Input: {input_path}")
        print(f"   Output: {output_path}")
        
        # Build trim command
        cmd = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(input_path),
            "-ss", "0",      # Start at 0 seconds
            "-t", "5",       # Duration 5 seconds
            "-c", "copy",    # Fast copy without re-encoding
            str(output_path)
        ]
        
        print(f"   Command: {' '.join(cmd)}")
        
        # Execute command
        result = await ffmpeg_wrapper.execute_command(cmd, timeout=60)
        
        print(f"   ✅ Success: {result['success']}")
        print(f"   📂 Output exists: {output_path.exists()}")
        
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"   📏 Output size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            print(f"   🎉 TRIM OPERATION SUCCESSFUL!")
            
            # Test 2: Get another video for concatenation test
            print(f"\n🔗 Testing video concatenation preparation...")
            
            # Get second video
            intro_id = file_manager.get_id_by_name("PXL_20250306_132546255.mp4")
            print(f"📋 Intro video ID: {intro_id}")
            
            if intro_id:
                # Trim intro video too
                intro_output_id, intro_output_path = file_manager.create_temp_file("mp4")
                intro_input_path = file_manager.resolve_id(intro_id)
                
                intro_cmd = [
                    SecurityConfig.FFMPEG_PATH,
                    "-i", str(intro_input_path),
                    "-ss", "0",
                    "-t", "5",
                    "-c", "copy",
                    str(intro_output_path)
                ]
                
                intro_result = await ffmpeg_wrapper.execute_command(intro_cmd, timeout=60)
                
                if intro_result['success'] and intro_output_path.exists():
                    print(f"   ✅ Intro trim successful")
                    
                    # Test concatenation
                    print(f"\n🔗 Testing video concatenation...")
                    
                    concat_output_id, concat_output_path = file_manager.create_temp_file("mp4")
                    
                    # Create concat list file
                    concat_list_path = Path("/tmp/music/temp") / "concat_list.txt"
                    with open(concat_list_path, 'w') as f:
                        f.write(f"file '{intro_output_path}'\n")
                        f.write(f"file '{output_path}'\n")
                    
                    concat_cmd = [
                        SecurityConfig.FFMPEG_PATH,
                        "-f", "concat",
                        "-safe", "0",
                        "-i", str(concat_list_path),
                        "-c", "copy",
                        str(concat_output_path)
                    ]
                    
                    concat_result = await ffmpeg_wrapper.execute_command(concat_cmd, timeout=120)
                    
                    print(f"   ✅ Concat success: {concat_result['success']}")
                    print(f"   📂 Concat output exists: {concat_output_path.exists()}")
                    
                    if concat_output_path.exists():
                        concat_size = concat_output_path.stat().st_size
                        print(f"   📏 Concat size: {concat_size:,} bytes ({concat_size/1024/1024:.1f} MB)")
                        print(f"   🎉 CONCATENATION SUCCESSFUL!")
                        
                        # Register the final output
                        final_id = file_manager.add_temp_file(concat_output_path)
                        print(f"   🆔 Final video ID: {final_id}")
                        
                        return True
                        
        else:
            print(f"   ❌ Trim failed: {result.get('logs', 'Unknown error')}")
            
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_basic_operations())
    if success:
        print(f"\n🎉 ALL BASIC OPERATIONS SUCCESSFUL!")
        print(f"✅ Ready for speech overlay implementation")
    else:
        print(f"\n❌ Basic operations failed - need to fix underlying issues first")