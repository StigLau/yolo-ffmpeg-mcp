import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import random

@dataclass
class VideoSegment:
    """Represents a video segment for the music video"""
    file_id: str
    start_time: float
    duration: float
    scene_description: str
    visual_score: float
    beat_start: int
    beat_end: int

@dataclass
class MusicVideoConfig:
    """Configuration for music video generation"""
    bpm: int = 120
    total_beats: int = 128
    beats_per_segment: int = 8
    target_resolution: str = "1920x1080"
    apply_leica_look: bool = True
    leica_style: str = "leica_look"  # or "leica_look_enhanced"

class MusicVideoBuilder:
    """Builds music videos using MCP server operations"""
    
    def __init__(self, mcp_client=None):
        self.mcp_client = mcp_client
        self.config = MusicVideoConfig()
        
    def calculate_timing(self) -> Dict[str, float]:
        """Calculate timing parameters for the music video"""
        seconds_per_beat = 60.0 / self.config.bpm
        segment_duration = self.config.beats_per_segment * seconds_per_beat
        total_duration = self.config.total_beats * seconds_per_beat
        num_segments = self.config.total_beats // self.config.beats_per_segment
        
        return {
            "seconds_per_beat": seconds_per_beat,
            "segment_duration": segment_duration,
            "total_duration": total_duration,
            "num_segments": num_segments
        }
    
    async def discover_source_files(self) -> Dict[str, List[str]]:
        """Discover available video and audio files"""
        if not self.mcp_client:
            # Mock data for testing
            return {
                "video_files": ["video1", "video2", "video3"],
                "audio_files": ["audio1", "audio2"]
            }
            
        try:
            files_result = await self.mcp_client.call_tool("list_files")
            files = files_result.get("files", {})
            
            video_files = []
            audio_files = []
            
            for file_id, file_info in files.items():
                file_type = file_info.get("type", "").lower()
                if file_type in ["video", "mp4", "mov", "avi", "mkv"]:
                    video_files.append(file_id)
                elif file_type in ["audio", "mp3", "wav", "m4a", "aac"]:
                    audio_files.append(file_id)
                    
            return {
                "video_files": video_files,
                "audio_files": audio_files
            }
            
        except Exception as e:
            print(f"Error discovering files: {e}")
            return {"video_files": [], "audio_files": []}
    
    async def analyze_video_scenes(self, video_file_id: str) -> List[Dict[str, Any]]:
        """Analyze video content to extract scene information"""
        if not self.mcp_client:
            # Mock scene data
            return [
                {"start": 0.0, "end": 5.0, "description": "Opening scene", "visual_score": 0.8},
                {"start": 5.0, "end": 10.0, "description": "Action sequence", "visual_score": 0.9},
                {"start": 10.0, "end": 15.0, "description": "Close-up shots", "visual_score": 0.7},
            ]
            
        try:
            analysis_result = await self.mcp_client.call_tool(
                "analyze_video_content", 
                file_id=video_file_id,
                force_reanalysis=False
            )
            
            if not analysis_result.get("success"):
                return []
                
            scenes = analysis_result.get("analysis", {}).get("scenes", [])
            processed_scenes = []
            
            for scene in scenes:
                processed_scenes.append({
                    "start": scene.get("start_time", 0.0),
                    "end": scene.get("end_time", 0.0),
                    "description": scene.get("description", "Scene"),
                    "visual_score": scene.get("visual_score", 0.5),
                    "objects": scene.get("detected_objects", []),
                    "characteristics": scene.get("frame_characteristics", [])
                })
                
            return processed_scenes
            
        except Exception as e:
            print(f"Error analyzing video {video_file_id}: {e}")
            return []
    
    def select_best_segments(self, all_scenes: Dict[str, List[Dict[str, Any]]], timing: Dict[str, float]) -> List[VideoSegment]:
        """Select the best video segments for the music video"""
        segments = []
        segment_duration = timing["segment_duration"]
        num_segments = int(timing["num_segments"])
        
        # Flatten all scenes with file_id reference
        all_available_scenes = []
        for file_id, scenes in all_scenes.items():
            for scene in scenes:
                scene_duration = scene["end"] - scene["start"]
                if scene_duration >= segment_duration * 0.8:  # Must be at least 80% of target duration
                    all_available_scenes.append({
                        "file_id": file_id,
                        "scene": scene,
                        "duration": scene_duration
                    })
        
        # Sort by visual score (best first)
        all_available_scenes.sort(key=lambda x: x["scene"]["visual_score"], reverse=True)
        
        # Select segments, trying to use different files for variety
        used_files = set()
        selected_scenes = []
        
        # First pass: select best scenes from different files
        for scene_data in all_available_scenes:
            if len(selected_scenes) >= num_segments:
                break
                
            file_id = scene_data["file_id"]
            if file_id not in used_files:
                selected_scenes.append(scene_data)
                used_files.add(file_id)
        
        # Second pass: fill remaining slots with any good scenes
        for scene_data in all_available_scenes:
            if len(selected_scenes) >= num_segments:
                break
                
            if scene_data not in selected_scenes:
                selected_scenes.append(scene_data)
        
        # Convert to VideoSegment objects
        for i, scene_data in enumerate(selected_scenes[:num_segments]):
            scene = scene_data["scene"]
            beat_start = i * self.config.beats_per_segment
            beat_end = beat_start + self.config.beats_per_segment
            
            segments.append(VideoSegment(
                file_id=scene_data["file_id"],
                start_time=scene["start"],
                duration=segment_duration,
                scene_description=scene["description"],
                visual_score=scene["visual_score"],
                beat_start=beat_start,
                beat_end=beat_end
            ))
        
        return segments
    
    def choose_backing_music(self, audio_files: List[str]) -> Optional[str]:
        """Choose the best audio file for backing music"""
        if not audio_files:
            return None
            
        # For now, just pick the first one
        # In a real implementation, you might analyze tempo, genre, etc.
        return audio_files[0]
    
    async def create_segment_clips(self, segments: List[VideoSegment]) -> List[str]:
        """Create individual video clips for each segment with Leica look"""
        if not self.mcp_client:
            return [f"mock_clip_{i}" for i in range(len(segments))]
            
        clip_ids = []
        
        for i, segment in enumerate(segments):
            try:
                # Create trimmed clip with Leica look applied
                result = await self.mcp_client.call_tool(
                    "process_file",
                    input_file_id=segment.file_id,
                    operation="apply_leica_and_trim",
                    output_extension="mp4",
                    params=f"start={segment.start_time} duration={segment.duration}"
                )
                
                if result.get("success"):
                    clip_ids.append(result["output_file_id"])
                    print(f"Created segment {i+1}/{len(segments)}: {segment.scene_description}")
                else:
                    print(f"Failed to create segment {i+1}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"Error creating segment {i+1}: {e}")
                
        return clip_ids
    
    async def concatenate_clips(self, clip_ids: List[str]) -> Optional[str]:
        """Concatenate all clips into final video"""
        if not self.mcp_client or len(clip_ids) < 2:
            return "mock_final_video" if not self.mcp_client else None
            
        try:
            # Start with first two clips
            current_video = clip_ids[0]
            
            for i in range(1, len(clip_ids)):
                result = await self.mcp_client.call_tool(
                    "process_file",
                    input_file_id=current_video,
                    operation="concatenate_simple",
                    output_extension="mp4",
                    params=f"second_video={clip_ids[i]}"
                )
                
                if result.get("success"):
                    current_video = result["output_file_id"]
                    print(f"Concatenated clip {i+1}/{len(clip_ids)}")
                else:
                    print(f"Failed to concatenate clip {i+1}: {result.get('error', 'Unknown error')}")
                    return None
                    
            return current_video
            
        except Exception as e:
            print(f"Error concatenating clips: {e}")
            return None
    
    async def add_backing_music(self, video_file_id: str, audio_file_id: str) -> Optional[str]:
        """Add backing music to the final video"""
        if not self.mcp_client:
            return "mock_final_with_music"
            
        try:
            result = await self.mcp_client.call_tool(
                "process_file",
                input_file_id=video_file_id,
                operation="replace_audio",
                output_extension="mp4",
                params=f"audio_file={audio_file_id}"
            )
            
            if result.get("success"):
                print("Successfully added backing music")
                return result["output_file_id"]
            else:
                print(f"Failed to add backing music: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"Error adding backing music: {e}")
            return None
    
    async def generate_komposition_json(self, segments: List[VideoSegment], audio_file_id: str, output_path: str = "music_video_komposition.json"):
        """Generate a komposition JSON file for the music video"""
        timing = self.calculate_timing()
        
        komposition = {
            "title": "Generated Music Video",
            "bpm": self.config.bpm,
            "resolution": self.config.target_resolution,
            "total_beats": self.config.total_beats,
            "duration_seconds": timing["total_duration"],
            "sources": [],
            "segments": [],
            "audio": {
                "file_id": audio_file_id,
                "type": "backing_track"
            },
            "effects": {
                "global": [
                    {
                        "type": self.config.leica_style,
                        "applies_to": "all_segments"
                    }
                ]
            }
        }
        
        # Add source files
        used_files = set()
        for segment in segments:
            if segment.file_id not in used_files:
                komposition["sources"].append({
                    "id": segment.file_id,
                    "type": "video",
                    "mediatype": "video"
                })
                used_files.add(segment.file_id)
        
        # Add audio source
        komposition["sources"].append({
            "id": audio_file_id,
            "type": "audio",
            "mediatype": "audio"
        })
        
        # Add segments
        for segment in segments:
            komposition["segments"].append({
                "beat_start": segment.beat_start,
                "beat_end": segment.beat_end,
                "source_ref": segment.file_id,
                "start_time": segment.start_time,
                "duration": segment.duration,
                "description": segment.scene_description,
                "visual_score": segment.visual_score
            })
        
        # Save komposition file
        with open(output_path, 'w') as f:
            json.dump(komposition, f, indent=2)
            
        print(f"Generated komposition file: {output_path}")
        return output_path
    
    async def build_music_video(self, custom_config: Optional[MusicVideoConfig] = None) -> Dict[str, Any]:
        """Main method to build the complete music video"""
        if custom_config:
            self.config = custom_config
            
        print(f"Building music video: {self.config.bpm} BPM, {self.config.total_beats} beats")
        
        # Calculate timing
        timing = self.calculate_timing()
        print(f"Video will be {timing['total_duration']:.1f} seconds with {timing['num_segments']} segments")
        
        # Discover source files
        print("Discovering source files...")
        source_files = await self.discover_source_files()
        
        if not source_files["video_files"]:
            return {"success": False, "error": "No video files found"}
        if not source_files["audio_files"]:
            return {"success": False, "error": "No audio files found"}
            
        print(f"Found {len(source_files['video_files'])} video files and {len(source_files['audio_files'])} audio files")
        
        # Analyze video content
        print("Analyzing video content...")
        all_scenes = {}
        for video_file in source_files["video_files"]:
            scenes = await self.analyze_video_scenes(video_file)
            if scenes:
                all_scenes[video_file] = scenes
                print(f"  {video_file}: {len(scenes)} scenes")
        
        if not all_scenes:
            return {"success": False, "error": "No usable video scenes found"}
        
        # Select best segments
        print("Selecting best video segments...")
        segments = self.select_best_segments(all_scenes, timing)
        
        if len(segments) < timing["num_segments"]:
            print(f"Warning: Only found {len(segments)} segments, needed {timing['num_segments']}")
        
        # Choose backing music
        backing_music = self.choose_backing_music(source_files["audio_files"])
        print(f"Selected backing music: {backing_music}")
        
        # Generate komposition file
        komposition_path = await self.generate_komposition_json(segments, backing_music)
        
        # Create video clips
        print("Creating video segments with Leica look...")
        clip_ids = await self.create_segment_clips(segments)
        
        if not clip_ids:
            return {"success": False, "error": "Failed to create video clips"}
        
        # Concatenate clips
        print("Concatenating video segments...")
        final_video = await self.concatenate_clips(clip_ids)
        
        if not final_video:
            return {"success": False, "error": "Failed to concatenate video clips"}
        
        # Add backing music
        print("Adding backing music...")
        final_with_music = await self.add_backing_music(final_video, backing_music)
        
        if not final_with_music:
            return {"success": False, "error": "Failed to add backing music"}
        
        return {
            "success": True,
            "final_video_id": final_with_music,
            "komposition_file": komposition_path,
            "segments_created": len(clip_ids),
            "total_duration": timing["total_duration"],
            "config": {
                "bpm": self.config.bpm,
                "total_beats": self.config.total_beats,
                "beats_per_segment": self.config.beats_per_segment,
                "leica_style": self.config.leica_style
            }
        }

# Example usage function
async def create_120bpm_music_video(mcp_client=None):
    """Create a 120 BPM, 128-beat music video with Leica look"""
    builder = MusicVideoBuilder(mcp_client)
    
    config = MusicVideoConfig(
        bpm=120,
        total_beats=128,
        beats_per_segment=8,
        target_resolution="1920x1080",
        apply_leica_look=True,
        leica_style="leica_look"
    )
    
    result = await builder.build_music_video(config)
    
    if result["success"]:
        print(f"\n✅ Music video created successfully!")
        print(f"Final video ID: {result['final_video_id']}")
        print(f"Duration: {result['total_duration']:.1f} seconds")
        print(f"Segments: {result['segments_created']}")
        print(f"Komposition file: {result['komposition_file']}")
    else:
        print(f"\n❌ Failed to create music video: {result['error']}")
    
    return result

if __name__ == "__main__":
    # For testing without MCP client
    asyncio.run(create_120bpm_music_video())
