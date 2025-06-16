"""
Komposition Processor - Bridge between beat-based komposition format and MCP video processing
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class BeatTiming:
    """Convert between beats and seconds"""
    bpm: int
    
    def beats_to_seconds(self, beats: float) -> float:
        """Convert beats to seconds: beats / (BPM / 60)"""
        return beats / (self.bpm / 60.0)
    
    def seconds_to_beats(self, seconds: float) -> float:
        """Convert seconds to beats: seconds * (BPM / 60)"""
        return seconds * (self.bpm / 60.0)

class KompositionProcessor:
    """Process komposition JSON files into MCP video operations"""
    
    def __init__(self, file_manager, ffmpeg_wrapper):
        self.file_manager = file_manager
        self.ffmpeg_wrapper = ffmpeg_wrapper
        
    async def load_komposition(self, komposition_path: str) -> Dict[str, Any]:
        """Load komposition JSON file"""
        with open(komposition_path, 'r') as f:
            return json.load(f)
    
    async def process_komposition(self, komposition_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing function: convert komposition to video"""
        
        # Initialize beat timing (handle both old and new format)
        bpm = komposition_data.get("bpm") or komposition_data.get("metadata", {}).get("bpm", 120)
        timing = BeatTiming(bpm)
        
        # Step 1: Extract and process all segments according to beat timing
        segment_clips = []
        for segment in komposition_data["segments"]:
            clip_id = await self.process_segment(segment, timing, komposition_data["sources"])
            segment_clips.append({
                "clip_id": clip_id,
                "segment_info": segment
            })
        
        # Step 2: Concatenate all segments
        final_video_id = await self.concatenate_segments(segment_clips)
        
        # Step 3: Add audio track
        audio_source = self.find_audio_source(komposition_data["sources"])
        if audio_source:
            audio_file_id = await self.resolve_source_to_file_id(audio_source)
            final_with_audio = await self.add_audio_track(final_video_id, audio_file_id, timing)
            return {
                "success": True,
                "output_file_id": final_with_audio,
                "composition_info": {
                    "total_duration_beats": komposition_data["beatpattern"]["tobeat"],
                    "total_duration_seconds": timing.beats_to_seconds(komposition_data["beatpattern"]["tobeat"]),
                    "bpm": bpm,
                    "segments_processed": len(segment_clips)
                }
            }
        
        return {
            "success": True,
            "output_file_id": final_video_id,
            "composition_info": {
                "total_duration_beats": komposition_data["beatpattern"]["tobeat"],
                "total_duration_seconds": timing.beats_to_seconds(komposition_data["beatpattern"]["tobeat"]),
                "bpm": bpm,
                "segments_processed": len(segment_clips)
            }
        }
    
    async def process_segment(self, segment: Dict[str, Any], timing: BeatTiming, sources: List[Dict[str, Any]]) -> str:
        """Process individual segment: extract, stretch to beat duration, handle media type"""
        
        # Calculate target duration in seconds
        target_duration_seconds = timing.beats_to_seconds(segment["duration"])
        
        # Find source for this segment
        source = self.find_source_by_id(segment.get("sourceid", ""), sources)
        
        if not source:
            # Try to match by segment description to available media
            source = await self.smart_match_segment_to_source(segment, sources)
        
        if not source:
            raise ValueError(f"No source found for segment: {segment['id']}")
        
        # Get file ID for source
        source_file_id = await self.resolve_source_to_file_id(source)
        
        # Handle different media types
        if source["mediatype"] == "image":
            # Convert image to video clip of target duration
            return await self.create_image_video(source_file_id, target_duration_seconds)
        
        elif source["mediatype"] == "video":
            # Extract and stretch video segment
            return await self.extract_and_stretch_video(
                source_file_id, 
                segment, 
                target_duration_seconds
            )
        
        else:
            raise ValueError(f"Unsupported media type: {source['mediatype']}")
    
    async def extract_and_stretch_video(self, source_file_id: str, segment: Dict[str, Any], target_duration: float) -> str:
        """Extract video segment and stretch/compress to target duration"""
        
        # Get original timing info
        source_timing = segment.get("source_timing", {})
        original_start = source_timing.get("original_start", 0)
        original_duration = source_timing.get("original_duration", target_duration)
        
        # Step 1: Extract the segment from source video
        try:
            from .video_operations import process_file_internal
        except ImportError:
            from video_operations import process_file_internal
            
        extracted_clip = await process_file_internal(
            input_file_id=source_file_id,
            operation="trim",
            output_extension="mp4",
            params_str=f"start={original_start} duration={original_duration}",
            file_manager=self.file_manager,
            ffmpeg=self.ffmpeg_wrapper
        )
        
        # Step 2: Calculate speed factor to fit target duration
        speed_factor = original_duration / target_duration
        
        # Step 3: Apply speed adjustment if needed
        if abs(speed_factor - 1.0) > 0.01:  # Only adjust if significant difference
            # Use setpts filter for video speed adjustment
            speed_adjusted = await process_file_internal(
                input_file_id=extracted_clip,
                operation="convert",
                output_extension="mp4",
                params_str=f"-vf 'setpts={speed_factor}*PTS' -af 'atempo={1/speed_factor}'",
                file_manager=self.file_manager,
                ffmpeg=self.ffmpeg_wrapper
            )
            return speed_adjusted
        
        return extracted_clip
    
    async def create_image_video(self, image_file_id: str, duration: float) -> str:
        """Convert image to video clip of specified duration"""
        try:
            from .video_operations import process_file_internal
        except ImportError:
            from video_operations import process_file_internal
        
        return await process_file_internal(
            input_file_id=image_file_id,
            operation="image_to_video",
            output_extension="mp4", 
            params_str=f"duration={duration}",
            file_manager=self.file_manager,
            ffmpeg=self.ffmpeg_wrapper
        )
    
    async def concatenate_segments(self, segment_clips: List[Dict[str, Any]]) -> str:
        """Concatenate all processed segments into final video"""
        try:
            from .video_operations import process_file_internal, process_file_as_finished
        except ImportError:
            from video_operations import process_file_internal, process_file_as_finished
        
        if len(segment_clips) < 2:
            return segment_clips[0]["clip_id"] if segment_clips else None
        
        # Start with first two clips (temp processing)
        current_result = await process_file_internal(
            input_file_id=segment_clips[0]["clip_id"],
            operation="concatenate_simple",
            output_extension="mp4",
            params_str=f"second_video={segment_clips[1]['clip_id']}",
            file_manager=self.file_manager,
            ffmpeg=self.ffmpeg_wrapper
        )
        
        # Add remaining clips one by one (temp processing)
        for i in range(2, len(segment_clips) - 1): # Iterate up to the second to last
            current_result = await process_file_internal(
                input_file_id=current_result,
                operation="concatenate_simple", 
                output_extension="mp4",
                params_str=f"second_video={segment_clips[i]['clip_id']}",
                file_manager=self.file_manager,
                ffmpeg=self.ffmpeg_wrapper
            )
        
        # Final concatenation goes to finished directory
        # If there are more than 2 segments, current_result holds the concatenation of first N-1 segments
        # The last segment is segment_clips[-1]['clip_id']
        # If there are exactly 2 segments, current_result is already the concatenation of these two.
        # The logic needs to handle the case where len(segment_clips) == 2 separately for the final step.

        if len(segment_clips) > 1: # Ensure there's at least one concatenation to make final
            # If len is 2, current_result is already the combination of the two.
            # If len > 2, current_result is combo of first N-1, and we add the last one.
            input_for_final = current_result
            second_video_for_final = segment_clips[-1]['clip_id']
            
            if len(segment_clips) == 2: # current_result is already the result of concatenating the two.
                                        # We need to re-process them into the finished directory.
                input_for_final = segment_clips[0]['clip_id']
                second_video_for_final = segment_clips[1]['clip_id']


            final_result = await process_file_as_finished(
                input_file_id=input_for_final,
                operation="concatenate_simple",
                output_extension="mp4",
                params_str=f"second_video={second_video_for_final}",
                file_manager=self.file_manager,
                ffmpeg=self.ffmpeg_wrapper,
                title="music_video"
            )
        else: # Only one segment, no concatenation needed, but should be "finished"
             # This case should ideally be handled by the caller, but for robustness:
             # We can't just use process_file_as_finished without an operation.
             # A "copy" or "convert" operation would be needed.
             # For now, assume len(segment_clips) >= 1 and if 1, it's returned by the initial check.
             # If the goal is to ensure the single clip is in "finished", it needs a different path.
             # The current logic implies concatenation, so a single clip means no concat.
             # Let's stick to the original logic: if len < 2, returns the clip_id (which is temp).
             # The caller (process_komposition) then handles audio addition which uses process_file_as_finished.
             # So, this function should primarily return a temp file if intermediate,
             # or the final file if it's the last step of concatenation.
             # The current logic for process_komposition seems to expect the *final concatenated video* (silent)
             # to be returned from here, which then has audio added.
             # The original code's final concatenation step was always to `process_file_as_finished`.
             # Let's simplify: if only one segment, it's not concatenated. If multiple, the final step is _as_finished.

            # Re-evaluating: The loop for i in range(2, len(segment_clips) -1) is for intermediate.
            # The final step should always use process_file_as_finished.
            if len(segment_clips) == 2: # Concatenate first two directly to finished
                 final_result = await process_file_as_finished(
                    input_file_id=segment_clips[0]["clip_id"],
                    operation="concatenate_simple",
                    output_extension="mp4",
                    params_str=f"second_video={segment_clips[1]['clip_id']}",
                    file_manager=self.file_manager,
                    ffmpeg=self.ffmpeg_wrapper,
                    title="music_video"
                )
            elif len(segment_clips) > 2: # More than 2, current_result is temp, concat with last one to finished
                final_result = await process_file_as_finished(
                    input_file_id=current_result, # This is temp from previous concats
                    operation="concatenate_simple",
                    output_extension="mp4",
                    params_str=f"second_video={segment_clips[-1]['clip_id']}",
                    file_manager=self.file_manager,
                    ffmpeg=self.ffmpeg_wrapper,
                    title="music_video"
                )
            else: # len(segment_clips) must be 1 or 0, handled by initial check
                final_result = segment_clips[0]["clip_id"] if segment_clips else None


        return final_result
    
    async def add_audio_track(self, video_file_id: str, audio_file_id: str, timing: BeatTiming) -> str:
        """Add audio track to video, trimming audio to video length"""
        try:
            from .video_operations import process_file_as_finished
        except ImportError:
            from video_operations import process_file_as_finished
        
        return await process_file_as_finished(
            input_file_id=video_file_id,
            operation="replace_audio",
            output_extension="mp4",
            params_str=f"audio_file={audio_file_id}",
            file_manager=self.file_manager,
            ffmpeg=self.ffmpeg_wrapper,
            title="music_video_with_audio"
        )
    
    async def smart_match_segment_to_source(self, segment: Dict[str, Any], sources: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Intelligently match segment description to available sources"""
        segment_id = segment["id"].lower()
        
        # Simple keyword matching
        if "dagny" in segment_id or "baybay" in segment_id:
            return self.find_source_by_keyword(sources, ["dagny", "baybay"])
        elif "boat" in segment_id or "image" in segment_id:
            return self.find_source_by_mediatype(sources, "image")
        elif "scene" in segment_id or "video" in segment_id:
            # Return first available video source
            return self.find_source_by_mediatype(sources, "video")
        
        return None
    
    def find_source_by_keyword(self, sources: List[Dict[str, Any]], keywords: List[str]) -> Optional[Dict[str, Any]]:
        """Find source containing any of the keywords"""
        for source in sources:
            source_id = source["id"].lower()
            if any(keyword in source_id for keyword in keywords):
                return source
        return None
    
    def find_source_by_mediatype(self, sources: List[Dict[str, Any]], mediatype: str) -> Optional[Dict[str, Any]]:
        """Find first source of specified media type"""
        for source in sources:
            if source.get("mediatype") == mediatype:
                return source
        return None
    
    def find_source_by_id(self, source_id: str, sources: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find source by exact ID match"""
        for source in sources:
            if source["id"] == source_id:
                return source
        return None
    
    def find_audio_source(self, sources: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find audio source for background track"""
        return self.find_source_by_mediatype(sources, "audio")
    
    async def resolve_source_to_file_id(self, source: Dict[str, Any]) -> str:
        """Convert source URL/path to MCP file ID"""
        # Handle file:// URLs
        url = source["url"]
        if url.startswith("file://"):
            filename = url[7:]  # Remove "file://" prefix
            
            # Find matching file in source directory
            try:
                from .config import SecurityConfig
            except ImportError:
                from config import SecurityConfig
            source_dir = SecurityConfig.SOURCE_DIR
            
            for file_path in source_dir.glob("*"):
                if file_path.name == filename and file_path.is_file():
                    # Register the file and return its ID
                    return self.file_manager.register_file(file_path)
            
            raise FileNotFoundError(f"Source file not found: {filename}")
        
        # Handle other URL types (would need downloading)
        raise NotImplementedError(f"URL type not supported yet: {url}")
