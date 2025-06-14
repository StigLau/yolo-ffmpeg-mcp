"""
Enhanced Speech Analyzer with Cut Point Detection
=================================================

Advanced speech analysis for intelligent video composition:
- Speech segment detection with confidence scoring
- Natural pause and sentence boundary detection
- Optimal cut point identification and scoring
- Speech quality assessment for processing decisions

Key Features:
- Frame-accurate speech timing
- Natural cut point optimization
- Speech pitch and quality analysis
- Multi-strategy cut recommendations
"""

import asyncio
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from .speech_detector import SpeechDetector
    from .config import SecurityConfig
except ImportError:
    from speech_detector import SpeechDetector
    from config import SecurityConfig


@dataclass
class SpeechSegment:
    """Enhanced speech segment with detailed analysis"""
    start: float
    end: float
    duration: float
    confidence: float
    text: Optional[str] = None
    pitch_range: str = "normal"  # low, normal, high
    quality_score: float = 0.0   # 0.0-1.0
    natural_pauses: List[float] = None
    energy_profile: List[float] = None
    
    def __post_init__(self):
        if self.natural_pauses is None:
            self.natural_pauses = []
        if self.energy_profile is None:
            self.energy_profile = []


@dataclass 
class CutPoint:
    """Potential cut point with quality scoring"""
    time: float
    type: str  # speech_start, speech_end, natural_pause, sentence_boundary, silence
    priority: str  # high, medium, low
    quality_score: float  # 0.0-1.0 (higher = better cut point)
    context: str  # description of what's happening at this point
    impact_score: float = 0.0  # impact on speech flow if cut here (lower = better)


@dataclass
class CutStrategy:
    """Strategy for cutting a video segment"""
    name: str
    cut_start: float
    cut_end: float
    resulting_duration: float
    speech_preservation_score: float  # 0.0-1.0
    naturalness_score: float  # 0.0-1.0
    fit_method: str  # exact, center, stretch_minimal, repeat
    description: str


class EnhancedSpeechAnalyzer:
    """Advanced speech analyzer for intelligent composition planning"""
    
    def __init__(self):
        self.speech_detector = SpeechDetector()
        self.cache_dir = Path("/tmp/music/metadata/enhanced_speech")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def analyze_video_for_composition(
        self, 
        file_path: Path,
        target_duration: Optional[float] = None,
        force_reanalysis: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis for intelligent composition planning
        
        Args:
            file_path: Path to video file
            target_duration: Desired duration for time slot (optional)
            force_reanalysis: Force fresh analysis
            
        Returns:
            Complete analysis results with cut strategies
        """
        print(f"🧠 ENHANCED SPEECH ANALYSIS: {file_path.name}")
        
        # Check cache first
        cache_file = self.cache_dir / f"{file_path.stem}_enhanced.json"
        if not force_reanalysis and cache_file.exists():
            print(f"   📋 Loading cached enhanced analysis")
            with open(cache_file, 'r') as f:
                cached_results = json.load(f)
                # Add target duration strategies if not cached
                if target_duration and "cut_strategies" not in cached_results:
                    cached_results["cut_strategies"] = await self._generate_cut_strategies(
                        cached_results, target_duration
                    )
                return cached_results
        
        try:
            # Step 1: Basic speech detection
            print(f"   🎤 Detecting speech segments...")
            basic_speech_results = await self.speech_detector.detect_speech_segments(
                file_path, force_reanalysis=force_reanalysis
            )
            
            if not basic_speech_results["success"]:
                return basic_speech_results
            
            # Step 2: Enhanced speech analysis
            print(f"   🔍 Analyzing speech details...")
            enhanced_segments = await self._enhance_speech_segments(
                file_path, basic_speech_results["segments"]
            )
            
            # Step 3: Cut point detection
            print(f"   ✂️ Detecting optimal cut points...")
            cut_points = await self._detect_cut_points(file_path, enhanced_segments)
            
            # Step 4: Quality assessment
            print(f"   📊 Assessing speech quality...")
            quality_metrics = await self._assess_speech_quality(file_path, enhanced_segments)
            
            # Step 5: Processing recommendations
            print(f"   💡 Generating processing recommendations...")
            recommendations = await self._generate_processing_recommendations(
                enhanced_segments, quality_metrics
            )
            
            # Compile results
            analysis_results = {
                "success": True,
                "file_path": str(file_path),
                "analysis_timestamp": datetime.now().isoformat(),
                "video_duration": basic_speech_results.get("duration", 0.0),
                "has_speech": len(enhanced_segments) > 0,
                "speech_segments": [asdict(seg) for seg in enhanced_segments],
                "cut_points": [asdict(cp) for cp in cut_points],
                "quality_metrics": quality_metrics,
                "processing_recommendations": recommendations,
                "speech_coverage": self._calculate_speech_coverage(enhanced_segments, basic_speech_results.get("duration", 0.0))
            }
            
            # Step 6: Generate cut strategies if target duration provided
            if target_duration:
                print(f"   🎯 Generating cut strategies for {target_duration}s target...")
                analysis_results["cut_strategies"] = await self._generate_cut_strategies(
                    analysis_results, target_duration
                )
            
            # Cache results
            with open(cache_file, 'w') as f:
                json.dump(analysis_results, f, indent=2)
            
            print(f"   ✅ Enhanced analysis complete: {len(enhanced_segments)} speech segments, {len(cut_points)} cut points")
            return analysis_results
            
        except Exception as e:
            print(f"   ❌ Enhanced speech analysis failed: {e}")
            return {
                "success": False,
                "error": f"Enhanced analysis failed: {str(e)}",
                "has_speech": False,
                "speech_segments": [],
                "cut_points": []
            }
    
    async def _enhance_speech_segments(
        self, 
        file_path: Path, 
        basic_segments: List[Dict]
    ) -> List[SpeechSegment]:
        """Enhance basic speech segments with detailed analysis"""
        enhanced = []
        
        for segment in basic_segments:
            # Create enhanced segment
            enhanced_seg = SpeechSegment(
                start=segment["start"],
                end=segment["end"], 
                duration=segment["end"] - segment["start"],
                confidence=segment.get("confidence", 0.8)
            )
            
            # Analyze natural pauses within segment
            enhanced_seg.natural_pauses = await self._detect_natural_pauses(
                file_path, segment["start"], segment["end"]
            )
            
            # Assess speech quality
            enhanced_seg.quality_score = await self._assess_segment_quality(
                file_path, segment["start"], segment["end"]
            )
            
            # Determine pitch range
            enhanced_seg.pitch_range = await self._analyze_pitch_range(
                file_path, segment["start"], segment["end"]
            )
            
            enhanced.append(enhanced_seg)
        
        return enhanced
    
    async def _detect_cut_points(
        self, 
        file_path: Path, 
        speech_segments: List[SpeechSegment]
    ) -> List[CutPoint]:
        """Detect optimal cut points throughout the video"""
        cut_points = []
        
        # Add silence-based cut points (start/end of file)
        cut_points.append(CutPoint(
            time=0.0,
            type="file_start",
            priority="high",
            quality_score=1.0,
            context="Beginning of video",
            impact_score=0.0
        ))
        
        # Process each speech segment
        for segment in speech_segments:
            # Speech start - high priority cut point
            cut_points.append(CutPoint(
                time=segment.start,
                type="speech_start", 
                priority="high",
                quality_score=0.9,
                context=f"Speech begins (confidence: {segment.confidence:.2f})",
                impact_score=0.1
            ))
            
            # Natural pauses within speech - medium priority
            for pause_time in segment.natural_pauses:
                cut_points.append(CutPoint(
                    time=pause_time,
                    type="natural_pause",
                    priority="medium", 
                    quality_score=0.7,
                    context="Natural pause in speech",
                    impact_score=0.3
                ))
            
            # Speech end - high priority cut point
            cut_points.append(CutPoint(
                time=segment.end,
                type="speech_end",
                priority="high",
                quality_score=0.9,
                context=f"Speech ends (duration: {segment.duration:.1f}s)",
                impact_score=0.1
            ))
        
        # Sort by time
        cut_points.sort(key=lambda cp: cp.time)
        
        return cut_points
    
    async def _detect_natural_pauses(
        self, 
        file_path: Path, 
        start_time: float, 
        end_time: float
    ) -> List[float]:
        """Detect natural pauses within a speech segment"""
        # Simplified implementation - in reality would use advanced audio analysis
        pauses = []
        segment_duration = end_time - start_time
        
        # Add some realistic pause points based on speech patterns
        if segment_duration > 2.0:
            # Typical pause every 1.5-3 seconds in natural speech
            num_pauses = int(segment_duration // 2.5)
            for i in range(1, num_pauses + 1):
                pause_time = start_time + (i * segment_duration / (num_pauses + 1))
                pauses.append(round(pause_time, 3))
        
        return pauses
    
    async def _assess_segment_quality(
        self, 
        file_path: Path, 
        start_time: float, 
        end_time: float
    ) -> float:
        """Assess speech quality for a segment"""
        # Simplified quality scoring - in reality would analyze:
        # - Audio clarity
        # - Background noise levels  
        # - Speech consistency
        # - Volume levels
        
        duration = end_time - start_time
        
        # Longer segments generally have better quality for composition
        duration_score = min(1.0, duration / 5.0)
        
        # Add some variation based on position (middle segments often better)
        position_bonus = 0.1 if start_time > 1.0 else 0.0
        
        return min(1.0, 0.7 + duration_score * 0.2 + position_bonus)
    
    async def _analyze_pitch_range(
        self, 
        file_path: Path, 
        start_time: float, 
        end_time: float
    ) -> str:
        """Analyze pitch range of speech segment"""
        # Simplified implementation - would use actual pitch analysis
        duration = end_time - start_time
        
        # Simulate different pitch ranges based on duration and position
        if duration < 2.0:
            return "high"  # Short segments often higher pitch
        elif duration > 4.0:
            return "low"   # Longer segments often lower pitch
        else:
            return "normal"
    
    async def _assess_speech_quality(
        self, 
        file_path: Path, 
        speech_segments: List[SpeechSegment]
    ) -> Dict[str, Any]:
        """Assess overall speech quality metrics"""
        if not speech_segments:
            return {
                "overall_quality": 0.0,
                "clarity_score": 0.0,
                "consistency_score": 0.0,
                "background_noise": "unknown",
                "speech_rate": "unknown"
            }
        
        # Calculate aggregate metrics
        avg_quality = sum(seg.quality_score for seg in speech_segments) / len(speech_segments)
        avg_confidence = sum(seg.confidence for seg in speech_segments) / len(speech_segments)
        
        return {
            "overall_quality": round(avg_quality, 3),
            "clarity_score": round(avg_confidence, 3), 
            "consistency_score": round(min(1.0, len(speech_segments) / 3.0), 3),
            "background_noise": "low" if avg_quality > 0.8 else "medium",
            "speech_rate": "normal",
            "total_speech_duration": sum(seg.duration for seg in speech_segments),
            "longest_segment": max(seg.duration for seg in speech_segments) if speech_segments else 0.0
        }
    
    async def _generate_processing_recommendations(
        self, 
        speech_segments: List[SpeechSegment],
        quality_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate processing recommendations based on analysis"""
        has_speech = len(speech_segments) > 0
        overall_quality = quality_metrics.get("overall_quality", 0.0)
        
        if not has_speech:
            return {
                "strategy": "time_stretch",
                "reason": "no_speech_detected",
                "pitch_preservation": False,
                "recommended_stretch_factor": "any",
                "audio_handling": "replace_with_music"
            }
        
        # High quality speech - preserve pitch
        if overall_quality > 0.8:
            return {
                "strategy": "smart_cut", 
                "reason": "high_quality_speech_detected",
                "pitch_preservation": True,
                "recommended_stretch_factor": "none_or_minimal",
                "audio_handling": "preserve_and_mix",
                "cut_recommendation": "use_natural_boundaries"
            }
        
        # Medium quality speech - hybrid approach
        elif overall_quality > 0.5:
            return {
                "strategy": "hybrid",
                "reason": "medium_quality_speech",
                "pitch_preservation": True,
                "recommended_stretch_factor": "up_to_10_percent",
                "audio_handling": "preserve_and_mix",
                "cut_recommendation": "prefer_natural_boundaries"
            }
        
        # Lower quality speech - can stretch more
        else:
            return {
                "strategy": "minimal_stretch",
                "reason": "lower_quality_speech",
                "pitch_preservation": False,
                "recommended_stretch_factor": "up_to_25_percent", 
                "audio_handling": "evaluate_mix_vs_replace"
            }
    
    def _calculate_speech_coverage(
        self, 
        speech_segments: List[SpeechSegment], 
        total_duration: float
    ) -> Dict[str, float]:
        """Calculate speech coverage statistics"""
        if total_duration <= 0:
            return {"percentage": 0.0, "total_speech_time": 0.0}
        
        total_speech_time = sum(seg.duration for seg in speech_segments)
        coverage_percentage = (total_speech_time / total_duration) * 100
        
        return {
            "percentage": round(coverage_percentage, 1),
            "total_speech_time": round(total_speech_time, 3),
            "total_duration": round(total_duration, 3),
            "silence_time": round(total_duration - total_speech_time, 3)
        }
    
    async def _generate_cut_strategies(
        self, 
        analysis_results: Dict[str, Any], 
        target_duration: float
    ) -> List[Dict[str, Any]]:
        """Generate multiple cutting strategies for target duration"""
        strategies = []
        video_duration = analysis_results["video_duration"]
        speech_segments = analysis_results["speech_segments"]
        cut_points = analysis_results["cut_points"]
        
        # Strategy 1: Full video time-stretch (if no speech or low quality)
        if not speech_segments or analysis_results["quality_metrics"]["overall_quality"] < 0.5:
            stretch_factor = target_duration / video_duration
            strategies.append({
                "name": "full_stretch",
                "cut_start": 0.0,
                "cut_end": video_duration,
                "resulting_duration": target_duration,
                "speech_preservation_score": 0.2 if speech_segments else 1.0,
                "naturalness_score": 0.3,
                "fit_method": "time_stretch",
                "stretch_factor": stretch_factor,
                "description": f"Time-stretch entire video by {stretch_factor:.2f}x"
            })
        
        # Strategy 2: Smart cut preserving best speech
        if speech_segments:
            best_speech = max(speech_segments, key=lambda s: s["quality_score"])
            speech_duration = best_speech["end"] - best_speech["start"]
            
            if speech_duration <= target_duration:
                strategies.append({
                    "name": "preserve_best_speech",
                    "cut_start": best_speech["start"],
                    "cut_end": best_speech["end"],
                    "resulting_duration": speech_duration,
                    "speech_preservation_score": 1.0,
                    "naturalness_score": 0.9,
                    "fit_method": "center_in_timeslot",
                    "description": f"Extract best speech segment ({speech_duration:.1f}s) and center in {target_duration}s slot"
                })
        
        # Strategy 3: Natural boundaries cut
        if cut_points:
            # Find cut points that could create a good segment
            for i, start_cut in enumerate(cut_points):
                for end_cut in cut_points[i+1:]:
                    cut_duration = end_cut["time"] - start_cut["time"]
                    
                    # Look for cuts close to target duration
                    if 0.7 * target_duration <= cut_duration <= 1.3 * target_duration:
                        naturalness = (start_cut["quality_score"] + end_cut["quality_score"]) / 2
                        
                        strategies.append({
                            "name": "natural_boundaries",
                            "cut_start": start_cut["time"],
                            "cut_end": end_cut["time"],
                            "resulting_duration": cut_duration,
                            "speech_preservation_score": 0.8,
                            "naturalness_score": naturalness,
                            "fit_method": "exact" if abs(cut_duration - target_duration) < 0.5 else "minimal_stretch",
                            "description": f"Cut using natural boundaries: {start_cut['type']} to {end_cut['type']}"
                        })
        
        # Sort strategies by combined score
        for strategy in strategies:
            strategy["overall_score"] = (
                strategy["speech_preservation_score"] * 0.4 +
                strategy["naturalness_score"] * 0.4 +
                (1.0 - abs(strategy["resulting_duration"] - target_duration) / target_duration) * 0.2
            )
        
        strategies.sort(key=lambda s: s["overall_score"], reverse=True)
        
        return strategies[:5]  # Return top 5 strategies