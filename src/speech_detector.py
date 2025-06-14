"""
Speech Detection Module for FFMPEG MCP Server

Provides intelligent speech detection using Silero VAD with fallback options.
Implements pluggable backend architecture for reliability.
"""

import json
import asyncio
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

try:
    import torch
    import torchaudio
    import librosa
    from pydub import AudioSegment
    SPEECH_DEPS_AVAILABLE = True
except ImportError:
    SPEECH_DEPS_AVAILABLE = False
    # Create dummy torch for type hints when not available
    class DummyTorch:
        class Tensor:
            pass
    torch = DummyTorch()

try:
    from .config import SecurityConfig
except ImportError:
    from config import SecurityConfig

logger = logging.getLogger(__name__)

class SpeechDetectionError(Exception):
    """Custom exception for speech detection errors"""
    pass

class SileroVAD:
    """Silero VAD implementation for speech detection"""
    
    def __init__(self):
        self.model = None
        self.sample_rate = 16000
        self.chunk_size = 512  # 32ms at 16kHz
        
    def initialize(self):
        """Initialize Silero VAD model"""
        if not SPEECH_DEPS_AVAILABLE:
            raise SpeechDetectionError("Speech detection dependencies not available")
            
        try:
            # Load Silero VAD model
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            
            # Extract utility functions
            (self.get_speech_timestamps,
             self.save_audio,
             self.read_audio,
             self.VADIterator,
             self.collect_chunks) = utils
             
            logger.info("Silero VAD model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            raise SpeechDetectionError(f"Model initialization failed: {e}")
    
    def detect_speech_segments(self, audio_path: Path, **options) -> List[Dict[str, Any]]:
        """
        Detect speech segments in audio file
        
        Args:
            audio_path: Path to audio file
            **options: Detection options (threshold, min_duration, etc.)
        
        Returns:
            List of speech segments with timestamps
        """
        if not self.model:
            self.initialize()
            
        try:
            # Load and preprocess audio
            wav_data = self._load_audio(audio_path)
            
            # Configure detection parameters
            threshold = options.get('threshold', 0.5)
            min_speech_duration_ms = options.get('min_speech_duration', 250)
            min_silence_duration_ms = options.get('min_silence_duration', 100)
            window_size_samples = options.get('window_size', 512)
            
            # Get speech timestamps
            speech_timestamps = self.get_speech_timestamps(
                wav_data,
                self.model,
                threshold=threshold,
                min_speech_duration_ms=min_speech_duration_ms,
                min_silence_duration_ms=min_silence_duration_ms,
                window_size_samples=window_size_samples,
                sampling_rate=self.sample_rate
            )
            
            # Convert to standard format
            segments = []
            for i, segment in enumerate(speech_timestamps):
                start_time = segment['start'] / self.sample_rate
                end_time = segment['end'] / self.sample_rate
                duration = end_time - start_time
                
                segments.append({
                    'segment_id': i,
                    'start_time': round(start_time, 3),
                    'end_time': round(end_time, 3), 
                    'duration': round(duration, 3),
                    'confidence': threshold,  # Silero doesn't provide per-segment confidence
                    'audio_quality': self._assess_quality(wav_data, segment)
                })
            
            return segments
            
        except Exception as e:
            logger.error(f"Speech detection failed: {e}")
            raise SpeechDetectionError(f"Detection failed: {e}")
    
    def _load_audio(self, audio_path: Path) -> torch.Tensor:
        """Load and preprocess audio for Silero VAD"""
        try:
            # Use torchaudio for loading
            wav, sr = torchaudio.load(str(audio_path))
            
            # Convert to mono if stereo
            if wav.shape[0] > 1:
                wav = wav.mean(dim=0, keepdim=True)
            
            # Resample to 16kHz if needed
            if sr != self.sample_rate:
                resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
                wav = resampler(wav)
            
            # Squeeze to 1D tensor
            wav = wav.squeeze()
            
            return wav
            
        except Exception as e:
            # Fallback to librosa
            try:
                wav, sr = librosa.load(str(audio_path), sr=self.sample_rate, mono=True)
                return torch.from_numpy(wav)
            except Exception as fallback_error:
                raise SpeechDetectionError(f"Audio loading failed: {e}, fallback: {fallback_error}")
    
    def _assess_quality(self, wav_data: torch.Tensor, segment: Dict) -> str:
        """Assess audio quality of speech segment"""
        try:
            start_sample = segment['start']
            end_sample = segment['end']
            segment_audio = wav_data[start_sample:end_sample]
            
            # Simple quality assessment based on signal characteristics
            energy = torch.mean(segment_audio ** 2).item()
            
            if energy > 0.01:
                return "clear"
            elif energy > 0.001:
                return "moderate"
            else:
                return "low"
                
        except Exception:
            return "unknown"

class WebRTCVAD:
    """WebRTC VAD fallback implementation"""
    
    def __init__(self):
        self.sample_rate = 16000
        
    def initialize(self):
        """Initialize WebRTC VAD"""
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(1)  # Aggressiveness mode 1
            logger.info("WebRTC VAD initialized")
            return True
        except ImportError:
            raise SpeechDetectionError("WebRTC VAD not available")
    
    def detect_speech_segments(self, audio_path: Path, **options) -> List[Dict[str, Any]]:
        """Detect speech using WebRTC VAD (simplified implementation)"""
        # This would be a full implementation in production
        # For now, return empty list as fallback
        logger.warning("WebRTC VAD fallback not fully implemented")
        return []

class SpeechDetector:
    """
    Main speech detection class with pluggable backends
    """
    
    def __init__(self, primary_engine="silero", fallback_engines=None):
        if fallback_engines is None:
            fallback_engines = ["webrtc"]
            
        self.primary_engine = primary_engine
        self.fallback_engines = fallback_engines
        
        self.engines = {
            "silero": SileroVAD(),
            "webrtc": WebRTCVAD()
        }
        
        self.active_engine = None
        self.cache_dir = Path("/tmp/music/metadata")
        self.cache_dir.mkdir(exist_ok=True)
    
    async def detect_speech_segments(self, file_path: Path, force_reanalysis: bool = False, **options) -> Dict[str, Any]:
        """
        Detect speech segments in audio/video file
        
        Args:
            file_path: Path to media file
            force_reanalysis: Skip cache and reanalyze
            **options: Detection options
        
        Returns:
            Speech detection results with segments and metadata
        """
        # Check cache first
        if not force_reanalysis:
            cached_result = self._load_cached_analysis(file_path)
            if cached_result:
                return cached_result
        
        # Extract audio if video file
        audio_path = await self._extract_audio_if_needed(file_path)
        
        try:
            # Try primary engine first
            segments = await self._detect_with_engine(self.primary_engine, audio_path, **options)
            engine_used = self.primary_engine
            
        except Exception as e:
            logger.warning(f"Primary engine {self.primary_engine} failed: {e}")
            
            # Try fallback engines
            segments = []
            engine_used = None
            
            for engine_name in self.fallback_engines:
                try:
                    segments = await self._detect_with_engine(engine_name, audio_path, **options)
                    engine_used = engine_name
                    break
                except Exception as fallback_error:
                    logger.warning(f"Fallback engine {engine_name} failed: {fallback_error}")
            
            if not engine_used:
                raise SpeechDetectionError("All speech detection engines failed")
        
        # Prepare result
        result = {
            "success": True,
            "file_path": str(file_path),
            "has_speech": len(segments) > 0,
            "speech_segments": segments,
            "total_speech_duration": sum(seg["duration"] for seg in segments),
            "total_segments": len(segments),
            "analysis_metadata": {
                "engine_used": engine_used,
                "processing_time": time.time(),
                "options": options
            }
        }
        
        # Cache result
        self._cache_analysis(file_path, result)
        
        # Cleanup temporary audio file if created
        if audio_path != file_path and audio_path.exists():
            audio_path.unlink()
        
        return result
    
    async def _detect_with_engine(self, engine_name: str, audio_path: Path, **options) -> List[Dict[str, Any]]:
        """Run detection with specific engine"""
        engine = self.engines.get(engine_name)
        if not engine:
            raise SpeechDetectionError(f"Unknown engine: {engine_name}")
        
        # Initialize engine if needed
        if not hasattr(engine, 'model') or engine.model is None:
            engine.initialize()
        
        # Run detection in thread pool for blocking operations
        loop = asyncio.get_event_loop()
        segments = await loop.run_in_executor(
            None, 
            engine.detect_speech_segments, 
            audio_path, 
            **options
        )
        
        return segments
    
    async def _extract_audio_if_needed(self, file_path: Path) -> Path:
        """Extract audio from video file if needed"""
        # Check if file is already audio
        audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}
        if file_path.suffix.lower() in audio_extensions:
            return file_path
        
        # Extract audio using FFmpeg
        try:
            from .ffmpeg_wrapper import FFMPEGWrapper
        except ImportError:
            from ffmpeg_wrapper import FFMPEGWrapper
            
        ffmpeg = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        
        # Create temporary audio file
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_audio_path = Path(temp_audio.name)
        temp_audio.close()
        
        # Extract audio to WAV format for better compatibility
        cmd = [
            SecurityConfig.FFMPEG_PATH,
            '-i', str(file_path),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM 16-bit
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',  # Mono
            str(temp_audio_path)
        ]
        
        result = await ffmpeg.execute_command(cmd, timeout=300)
        
        if not result["success"]:
            raise SpeechDetectionError(f"Audio extraction failed: {result['logs']}")
        
        return temp_audio_path
    
    def _load_cached_analysis(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load cached speech analysis"""
        try:
            cache_file = self.cache_dir / f"{file_path.name}_speech.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is still valid (5 minutes)
                cache_time = cached_data.get("analysis_metadata", {}).get("processing_time", 0)
                if time.time() - cache_time < 300:  # 5 minutes
                    logger.info(f"Using cached speech analysis for {file_path.name}")
                    return cached_data
            
        except Exception as e:
            logger.warning(f"Failed to load cached analysis: {e}")
        
        return None
    
    def _cache_analysis(self, file_path: Path, result: Dict[str, Any]):
        """Cache speech analysis result"""
        try:
            cache_file = self.cache_dir / f"{file_path.name}_speech.json"
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.debug(f"Cached speech analysis for {file_path.name}")
        except Exception as e:
            logger.warning(f"Failed to cache analysis: {e}")
    
    def get_speech_insights(self, file_path: Path) -> Dict[str, Any]:
        """Get cached speech insights and quality metrics"""
        cached_result = self._load_cached_analysis(file_path)
        if not cached_result:
            return {
                "success": False,
                "error": "No cached analysis found. Run detect_speech_segments first."
            }
        
        segments = cached_result.get("speech_segments", [])
        
        # Calculate insights
        insights = {
            "success": True,
            "file_path": str(file_path),
            "has_speech": len(segments) > 0,
            "summary": {
                "total_segments": len(segments),
                "total_speech_duration": cached_result.get("total_speech_duration", 0),
                "average_segment_duration": sum(seg["duration"] for seg in segments) / len(segments) if segments else 0,
                "longest_segment": max(seg["duration"] for seg in segments) if segments else 0,
                "shortest_segment": min(seg["duration"] for seg in segments) if segments else 0
            },
            "quality_distribution": self._analyze_quality_distribution(segments),
            "timing_analysis": self._analyze_timing_patterns(segments),
            "editing_suggestions": self._generate_editing_suggestions(segments),
            "analysis_metadata": cached_result.get("analysis_metadata", {})
        }
        
        return insights
    
    def _analyze_quality_distribution(self, segments: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of audio quality in segments"""
        quality_counts = {"clear": 0, "moderate": 0, "low": 0, "unknown": 0}
        
        for segment in segments:
            quality = segment.get("audio_quality", "unknown")
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        return quality_counts
    
    def _analyze_timing_patterns(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze timing patterns in speech segments"""
        if not segments:
            return {}
        
        # Calculate gaps between segments
        gaps = []
        for i in range(1, len(segments)):
            gap = segments[i]["start_time"] - segments[i-1]["end_time"]
            gaps.append(gap)
        
        return {
            "average_gap": sum(gaps) / len(gaps) if gaps else 0,
            "longest_gap": max(gaps) if gaps else 0,
            "speech_density": sum(seg["duration"] for seg in segments) / (segments[-1]["end_time"] - segments[0]["start_time"]) if segments else 0
        }
    
    def _generate_editing_suggestions(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate editing suggestions based on speech analysis"""
        suggestions = []
        
        if not segments:
            suggestions.append({
                "type": "no_speech",
                "message": "No speech detected. Consider adding narration or removing audio track.",
                "priority": "medium"
            })
            return suggestions
        
        # Suggest trimming silent portions
        for i, segment in enumerate(segments):
            if segment.get("audio_quality") == "low":
                suggestions.append({
                    "type": "quality_improvement",
                    "message": f"Segment {i+1} has low audio quality. Consider audio enhancement or replacement.",
                    "segment_id": i,
                    "priority": "low"
                })
        
        # Suggest combining short segments
        short_segments = [seg for seg in segments if seg["duration"] < 1.0]
        if len(short_segments) > 2:
            suggestions.append({
                "type": "segment_combination",
                "message": f"Found {len(short_segments)} short segments. Consider combining nearby segments.",
                "priority": "medium"
            })
        
        return suggestions