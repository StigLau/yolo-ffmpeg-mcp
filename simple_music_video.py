#!/usr/bin/env python3
"""
Simple 128-beat music video creation using direct MCP tools
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

async def create_simple_128_beat_video():
    """
    Create a 128-beat music video using basic MCP operations
    """
    print("🎬 CREATING SIMPLE 128-BEAT MUSIC VIDEO")
    print("=" * 60)
    
    try:
        # Import basic MCP server tools
        from server import (
            list_files, get_file_info, process_file, 
            batch_process, cleanup_temp_files
        )
        
        # Step 1: List and find our video files
        print("\n📁 STEP 1: FINDING SOURCE VIDEOS")
        files_result = await list_files()
        
        files = files_result.get("files", [])
        print(f"   ✅ Found {len(files)} files")
        
        video_1 = None
        video_2 = None
        
        for file in files:
            if file.name == "JJVtt947FfI_136.mp4":
                video_1 = file
                print(f"   📹 Video 1: {file.name} (ID: {file.id})")
            elif file.name == "_wZ5Hof5tXY_136.mp4":
                video_2 = file  
                print(f"   📹 Video 2: {file.name} (ID: {file.id})")
        
        if not video_1 or not video_2:
            print("❌ Required videos not found")
            return False
        
        # Step 2: Calculate timing for 128 beats
        print(f"\n⏰ STEP 2: CALCULATING 128-BEAT TIMING")
        
        bpm = 120
        beats = 128
        total_duration = (beats / bpm) * 60  # 64 seconds
        
        # Start video 1 at 16 beats in (8 seconds)
        video_1_start = (16 / bpm) * 60  # 8 seconds
        video_1_duration = 32.0  # 32 seconds for smooth transition
        
        # Start video 2 at 24 beats in (12 seconds)  
        video_2_start = (24 / bpm) * 60  # 12 seconds
        video_2_duration = 26.0  # 26 seconds
        
        print(f"   🎵 Total duration: {total_duration}s ({beats} beats @ {bpm} BPM)")
        print(f"   📹 Video 1: {video_1_start}s start, {video_1_duration}s duration")
        print(f"   📹 Video 2: {video_2_start}s start, {video_2_duration}s duration")
        
        # Step 3: Extract segments using batch processing
        print(f"\n✂️ STEP 3: EXTRACTING VIDEO SEGMENTS")
        
        operations = [
            {
                "input_file_id": video_1.id,
                "operation": "trim",
                "output_extension": "mp4",
                "params": f"start={video_1_start} duration={video_1_duration}"
            },
            {
                "input_file_id": video_2.id, 
                "operation": "trim",
                "output_extension": "mp4",
                "params": f"start={video_2_start} duration={video_2_duration}"
            }
        ]
        
        batch_result = await batch_process(operations)
        
        if not batch_result["success"]:
            print(f"   ❌ Batch processing failed: {batch_result.get('error', 'Unknown')}")
            return False
        
        print(f"   ✅ Extracted {len(batch_result['completed_steps'])} segments")
        
        # Get the output file IDs
        segment_1_id = None
        segment_2_id = None
        
        for step in batch_result["completed_steps"]:
            if step["success"] and step["output_file_id"]:
                if step["step"] == 1:
                    segment_1_id = step["output_file_id"]
                    print(f"      📹 Segment 1 ID: {segment_1_id}")
                elif step["step"] == 2:
                    segment_2_id = step["output_file_id"]
                    print(f"      📹 Segment 2 ID: {segment_2_id}")
        
        if not segment_1_id or not segment_2_id:
            print("   ❌ Failed to get segment IDs")
            return False
        
        # Step 4: Concatenate segments
        print(f"\n🔗 STEP 4: COMBINING SEGMENTS")
        
        concat_result = await process_file(
            input_file_id=segment_1_id,
            operation="concatenate_simple",
            output_extension="mp4", 
            params=f"second_video={segment_2_id}"
        )
        
        if not concat_result.success:
            print(f"   ❌ Concatenation failed: {concat_result.message}")
            return False
        
        final_video_id = concat_result.output_file_id
        print(f"   ✅ Combined video created (ID: {final_video_id})")
        
        # Step 5: Get final video info
        print(f"\n📊 STEP 5: FINAL VIDEO INFO")
        
        final_info = await get_file_info(final_video_id)
        if final_info.get("media_info", {}).get("success"):
            media_info = final_info["media_info"]["info"]["format"]
            duration = float(media_info.get("duration", 0))
            size_mb = final_info["basic_info"]["size"] / (1024 * 1024)
            
            print(f"   🎬 Final video: {duration:.1f}s duration, {size_mb:.1f}MB")
            print(f"   📄 File ID: {final_video_id}")
        
        # Step 6: Create video composition manifest
        print(f"\n📄 STEP 6: CREATING COMPOSITION MANIFEST")
        
        composition_manifest = {
            "metadata": {
                "title": "128-Beat Music Video Transition",
                "description": "Simple transition video from JJVtt947FfI_136.mp4 to _wZ5Hof5tXY_136.mp4",
                "bpm": bpm,
                "total_beats": beats,
                "total_duration": total_duration,
                "created_by": "Claude YOLO MCP Simple"
            },
            "source_videos": {
                "video_1": {
                    "filename": "JJVtt947FfI_136.mp4",
                    "file_id": video_1.id,
                    "segment_start": video_1_start,
                    "segment_duration": video_1_duration
                },
                "video_2": {
                    "filename": "_wZ5Hof5tXY_136.mp4", 
                    "file_id": video_2.id,
                    "segment_start": video_2_start,
                    "segment_duration": video_2_duration
                }
            },
            "output": {
                "final_video_id": final_video_id,
                "processing_steps": len(operations) + 1,
                "composition_type": "simple_concatenation"
            },
            "next_steps": [
                "Use final video for further editing",
                "Add background music if desired", 
                "Apply transitions in external editor",
                "Export in desired format for platform"
            ]
        }
        
        manifest_path = Path("simple_128_beat_composition.json")
        with open(manifest_path, 'w') as f:
            json.dump(composition_manifest, f, indent=2)
        
        print(f"   📄 Composition manifest saved: {manifest_path}")
        
        print(f"\n🎉 128-BEAT MUSIC VIDEO CREATION COMPLETE!")
        print(f"✅ Final video file ID: {final_video_id}")
        print(f"📁 Composition details: {manifest_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup temp files
        try:
            await cleanup_temp_files()
            print(f"\n🧹 Temporary files cleaned up")
        except:
            pass

async def main():
    """Main function"""
    print("🎬 SIMPLE CLAUDE YOLO MCP CLIENT")
    print("Creating 128-beat music video with basic operations")
    print("=" * 60)
    
    success = await create_simple_128_beat_video()
    
    if success:
        print(f"\n✅ SUCCESS! Simple 128-beat music video created")
        print(f"🎥 Your video is ready for additional editing")
    else:
        print(f"\n❌ FAILED! Check error messages above")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)