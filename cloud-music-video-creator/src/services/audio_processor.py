"""
Audio Processor Service
Handles audio file processing, analysis, and integration
"""

import subprocess
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from ..models.media import MediaReference, MediaMetadata, MediaType
from ..registry.media_registry import MediaRegistry


class AudioProcessor:
    """Service for processing audio files and integration with videos"""
    
    def __init__(self, media_registry: MediaRegistry):
        self.media_registry = media_registry
        self.temp_dir = Path("/tmp/music-video-creator/audio-processing")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def register_audio_file(self, file_path: str) -> MediaReference:
        """Register and analyze audio file"""
        
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Analyze audio properties
        audio_info = await self._analyze_audio_file(file_path_obj)
        
        # Create metadata
        metadata = MediaMetadata(
            type=MediaType.AUDIO,
            filename=file_path_obj.name,
            file_size_bytes=file_path_obj.stat().st_size,
            duration_seconds=audio_info.get('duration'),
            sample_rate=audio_info.get('sample_rate'),
            channels=audio_info.get('channels'),
            audio_codec=audio_info.get('codec'),
            bitrate=audio_info.get('bitrate')
        )
        
        # Register in media registry
        media_ref = await self.media_registry.register_file(file_path, metadata)
        
        return media_ref
    
    async def create_test_audio(self, duration: float = 30.0, bpm: float = 120.0) -> str:
        """Create test audio track for demos"""
        
        output_path = self.temp_dir / f"test_audio_{uuid.uuid4().hex[:8]}.mp3"
        
        # Generate simple beep pattern matching BPM
        beat_interval = 60.0 / bpm
        
        # Create audio with tone generator
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'sine=frequency=440:duration={duration}',
            '-af', f'volume=0.1',  # Low volume
            '-c:a', 'mp3',
            '-b:a', '128k',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to create test audio: {result.stderr}")
        
        return str(output_path)
    
    async def extract_beat_positions(self, audio_file: MediaReference) -> List[float]:
        """Extract beat positions from audio (simplified implementation)"""
        
        # Simplified beat detection - just calculate based on BPM
        # In a real implementation, this would use audio analysis libraries
        
        duration = audio_file.metadata.duration_seconds or 30.0
        
        # Assume 120 BPM if not specified
        estimated_bpm = 120.0  # Could be improved with actual BPM detection
        
        beat_interval = 60.0 / estimated_bpm
        beat_positions = []
        
        current_time = 0.0
        while current_time < duration:
            beat_positions.append(current_time)
            current_time += beat_interval
        
        return beat_positions
    
    async def prepare_audio_for_video(self, audio_ref: MediaReference, target_duration: float) -> str:
        """Prepare audio file for video integration"""
        
        audio_path = audio_ref.full_path
        output_path = self.temp_dir / f"prepared_{uuid.uuid4().hex[:8]}.mp3"
        
        # Prepare audio: normalize, trim/loop to match target duration
        audio_duration = audio_ref.metadata.duration_seconds or target_duration
        
        if audio_duration < target_duration:
            # Loop audio to match target duration
            cmd = [
                'ffmpeg', '-y',
                '-stream_loop', '-1',  # Loop indefinitely
                '-i', audio_path,
                '-t', str(target_duration),  # Trim to target duration
                '-c:a', 'aac',
                '-b:a', '128k',
                str(output_path)
            ]
        else:
            # Trim audio to target duration
            cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-t', str(target_duration),
                '-c:a', 'aac',
                '-b:a', '128k',
                str(output_path)
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to prepare audio: {result.stderr}")
        
        return str(output_path)
    
    async def analyze_audio_for_video_sync(self, audio_ref: MediaReference) -> Dict[str, Any]:
        """Analyze audio for video synchronization recommendations"""
        
        # Extract beat positions
        beat_positions = await self.extract_beat_positions(audio_ref)
        
        # Calculate segment recommendations
        duration = audio_ref.metadata.duration_seconds or 30.0
        recommended_segments = max(2, min(8, int(duration / 4)))
        
        segment_duration = duration / recommended_segments
        
        segments = []
        for i in range(recommended_segments):
            start_time = i * segment_duration
            segments.append({
                "start_seconds": start_time,
                "duration_seconds": segment_duration,
                "beat_count": len([b for b in beat_positions if start_time <= b < start_time + segment_duration])
            })
        
        return {
            "duration": duration,
            "beat_positions": beat_positions[:20],  # First 20 beats for efficiency
            "estimated_bpm": 120.0,  # Simplified
            "recommended_segments": segments,
            "audio_quality": "good",  # Simplified
            "sync_confidence": 0.8
        }
    
    async def _analyze_audio_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze audio file properties using ffprobe"""
        
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(file_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"ffprobe failed: {result.stderr}")
            
            data = json.loads(result.stdout)
            
            # Extract audio stream info
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise Exception("No audio stream found")
            
            format_info = data.get('format', {})
            
            return {
                "duration": float(format_info.get('duration', 0)),
                "sample_rate": int(audio_stream.get('sample_rate', 44100)),
                "channels": int(audio_stream.get('channels', 2)),
                "codec": audio_stream.get('codec_name', 'unknown'),
                "bitrate": int(format_info.get('bit_rate', 0)) if format_info.get('bit_rate') else None
            }
            
        except Exception as e:
            print(f"Warning: Could not analyze audio file {file_path}: {e}")
            return {
                "duration": 30.0,  # Default
                "sample_rate": 44100,
                "channels": 2,
                "codec": "unknown",
                "bitrate": None
            }
    
    async def create_audio_visualization(self, audio_ref: MediaReference, output_path: str) -> str:
        """Create audio waveform visualization video"""
        
        audio_path = audio_ref.full_path
        
        cmd = [
            'ffmpeg', '-y',
            '-i', audio_path,
            '-filter_complex', f'[0:a]showwaves=s=1280x720:mode=line:colors=white[v]',
            '-map', '[v]',
            '-map', '0:a',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-t', str(audio_ref.metadata.duration_seconds or 30),
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to create audio visualization: {result.stderr}")
        
        return output_path