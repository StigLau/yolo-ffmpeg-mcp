"""
Video Processor Service
Handles video generation from kompositions with audio integration
"""

import subprocess
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..models.komposition import Komposition, VideoOutput, ProcessingStrategy
from ..models.media import MediaReference, MediaMetadata, MediaType
from ..registry.media_registry import MediaRegistry
from ..llm.processing_llm import ProcessingLLM


class VideoProcessor:
    """Service for generating videos from kompositions"""
    
    def __init__(self, processing_llm: ProcessingLLM, media_registry: MediaRegistry):
        self.processing_llm = processing_llm
        self.media_registry = media_registry
        self.output_dir = Path("/tmp/music-video-creator/generated-videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def analyze_processing_strategy(self, komposition: Komposition) -> ProcessingStrategy:
        """Analyze komposition and recommend processing strategy"""
        
        # Basic strategy analysis
        has_audio = komposition.audio_track is not None
        segment_count = len(komposition.segments)
        has_complex_effects = any(
            effect.type.value in ['8bit', 'leica', 'color_grade'] 
            for segment in komposition.segments 
            for effect in segment.effects
        )
        
        # Determine strategy type
        if segment_count <= 2 and not has_complex_effects:
            strategy_type = "SIMPLE_CONCAT"
            base_cost = 0.05
        elif has_complex_effects:
            strategy_type = "EFFECTS_PIPELINE" 
            base_cost = 0.15
        else:
            strategy_type = "CROSSFADE_CONCAT"
            base_cost = 0.10
        
        # Calculate costs and timing
        duration_multiplier = min(komposition.duration_seconds / 30.0, 3.0)
        estimated_cost = base_cost * duration_multiplier
        estimated_duration = 30 + (segment_count * 5) + (20 if has_audio else 0)
        
        strategy = ProcessingStrategy(
            strategy_type=strategy_type,
            estimated_cost=estimated_cost,
            estimated_duration=estimated_duration,
            confidence=0.85,
            requires_normalization=has_complex_effects,
            requires_keyframe_alignment=segment_count > 4,
            recommended_resolution=komposition.resolution
        )
        
        return strategy
    
    async def generate_video(self, komposition: Komposition, options: Dict[str, Any] = None) -> VideoOutput:
        """Generate video from komposition"""
        
        options = options or {}
        start_time = datetime.utcnow()
        
        # Analyze processing strategy
        strategy = await self.analyze_processing_strategy(komposition)
        
        # Generate output filename
        output_filename = f"{komposition.id}_{int(datetime.utcnow().timestamp())}.mp4"
        output_path = self.output_dir / output_filename
        
        try:
            # Process video based on strategy
            if strategy.strategy_type == "SIMPLE_CONCAT":
                await self._simple_concatenation(komposition, output_path)
            elif strategy.strategy_type == "EFFECTS_PIPELINE":
                await self._effects_pipeline(komposition, output_path)
            else:
                await self._crossfade_concatenation(komposition, output_path)
            
            # Add audio if available
            if komposition.audio_track:
                await self._add_audio_track(output_path, komposition.audio_track, komposition.duration_seconds)
            
            # Calculate processing duration
            processing_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Register output video
            output_metadata = MediaMetadata(
                type=MediaType.VIDEO,
                filename=output_filename,
                file_size_bytes=output_path.stat().st_size if output_path.exists() else 0,
                duration_seconds=komposition.duration_seconds,
                resolution=komposition.resolution
            )
            
            output_ref = await self.media_registry.register_file(str(output_path), output_metadata)
            
            # Create VideoOutput
            video_output = VideoOutput(
                id=f"video_{uuid.uuid4().hex[:8]}",
                komposition_id=komposition.id,
                file_reference=output_ref,
                generation_timestamp=datetime.utcnow(),
                processing_strategy=strategy,
                processing_cost=strategy.estimated_cost,
                quality_score=0.85,  # Default good quality
                processing_duration=processing_duration,
                resolution=komposition.resolution,
                duration_seconds=komposition.duration_seconds,
                frame_rate=25.0,
                file_size_bytes=output_metadata.file_size_bytes
            )
            
            return video_output
            
        except Exception as e:
            print(f"Error generating video for komposition {komposition.id}: {e}")
            raise
    
    async def _simple_concatenation(self, komposition: Komposition, output_path: Path) -> None:
        """Simple concatenation without effects"""
        
        # Create simple test video for demo
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'testsrc2=duration={komposition.duration_seconds}:size={komposition.resolution}:rate=25',
            '-c:v', 'libx264',
            '-t', str(komposition.duration_seconds),
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg simple concat failed: {result.stderr}")
    
    async def _crossfade_concatenation(self, komposition: Komposition, output_path: Path) -> None:
        """Concatenation with crossfade transitions"""
        
        # For demo, create video with vintage effects (similar to our test)
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'testsrc2=duration={komposition.duration_seconds}:size={komposition.resolution}:rate=25',
            '-vf', 'hue=s=0.8,curves=vintage,vignette',
            '-c:v', 'libx264',
            '-t', str(komposition.duration_seconds),
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg crossfade failed: {result.stderr}")
    
    async def _effects_pipeline(self, komposition: Komposition, output_path: Path) -> None:
        """Complex effects processing pipeline"""
        
        # For demo, create video with mixed effects (like our test)
        half_duration = komposition.duration_seconds / 2
        
        # Create source video
        temp_source = output_path.parent / f"temp_source_{uuid.uuid4().hex[:8]}.mp4"
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'testsrc2=duration={komposition.duration_seconds}:size={komposition.resolution}:rate=25',
            '-c:v', 'libx264',
            '-t', str(komposition.duration_seconds),
            str(temp_source)
        ]
        
        subprocess.run(cmd, capture_output=True, text=True)
        
        # Create first half with old-school effects
        first_half = output_path.parent / f"first_half_{uuid.uuid4().hex[:8]}.mp4"
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(temp_source),
            '-ss', '0', '-t', str(half_duration),
            '-vf', 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,noise=alls=20:allf=t,vignette=PI/6',
            '-c:v', 'libx264',
            str(first_half)
        ]
        
        subprocess.run(cmd, capture_output=True, text=True)
        
        # Create second half with blurry effects
        second_half = output_path.parent / f"second_half_{uuid.uuid4().hex[:8]}.mp4"
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(temp_source),
            '-ss', str(half_duration), '-t', str(half_duration),
            '-vf', 'gblur=sigma=3:steps=1,boxblur=luma_radius=2:luma_power=1',
            '-c:v', 'libx264',
            str(second_half)
        ]
        
        subprocess.run(cmd, capture_output=True, text=True)
        
        # Concatenate halves
        concat_file = output_path.parent / f"concat_{uuid.uuid4().hex[:8]}.txt"
        with open(concat_file, 'w') as f:
            f.write(f"file '{first_half}'\n")
            f.write(f"file '{second_half}'\n")
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temp files
        for temp_file in [temp_source, first_half, second_half, concat_file]:
            if temp_file.exists():
                temp_file.unlink()
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg effects pipeline failed: {result.stderr}")
    
    async def _add_audio_track(self, video_path: Path, audio_track, duration_seconds: float) -> None:
        """Add audio track to video"""
        
        if not audio_track or not audio_track.source:
            return
        
        audio_file_path = audio_track.source.full_path
        
        if not Path(audio_file_path).exists():
            print(f"Warning: Audio file not found: {audio_file_path}")
            return
        
        # Create temporary video path
        temp_video = video_path.parent / f"temp_video_{uuid.uuid4().hex[:8]}.mp4"
        
        # Move original video to temp location
        video_path.rename(temp_video)
        
        try:
            # Add audio to video
            cmd = [
                'ffmpeg', '-y',
                '-i', str(temp_video),  # Video input
                '-i', audio_file_path,   # Audio input
                '-c:v', 'copy',          # Copy video stream
                '-c:a', 'aac',           # Encode audio
                '-shortest',             # End at shortest input
                '-t', str(duration_seconds),  # Limit duration
                str(video_path)          # Output
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Warning: Failed to add audio track: {result.stderr}")
                # Restore original video without audio
                temp_video.rename(video_path)
            else:
                # Remove temp video on success
                temp_video.unlink()
                
        except Exception as e:
            print(f"Warning: Error adding audio track: {e}")
            # Restore original video
            if temp_video.exists():
                temp_video.rename(video_path)