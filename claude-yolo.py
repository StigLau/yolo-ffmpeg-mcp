#!/usr/bin/env python3
"""
Claude YOLO MCP Client - Demonstrates 128-beat music video creation
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

async def create_128_beat_music_video():
    """
    Create a 128-beat music video that transitions from JJVtt947FfI_136.mp4 
    to _wZ5Hof5tXY_136.mp4 with transitional effects
    """
    print("🎬 CREATING 128-BEAT MUSIC VIDEO")
    print("=" * 60)
    
    try:
        # Import MCP server tools directly
        from server import (
            list_files, get_file_info, 
            analyze_composition_sources,
            generate_composition_plan,
            process_composition_plan,
            cleanup_temp_files
        )
        
        # Step 1: List available files
        print("\n📁 STEP 1: LISTING AVAILABLE FILES")
        files_result = await list_files()
        
        if not files_result.get("success", True):
            print(f"❌ Failed to list files: {files_result.get('error', 'Unknown error')}")
            return False
        
        files = files_result.get("files", [])
        print(f"   ✅ Found {len(files)} files")
        
        # Find our target video files
        video_1 = None
        video_2 = None
        
        for file in files:
            if file.name == "JJVtt947FfI_136.mp4":
                video_1 = file
                print(f"   📹 Video 1: {file.name} ({file.size/1024/1024:.1f}MB)")
            elif file.name == "_wZ5Hof5tXY_136.mp4":
                video_2 = file
                print(f"   📹 Video 2: {file.name} ({file.size/1024/1024:.1f}MB)")
        
        if not video_1 or not video_2:
            print("❌ Target video files not found in source directory")
            print("   Expected: JJVtt947FfI_136.mp4 and _wZ5Hof5tXY_136.mp4")
            return False
        
        # Step 2: Get detailed file info
        print(f"\n📊 STEP 2: ANALYZING VIDEO PROPERTIES")
        
        video_1_info = await get_file_info(video_1.id)
        video_2_info = await get_file_info(video_2.id)
        
        if video_1_info.get("basic_info"):
            v1_media = video_1_info.get("media_info", {}).get("info", {}).get("format", {})
            v1_duration = float(v1_media.get("duration", 0))
            print(f"   🎥 Video 1: {v1_duration:.1f}s duration")
        
        if video_2_info.get("basic_info"):
            v2_media = video_2_info.get("media_info", {}).get("info", {}).get("format", {})
            v2_duration = float(v2_media.get("duration", 0))
            print(f"   🎥 Video 2: {v2_duration:.1f}s duration")
        
        # Step 3: Create 128-beat composition (64 seconds at 120 BPM)
        print(f"\n🎼 STEP 3: CREATING 128-BEAT COMPOSITION PLAN")
        
        # 128 beats at 120 BPM = 64 seconds
        bpm = 120
        beats = 128
        total_duration = (beats / bpm) * 60  # 64 seconds
        
        print(f"   🥁 BPM: {bpm}")
        print(f"   🎵 Total beats: {beats}")
        print(f"   ⏱️ Duration: {total_duration}s")
        
        # Create komposition JSON for advanced music video
        komposition = {
            "metadata": {
                "title": "128-Beat Music Video Transition",
                "bpm": bpm,
                "estimatedDuration": total_duration,
                "creator": "Claude YOLO MCP",
                "description": "Transitional music video from JJVtt947FfI_136.mp4 to _wZ5Hof5tXY_136.mp4"
            },
            "timeline": {
                "totalBeats": beats,
                "beatsPerMeasure": 16,
                "totalMeasures": 8
            },
            "segments": [
                {
                    "id": "transition_intro",
                    "sourceRef": "JJVtt947FfI_136.mp4",
                    "timing": {
                        "startBeat": 16,  # Start 16 beats in
                        "endBeat": 80,    # 64 beats duration
                        "sourceStart": 16 * (60/bpm),  # 8 seconds in
                        "sourceDuration": 32.0  # Take 32 seconds
                    },
                    "effects": {
                        "fadeIn": {"duration": 2.0},
                        "crossfade": {"enabled": True, "duration": 4.0}
                    }
                },
                {
                    "id": "transition_outro", 
                    "sourceRef": "_wZ5Hof5tXY_136.mp4",
                    "timing": {
                        "startBeat": 76,  # Start 76 beats in (overlap for transition)
                        "endBeat": 128,   # 52 beats duration  
                        "sourceStart": 24 * (60/bpm),  # 12 seconds in
                        "sourceDuration": 26.0  # Take 26 seconds
                    },
                    "effects": {
                        "fadeOut": {"duration": 2.0},
                        "crossfade": {"enabled": True, "duration": 4.0}
                    }
                }
            ],
            "effects_tree": {
                "type": "sequence",
                "effects": [
                    {
                        "type": "transition",
                        "name": "crossfade",
                        "start_time": 30.0,
                        "duration": 4.0,
                        "options": {
                            "transition_type": "fade",
                            "ease": "cubic-bezier"
                        }
                    },
                    {
                        "type": "color_correction",
                        "name": "brightness_sync",
                        "start_time": 0.0,
                        "duration": total_duration,
                        "options": {
                            "auto_levels": True,
                            "contrast": 1.1
                        }
                    }
                ]
            },
            "audio": {
                "backgroundMusic": None,  # Will be pure video audio with crossfade
                "mixingStrategy": "crossfade_original_audio"
            }
        }
        
        # Save komposition file
        komposition_path = Path("128_beat_music_video_komposition.json")
        with open(komposition_path, 'w') as f:
            json.dump(komposition, f, indent=2)
        
        print(f"   📄 Komposition saved: {komposition_path}")
        
        # Step 4: Analyze sources for intelligent processing
        print(f"\n🧠 STEP 4: ANALYZING SOURCES FOR INTELLIGENT PROCESSING")
        
        source_filenames = ["JJVtt947FfI_136.mp4", "_wZ5Hof5tXY_136.mp4"]
        analysis_result = await analyze_composition_sources(source_filenames, force_reanalysis=True)
        
        if analysis_result["success"]:
            print(f"   ✅ Analysis complete: {len(analysis_result['analyzed_sources'])} sources")
            for source in analysis_result["analyzed_sources"]:
                has_speech = "🎤" if source['has_speech'] else "🔇"
                print(f"      {has_speech} {source['filename']}: {source['recommended_strategy']} (priority: {source['priority_score']:.2f})")
        else:
            print(f"   ⚠️ Analysis failed, proceeding with basic processing: {analysis_result.get('error', 'Unknown')}")
        
        # Step 5: Generate and process composition plan
        print(f"\n🎯 STEP 5: GENERATING INTELLIGENT COMPOSITION PLAN")
        
        plan_result = await generate_composition_plan(
            source_filenames=source_filenames,
            background_music="",  # No background music, use original audio
            total_duration=total_duration,
            bpm=bpm,
            composition_title="128-Beat Music Video Transition",
            force_reanalysis=False
        )
        
        if plan_result["success"]:
            print(f"   ✅ Plan generated successfully")
            summary = plan_result["processing_summary"]
            print(f"      📊 Total segments: {summary['total_segments']}")
            print(f"      🎤 Speech segments: {summary['speech_segments']}")
            print(f"      ⏱️ Estimated processing: {summary['estimated_processing_time']/60:.1f} minutes")
            
            # Process the plan
            print(f"\n🚀 STEP 6: PROCESSING COMPOSITION PLAN")
            
            process_result = await process_composition_plan(plan_result["plan_file_path"])
            
            if process_result["success"]:
                print(f"   ✅ Processing complete!")
                print(f"      📁 Generated {len(process_result['output_files'])} files")
                
                for output_file in process_result["output_files"]:
                    print(f"         📄 {output_file['type']}: {output_file['description']} (ID: {output_file['file_id']})")
                
                # Show audio manifest for external mixing
                if process_result.get("audio_manifest"):
                    manifest_path = Path("audio_timing_manifest.json")
                    with open(manifest_path, 'w') as f:
                        json.dump(process_result["audio_manifest"], f, indent=2)
                    print(f"      🎵 Audio timing manifest saved: {manifest_path}")
                
                print(f"\n🎉 128-BEAT MUSIC VIDEO CREATION COMPLETE!")
                print(f"✅ Files ready for final assembly in external video editor")
                
                return True
            else:
                print(f"   ❌ Processing failed: {process_result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Plan generation failed: {plan_result.get('error', 'Unknown error')}")
            return False
        
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
    """Main function to run the music video creation"""
    print("🎬 CLAUDE YOLO MCP CLIENT")
    print("Creating 128-beat music video with transitional effects")
    print("=" * 60)
    
    success = await create_128_beat_music_video()
    
    if success:
        print(f"\n✅ MISSION ACCOMPLISHED!")
        print(f"🎥 Your 128-beat music video components are ready")
        print(f"📁 Check generated files and audio manifest for final assembly")
    else:
        print(f"\n❌ MISSION FAILED!")
        print(f"🔧 Check the error messages above for troubleshooting")
    
    return success

if __name__ == "__main__":
    # Run the async main function
    success = asyncio.run(main())
    sys.exit(0 if success else 1)