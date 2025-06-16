"""
Transition Effects Processor - Advanced visual effects and transitions system
Based on the specifications from documents/Describing_effects.md
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass 
class EffectNode:
    """Represents a node in the effects tree"""
    effect_id: str
    effect_type: str
    parameters: Dict[str, Any]
    children: List['EffectNode']
    applies_to: List[Dict[str, Any]]
    
class TransitionProcessor:
    """Processes komposition files with advanced transition effects tree"""
    
    def __init__(self, file_manager, ffmpeg_wrapper):
        self.file_manager = file_manager
        self.ffmpeg_wrapper = ffmpeg_wrapper
        
    async def load_komposition_with_effects(self, komposition_path: str) -> Dict[str, Any]:
        """Load komposition JSON with effects tree"""
        with open(komposition_path, 'r') as f:
            return json.load(f)
    
    async def process_effects_tree(self, komposition_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process komposition with advanced effects tree"""
        
        # Extract basic info
        bpm = komposition_data["bpm"]
        segments = komposition_data["segments"]
        effects_tree = komposition_data.get("effects_tree", {})
        
        # Convert beat timing
        beats_per_second = bpm / 60.0
        
        # Step 1: Process all segments and prepare base clips
        segment_clips = {}
        for segment in segments:
            segment_id = segment["segment_id"] 
            source_ref = segment["source_ref"]
            
            # Find source file for this segment
            source_file_id = await self.resolve_source_ref(source_ref, komposition_data.get("sources", []))
            
            # Extract segment timing
            start_beat = segment.get("start_beat", 0)
            end_beat = segment.get("end_beat", 16)
            duration_beats = end_beat - start_beat
            duration_seconds = duration_beats / beats_per_second
            
            # Create base clip for this segment
            if segment.get("source_timing"):
                source_timing = segment["source_timing"]
                original_start = source_timing.get("original_start", 0)
                original_duration = source_timing.get("original_duration", duration_seconds)
                
                # Extract and potentially stretch the segment
                base_clip = await self.extract_segment(
                    source_file_id, 
                    original_start, 
                    original_duration,
                    duration_seconds
                )
            else:
                # Use full duration as-is
                base_clip = source_file_id
                
            segment_clips[segment_id] = {
                "file_id": base_clip,
                "duration_seconds": duration_seconds,
                "start_beat": start_beat,
                "end_beat": end_beat
            }
        
        # Step 2: Process effects tree
        if effects_tree:
            final_output = await self.process_effect_node(effects_tree, segment_clips, beats_per_second)
            
            return {
                "success": True,
                "output_file_id": final_output,
                "effects_applied": True,
                "composition_info": {
                    "total_segments": len(segments),
                    "bpm": bpm,
                    "effects_schema_version": komposition_data.get("effects_schema_version", "1.0")
                }
            }
        else:
            # Fallback to simple concatenation if no effects tree
            return await self.simple_concatenation(segment_clips)
    
    async def process_effect_node(self, effect_node: Dict[str, Any], segment_clips: Dict[str, Any], beats_per_second: float) -> str:
        """Process a single effect node recursively (post-order traversal)"""
        
        effect_id = effect_node["effect_id"]
        effect_type = effect_node["type"]
        parameters = effect_node.get("parameters", {})
        children = effect_node.get("children", [])
        applies_to = effect_node.get("applies_to", [])
        
        # Step 1: Process all children first (post-order traversal)
        child_outputs = []
        for child in children:
            child_output = await self.process_effect_node(child, segment_clips, beats_per_second)
            child_outputs.append(child_output)
        
        # Step 2: Apply current effect
        if effect_type == "passthrough":
            # Root effect - just return the first child or concatenate multiple children
            if len(child_outputs) == 1:
                return child_outputs[0]
            elif len(child_outputs) > 1:
                return await self.concatenate_clips(child_outputs)
            else:
                # Apply to segments directly
                return await self.apply_to_segments(applies_to, segment_clips)
                
        elif effect_type == "gradient_wipe":
            return await self.apply_gradient_wipe(applies_to, segment_clips, parameters, beats_per_second)
            
        elif effect_type == "crossfade_transition":
            return await self.apply_crossfade(applies_to, segment_clips, parameters, beats_per_second)
            
        elif effect_type == "opacity_transition":
            return await self.apply_opacity_transition(applies_to, segment_clips, parameters, beats_per_second)
            
        else:
            raise ValueError(f"Unknown effect type: {effect_type}")
    
    async def apply_gradient_wipe(self, applies_to: List[Dict[str, Any]], segment_clips: Dict[str, Any], 
                                 parameters: Dict[str, Any], beats_per_second: float) -> str:
        """Apply gradient wipe transition between two clips"""
        
        # Get the two clips to transition between
        if len(applies_to) != 2:
            raise ValueError("Gradient wipe requires exactly 2 input clips")
        
        first_clip = await self.resolve_applies_to(applies_to[0], segment_clips)
        second_clip = await self.resolve_applies_to(applies_to[1], segment_clips) 
        
        # Calculate timing
        duration_beats = parameters.get("duration_beats", 2)
        start_offset_beats = parameters.get("start_offset_beats", -1)
        
        duration_seconds = duration_beats / beats_per_second
        offset_seconds = abs(start_offset_beats) / beats_per_second
        
        # Apply gradient wipe using FFmpeg xfade
        try:
            from .video_operations import process_file_internal
        except ImportError:
            from video_operations import process_file_internal
        
        result = await process_file_internal(
            input_file_id=first_clip,
            operation="gradient_wipe", 
            output_extension="mp4",
            params_str=f"second_video={second_clip} duration={duration_seconds} offset={offset_seconds}",
            file_manager=self.file_manager,
            ffmpeg=self.ffmpeg_wrapper
        )
        
        return result
    
    async def apply_crossfade(self, applies_to: List[Dict[str, Any]], segment_clips: Dict[str, Any],
                             parameters: Dict[str, Any], beats_per_second: float) -> str:
        """Apply crossfade transition between two clips"""
        
        if len(applies_to) != 2:
            raise ValueError("Crossfade requires exactly 2 input clips")
            
        first_clip = await self.resolve_applies_to(applies_to[0], segment_clips)
        second_clip = await self.resolve_applies_to(applies_to[1], segment_clips)
        
        # Calculate timing
        duration_beats = parameters.get("duration_beats", 2) 
        duration_seconds = duration_beats / beats_per_second
        offset_seconds = parameters.get("offset_seconds", 0) # This param might not be used by crossfade_transition op
        
        try:
            from .video_operations import process_file_internal
        except ImportError:
            from video_operations import process_file_internal
        
        result = await process_file_internal(
            input_file_id=first_clip,
            operation="crossfade_transition", # Assuming this operation exists and handles these params
            output_extension="mp4", 
            params_str=f"second_video={second_clip} duration={duration_seconds} offset={offset_seconds}",
            file_manager=self.file_manager,
            ffmpeg=self.ffmpeg_wrapper
        )
        
        return result
    
    async def apply_opacity_transition(self, applies_to: List[Dict[str, Any]], segment_clips: Dict[str, Any],
                                      parameters: Dict[str, Any], beats_per_second: float) -> str:
        """Apply opacity-based transition"""
        
        if len(applies_to) != 2:
            raise ValueError("Opacity transition requires exactly 2 input clips")
            
        first_clip = await self.resolve_applies_to(applies_to[0], segment_clips)
        second_clip = await self.resolve_applies_to(applies_to[1], segment_clips)
        
        opacity = parameters.get("opacity", 0.5)
        # Note: duration/offset might be relevant for opacity transitions too, depending on FFMPEG op
        
        try:
            from .video_operations import process_file_internal
        except ImportError:
            from video_operations import process_file_internal
        
        result = await process_file_internal(
            input_file_id=first_clip,
            operation="opacity_transition", # Assuming this operation exists
            output_extension="mp4",
            params_str=f"second_video={second_clip} opacity={opacity}",
            file_manager=self.file_manager,
            ffmpeg=self.ffmpeg_wrapper
        )
        
        return result
    
    async def resolve_applies_to(self, applies_to_item: Dict[str, Any], segment_clips: Dict[str, Any]) -> str:
        """Resolve an applies_to reference to a file ID"""
        
        if applies_to_item["type"] == "segment":
            segment_id = applies_to_item["id"]
            if segment_id not in segment_clips:
                raise ValueError(f"Segment not found: {segment_id}")
            return segment_clips[segment_id]["file_id"]
            
        elif applies_to_item["type"] == "effect_output":
            # For now, assume this is handled in the recursive processing
            effect_id = applies_to_item["id"]
            raise NotImplementedError("Effect output references not yet implemented")
            
        else:
            raise ValueError(f"Unknown applies_to type: {applies_to_item['type']}")
    
    async def extract_segment(self, source_file_id: str, start_seconds: float, 
                             duration_seconds: float, target_duration: float) -> str:
        """Extract and potentially stretch a video segment"""
        
        try:
            from .video_operations import process_file_internal
        except ImportError:
            from video_operations import process_file_internal
        
        # Step 1: Extract the segment
        extracted = await process_file_internal(
            input_file_id=source_file_id,
            operation="trim",
            output_extension="mp4", 
            params_str=f"start={start_seconds} duration={duration_seconds}",
            file_manager=self.file_manager,
            ffmpeg=self.ffmpeg_wrapper
        )
        
        # Step 2: Stretch if needed
        if abs(duration_seconds - target_duration) > 0.01:
            speed_factor = duration_seconds / target_duration
            
            stretched = await process_file_internal(
                input_file_id=extracted,
                operation="convert", # Assuming 'convert' can take filter params like this
                output_extension="mp4",
                params_str=f"-vf 'setpts={speed_factor}*PTS' -af 'atempo={1/speed_factor}'",
                file_manager=self.file_manager,
                ffmpeg=self.ffmpeg_wrapper
            )
            return stretched
            
        return extracted
    
    async def resolve_source_ref(self, source_ref: str, sources: List[Dict[str, Any]]) -> str:
        """Resolve source reference to file ID"""
        
        # Find the source by reference
        for source in sources:
            if source["id"] == source_ref:
                return await self.resolve_source_to_file_id(source)
        
        raise ValueError(f"Source reference not found: {source_ref}")
    
    async def resolve_source_to_file_id(self, source: Dict[str, Any]) -> str:
        """Convert source URL/path to MCP file ID"""
        url = source["url"]
        if url.startswith("file://"):
            filename = url[7:]  # Remove "file://" prefix
            
            try:
                from .config import SecurityConfig
            except ImportError:
                from config import SecurityConfig
            source_dir = SecurityConfig.SOURCE_DIR
            
            for file_path in source_dir.glob("*"):
                if file_path.name == filename and file_path.is_file():
                    return self.file_manager.register_file(file_path)
            
            raise FileNotFoundError(f"Source file not found: {filename}")
        
        raise NotImplementedError(f"URL type not supported yet: {url}")
    
    async def concatenate_clips(self, clip_ids: List[str]) -> str:
        """Concatenate multiple clips"""
        if len(clip_ids) < 2:
            return clip_ids[0] if clip_ids else None
            
        try:
            from .video_operations import process_file_internal
        except ImportError:
            from video_operations import process_file_internal
        
        # Start with first two clips
        current_result = await process_file_internal(
            input_file_id=clip_ids[0],
            operation="concatenate_simple",
            output_extension="mp4",
            params_str=f"second_video={clip_ids[1]}",
            file_manager=self.file_manager,
            ffmpeg=self.ffmpeg_wrapper
        )
        
        # Add remaining clips
        for i in range(2, len(clip_ids)):
            current_result = await process_file_internal(
                input_file_id=current_result,
                operation="concatenate_simple", 
                output_extension="mp4",
                params_str=f"second_video={clip_ids[i]}",
                file_manager=self.file_manager,
                ffmpeg=self.ffmpeg_wrapper
            )
        
        return current_result
    
    async def apply_to_segments(self, applies_to: List[Dict[str, Any]], segment_clips: Dict[str, Any]) -> str:
        """Apply effect to specified segments"""
        
        clip_ids = []
        for item in applies_to:
            clip_id = await self.resolve_applies_to(item, segment_clips)
            clip_ids.append(clip_id)
        
        return await self.concatenate_clips(clip_ids)
    
    async def simple_concatenation(self, segment_clips: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: simple concatenation without effects"""
        
        # Sort segments by start beat
        sorted_segments = sorted(segment_clips.items(), key=lambda x: x[1]["start_beat"])
        clip_ids = [clip["file_id"] for _, clip in sorted_segments]
        
        final_output = await self.concatenate_clips(clip_ids)
        
        return {
            "success": True,
            "output_file_id": final_output,
            "effects_applied": False,
            "composition_info": {
                "total_segments": len(segment_clips),
                "effects_schema_version": "1.0"
            }
        }
