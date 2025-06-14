#!/usr/bin/env python3
"""
Create video-only composition with timing manifest for external audio mixing.
This separates video composition from audio mixing responsibilities.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path  
sys.path.append(str(Path(__file__).parent / 'src'))

async def create_video_only_composition():
    print("🎬 CREATING VIDEO-ONLY COMPOSITION + AUDIO TIMING MANIFEST")
    print("=" * 70)
    
    try:
        # Import components
        from file_manager import FileManager
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        
        # Initialize components
        file_manager = FileManager()
        ffmpeg_wrapper = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        
        print(f"🎯 VIDEO-ONLY COMPOSITION PLAN:")
        print(f"   1. Create time-stretched video segments (no audio mixing)")
        print(f"   2. Extract and prepare speech audio file")
        print(f"   3. Generate audio timing manifest for external mixing")
        print(f"   4. Create silent video composition")
        
        # Verify source files
        video_files = {
            "PXL": "PXL_20250306_132546255.mp4",
            "lookin": "lookin.mp4",
            "panning": "panning back and forth.mp4",
            "music": "16BL - Deep In My Soul (Original Mix).mp3"
        }
        
        file_ids = {}
        for name, filename in video_files.items():
            file_id = file_manager.get_id_by_name(filename)
            if file_id:
                file_ids[name] = file_id
                print(f"   ✅ {name}: {filename}")
            else:
                print(f"   ❌ {name}: {filename} - NOT FOUND")
                return False
        
        # Get file paths
        pxl_path = file_manager.resolve_id(file_ids["PXL"])
        lookin_path = file_manager.resolve_id(file_ids["lookin"])
        panning_path = file_manager.resolve_id(file_ids["panning"])
        
        # Step 1: Create silent video segments (time-stretched, no audio)
        print(f"\n🎬 STEP 1: CREATING TIME-STRETCHED VIDEO SEGMENTS (SILENT)")
        video_segments = []
        
        # Segment 1: PXL video (3.567s → 8s, silent)
        print(f"📹 Creating silent PXL segment (3.567s → 8s)")
        segment1_video = Path("/tmp/music/temp/silent_pxl_8s.mp4")
        
        cmd1 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(pxl_path),
            "-vf", "setpts=PTS*2.243",    # Time-stretch video
            "-an",                        # Remove audio completely
            "-t", "8",                    # Exactly 8 seconds
            "-c:v", "libx264",
            "-y",
            str(segment1_video)
        ]
        
        result1 = await ffmpeg_wrapper.execute_command(cmd1, timeout=120)
        if result1["success"] and segment1_video.exists():
            print(f"   ✅ Silent PXL segment: {segment1_video.stat().st_size:,} bytes")
            video_segments.append(segment1_video)
        else:
            print(f"   ❌ Silent PXL segment failed")
            return False
        
        # Segment 2: lookin video (5.801s → 8s, silent)
        print(f"📹 Creating silent lookin segment (5.801s → 8s)")
        segment2_video = Path("/tmp/music/temp/silent_lookin_8s.mp4")
        
        cmd2 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(lookin_path),
            "-vf", "setpts=PTS*1.379",    # Time-stretch video
            "-an",                        # Remove audio completely
            "-t", "8",                    # Exactly 8 seconds
            "-c:v", "libx264",
            "-y",
            str(segment2_video)
        ]
        
        result2 = await ffmpeg_wrapper.execute_command(cmd2, timeout=120)
        if result2["success"] and segment2_video.exists():
            print(f"   ✅ Silent lookin segment: {segment2_video.stat().st_size:,} bytes")
            video_segments.append(segment2_video)
        else:
            print(f"   ❌ Silent lookin segment failed")
            return False
        
        # Segment 3: panning video (12.262s → 8s, silent)
        print(f"📹 Creating silent panning segment (12.262s → 8s)")
        segment3_video = Path("/tmp/music/temp/silent_panning_8s.mp4")
        
        cmd3 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(panning_path),
            "-vf", "setpts=PTS*0.652",    # Time-stretch video
            "-an",                        # Remove audio completely
            "-t", "8",                    # Exactly 8 seconds
            "-c:v", "libx264",
            "-y",
            str(segment3_video)
        ]
        
        result3 = await ffmpeg_wrapper.execute_command(cmd3, timeout=120)
        if result3["success"] and segment3_video.exists():
            print(f"   ✅ Silent panning segment: {segment3_video.stat().st_size:,} bytes")
            video_segments.append(segment3_video)
        else:
            print(f"   ❌ Silent panning segment failed")
            return False
        
        # Step 2: Extract and prepare speech audio
        print(f"\n🎤 STEP 2: EXTRACTING TIME-STRETCHED SPEECH AUDIO")
        
        # Extract original speech
        original_speech = Path("/tmp/music/temp/original_speech.wav")
        cmd_extract = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(lookin_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",
            "-y",
            str(original_speech)
        ]
        
        result_extract = await ffmpeg_wrapper.execute_command(cmd_extract, timeout=60)
        if not (result_extract["success"] and original_speech.exists()):
            print(f"   ❌ Speech extraction failed")
            return False
        
        # Time-stretch speech to 8 seconds
        stretched_speech = Path("/tmp/music/temp/stretched_speech_8s.wav")
        cmd_stretch = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(original_speech),
            "-af", "atempo=0.725",  # Time-stretch speech
            "-t", "8",
            "-y",
            str(stretched_speech)
        ]
        
        result_stretch = await ffmpeg_wrapper.execute_command(cmd_stretch, timeout=60)
        if result_stretch["success"] and stretched_speech.exists():
            print(f"   ✅ Time-stretched speech ready: {stretched_speech.stat().st_size:,} bytes")
        else:
            print(f"   ❌ Speech time-stretching failed")
            return False
        
        # Step 3: Create silent video composition
        print(f"\n🔗 STEP 3: CREATING SILENT VIDEO COMPOSITION")
        
        # Create concat list
        concat_list = Path("/tmp/music/temp/silent_concat_list.txt")
        with open(concat_list, 'w') as f:
            for segment in video_segments:
                f.write(f"file '{segment}'\n")
        
        silent_video = Path("/tmp/music/temp/SILENT_VIDEO_COMPOSITION.mp4")
        
        cmd_concat = [
            SecurityConfig.FFMPEG_PATH,
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",  # Copy video streams
            "-y",
            str(silent_video)
        ]
        
        result_concat = await ffmpeg_wrapper.execute_command(cmd_concat, timeout=180)
        
        if not (result_concat["success"] and silent_video.exists()):
            print(f"   ❌ Silent video composition failed")
            return False
        
        # Step 4: Generate audio timing manifest
        print(f"\n📋 STEP 4: GENERATING AUDIO TIMING MANIFEST")
        
        manifest = {
            "metadata": {
                "title": "Beat-Synchronized Audio Timing Manifest",
                "description": "Timing information for manual audio mixing",
                "totalDuration": 24.0,
                "backgroundMusic": "16BL - Deep In My Soul (Original Mix).mp3",
                "createdAt": datetime.now().isoformat(),
                "silentVideoFile": str(silent_video)
            },
            "videoSegments": [
                {
                    "segmentId": "segment_1",
                    "videoFile": "PXL_20250306_132546255.mp4",
                    "originalDuration": 3.567133,
                    "targetDuration": 8.0,
                    "timeSlot": {"startTime": 0.0, "endTime": 8.0},
                    "audioHandling": {"useOriginalAudio": False, "musicOnly": True}
                },
                {
                    "segmentId": "segment_2",
                    "videoFile": "lookin.mp4",
                    "originalDuration": 5.800567,
                    "targetDuration": 8.0,
                    "timeSlot": {"startTime": 8.0, "endTime": 16.0},
                    "audioHandling": {
                        "useOriginalAudio": True,
                        "extractedAudioFile": str(stretched_speech),
                        "insertAtTime": 8.0,
                        "speechVolume": 0.9,
                        "musicVolume": 0.2
                    }
                },
                {
                    "segmentId": "segment_3",
                    "videoFile": "panning back and forth.mp4",
                    "originalDuration": 12.262044,
                    "targetDuration": 8.0,
                    "timeSlot": {"startTime": 16.0, "endTime": 24.0},
                    "audioHandling": {"useOriginalAudio": False, "musicOnly": True}
                }
            ],
            "finalAssemblyInstructions": {
                "step1": "Load silent video: " + str(silent_video),
                "step2": "Load background music: 16BL - Deep In My Soul (Original Mix).mp3",
                "step3": "Set music volume to 0.5 for entire 24-second duration",
                "step4": "At 8.0s: Insert stretched_speech_8s.wav at volume 0.9",
                "step5": "Ensure speech ends at 16.0s",
                "step6": "Export final audio track",
                "step7": "Combine: ffmpeg -i SILENT_VIDEO_COMPOSITION.mp4 -i final_audio.wav -c:v copy -map 0:v -map 1:a FINAL_COMPOSITION.mp4"
            }
        }
        
        manifest_file = Path("/tmp/music/temp/AUDIO_TIMING_MANIFEST.json")
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"   ✅ Audio timing manifest: {manifest_file}")
        
        # Summary
        video_size = silent_video.stat().st_size
        speech_size = stretched_speech.stat().st_size
        
        print(f"\n🎉 VIDEO-ONLY COMPOSITION COMPLETE!")
        print(f"📂 Silent video: {silent_video} ({video_size:,} bytes)")
        print(f"🎤 Extracted speech: {stretched_speech} ({speech_size:,} bytes)")
        print(f"📋 Timing manifest: {manifest_file}")
        
        print(f"\n📊 WHAT YOU HAVE:")
        print(f"   ✅ Perfect 24-second video composition (no audio)")
        print(f"   ✅ Time-stretched speech audio (8 seconds)")
        print(f"   ✅ Detailed timing manifest for external audio mixing")
        
        print(f"\n🎵 AUDIO MIXING INSTRUCTIONS:")
        print(f"   • 0-8s: Background music only")
        print(f"   • 8-16s: Background music + speech overlay")
        print(f"   • 16-24s: Background music only")
        print(f"   • Speech file: {stretched_speech}")
        print(f"   • Insert speech at exactly 8.0 seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Video-only composition failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(create_video_only_composition())
    
    if success:
        print(f"\n✅ VIDEO-ONLY COMPOSITION SUCCESSFUL!")
        print(f"📁 Check /tmp/music/temp/ for:")
        print(f"   • SILENT_VIDEO_COMPOSITION.mp4 (perfect video)")
        print(f"   • stretched_speech_8s.wav (speech audio)")
        print(f"   • AUDIO_TIMING_MANIFEST.json (mixing instructions)")
    else:
        print(f"\n❌ Video-only composition failed")