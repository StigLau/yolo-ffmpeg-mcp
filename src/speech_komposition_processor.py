"""
Speech-Aware Komposition Processor
Extends komposition processing with speech detection and audio layering
"""
import json
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from .komposition_processor import KompositionProcessor, BeatTiming
    from .file_manager import FileManager
    from .ffmpeg_wrapper import FFMPEGWrapper
    from .config import SecurityConfig
except ImportError:
    from komposition_processor import KompositionProcessor, BeatTiming
    from file_manager import FileManager
    from ffmpeg_wrapper import FFMPEGWrapper
    from config import SecurityConfig

class SpeechKompositionProcessor(KompositionProcessor):
    """Extended komposition processor with speech overlay capabilities"""
    
    def __init__(self, file_manager: FileManager, ffmpeg_wrapper: FFMPEGWrapper):
        super().__init__(file_manager, ffmpeg_wrapper)
        self.temp_dir = Path("/tmp/music/temp")
        self.temp_dir.mkdir(exist_ok=True)
    
    async def process_speech_komposition(self, komposition_path: str) -> Dict[str, Any]:
        """Process komposition with speech overlay support"""
        
        # Load komposition data
        komposition_data = await self.load_komposition(komposition_path)
        
        # Initialize beat timing
        metadata = komposition_data["metadata"]
        bpm = metadata["bpm"]
        timing = BeatTiming(bpm)
        
        print(f"🎵 Processing speech-enabled komposition: {metadata['title']}")
        print(f"   BPM: {bpm}, Duration: {metadata['estimatedDuration']}s")
        
        # Step 1: Process video segments
        video_segments = []
        for segment in komposition_data["segments"]:
            print(f"\n📹 Processing segment: {segment['id']}")
            
            # Get source file ID
            source_file = segment["sourceRef"]
            file_id = self.file_manager.get_id_by_name(source_file)
            
            if not file_id:
                return {"success": False, "error": f"Source file not found: {source_file}"}
            
            # Process video segment
            if segment.get("speechOverlay", {}).get("enabled", False):
                # Special processing for speech overlay segment
                video_clip_id = await self.process_speech_segment(segment, file_id, timing)
            else:
                # Regular video processing
                video_clip_id = await self.process_regular_segment(segment, file_id, timing)
            
            if not video_clip_id:
                return {"success": False, "error": f"Failed to process segment: {segment['id']}"}
            
            video_segments.append({
                "clip_id": video_clip_id,
                "segment": segment,
                "duration": segment["duration"]
            })
        
        # Step 2: Concatenate all video segments
        print(f"\n🔗 Concatenating {len(video_segments)} video segments...")
        final_video_id = await self.concatenate_segments(video_segments)
        
        if not final_video_id:
            return {"success": False, "error": "Failed to concatenate video segments"}
        
        # Step 3: Add global background music if specified
        global_audio = komposition_data.get("globalAudio")
        if global_audio and global_audio.get("backgroundMusic"):
            print(f"\n🎶 Adding global background music...")
            final_video_id = await self.add_global_music(final_video_id, global_audio, metadata["estimatedDuration"])
        
        print(f"\n✅ Speech komposition completed successfully!")
        return {
            "success": True,
            "output_file_id": final_video_id,
            "metadata": metadata,
            "processing_summary": {
                "segments_processed": len(video_segments),
                "total_duration": metadata["estimatedDuration"],
                "speech_segments_found": sum(1 for seg in komposition_data["segments"] if seg.get("speechOverlay", {}).get("enabled", False))
            }
        }
    
    async def process_speech_segment(self, segment: Dict[str, Any], file_id: str, timing: BeatTiming) -> Optional[str]:
        """Process video segment with speech overlay"""
        
        speech_overlay = segment["speechOverlay"]
        background_music = speech_overlay["backgroundMusic"]
        music_volume = speech_overlay.get("musicVolume", 0.3)
        speech_volume = speech_overlay.get("speechVolume", 0.8)
        
        print(f"   🎤 Processing speech overlay with background music: {background_music}")
        print(f"   🔊 Music volume: {music_volume}, Speech volume: {speech_volume}")
        
        # Step 1: Trim video to desired duration
        duration = segment["duration"]
        start_time = segment["params"].get("start", 0)
        
        # Trim the source video
        trim_result = await self._execute_ffmpeg_operation(
            file_id, "trim", "mp4",
            start=start_time, duration=duration
        )
        
        if not trim_result["success"]:
            print(f"   ❌ Failed to trim video: {trim_result.get('error', 'Unknown error')}")
            return None
        
        trimmed_video_id = trim_result["output_file_id"]
        
        # Step 2: Extract original audio from video
        audio_result = await self._execute_ffmpeg_operation(
            trimmed_video_id, "extract_audio", "wav"
        )
        
        if not audio_result["success"]:
            print(f"   ❌ Failed to extract audio: {audio_result.get('error', 'Unknown error')}")
            return None
        
        original_audio_id = audio_result["output_file_id"]
        
        # Step 3: Get background music file ID
        music_file_id = self.file_manager.get_id_by_name(background_music)
        if not music_file_id:
            print(f"   ❌ Background music file not found: {background_music}")
            return None
        
        # Step 4: Create mixed audio track
        mixed_audio_id = await self.create_speech_music_mix(
            original_audio_id, music_file_id, duration, 
            music_volume, speech_volume, speech_overlay["speechSegments"]
        )
        
        if not mixed_audio_id:
            print(f"   ❌ Failed to create speech-music mix")
            return None
        
        # Step 5: Replace video audio with mixed track
        final_result = await self._execute_ffmpeg_operation(
            trimmed_video_id, "replace_audio", "mp4",
            audio_file=self.file_manager.resolve_id(mixed_audio_id)
        )
        
        if not final_result["success"]:
            print(f"   ❌ Failed to replace audio: {final_result.get('error', 'Unknown error')}")
            return None
        
        print(f"   ✅ Speech overlay completed successfully")
        return final_result["output_file_id"]
    
    async def process_regular_segment(self, segment: Dict[str, Any], file_id: str, timing: BeatTiming) -> Optional[str]:
        """Process regular video segment without speech overlay"""
        
        operation = segment.get("operation", "trim")
        params = segment.get("params", {})
        
        print(f"   📹 Regular processing: {operation} with params {params}")
        
        if operation == "trim":
            result = await self._execute_ffmpeg_operation(
                file_id, "trim", "mp4",
                start=params.get("start", 0),
                duration=segment["duration"]
            )
        else:
            # Other operations can be added here
            result = {"success": False, "error": f"Unsupported operation: {operation}"}
        
        if result["success"]:
            print(f"   ✅ Regular segment processed successfully")
            return result["output_file_id"]
        else:
            print(f"   ❌ Failed to process regular segment: {result.get('error', 'Unknown error')}")
            return None
    
    async def create_speech_music_mix(self, speech_audio_id: str, music_file_id: str, 
                                    duration: float, music_volume: float, speech_volume: float,
                                    speech_segments: List[Dict[str, Any]]) -> Optional[str]:
        """Create audio mix with speech over background music"""
        
        print(f"   🎛️  Creating speech-music mix...")
        print(f"      Speech segments: {len(speech_segments)}")
        print(f"      Duration: {duration}s")
        
        # Create temporary files for processing
        speech_path = self.file_manager.resolve_id(speech_audio_id)
        music_path = self.file_manager.resolve_id(music_file_id)
        
        if not speech_path or not music_path:
            return None
        
        # Generate unique output filename
        output_file = self.temp_dir / f"speech_music_mix_{self._generate_unique_id()}.wav"
        
        # Build complex FFmpeg command for audio mixing
        # This preserves speech at detected segments while adding background music
        cmd = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(speech_path),  # Input 0: Original speech audio
            "-i", str(music_path),   # Input 1: Background music
            "-filter_complex", self._build_speech_music_filter(duration, music_volume, speech_volume, speech_segments),
            "-t", str(duration),     # Limit to desired duration
            "-c:a", "pcm_s16le",     # High quality audio
            "-ar", "44100",          # Sample rate
            str(output_file)
        ]
        
        result = await self.ffmpeg_wrapper.execute_command(cmd, timeout=300)
        
        if result["success"] and output_file.exists():
            # Register the new file with file manager
            file_id = self.file_manager.add_temp_file(output_file)
            print(f"   ✅ Speech-music mix created: {file_id}")
            return file_id
        else:
            print(f"   ❌ Failed to create speech-music mix: {result.get('logs', 'Unknown error')}")
            return None
    
    def _build_speech_music_filter(self, duration: float, music_volume: float, 
                                 speech_volume: float, speech_segments: List[Dict[str, Any]]) -> str:
        """Build FFmpeg filter for speech-music mixing"""
        
        # Start with background music at reduced volume for full duration
        filters = [
            f"[1:a]volume={music_volume}[bg_music]"
        ]
        
        # Create speech volume adjustment
        filters.append(f"[0:a]volume={speech_volume}[speech]")
        
        # Mix speech and background music
        # The speech will naturally be present only during speech segments
        # Background music fills the entire duration
        filters.append("[bg_music][speech]amix=inputs=2:duration=first:dropout_transition=2[output]")
        
        return ";".join(filters)
    
    async def concatenate_segments(self, video_segments: List[Dict[str, Any]]) -> Optional[str]:
        """Concatenate multiple video segments"""
        
        if len(video_segments) == 1:
            return video_segments[0]["clip_id"]
        
        # Start with first two segments
        current_id = video_segments[0]["clip_id"]
        
        for i in range(1, len(video_segments)):
            next_id = video_segments[i]["clip_id"]
            
            print(f"   🔗 Concatenating segment {i+1}/{len(video_segments)}")
            
            # For the final concatenation, use finished directory
            if i == len(video_segments) - 1:
                result = await self._execute_ffmpeg_operation_finished(
                    current_id, "concatenate_simple", "mp4",
                    title="speech_music_video",
                    second_video=self.file_manager.resolve_id(next_id)
                )
            else:
                result = await self._execute_ffmpeg_operation(
                    current_id, "concatenate_simple", "mp4",
                    second_video=self.file_manager.resolve_id(next_id)
                )
            
            if not result["success"]:
                print(f"   ❌ Failed to concatenate segments: {result.get('error', 'Unknown error')}")
                return None
            
            current_id = result["output_file_id"]
        
        return current_id
    
    async def add_global_music(self, video_id: str, global_audio: Dict[str, Any], duration: float) -> Optional[str]:
        """Add global background music to entire video"""
        
        background_music = global_audio["backgroundMusic"]
        music_file_id = self.file_manager.get_id_by_name(background_music)
        
        if not music_file_id:
            print(f"   ❌ Global background music not found: {background_music}")
            return video_id  # Return original video if music not found
        
        print(f"   🎵 Adding global background music: {background_music}")
        
        # Replace audio with background music (final operation - use finished directory)
        result = await self._execute_ffmpeg_operation_finished(
            video_id, "replace_audio", "mp4",
            title="speech_video_with_music",
            audio_file=self.file_manager.resolve_id(music_file_id)
        )
        
        if result["success"]:
            print(f"   ✅ Global background music added successfully")
            return result["output_file_id"]
        else:
            print(f"   ❌ Failed to add global music: {result.get('error', 'Unknown error')}")
            return video_id  # Return original video if music replacement fails
    
    async def _execute_ffmpeg_operation(self, file_id: str, operation: str, extension: str, **params) -> Dict[str, Any]:
        """Execute FFMPEG operation directly using wrapper"""
        
        input_path = self.file_manager.resolve_id(file_id)
        if not input_path:
            return {"success": False, "error": f"File with ID '{file_id}' not found"}
        
        # Create output file
        output_file_id, output_path = self.file_manager.create_temp_file(extension)
        
        try:
            # Execute operation based on type
            if operation == "trim":
                start = params.get("start", 0)
                duration = params.get("duration", 10)
                
                cmd = [
                    SecurityConfig.FFMPEG_PATH,
                    "-i", str(input_path),
                    "-ss", str(start),
                    "-t", str(duration),
                    "-c:v", "libx264",  # Re-encode video for compatibility
                    "-c:a", "aac",      # Re-encode audio for compatibility
                    "-y",               # Overwrite output
                    str(output_path)
                ]
                
            elif operation == "extract_audio":
                cmd = [
                    SecurityConfig.FFMPEG_PATH,
                    "-i", str(input_path),
                    "-vn",  # No video
                    "-acodec", "pcm_s16le",  # High quality audio
                    "-ar", "44100",  # Sample rate
                    str(output_path)
                ]
                
            elif operation == "replace_audio":
                audio_file = params.get("audio_file")
                if not audio_file:
                    return {"success": False, "error": "audio_file parameter required"}
                
                cmd = [
                    SecurityConfig.FFMPEG_PATH,
                    "-i", str(input_path),
                    "-i", str(audio_file),
                    "-c:v", "copy",  # Copy video stream
                    "-c:a", "aac",   # Re-encode audio
                    "-map", "0:v:0", # Video from first input
                    "-map", "1:a:0", # Audio from second input
                    str(output_path)
                ]
                
            elif operation == "concatenate_simple":
                second_video = params.get("second_video")
                if not second_video:
                    return {"success": False, "error": "second_video parameter required"}
                
                # Create concat list file
                concat_file = self.temp_dir / f"concat_{self._generate_unique_id()}.txt"
                with open(concat_file, 'w') as f:
                    f.write(f"file '{input_path}'\n")
                    f.write(f"file '{second_video}'\n")
                
                cmd = [
                    SecurityConfig.FFMPEG_PATH,
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_file),
                    "-c:v", "libx264",  # Re-encode for compatibility
                    "-c:a", "aac",      # Re-encode audio
                    "-y",               # Overwrite output
                    str(output_path)
                ]
                
            else:
                return {"success": False, "error": f"Unsupported operation: {operation}"}
            
            # Execute command
            result = await self.ffmpeg_wrapper.execute_command(cmd, timeout=300)
            
            if result["success"] and output_path.exists():
                return {
                    "success": True,
                    "output_file_id": output_file_id,
                    "output_path": str(output_path),
                    "operation": operation
                }
            else:
                return {
                    "success": False,
                    "error": f"Operation {operation} failed: {result.get('logs', 'Unknown error')}"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Operation {operation} exception: {str(e)}"}
    
    async def _execute_ffmpeg_operation_finished(self, file_id: str, operation: str, extension: str, title: str = None, **params) -> Dict[str, Any]:
        """Execute FFMPEG operation and save output to finished directory"""
        
        input_path = self.file_manager.resolve_id(file_id)
        if not input_path:
            return {"success": False, "error": f"File with ID '{file_id}' not found"}
        
        # Create finished output file
        output_file_id, output_path = self.file_manager.create_finished_file(extension, title)
        
        try:
            # Execute operation based on type
            if operation == "concatenate_simple":
                second_video = params.get("second_video")
                if not second_video:
                    return {"success": False, "error": "second_video parameter required"}
                
                cmd = [
                    SecurityConfig.FFMPEG_PATH,
                    "-i", str(input_path),
                    "-i", str(second_video),
                    "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
                    "-map", "[v]",
                    "-map", "[a]",
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-y",
                    str(output_path)
                ]
            elif operation == "replace_audio":
                audio_file = params.get("audio_file")
                if not audio_file:
                    return {"success": False, "error": "audio_file parameter required"}
                
                cmd = [
                    SecurityConfig.FFMPEG_PATH,
                    "-i", str(input_path),
                    "-i", str(audio_file),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-shortest",
                    "-y",
                    str(output_path)
                ]
            else:
                return {"success": False, "error": f"Unsupported operation for finished files: {operation}"}
            
            # Execute command
            result = await self.ffmpeg_wrapper.execute_command(cmd, SecurityConfig.PROCESS_TIMEOUT)
            
            if result["success"]:
                return {
                    "success": True,
                    "output_file_id": output_file_id,
                    "file_path": str(output_path)
                }
            else:
                # Clean up failed output file
                output_path.unlink(missing_ok=True)
                return {
                    "success": False,
                    "error": f"Operation {operation} failed: {result.get('logs', 'Unknown error')}"
                }
                
        except Exception as e:
            # Clean up failed output file
            output_path.unlink(missing_ok=True)
            return {"success": False, "error": f"Operation {operation} exception: {str(e)}"}
    
    def _generate_unique_id(self) -> str:
        """Generate unique ID for temporary files"""
        import time
        import random
        return f"{int(time.time())}_{random.randint(1000, 9999)}"